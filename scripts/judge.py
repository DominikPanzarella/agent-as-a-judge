"""The judge: GPT-6 Luna says whether a method does what its docstring says.

It sees the class skeleton, the methods written before and the new one, never the tests, which
only give the grade. It answers in JSON with a reason and a verdict, OK or NOT OK. Judge v1 only
reads the code; v2 can also run Python up to 5 times on the class written so far. v3, v4 and v5
are v2 with one more paragraph, the prompt variants tried on the pilot classes (11 November): v3
judges only what the docstring asks, v4 sorts each problem by kind and fails only the serious
ones, v5 tries every behaviour the docstring describes. v6 and v7 are v1 with the paragraph of v3
and of v4: the same two variants for the judge that only reads (12 November). All use the
Responses API, because Chat Completions does not accept tools with a reasoning effort for this
model.

Three options work with every version. With a memory (setup C3) the judge also reads its earlier
reviews of the same class. With --confidence it adds to the verdict how sure it is, from 0 to 100.
With --min-confidence a verdict below the threshold sends it to look again, at most twice.

Run as a script, it judges a finished run and compares the verdicts with the tests.

The defaults are the study's: judge v1 with medium effort.

    .venv/bin/python scripts/judge.py C0-9b --dry-run ClassEval_55
    .venv/bin/python scripts/judge.py C0-9b --all
    .venv/bin/python scripts/judge.py C0-9b --summary
    .venv/bin/python scripts/judge.py C0-9b --tag r2 --all                                # a repeat
    .venv/bin/python scripts/judge.py C0-9b --version v6 --all                            # a variant
    .venv/bin/python scripts/judge.py C0-9b --version v2 --confidence --tag conf --all    # the pilot of 12 November
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

import budget
import coder
import harness

ROOT = harness.ROOT
MODEL = "gpt-6-luna"
VERSIONS = ["v1", "v2", "v3", "v4", "v5", "v6", "v7"]
READ_ONLY = ("v1", "v6", "v7")  # these judges get no tool: they only read the code
EFFORTS = ["low", "medium"]  # the course allows low or medium reasoning effort
EFFORT = "medium"  # the study's; with "low", GPT-6 Luna used no reasoning tokens in the first test
MAX_RUNS = 5  # code runs that judge v2 may ask for on one method, and again on each new look
MAX_LOOKS = 2  # times an unsure judge is sent to look again at one method
OUTPUT_LIMIT = 2000  # characters of stdout and of stderr shown to the judge
# OpenAI does not return the cost of a request, so we compute it. Standard tier, dollars per
# million tokens, as OpenRouter lists it on 6 Nov 2026. The OpenAI dashboard has the real spend.
PRICE = {"input": 0.10, "cached_input": 0.01, "output": 0.50}

SYSTEM = (
    "You review Python code. A developer is writing a class one method at a time, and you check "
    "the method they have just written. Decide whether it does what its docstring says, given "
    "the rest of the class: the constructor, the fields and the other methods. Look for wrong "
    "results, exceptions, cases in the docstring that the code does not handle, and uses of "
    "fields or methods that the class does not have. Answer OK if the method is correct and "
    "NOT OK if you find a concrete problem. In the reason, say in one or two sentences what is "
    "wrong and how to fix it, or why the method is correct. The reason must explain the "
    "verdict: never write only OK or NOT OK there."
)

TOOLS_NOTE = (
    " You can run Python code with the tool run_python, at most " + str(MAX_RUNS) + " times. "
    "Use it to check the examples in the docstring and any case you doubt before you answer. "
    "The class is already defined when your code runs: call it directly and never copy or "
    "redefine it, or you would test your copy instead of the developer's code. "
    "When the reason says what the code returns or raises, it must be what you saw when you "
    "ran it, not what you expect."
)
SYSTEM_TOOLS = SYSTEM + TOOLS_NOTE

# The prompt variants, each added to v2. Each one targets an error of v2 on the pilot of the 9B.
# The first two need no tool, so v6 and v7 add them to v1.
# v3: the judge failed correct methods for checks or messages the docstring does not ask for
# (CodeJudge, Tong and Zhang 2024, found the same over-strict error handling).
SCOPE_NOTE = (
    " Judge only what the docstring and the rest of the class ask for. A check, a message or a "
    "behaviour that the docstring does not describe is not a problem: do not answer NOT OK for it."
)
# v4: CodeJudge's idea of sorting each problem by kind and severity, with a binary verdict.
SEVERITY_NOTE = (
    " Before the verdict, sort each problem you find into one kind. Serious: a wrong result or an "
    "exception on an input the docstring describes, a case named in the docstring that the code "
    "does not handle, a field or method the class does not have, incomplete code. Minor: missing "
    "error handling, an input the docstring does not mention, efficiency, style. Answer NOT OK only "
    "for a serious problem, and name its kind in the reason."
)
# v5: the judge passed wrong methods after trying only the docstring example.
PLAN_NOTE = (
    " Before you answer, run the examples of the docstring and at least one more case for each "
    "behaviour it describes: each branch, each special value it names, such as an empty input, a "
    "missing key or a limit, and the fields the method changes that other methods read. You can "
    "check several cases in one run."
)
INSTRUCTIONS = {"v1": SYSTEM, "v2": SYSTEM_TOOLS, "v3": SYSTEM_TOOLS + SCOPE_NOTE,
                "v4": SYSTEM_TOOLS + SEVERITY_NOTE, "v5": SYSTEM_TOOLS + PLAN_NOTE,
                "v6": SYSTEM + SCOPE_NOTE, "v7": SYSTEM + SEVERITY_NOTE}

# Structured output: the reply is always this JSON object. The reason comes first, so the
# verdict follows from it.
def verdict_format(reason, confidence=False):
    properties = {"reason": {"type": "string", "description": reason},
                  "verdict": {"type": "string", "enum": ["OK", "NOT OK"]}}
    if confidence:
        properties["confidence"] = {"type": "integer", "description": CONFIDENCE}
    return {
        "format": {
            "type": "json_schema",
            "name": "verdict",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": properties,
                "required": list(properties),
                "additionalProperties": False,
            },
        },
    }


# The confidence is only one more field of the answer, after the verdict: the instructions of
# the judge stay the same.
CONFIDENCE = "How sure you are that the verdict is right, from 0 (a guess) to 100 (certain)."
METHOD_REASON = ("One or two sentences: what is wrong and how to fix it, "
                 "or why the method is correct. Not the verdict alone.")
VERDICT_FORMAT = verdict_format(METHOD_REASON)
VERDICT_FORMAT_CONFIDENCE = verdict_format(METHOD_REASON, confidence=True)

RUN_PYTHON = {
    "type": "function",
    "name": "run_python",
    "description": (
        "Run Python code placed after the class definition and get back what it prints and any "
        "error. The class contains the method under review and the methods written so far; "
        "methods not written yet only return None. Do not redefine the class: it is already "
        "defined, so call it directly. Use print() to see values. Every run starts "
        "from scratch and stops after " + str(harness.TIMEOUT) + " seconds."
    ),
    "strict": True,
    "parameters": {
        "type": "object",
        "properties": {
            "code": {"type": "string",
                     "description": "Python code to run, for example: print(Stack().size())"},
        },
        "required": ["code"],
        "additionalProperties": False,
    },
}


def memory_line(name, review, rewritten):
    """One line of the judge's memory in setup C3: its review of an earlier method of the class."""
    line = f"- `{name}`: {review['verdict']}. {review['reason']}"
    return line + (" The developer then rewrote the method; the code above is the new version."
                   if rewritten else "")


