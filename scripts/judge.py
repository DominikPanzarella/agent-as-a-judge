"""Judge v1: GPT-6 Luna reads one method and says whether it does what its docstring says.

The judge gets the class skeleton (the class description and every docstring), the methods
written before this one and the new method. It never sees the tests. It answers in JSON with a
short reason and a verdict, OK or NOT OK. The reason is also the feedback that the coder will get
in setups C1 and C2, which will call judge_method().

Run as a script, the judge reads the methods of a finished run, such as runs/C0, one by one in the
order they were written, and we compare its verdicts with the tests. This is how the pilot measures
the judge: agreement with the tests, Cohen's kappa, and how often it says OK to a method that fails.
Verdicts go to runs/judge/<setup>-<effort>/<task_id>.json and every request to runs/cost_log.csv.

    .venv/bin/python scripts/judge.py C0 --dry-run ClassEval_55   # show the first prompt, no request
    .venv/bin/python scripts/judge.py C0 ClassEval_19 ClassEval_55
    .venv/bin/python scripts/judge.py C0 --effort medium ClassEval_19   # more reasoning
    .venv/bin/python scripts/judge.py C0 --all                    # every class of runs/C0
    .venv/bin/python scripts/judge.py C0 --summary                # only the comparison with the tests
"""
import argparse
import json
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

import budget
import coder
import harness

ROOT = harness.ROOT
MODEL = "gpt-6-luna"
EFFORTS = ["low", "medium"]  # the course allows low or medium reasoning effort
EFFORT = "low"  # with "low", GPT-6 Luna used no reasoning tokens in the first test
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

# Structured output: the reply is always this JSON object. The reason comes first, so the
# verdict follows from it.
VERDICT_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "verdict",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "reason": {"type": "string",
                           "description": "One or two sentences: what is wrong and how to fix it, "
                                          "or why the method is correct. Not the verdict alone."},
                "verdict": {"type": "string", "enum": ["OK", "NOT OK"]},
            },
            "required": ["reason", "verdict"],
            "additionalProperties": False,
        },
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


def judge_method(client, task, written, name, code, effort=EFFORT):
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt(task, written, name, code)}]
    reply = client.chat.completions.create(model=MODEL, messages=messages, reasoning_effort=effort,
                                           response_format=VERDICT_FORMAT)
    u = reply.usage
    cached = getattr(getattr(u, "prompt_tokens_details", None), "cached_tokens", None) or 0
    reasoning = getattr(getattr(u, "completion_tokens_details", None), "reasoning_tokens", None)
    cost = ((u.prompt_tokens - cached) * PRICE["input"] + cached * PRICE["cached_input"]
            + u.completion_tokens * PRICE["output"]) / 1e6
    content = reply.choices[0].message.content or ""
    try:
        answer = json.loads(content)
        verdict, reason = answer["verdict"], answer["reason"]
    except (ValueError, KeyError, TypeError):
        verdict, reason = None, content  # counted apart in the summary
    return {"verdict": verdict, "reason": reason, "finish_reason": reply.choices[0].finish_reason,
            "provider": "OpenAI", "prompt_tokens": u.prompt_tokens, "cached_tokens": cached,
            "completion_tokens": u.completion_tokens, "reasoning_tokens": reasoning, "cost": cost}


def judge_run(client, task, run, effort=EFFORT):
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
        r = judge_method(client, task, written, name, m["code"], effort)
        budget.log(setup=run["setup"], task_id=task["task_id"], method_name=name, role="judge",
                   service="openai", model=MODEL, **r)
        records.append({"method_name": name, "auto": False, "passed": m["passed"], **r})
        written[name] = m["code"]
    return {"task_id": task["task_id"], "setup": run["setup"], "model": MODEL, "effort": effort,
            "methods": records}


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


def summary(setup, effort=EFFORT):
    folder = ROOT / "runs/judge" / f"{setup}-{effort}"
    rows = [r for f in sorted(folder.glob("*.json"))
            for r in json.loads(f.read_text(encoding="utf-8"))["methods"]]
    judged = [r for r in rows if not r.get("auto")]
    a = agreement(judged)
    unreadable = sum(r["verdict"] is None for r in judged)
    cost = sum(r.get("cost") or 0 for r in judged)
    print(f"{setup}, effort {effort}: {len(rows)} methods, {len(judged)} judged, {unreadable} unreadable replies, {cost:.5f} $")
    if a["n"]:
        print(f"  agreement with the tests {a['accuracy']:.2f}, kappa {a['kappa']:.2f}")
        print(f"  OK to a failing method: {a['false_ok']:.2f} of {a['n_failing']}; "
              f"NOT OK to a passing method: {a['false_not_ok']:.2f} of {a['n_passing']}")


def main():
    parser = argparse.ArgumentParser(description="Judge v1 on the methods of a finished run.")
    parser.add_argument("setup", help="the run to judge, such as C0")
    parser.add_argument("tasks", nargs="*", help="task ids, such as ClassEval_19")
    parser.add_argument("--all", action="store_true", help="every class of the run")
    parser.add_argument("--dry-run", action="store_true", help="print the first prompt and send nothing")
    parser.add_argument("--force", action="store_true", help="judge again classes that already have verdicts")
    parser.add_argument("--summary", action="store_true", help="only compare the saved verdicts with the tests")
    parser.add_argument("--effort", choices=EFFORTS, default=EFFORT, help="reasoning effort of the judge")
    args = parser.parse_args()

    if args.summary:
        summary(args.setup, args.effort)
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
        print("SYSTEM:\n" + SYSTEM + "\n\nUSER:\n" + prompt(tasks[chosen[0]], {}, m["method_name"], m["code"]))
        return

    load_dotenv(ROOT / ".env")
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], max_retries=5)
    out_dir = ROOT / "runs/judge" / f"{args.setup}-{args.effort}"
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
        result = judge_run(client, tasks[task_id], run, args.effort)
        out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        verdicts = ", ".join(f"{m['method_name']} {m['verdict']} (tests {'pass' if m['passed'] else 'fail'})"
                             for m in result["methods"])
        print(f"{task_id}: {verdicts}")
    summary(args.setup, args.effort)


if __name__ == "__main__":
    main()
