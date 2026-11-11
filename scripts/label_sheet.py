"""The sheet for our labels of the pilot: the methods of the 9B to check by hand. Sends no request.

The cases are every method of C0-9b and C0-9b-r2 where a judge and the tests disagree, plus a
sample of methods where judge v2 and the tests agree, shuffled together. For each case
runs/labels/pilot_9b_cases.md shows the docstring, the 9B's code, the tests with the error of each
failing test and, last, what the judges said. Each rater fills in a separate CSV without looking
at the other; --merge then gives the agreement between the two and the cases to settle together.

    .venv/bin/python scripts/label_sheet.py           # the cases and the two empty CSVs
    .venv/bin/python scripts/label_sheet.py --merge   # agreement and runs/labels/pilot_9b_consensus.csv
"""
import argparse
import csv
import json
import random
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

import compare_judges
import harness

ROOT = harness.ROOT
OUT = ROOT / "runs/labels"
CASES = OUT / "pilot_9b_cases.md"
RATERS = [OUT / "pilot_9b_rater1.csv", OUT / "pilot_9b_rater2.csv"]
CONSENSUS = OUT / "pilot_9b_consensus.csv"
N_AGREEMENTS = 10
SEED = 2026
LABELS = ["correct", "wrong", "unclear"]
FIELDS = ["case", "run", "task_id", "method_name", "label", "kind", "note"]

# Written before reading any case, because criteria drift while people label (Shankar et al. 2024).
CRITERION = """\
A method is **correct** if, on the inputs its docstring describes, it does what the docstring and
the rest of the class ask: the description, the parameters, the return value and the examples.
Behaviour the docstring does not describe does not count either way: a check or a message the
docstring never asks for is not needed, and a test that asks for it does not make the method
wrong. It is **wrong** if it breaks something the docstring asks. It is **unclear** if the
docstring can be read both ways or contradicts itself, for example when its example disagrees
with its text."""

KINDS = """\
- `coder bug`: the method is wrong and the tests see it.
- `bug the tests miss`: the method is wrong but the tests pass.
- `hidden requirement`: a test asks for something the docstring does not say.
- `wrong docstring example`: the example in the docstring does not match the text or the tests.
- `judge misread`: the judge's claim about the code is false (what it returns, raises or does).
- `none`: judge and tests are right.
- `other`: say what in the note."""


def docstring(info):
    """The signature and docstring of a method, with the docstring indented under the def line."""
    first, _, rest = info["method_description"].strip().partition("\n")
    return first + "\n" + textwrap.indent(textwrap.dedent(rest), "    ")


def failing_tests(task, source, name):
    """Run the tests of one method with unittest: the failing tests and their error lines."""
    test_class = next(m for m in task["methods_info"] if m["method_name"] == name)["test_class"].strip()
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "candidate.py").write_text(source + "\n\n" + task["test"], encoding="utf-8")
        try:
            proc = subprocess.run([sys.executable, "-m", "unittest", f"candidate.{test_class}"], cwd=tmp,
                                  capture_output=True, text=True, timeout=harness.TIMEOUT)
        except subprocess.TimeoutExpired:
            return [f"stopped after {harness.TIMEOUT} seconds"]
    lines = []
    for chunk in proc.stderr.split("=" * 70)[1:]:
        head = chunk.strip().splitlines()[0]
        body = chunk.split("-" * 70)[1] if "-" * 70 in chunk else ""
        errors = [l.strip() for l in body.splitlines() if re.match(r"^\w*(Error|Exception)\b", l.strip())]
        lines.append(f"{head.split(' (')[0]}: {errors[-1][:200] if errors else 'error'}")
    return lines


def cases():
    """The disagreements of any judge, plus a sample of the methods where v2 agrees with the tests."""
    names = compare_judges.judges()
    verdicts = {name: compare_judges.verdicts(name) for name in names}
    keys = sorted({k for v in verdicts.values() for k, m in v.items() if not compare_judges.right(m)})
    agree = sorted(k for k, m in verdicts[compare_judges.BASE].items()
                   if compare_judges.right(m) and k not in keys)
    keys += random.Random(SEED).sample(agree, N_AGREEMENTS)
    random.Random(SEED).shuffle(keys)
    return [(f"P{i:02d}", k, {n: verdicts[n].get(k) for n in names}) for i, k in enumerate(keys, start=1)]


