"""Run the docstring examples of every kept method on the reference solution.

A wrong example can mislead both coder and judge. Each example ends as match, mismatch (both sides
are Python values and differ), unclear (they cannot be compared), raised, or no expected value.
Values are compared as Python objects, so quotes, NumPy types and rounding do not count. We read
every mismatch by hand. Output: data/selection/docstring_examples.csv.
"""
import csv
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import harness

ROOT = harness.ROOT
OUT = ROOT / "data/selection/docstring_examples.csv"
DEV = ROOT / "data/selection/dev_classes.csv"
TIMEOUT = 30

RUNNER = r'''
import ast, contextlib, doctest, io, json, math, re, sys

def value(text):
    """The Python value written in text, or raise ValueError."""
    text = re.sub(r"np\.(?:float|int|bool_?)\w*\((.*?)\)", r"\1", text.strip())
    text = re.sub(r"^array\((.*)\)$", r"\1", text, flags=re.S)
    return ast.literal_eval(text)

def decimals(text):
    found = re.search(r"\d\.(\d+)", text)
    return len(found.group(1)) if found else None

def same(want, got, digits):
    if isinstance(want, bool) or isinstance(got, bool):
        return want == got
    if isinstance(want, (int, float)) and isinstance(got, (int, float)):
        tolerance = 0.5 * 10 ** -digits if digits else 1e-9
        return math.isclose(want, got, rel_tol=1e-9, abs_tol=tolerance)
    if isinstance(want, (list, tuple)) and isinstance(got, (list, tuple)):
        return len(want) == len(got) and all(same(a, b, digits) for a, b in zip(want, got))
    if isinstance(want, dict) and isinstance(got, dict):
        return want.keys() == got.keys() and all(same(want[k], got[k], digits) for k in want)
    return want == got
job = json.load(open("job.json", encoding="utf-8"))
base = {"__name__": "__main__"}
exec(compile(job["source"], "reference.py", "exec"), base)
parser, checker = doctest.DocTestParser(), doctest.OutputChecker()
flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
results = []
for name, doc in job["docs"]:
    row = {"method_name": name, "examples": 0, "match": 0, "mismatch": 0, "unclear": 0, "raised": 0,
           "no_expected": 0, "first_problem": None}
    try:
        examples = parser.get_examples(doc)
    except ValueError as e:
        row["first_problem"] = {"kind": "unparsable", "detail": str(e)[:200]}
        results.append(row)
        continue
    globs = dict(base)
    for ex in examples:
        row["examples"] += 1
        buffer, error = io.StringIO(), None
        with contextlib.redirect_stdout(buffer):
            try:
                exec(compile(ex.source, "<example>", "single"), globs)
            except BaseException as e:
                error = f"{type(e).__name__}: {e}"
        got = buffer.getvalue()
        if error and "Traceback" not in ex.want:
            kind = "raised"
        elif not ex.want.strip():
            kind = "no_expected" if got.strip() else "match"
        elif checker.check_output(ex.want, got, flags):
            kind = "match"
        else:
            try:
                kind = "match" if same(value(ex.want), value(got), decimals(ex.want)) else "mismatch"
            except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
                kind = "unclear"
        row[kind] += 1
        if kind in ("mismatch", "raised") and (row["first_problem"] is None or
                                              (kind == "mismatch" and row["first_problem"]["kind"] != "mismatch")):
            row["first_problem"] = {"kind": kind, "source": ex.source.strip(), "want": ex.want.strip(),
                                    "got": (error or got.strip())[:300]}
    results.append(row)
print("@@RESULT@@" + json.dumps(results))
'''


def docstring(method):
    found = re.search(r'"""(.*?)"""', method["method_description"], flags=re.S)
    return found.group(1) if found else method["method_description"]


def check_class(task):
    source = harness.build_class(task, {m["method_name"]: m["solution_code"] for m in task["methods_info"]})
    job = {"source": source, "docs": [(m["method_name"], docstring(m)) for m in task["methods_info"]]}
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "job.json").write_text(json.dumps(job), encoding="utf-8")
        Path(tmp, "runner.py").write_text(RUNNER, encoding="utf-8")
        try:
            proc = subprocess.run([sys.executable, "-I", "runner.py"], cwd=tmp, capture_output=True,
                                  text=True, timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            return None
    line = next((l for l in proc.stdout.splitlines() if l.startswith("@@RESULT@@")), None)
    return json.loads(line[len("@@RESULT@@"):]) if line else None


def main():
    with DEV.open(encoding="utf-8") as f:
        dev = {r["task_id"] for r in csv.DictReader(f)}
    rows = []
    for task in harness.load_tasks():
        results = check_class(task)
        if results is None:
            print(f"{task['task_id']}: the examples could not run (timeout or crash)")
            continue
        for r in results:
            problem = r.pop("first_problem") or {}
            rows.append({"task_id": task["task_id"], "dev": int(task["task_id"] in dev), **r,
                         "problem_kind": problem.get("kind", ""), "source": problem.get("source", ""),
                         "want": problem.get("want", ""), "got": problem.get("got", problem.get("detail", ""))})
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    mismatched = [r for r in rows if r["mismatch"]]
    print(f"{len(rows)} methods, {sum(r['examples'] for r in rows)} examples: "
          f"{sum(r['match'] for r in rows)} match, {sum(r['mismatch'] for r in rows)} mismatch, "
          f"{sum(r['unclear'] for r in rows)} unclear, "
          f"{sum(r['raised'] for r in rows)} raise an error, {sum(r['no_expected'] for r in rows)} without expected value")
    print(f"{len(mismatched)} methods in {len({r['task_id'] for r in mismatched})} classes have at least one "
          f"mismatching example -> {OUT.relative_to(ROOT)}")
    for r in mismatched:
        print(f"  {r['task_id']:<13} {r['method_name']:<28} want {r['want'][:40]!r:<44} got {r['got'][:40]!r}")


if __name__ == "__main__":
    main()