def prompt(task, written, name, code, memory=None):
    """The judge's message. `memory` holds the lines of its earlier reviews of this class (C3)."""
    parts = [f"This is the skeleton of the class {task['class_name']}:", "",
             "```python", coder.skeleton(task), "```"]
    if written:
        parts += ["", "These methods were written before:", "",
                  "```python", "\n\n".join(written.values()), "```"]
    if memory:
        parts += ["", "These are your earlier reviews of the methods of this class:", "", *memory]
    parts += ["", f"The developer has just written the method `{name}`:", "",
              "```python", code, "```", "", f"Is `{name}` correct?"]
    return "\n".join(parts)


def ask(client, instructions, input, effort, tools=None, tool_choice=None, previous=None,
        text_format=VERDICT_FORMAT):
    """One request to the Responses API. With `previous`, the judge continues that conversation."""
    kwargs = {"model": MODEL, "instructions": instructions, "input": input,
              "reasoning": {"effort": effort}, "text": text_format}
    if tools:
        kwargs.update(tools=tools, tool_choice=tool_choice)
    if previous:
        kwargs["previous_response_id"] = previous
    return client.responses.create(**kwargs)


def usage_of(response):
    """Tokens and computed cost of one OpenAI request."""
    u = response.usage
    cached = getattr(getattr(u, "input_tokens_details", None), "cached_tokens", None) or 0
    reasoning = getattr(getattr(u, "output_tokens_details", None), "reasoning_tokens", None) or 0
    cost = ((u.input_tokens - cached) * PRICE["input"] + cached * PRICE["cached_input"]
            + u.output_tokens * PRICE["output"]) / 1e6
    return {"provider": "OpenAI", "prompt_tokens": u.input_tokens, "cached_tokens": cached,
            "completion_tokens": u.output_tokens, "reasoning_tokens": reasoning, "cost": cost}