def write_cases():
    tasks = {t["task_id"]: t for t in harness.load_tasks()}
    parts = ["# Our labels of the pilot: the 9B's methods", "",
             "Label each case in your own CSV, without looking at the other one. Read the docstring, "
             "the code and the tests, write the label, and only then open the judges' part and write "
             "the kind.", "", "## Criterion", "", CRITERION, "", "## Kinds", "", KINDS, ""]
    rows = []
    for case, (run, task_id, name), judged in cases():
        task = tasks[task_id]
        result = json.loads((ROOT / "runs" / run / f"{task_id}.json").read_text(encoding="utf-8"))
        methods = {m["method_name"]: m for m in result["methods"]}
        code = {n: m["code"] for n, m in methods.items() if m["valid"]}
        source = harness.build_class(task, code)
        info = next(m for m in task["methods_info"] if m["method_name"] == name)
        failing = failing_tests(task, source, name)
        base = judged[compare_judges.BASE]
        parts += [f"## {case}: {task['class_name']}.{name} ({task_id}, run {run})", "",
                  "Docstring:", "", "```python", docstring(info), "```", "",
                  "The 9B's code:", "", "```python", code[name], "```", "",
                  "<details><summary>The whole class written by the 9B</summary>", "",
                  "```python", source, "```", "", "</details>", "",
                  f"Tests of the method: **{'pass' if methods[name]['passed'] else 'fail'}**", "",
                  "```python", info["test_code"].strip(), "```", ""]
        parts += [f"- {line}" for line in failing] + ([""] if failing else [])
        parts += ["<details><summary>The judges (open after the label)</summary>", "",
                  "Verdicts: " + ", ".join(f"{n.replace('-medium', '')} {m['verdict'] if m else '-'}"
                                           for n, m in judged.items()), "",
                  f"Reason of {compare_judges.BASE}: {base['reason']}", ""]
        for r in base.get("runs", []):
            parts += ["```python", r["code"], "```", "", "```text", r["output"].strip(), "```", ""]
        parts += ["</details>", ""]
        rows.append({"case": case, "run": run, "task_id": task_id, "method_name": name,
                     "label": "", "kind": "", "note": ""})
    OUT.mkdir(parents=True, exist_ok=True)
    CASES.write_text("\n".join(parts), encoding="utf-8")
    print(f"{len(rows)} cases -> {CASES.relative_to(ROOT)}")
    for path in RATERS:
        if path.exists():
            print(f"{path.relative_to(ROOT)} already exists: left as it is")
            continue
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        print(f"-> {path.relative_to(ROOT)}")


def kappa(a, b):
    """Cohen's kappa of two raters over the same cases."""
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    chance = sum((a.count(c) / n) * (b.count(c) / n) for c in set(a) | set(b))
    return (observed - chance) / (1 - chance) if chance < 1 else float("nan")


def merge():
    filled = []
    for path in RATERS:
        with path.open(encoding="utf-8") as f:
            filled.append({r["case"]: r for r in csv.DictReader(f)})
    one, two = filled
    done = [c for c in one if one[c]["label"] in LABELS and two.get(c, {}).get("label") in LABELS]
    if not done:
        print("no case has a label from both of us yet")
        return
    a, b = [one[c]["label"] for c in done], [two[c]["label"] for c in done]
    print(f"{len(done)} cases labelled by both: same label {sum(x == y for x, y in zip(a, b))}, "
          f"Cohen's kappa {kappa(a, b):.2f}")
    with CONSENSUS.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS[:4] + ["label_1", "label_2", "kind_1", "kind_2",
                                                             "label", "kind", "note"])
        writer.writeheader()
        for c in done:
            same = one[c]["label"] == two[c]["label"]
            writer.writerow({**{k: one[c][k] for k in FIELDS[:4]}, "label_1": one[c]["label"],
                             "label_2": two[c]["label"], "kind_1": one[c]["kind"], "kind_2": two[c]["kind"],
                             "label": one[c]["label"] if same else "", "kind": "", "note": ""})
    print(f"-> {CONSENSUS.relative_to(ROOT)}: settle together the cases with an empty label")


def main():
    parser = argparse.ArgumentParser(description="The sheet for our labels of the 9B's pilot methods.")
    parser.add_argument("--merge", action="store_true", help="compare the two filled CSVs")
    if parser.parse_args().merge:
        merge()
    else:
        write_cases()


if __name__ == "__main__":
    main()
