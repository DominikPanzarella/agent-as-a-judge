"""Run the ClassEval tests on a class put together from single methods.

build_class() turns missing or broken methods into stubs, so they fail only their own tests.
run_tests() runs each test class in its own process, in a temporary folder, with a timeout.

Run as a script, it checks itself: every reference method must pass (failures go to
data/selection/reference_check.csv) and stubs must fail (the ones that pass go to
data/selection/weak_tests.csv).
"""
import ast
import csv
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLASSEVAL = ROOT / "data/raw/classeval/ClassEval_data.json"
CLASSES = ROOT / "data/selection/classes.csv"
REFERENCE_CHECK = ROOT / "data/selection/reference_check.csv"
WEAK_TESTS = ROOT / "data/selection/weak_tests.csv"

TIMEOUT = 10  # seconds for one test class
MARK = "@@RESULT@@"

RUNNER = f"""
import json, os, sys, unittest, importlib.util
spec = importlib.util.spec_from_file_location("candidate", "candidate.py")
module = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(module)
except BaseException as e:
    print("{MARK}" + json.dumps({{"status": "load_error", "detail": repr(e)[:300]}}))
    sys.exit(0)
case = getattr(module, sys.argv[1], None)
if case is None:
    print("{MARK}" + json.dumps({{"status": "missing_test_class"}}))
    sys.exit(0)
suite = unittest.defaultTestLoader.loadTestsFromTestCase(case)
with open(os.devnull, "w") as sink:
    result = unittest.TextTestRunner(stream=sink, verbosity=0).run(suite)
print("{MARK}" + json.dumps({{"status": "ok", "tests": result.testsRun,
                             "failures": len(result.failures), "errors": len(result.errors)}}))
"""


def load_tasks(kept_only=True):
    tasks = json.loads(CLASSEVAL.read_text(encoding="utf-8"))
    if not kept_only:
        return tasks
    kept = {r["task_id"] for r in csv.DictReader(CLASSES.open(encoding="utf-8")) if r["kept"] == "1"}
    return [t for t in tasks if t["task_id"] in kept]


def parses_in_class(member):
    try:
        ast.parse("class _C:\n" + member)
        return True
    except SyntaxError:
        return False


def as_class_member(code):
    """Indent one method so that it sits inside a class body, or return None if it cannot."""
    text = code.expandtabs(4).strip("\n").rstrip()
    first, _, rest = text.partition("\n")
    candidates = [
        # ClassEval stores methods with the first line unindented and the rest at class depth.
        "    " + first.lstrip() + ("\n" + rest if rest else ""),
        # A plain function, as a model usually writes it.
        textwrap.indent(textwrap.dedent(text), "    "),
    ]
    return next((c for c in candidates if parses_in_class(c)), None)


def stub(method):
    """Signature of a method that has not been written yet, with a body that returns None.

    We keep only the signature because some ClassEval docstrings do not compile (curly quotes
    in ClassEval_46, wrong indentation in ClassEval_5 and ClassEval_73).
    """
    name = re.escape(method["method_name"])
    found = re.search(r"def\s+" + name + r"\s*\(.*?\)\s*(?:->[^:\n]*)?:", method["method_description"], flags=re.S)
    signature = " ".join(found.group(0).split()) if found else f"def {method['method_name']}(self, *args, **kwargs):"
    return signature + "\n    return None"


def skeleton_decorators(task, name):
    """Decorators that the skeleton puts on a method, such as @staticmethod."""
    found = re.search(r"((?:^[ \t]*@[^\n]*\n)+)[ \t]*def " + re.escape(name) + r"\(", task["skeleton"], flags=re.M)
    return [line.strip() for line in found.group(1).splitlines()] if found else []


def with_decorators(task, name, member):
    """ClassEval loses the decorator of some methods, so we take it back from the skeleton."""
    if member is None or member.lstrip().startswith("@"):
        return member
    return "".join(f"    {d}\n" for d in skeleton_decorators(task, name)) + member


def build_class(task, methods):
    """Full module source: imports, constructor, and one entry per method of the class."""
    parts = ["\n".join(task["import_statement"]), "", task["class_constructor"].rstrip(), ""]
    for m in task["methods_info"]:
        name = m["method_name"]
        code = methods.get(name)
        member = as_class_member(code) if code else None
        # A method that does not compile becomes a stub, so it fails only its own tests.
        parts.append(with_decorators(task, name, member or as_class_member(stub(m))))
        parts.append("")
    return "\n".join(parts)


def run_test_class(source, test_code, test_class):
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "candidate.py").write_text(source + "\n\n" + test_code, encoding="utf-8")
        Path(tmp, "runner.py").write_text(RUNNER, encoding="utf-8")
        try:
            proc = subprocess.run([sys.executable, "runner.py", test_class], cwd=tmp,
                                  capture_output=True, text=True, timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "passed": False}
    line = next((l for l in proc.stdout.splitlines() if l.startswith(MARK)), None)
    if line is None:
        return {"status": "crash", "passed": False, "detail": proc.stderr[-300:]}
    result = json.loads(line[len(MARK):])
    result["passed"] = (result["status"] == "ok" and result["tests"] > 0
                        and result["failures"] == 0 and result["errors"] == 0)
    return result


def run_tests(task, source):
    """Result of every test class of the task, keyed by test class name."""
    # One ClassEval test class name starts with a space, hence strip().
    return {tc.strip(): run_test_class(source, task["test"], tc.strip()) for tc in task["test_classes"]}


def method_passed(task, results):
    return {m["method_name"]: results[m["test_class"].strip()]["passed"] for m in task["methods_info"]}


def class_passed(results):
    return all(r["passed"] for r in results.values())


def check_references():
    rows, n_methods, n_classes = [], 0, 0
    tasks = load_tasks()
    for t in tasks:
        reference = {m["method_name"]: m["solution_code"] for m in t["methods_info"]}
        results = run_tests(t, build_class(t, reference))
        n_classes += class_passed(results)
        for m in t["methods_info"]:
            r = results[m["test_class"].strip()]
            n_methods += r["passed"]
            if not r["passed"]:
                rows.append({"task_id": t["task_id"], "method_name": m["method_name"],
                             "test_class": m["test_class"], "status": r["status"],
                             "detail": r.get("detail", f"failures={r.get('failures')} errors={r.get('errors')}")})
        main = [tc for tc in results if tc not in {m["test_class"].strip() for m in t["methods_info"]}]
        for tc in main:
            if not results[tc]["passed"]:
                rows.append({"task_id": t["task_id"], "method_name": "", "test_class": tc,
                             "status": results[tc]["status"],
                             "detail": results[tc].get("detail", "class-level test failed")})
    total = sum(len(t["methods_info"]) for t in tasks)
    print(f"reference solutions: {n_methods} of {total} methods pass, {n_classes} of {len(tasks)} classes pass")
    with REFERENCE_CHECK.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "method_name", "test_class", "status", "detail"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} failing test classes -> {REFERENCE_CHECK.relative_to(ROOT)}")

    weak = []
    for t in tasks:
        results = run_tests(t, build_class(t, {}))
        weak += [{"task_id": t["task_id"], "method_name": n}
                 for n, ok in method_passed(t, results).items() if ok]
    with WEAK_TESTS.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "method_name"])
        writer.writeheader()
        writer.writerows(weak)
    print(f"{len(weak)} methods pass with a stub that returns None -> {WEAK_TESTS.relative_to(ROOT)}")


if __name__ == "__main__":
    check_references()