def parse_verdict(content):
    try:
        answer = json.loads(content or "")
        return answer["verdict"], answer["reason"]
    except (ValueError, KeyError, TypeError):
        return None, content  # counted apart in the summary


def parse_confidence(content):
    """The confidence in the judge's answer, or None when it was not asked for."""
    try:
        return json.loads(content or "").get("confidence")
    except (ValueError, AttributeError):
        return None


def method_format(confidence):
    return VERDICT_FORMAT_CONFIDENCE if confidence else VERDICT_FORMAT


def look_again(tools):
    """The message to a judge whose confidence is below the threshold."""
    return ("You are not sure of this verdict. Look again at the cases you doubt"
            + (", running code if it helps," if tools else "") + " and answer again.")


def judge_method(client, task, written, name, code, effort=EFFORT, memory=None, confidence=False,
                 min_confidence=None, version="v1"):
    """Judge v1 (or v6, v7) on one method: one request, the judge only reads the code."""
    return review(client, task, INSTRUCTIONS[version], prompt(task, written, name, code, memory), None,
                  version, effort, method_format(confidence or min_confidence is not None), min_confidence)


def run_python(source, code):
    """Run the judge's code after the class, the way the harness runs generated code."""
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "snippet.py").write_text(source + "\n\n" + code, encoding="utf-8")
        try:
            proc = subprocess.run([sys.executable, "-I", "snippet.py"], cwd=tmp, capture_output=True,
                                  text=True, timeout=harness.TIMEOUT)
        except subprocess.TimeoutExpired:
            return f"Stopped after {harness.TIMEOUT} seconds."
    return (f"exit code {proc.returncode}\nstdout:\n{proc.stdout[-OUTPUT_LIMIT:]}"
            f"\nstderr:\n{proc.stderr[-OUTPUT_LIMIT:]}")


def judge_method_with_tools(client, task, written, name, code, effort=EFFORT, version="v2",
                            memory=None, confidence=False, min_confidence=None):
    """Judge v2 (or a variant of it) on one method: it may run code on the class written so far,
    then answers."""
    source = harness.build_class(task, {**written, name: code})
    return review(client, task, INSTRUCTIONS[version], prompt(task, written, name, code, memory),
                  source, version, effort, method_format(confidence or min_confidence is not None),
                  min_confidence)


def judge_any(client, task, written, name, code, version="v1", effort=EFFORT, memory=None,
              confidence=False, min_confidence=None):
    """One method with any version of the judge."""
    if version in READ_ONLY:
        return judge_method(client, task, written, name, code, effort, memory, confidence, min_confidence,
                            version)
    return judge_method_with_tools(client, task, written, name, code, effort, version, memory,
                                   confidence, min_confidence)


