"""Setup C0: the coder writes each class one method at a time, with no feedback.

The coder is Qwen on OpenRouter. For each method, in the order of
data/selection/method_order.csv, it gets the class skeleton, the methods it has already
written and the name of the next method. It never sees the tests. The method must come back
in a Python code block. If it does not, or if it does not compile, the method stays empty and
fails only its own tests. We never ask a second time, so every setup sends the coder the same
number of requests.

When a class is finished the harness runs its tests. The result goes to
runs/C0/<task_id>.json: code, tokens, cost and provider of every request, and the test result
of every method. Every request also adds a line to runs/cost_log.csv.

    .venv/bin/python scripts/coder.py --dry-run ClassEval_19      # show the first prompt, no request
    .venv/bin/python scripts/coder.py ClassEval_19 ClassEval_53   # run these classes
    .venv/bin/python scripts/coder.py --all                       # every kept class not run yet
    .venv/bin/python scripts/coder.py --name C0-r2 ClassEval_19   # a second run, saved in runs/C0-r2
    .venv/bin/python scripts/coder.py --model qwen/qwen3.5-9b --name C0-9b ClassEval_19   # another coder
"""
import argparse
import ast
import csv
import json
import os
import re
import sys
import textwrap

from dotenv import load_dotenv
from openai import OpenAI

import budget
import harness

ROOT = harness.ROOT
METHOD_ORDER = ROOT / "data/selection/method_order.csv"
SETUP = "C0"

MODEL = "qwen/qwen3.8-27b"
MAX_TOKENS = 4000  # the reasoning tokens count against this limit too
EXTRA_BODY = {
    "reasoning": {"effort": "low"},
    # The course asks for the cheapest provider that serves the model in full precision.
    "provider": {"sort": "price", "quantizations": ["bf16", "fp16", "fp32"]},
    "usage": {"include": True},
}

SYSTEM = (
    "You are completing a Python class one method at a time. Write only the method you are "
    "asked for: its def line and its body. Put it in a single ```python code block and write "
    "nothing outside the block. Do not repeat the other methods and do not write tests. Use "
    "the imports of the skeleton; if you need another module, import it inside the method."
)

CODE_BLOCK = re.compile(r"```[ \t]*(?:python|py)?[ \t]*\n(.*?)```", re.S)


def method_order():
    order = {}
    with METHOD_ORDER.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            order.setdefault(r["task_id"], []).append((int(r["step"]), r["method_name"]))
    return {task_id: [name for _, name in sorted(steps)] for task_id, steps in order.items()}


def skeleton(task):
    text = task["skeleton"].strip()
    # The skeleton of ClassEval_5 sits inside a pair of ''' quotes.
    if text.startswith("'''") and text.endswith("'''"):
        text = text[3:-3].strip()
    return text


def prompt(task, written, name):
    parts = [f"This is the skeleton of the class {task['class_name']}:", "",
             "```python", skeleton(task), "```"]
    if written:
        parts += ["", "These methods are already written:", "",
                  "```python", "\n\n".join(written.values()), "```"]
    parts += ["", f"Write the method `{name}`, as its docstring in the skeleton describes."]
    return "\n".join(parts)


def extract_method(reply, name):
    """Source of the method `name` in the reply, or None if the reply does not define it.

    If the model sends back the whole class, or more than one method, we keep only `name`.
    """
    for block in CODE_BLOCK.findall(reply) or [reply]:
        text = textwrap.dedent(block.expandtabs(4)).strip("\n")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            # Keep the broken method: the harness turns it into a stub, and we can read it later.
            if re.search(r"^\s*def\s+" + re.escape(name) + r"\s*\(", text, flags=re.M):
                return text
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
                lines = text.splitlines()
                start = min([d.lineno for d in node.decorator_list] + [node.lineno]) - 1
                return textwrap.dedent("\n".join(lines[start:node.end_lineno]))
    return None


