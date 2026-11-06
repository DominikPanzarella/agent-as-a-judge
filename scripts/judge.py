"""The judge: GPT-6 Luna reads one method and says whether it does what its docstring says.

The judge gets the class skeleton (the class description and every docstring), the methods
written before this one and the new method. It never sees the tests. It answers in JSON with a
short reason and a verdict, OK or NOT OK. The reason is also the feedback that the coder will get
in setups C1 and C2, which will call judge_method().

There are two versions. Judge v1 only reads the code. Judge v2 can also run Python before it
answers, with the tool run_python: the code runs after the class written so far, so the judge can
try the docstring examples or a case it doubts. We added v2 because v1, on the first methods,
described results that the code does not produce. The tests stay hidden in both versions. The
judge's code runs like the harness runs generated code: in a separate process, in a temporary
folder, with a time limit.

Both versions use the OpenAI Responses API with the same settings, so they differ only in the
tool. The older Chat Completions API does not accept tools together with a reasoning effort for
GPT-6 Luna.

Run as a script, the judge reads the methods of a finished run, such as runs/C0, one by one in the
order they were written, and we compare its verdicts with the tests: agreement, Cohen's kappa, and
how often it says OK to a method that fails. Verdicts go to
runs/judge/<setup>-<version>-<effort>/<task_id>.json and every request to runs/cost_log.csv.

    .venv/bin/python scripts/judge.py C0 --dry-run ClassEval_55          # show the prompt, no request
    .venv/bin/python scripts/judge.py C0 ClassEval_19 ClassEval_55       # v1, low effort
    .venv/bin/python scripts/judge.py C0 --version v2 --effort medium ClassEval_19
    .venv/bin/python scripts/judge.py C0 --all                           # every class of runs/C0
    .venv/bin/python scripts/judge.py C0 --version v2 --summary          # only the comparison with the tests
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
VERSIONS = ["v1", "v2"]
EFFORTS = ["low", "medium"]  # the course allows low or medium reasoning effort
EFFORT = "low"  # with "low", GPT-6 Luna used no reasoning tokens in the first test
MAX_RUNS = 5  # code runs that judge v2 may ask for on one method
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

# Setup C1: the judge reads the finished class instead of one method.
SYSTEM_CLASS = (
    "You review Python code. A developer has written a whole class, one method at a time. Decide "
    "whether every method does what its docstring says, given the rest of the class. Look for "
    "wrong results, exceptions, cases in the docstrings that the code does not handle, and uses "
    "of fields or methods that the class does not have. Answer OK if all methods are correct and "
    "NOT OK if you find a concrete problem. In the reason, name each method with a problem and "
    "say briefly what is wrong and how to fix it, or say why the class is correct. The reason "
    "must explain the verdict: never write only OK or NOT OK there."
)
SYSTEM_CLASS_TOOLS = SYSTEM_CLASS + TOOLS_NOTE

# Structured output: the reply is always this JSON object. The reason comes first, so the
# verdict follows from it.
def verdict_format(reason):
    return {
        "format": {
            "type": "json_schema",
            "name": "verdict",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": reason},
                    "verdict": {"type": "string", "enum": ["OK", "NOT OK"]},
                },
                "required": ["reason", "verdict"],
                "additionalProperties": False,
            },
        },
    }


VERDICT_FORMAT = verdict_format("One or two sentences: what is wrong and how to fix it, "
                                "or why the method is correct. Not the verdict alone.")
CLASS_VERDICT_FORMAT = verdict_format("Each method with a problem, what is wrong and how to fix it, "
                                      "or why the class is correct. Not the verdict alone.")

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


def prompt(task, written, name, code):
    parts = [f"This is the skeleton of the class {task['class_name']}:", "",
             "```python", coder.skeleton(task), "```"]
    if written:
        parts += ["", "These methods were written before:", "",
                  "```python", "\n\n".join(written.values()), "```"]
    parts += ["", f"The developer has just written the method `{name}`:", "",
              "```python", code, "```", "", f"Is `{name}` correct?"]
    return "\n".join(parts)


def class_prompt(task, source):
    return "\n".join([f"This is the skeleton of the class {task['class_name']}:", "",
                      "```python", coder.skeleton(task), "```", "",
                      "The developer has written the whole class:", "",
                      "```python", source, "```", "", f"Is the class {task['class_name']} correct?"])


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


def judge_method(client, task, written, name, code, effort=EFFORT):
    """Judge v1 on one method: one request, the judge only reads the code."""
    return review(client, task, SYSTEM, prompt(task, written, name, code), None, "v1", effort)


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


def judge_method_with_tools(client, task, written, name, code, effort=EFFORT):
    """Judge v2 on one method: it may run code on the class written so far, then answers."""
    source = harness.build_class(task, {**written, name: code})
    return review(client, task, SYSTEM_TOOLS, prompt(task, written, name, code), source, "v2", effort)


def judge_class(client, task, written, version="v1", effort=EFFORT):
    """Setup C1: one verdict on the finished class, with v1 or v2."""
    source = harness.build_class(task, written)
    instructions = SYSTEM_CLASS if version == "v1" else SYSTEM_CLASS_TOOLS
    return review(client, task, instructions, class_prompt(task, source), source, version, effort,
                  CLASS_VERDICT_FORMAT)


def review(client, task, instructions, content, source, version, effort, text_format=VERDICT_FORMAT):
    """One review by the judge. v1 answers at once; v2 may first run code on `source`, up to
    MAX_RUNS times, and then gives its verdict."""
    tools = [RUN_PYTHON] if version == "v2" else None
    runs, requests = [], []
    response = ask(client, instructions, [{"role": "user", "content": content}], effort,
                   tools, "auto" if tools else None, text_format=text_format)
    while True:
        requests.append(usage_of(response))
        calls = [item for item in response.output if item.type == "function_call"] if tools else []
        # The second condition only guards against a model that ignores tool_choice="none".
        if not calls or len(requests) > MAX_RUNS + 1:
            break
        outputs = []
        for call in calls:
            # Every call needs an answer, also the ones beyond the limit.
            if len(runs) >= MAX_RUNS:
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
                       "auto" if len(runs) < MAX_RUNS else "none", previous=response.id,
                       text_format=text_format)
    verdict, reason = parse_verdict(response.output_text)
    totals = {k: sum(r[k] for r in requests)
              for k in ("prompt_tokens", "cached_tokens", "completion_tokens", "reasoning_tokens", "cost")}
    return {"verdict": verdict, "reason": reason, "status": response.status, "provider": "OpenAI",
            "n_runs": len(runs), "runs": runs, "requests": requests, **totals}


def judge_run(client, task, run, version="v1", effort=EFFORT):
    """Verdicts on every method of a finished class, each judged with the methods before it."""
    judge = judge_method if version == "v1" else judge_method_with_tools
    written, records = {}, []
    for m in run["methods"]:
        name = m["method_name"]
        if not m["valid"]:
            # Nothing to read: the coder's reply had no usable method.
            records.append({"method_name": name, "verdict": "NOT OK", "auto": True,
                            "reason": "The reply did not contain a method that compiles.",
                            "passed": m["passed"]})
            continue
        r = judge(client, task, written, name, m["code"], effort)
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
    }


def folder(setup, version, effort):
    return ROOT / "runs/judge" / f"{setup}-{version}-{effort}"


def summary(setup, version="v1", effort=EFFORT):
    rows = [r for f in sorted(folder(setup, version, effort).glob("*.json"))
            for r in json.loads(f.read_text(encoding="utf-8"))["methods"]]
    judged = [r for r in rows if not r.get("auto")]
    a = agreement(judged)
    unreadable = sum(r["verdict"] is None for r in judged)
    cost = sum(r.get("cost") or 0 for r in judged)
    runs = sum(r.get("n_runs", 0) for r in judged)
    print(f"{setup}, judge {version}, effort {effort}: {len(rows)} methods, {len(judged)} judged, "
          f"{unreadable} unreadable replies, {runs} code runs, {cost:.5f} $")
    if a["n"]:
        print(f"  agreement with the tests {a['accuracy']:.2f}, kappa {a['kappa']:.2f}")
        print(f"  OK to a failing method: {a['false_ok']:.2f} of {a['n_failing']}; "
              f"NOT OK to a passing method: {a['false_not_ok']:.2f} of {a['n_passing']}")


def main():
    parser = argparse.ArgumentParser(description="The judge on the methods of a finished run.")
    parser.add_argument("setup", help="the run to judge, such as C0")
    parser.add_argument("tasks", nargs="*", help="task ids, such as ClassEval_19")
    parser.add_argument("--version", choices=VERSIONS, default="v1", help="v2 can run code")
    parser.add_argument("--effort", choices=EFFORTS, default=EFFORT, help="reasoning effort of the judge")
    parser.add_argument("--all", action="store_true", help="every class of the run")
    parser.add_argument("--dry-run", action="store_true", help="print the first prompt and send nothing")
    parser.add_argument("--force", action="store_true", help="judge again classes that already have verdicts")
    parser.add_argument("--summary", action="store_true", help="only compare the saved verdicts with the tests")
    args = parser.parse_args()

    if args.summary:
        summary(args.setup, args.version, args.effort)
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
        system = SYSTEM if args.version == "v1" else SYSTEM_TOOLS
        print("SYSTEM:\n" + system + "\n\nUSER:\n" + prompt(tasks[chosen[0]], {}, m["method_name"], m["code"]))
        if args.version == "v2":
            print("\nTOOL:\n" + json.dumps(RUN_PYTHON, indent=2))
        return

    load_dotenv(ROOT / ".env")
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], max_retries=5)
    out_dir = folder(args.setup, args.version, args.effort)
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
        result = judge_run(client, tasks[task_id], run, args.version, args.effort)
        out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        verdicts = ", ".join(f"{m['method_name']} {m['verdict']} (tests {'pass' if m['passed'] else 'fail'})"
                             for m in result["methods"])
        print(f"{task_id}: {verdicts}")
    summary(args.setup, args.version, args.effort)


if __name__ == "__main__":
    main()