def review(client, task, instructions, content, source, version, effort, text_format=VERDICT_FORMAT,
           min_confidence=None):
    """One review by the judge. v1 answers at once; v2 may first run code on `source`, up to
    MAX_RUNS times, and then gives its verdict. With `min_confidence`, a verdict below it sends
    the judge to look again, at most MAX_LOOKS times; the last answer counts."""
    tools = [RUN_PYTHON] if version not in READ_ONLY else None
    runs, requests, looks = [], [], []
    message, previous = content, None
    while True:
        first_run, first_request = len(runs), len(requests)
        response = ask(client, instructions, [{"role": "user", "content": message}], effort,
                       tools, "auto" if tools else None, previous, text_format)
        while True:
            requests.append(usage_of(response))
            calls = [item for item in response.output if item.type == "function_call"] if tools else []
            # The second condition only guards against a model that ignores tool_choice="none".
            if not calls or len(requests) - first_request > MAX_RUNS + 1:
                break
            outputs = []
            for call in calls:
                # Every call needs an answer, also the ones beyond the limit.
                if len(runs) - first_run >= MAX_RUNS:
                    output = "No more runs are allowed. Give your verdict now."
                else:
                    try:
                        snippet = json.loads(call.arguments)["code"]
                    except (ValueError, KeyError, TypeError):
                        snippet, output = call.arguments, "The arguments were not valid JSON."
                    else:
                        # In the first tests the judge copied the class into its code. A copy can
                        # differ from the developer's code, so we do not run it.
                        if re.search(r"^\s*class\s+" + re.escape(task["class_name"]) + r"\b", snippet, flags=re.M):
                            output = (f"Not run: do not redefine the class {task['class_name']}. It is "
                                      "already defined with the developer's code, so call it directly.")
                        else:
                            output = run_python(source, snippet)
                    runs.append({"code": snippet, "output": output})
                outputs.append({"type": "function_call_output", "call_id": call.call_id, "output": output})
            response = ask(client, instructions, outputs, effort, tools,
                           "auto" if len(runs) - first_run < MAX_RUNS else "none", response.id, text_format)
        verdict, reason = parse_verdict(response.output_text)
        confidence = parse_confidence(response.output_text)
        looks.append({"verdict": verdict, "reason": reason, "confidence": confidence})
        if (min_confidence is None or confidence is None or confidence >= min_confidence
                or len(looks) > MAX_LOOKS):
            break
        message, previous = look_again(tools), response.id
    totals = {k: sum(r[k] for r in requests)
              for k in ("prompt_tokens", "cached_tokens", "completion_tokens", "reasoning_tokens", "cost")}
    return {"verdict": verdict, "reason": reason, "confidence": confidence, "looks": looks,
            "status": response.status, "provider": "OpenAI",
            "n_runs": len(runs), "runs": runs, "requests": requests, **totals}


def judge_run(client, task, run, version="v1", effort=EFFORT, confidence=False, min_confidence=None):
    """Verdicts on every method of a finished class, each judged with the methods before it."""
    written, records = {}, []
    for m in run["methods"]:
        name = m["method_name"]
        if not m["valid"]:
            # Nothing to read: the coder's reply had no usable method.
            records.append({"method_name": name, "verdict": "NOT OK", "auto": True,
                            "reason": "The reply did not contain a method that compiles.",
                            "passed": m["passed"]})
            continue
        r = judge_any(client, task, written, name, m["code"], version, effort, confidence=confidence,
                      min_confidence=min_confidence)
        for request in r["requests"]:
            budget.log(setup=run["setup"], task_id=task["task_id"], method_name=name,
                       role=f"judge-{version}", service="openai", model=MODEL, **request)
        records.append({"method_name": name, "auto": False, "passed": m["passed"], **r})
        written[name] = m["code"]
    return {"task_id": task["task_id"], "setup": run["setup"], "model": MODEL, "version": version,
            "effort": effort, "methods": records}


def agreement(rows):
    """Judge against tests. OK is the judge's positive answer, a pass is the tests' one."""
    rows = [r for r in rows if r["verdict"] in ("OK", "NOT OK")]
    n = len(rows)
    if n == 0:
        return {"n": 0}
    ok = [r["verdict"] == "OK" for r in rows]
    passed = [bool(r["passed"]) for r in rows]
    agree = sum(o == p for o, p in zip(ok, passed)) / n
    p_ok, p_pass = sum(ok) / n, sum(passed) / n
    chance = p_ok * p_pass + (1 - p_ok) * (1 - p_pass)
    failing = [o for o, p in zip(ok, passed) if not p]
    passing = [o for o, p in zip(ok, passed) if p]
    return {
        "n": n,
        "accuracy": agree,
        "kappa": (agree - chance) / (1 - chance) if chance < 1 else float("nan"),
        "false_ok": (sum(failing) / len(failing)) if failing else float("nan"),
        "false_not_ok": (sum(not o for o in passing) / len(passing)) if passing else float("nan"),
        "n_failing": len(failing),
        "n_passing": len(passing),
        # With pass as the positive answer: TPR is the share of passing methods the judge calls
        # OK, TNR the share of failing methods it calls NOT OK.
        "tpr": (sum(passing) / len(passing)) if passing else float("nan"),
        "tnr": (sum(not o for o in failing) / len(failing)) if failing else float("nan"),
        "p_ok": p_ok,
        "p_pass": p_pass,
    }


def folder(setup, version, effort, tag=""):
    """runs/judge/<setup>-<version>-<effort>, with -<tag> for a repeat of the same judge."""
    return ROOT / "runs/judge" / (f"{setup}-{version}-{effort}" + (f"-{tag}" if tag else ""))