def ask(client, messages, model=MODEL):
    reply = client.chat.completions.create(model=model, messages=messages,
                                           max_tokens=MAX_TOKENS, extra_body=EXTRA_BODY)
    u = reply.usage
    prompt_details = getattr(u, "prompt_tokens_details", None)
    completion_details = getattr(u, "completion_tokens_details", None)
    return {
        "reply": reply.choices[0].message.content or "",
        "finish_reason": reply.choices[0].finish_reason,
        "provider": getattr(reply, "provider", None),
        "prompt_tokens": u.prompt_tokens,
        "cached_tokens": getattr(prompt_details, "cached_tokens", None),
        "completion_tokens": u.completion_tokens,
        "reasoning_tokens": getattr(completion_details, "reasoning_tokens", None),
        "cost": getattr(u, "cost", None),
    }


def run_class(client, task, steps, setup=SETUP, model=MODEL):
    written, records = {}, []
    for name in steps:
        messages = [{"role": "system", "content": SYSTEM},
                    {"role": "user", "content": prompt(task, written, name)}]
        r = ask(client, messages, model)
        code = extract_method(r["reply"], name)
        valid = code is not None and harness.as_class_member(code) is not None
        if valid:
            written[name] = code
        budget.log(setup=setup, task_id=task["task_id"], method_name=name, role="coder",
                   service="openrouter", model=model, **r)
        records.append({"method_name": name, "code": code, "valid": valid, **r})

    source = harness.build_class(task, written)
    results = harness.run_tests(task, source)
    passed = harness.method_passed(task, results)
    for record in records:
        record["passed"] = passed[record["method_name"]]
    return {"task_id": task["task_id"], "class_name": task["class_name"], "setup": setup,
            "model": model, "methods": records, "class_passed": harness.class_passed(results),
            "tests": results, "source": source}


def main():
    parser = argparse.ArgumentParser(description="Setup C0: the coder writes each class with no feedback.")
    parser.add_argument("tasks", nargs="*", help="task ids, such as ClassEval_19")
    parser.add_argument("--all", action="store_true", help="every kept class")
    parser.add_argument("--dry-run", action="store_true", help="print the first prompt and send nothing")
    parser.add_argument("--force", action="store_true", help="run again classes that already have a result")
    parser.add_argument("--name", default=SETUP,
                        help="name of the run and of its folder in runs/, such as C0-r2 for a second run")
    parser.add_argument("--model", default=MODEL, help="OpenRouter model of the coder")
    args = parser.parse_args()

    tasks = {t["task_id"]: t for t in harness.load_tasks()}
    order = method_order()
    chosen = list(tasks) if args.all else args.tasks
    unknown = [t for t in chosen if t not in tasks]
    if not chosen or unknown:
        parser.error(f"give kept task ids or --all (not kept or unknown: {unknown})")

    if args.dry_run:
        task = tasks[chosen[0]]
        print(f"method order: {order[task['task_id']]}\n")
        print("SYSTEM:\n" + SYSTEM + "\n\nUSER:\n" + prompt(task, {}, order[task["task_id"]][0]))
        return

    load_dotenv(ROOT / ".env")
    client = OpenAI(api_key=os.environ["OPENROUTER_API_KEY"], base_url="https://openrouter.ai/api/v1",
                    max_retries=5)
    runs = ROOT / "runs" / args.name
    runs.mkdir(parents=True, exist_ok=True)
    for task_id in chosen:
        out = runs / f"{task_id}.json"
        if out.exists() and not args.force:
            print(f"{task_id}: already done, skipped")
            continue
        try:
            budget.check("openrouter")
        except budget.BudgetReached as stop:
            print(f"Stopped before {task_id}: {stop}")
            sys.exit(1)
        result = run_class(client, tasks[task_id], order[task_id], args.name, args.model)
        out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        ms = result["methods"]
        tokens = sum(m["prompt_tokens"] + m["completion_tokens"] for m in ms)
        cost = sum(m["cost"] or 0 for m in ms)
        print(f"{task_id}: {sum(m['passed'] for m in ms)} of {len(ms)} methods pass, "
              f"class {'passes' if result['class_passed'] else 'fails'}, "
              f"{sum(not m['valid'] for m in ms)} invalid replies, {tokens} tokens, {cost:.5f} $")


if __name__ == "__main__":
    main()