def summary(setup, version="v1", effort=EFFORT, tag=""):
    rows = [r for f in sorted(folder(setup, version, effort, tag).glob("*.json"))
            for r in json.loads(f.read_text(encoding="utf-8"))["methods"]]
    judged = [r for r in rows if not r.get("auto")]
    a = agreement(judged)
    unreadable = sum(r["verdict"] is None for r in judged)
    cost = sum(r.get("cost") or 0 for r in judged)
    runs = sum(r.get("n_runs", 0) for r in judged)
    name = f"{setup}, judge {version}, effort {effort}" + (f", {tag}" if tag else "")
    print(f"{name}: {len(rows)} methods, {len(judged)} judged, "
          f"{unreadable} unreadable replies, {runs} code runs, {cost:.5f} $")
    if a["n"]:
        print(f"  agreement with the tests {a['accuracy']:.2f}, kappa {a['kappa']:.2f}")
        print(f"  OK to a failing method: {a['false_ok']:.2f} of {a['n_failing']}; "
              f"NOT OK to a passing method: {a['false_not_ok']:.2f} of {a['n_passing']}")


def main():
    parser = argparse.ArgumentParser(description="The judge on the methods of a finished run.")
    parser.add_argument("setup", help="the run to judge, such as C0-9b")
    parser.add_argument("tasks", nargs="*", help="task ids, such as ClassEval_19")
    parser.add_argument("--version", choices=VERSIONS, default="v1",
                        help="v1, v6 and v7 only read the code; v2 to v5 can run it")
    parser.add_argument("--effort", choices=EFFORTS, default=EFFORT, help="reasoning effort of the judge")
    parser.add_argument("--tag", default="", help="suffix of the folder, such as r2 for a repeat")
    parser.add_argument("--confidence", action="store_true", help="the judge also says how sure it is, 0 to 100")
    parser.add_argument("--min-confidence", type=int, help="below this confidence the judge looks again")
    parser.add_argument("--all", action="store_true", help="every class of the run")
    parser.add_argument("--dry-run", action="store_true", help="print the first prompt and send nothing")
    parser.add_argument("--force", action="store_true", help="judge again classes that already have verdicts")
    parser.add_argument("--summary", action="store_true", help="only compare the saved verdicts with the tests")
    args = parser.parse_args()

    if args.summary:
        summary(args.setup, args.version, args.effort, args.tag)
        return
    runs = ROOT / "runs" / args.setup
    chosen = sorted(f.stem for f in runs.glob("*.json")) if args.all else args.tasks
    missing = [t for t in chosen if not (runs / f"{t}.json").exists()]
    if not chosen or missing:
        parser.error(f"give task ids that have a result in {runs.relative_to(ROOT)} (missing: {missing})")
    tasks = {t["task_id"]: t for t in harness.load_tasks()}

    if args.dry_run:
        run = json.loads((runs / f"{chosen[0]}.json").read_text(encoding="utf-8"))
        m = next(m for m in run["methods"] if m["valid"])
        print("SYSTEM:\n" + INSTRUCTIONS[args.version] + "\n\nUSER:\n"
              + prompt(tasks[chosen[0]], {}, m["method_name"], m["code"]))
        if args.version not in READ_ONLY:
            print("\nTOOL:\n" + json.dumps(RUN_PYTHON, indent=2))
        if args.confidence or args.min_confidence is not None:
            print("\nANSWER:\n" + json.dumps(VERDICT_FORMAT_CONFIDENCE["format"]["schema"], indent=2))
        return

    load_dotenv(ROOT / ".env")
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], max_retries=5)
    out_dir = folder(args.setup, args.version, args.effort, args.tag)
    out_dir.mkdir(parents=True, exist_ok=True)
    for task_id in chosen:
        out = out_dir / f"{task_id}.json"
        if out.exists() and not args.force:
            print(f"{task_id}: already judged, skipped")
            continue
        try:
            budget.check("openai")
        except budget.BudgetReached as stop:
            print(f"Stopped before {task_id}: {stop}")
            sys.exit(1)
        run = json.loads((runs / f"{task_id}.json").read_text(encoding="utf-8"))
        result = judge_run(client, tasks[task_id], run, args.version, args.effort, args.confidence,
                           args.min_confidence)
        out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        verdicts = ", ".join(f"{m['method_name']} {m['verdict']} (tests {'pass' if m['passed'] else 'fail'})"
                             for m in result["methods"])
        print(f"{task_id}: {verdicts}")
    summary(args.setup, args.version, args.effort, args.tag)


if __name__ == "__main__":
    main()
