"""Analysis of the runs (week 2). It reads saved results and sends no request.

For each run it reports the share of methods and of classes that pass their tests, with and
without the 4 weak methods. For a run with a judge it also scores the judge's verdicts on the
first versions against the tests on those versions: accuracy, Cohen's kappa, TPR (passing methods
called OK) and TNR (failing methods called NOT OK), the two numbers that Engineering AI Systems
(USI) recommends instead of overall agreement. In C2 the judge gives one verdict per method, in C1 one per class. It also counts how
many methods the revisions fixed and how many they broke.

Then it compares every pair of runs method by method, with an exact McNemar test, and gives a 95%
bootstrap interval for the difference in the share of passing methods. The bootstrap resamples
whole classes, because the methods of one class depend on each other.

With --sample N it writes N random disagreements between the judge and the tests of each run to
runs/error_analysis_<run>.csv. The columns type and who_is_right are left empty: we fill them in
by hand.

    .venv/bin/python scripts/analyze.py --classes dev C0 C1-v2-medium C2-v2-medium
    .venv/bin/python scripts/analyze.py --classes test C0 C1-v2-medium C2-v2-medium --sample 20
"""
import argparse
import csv
import json
import random
from itertools import combinations

import numpy as np
from scipy.stats import binomtest

import harness
import judge

ROOT = harness.ROOT
SEED = 2026
N_BOOT = 10000


def class_ids(which):
    kept = [t["task_id"] for t in harness.load_tasks()]
    with (ROOT / "data/selection/dev_classes.csv").open(encoding="utf-8") as f:
        dev = {r["task_id"] for r in csv.DictReader(f)}
    return {"dev": [t for t in kept if t in dev], "test": [t for t in kept if t not in dev],
            "all": kept}[which]


def weak_methods():
    with (ROOT / "data/selection/weak_tests.csv").open(encoding="utf-8") as f:
        return {(r["task_id"], r["method_name"]) for r in csv.DictReader(f)}


def load_run(name, task_ids):
    results = {}
    for t in task_ids:
        f = ROOT / "runs" / name / f"{t}.json"
        if f.exists():
            results[t] = json.loads(f.read_text(encoding="utf-8"))
    return results


def outcomes(results):
    """(task_id, method_name) -> True if the final version passes its tests."""
    return {(t, m["method_name"]): bool(m["passed"]) for t, r in results.items() for m in r["methods"]}


def share(values):
    return f"{sum(values)} of {len(values)} ({sum(values) / len(values):.1%})" if values else "none"


def judge_rows(results):
    """The judge's verdicts on first versions, with the tests on the same versions."""
    rows = []
    for t, r in results.items():
        if r.get("setup") == "C2":
            rows += [{"task_id": t, "method_name": m["method_name"], "verdict": m["review"]["verdict"],
                      "passed": m["passed_first"], "reason": m["review"]["reason"],
                      "revised": m["revision"] is not None, "passed_final": m["passed"]}
                     for m in r["methods"] if m.get("review")]
        elif r.get("setup") == "C1" and r.get("review"):
            rows.append({"task_id": t, "method_name": "(whole class)", "verdict": r["review"]["verdict"],
                         "passed": r["class_passed_first"], "reason": r["review"]["reason"],
                         "revised": r["revision"] is not None, "passed_final": r["class_passed"]})
    return rows


def describe(name, results, weak):
    out = outcomes(results)
    print(f"\n{name}: {len(results)} classes")
    print(f"  methods passing: {share(list(out.values()))}")
    print(f"  without the weak methods: {share([v for k, v in out.items() if k not in weak])}")
    print(f"  classes passing: {share([bool(r['class_passed']) for r in results.values()])}")
    rows = judge_rows(results)
    if not rows:
        return
    unit = "classes" if rows[0]["method_name"] == "(whole class)" else "methods"
    a = judge.agreement(rows)
    print(f"  judge on first versions ({a['n']} {unit}): agreement {a['accuracy']:.2f}, kappa {a['kappa']:.2f}, "
          f"TPR {a['tpr']:.2f} of {a['n_passing']} passing, TNR {a['tnr']:.2f} of {a['n_failing']} failing")
    first = {(t, m["method_name"]): bool(m["passed_first"]) for t, r in results.items() for m in r["methods"]}
    fixed = sum(not first[k] and out[k] for k in out)
    broken = sum(first[k] and not out[k] for k in out)
    p = binomtest(min(fixed, broken), fixed + broken).pvalue if fixed + broken else 1.0
    print(f"  revisions: {sum(r['revised'] for r in rows)} after a NOT OK; methods fixed {fixed}, "
          f"broken {broken} (McNemar p = {p:.3f})")


def compare(name_a, a, name_b, b):
    common = sorted(set(a) & set(b))
    oa, ob = outcomes({t: a[t] for t in common}), outcomes({t: b[t] for t in common})
    keys = sorted(set(oa) & set(ob))
    only_a = sum(oa[k] and not ob[k] for k in keys)
    only_b = sum(ob[k] and not oa[k] for k in keys)
    p = binomtest(min(only_a, only_b), only_a + only_b).pvalue if only_a + only_b else 1.0
    # Cluster bootstrap over classes of the difference in the share of passing methods (b - a).
    per_class = np.array([[sum(ob[k] for k in keys if k[0] == t) - sum(oa[k] for k in keys if k[0] == t),
                           sum(k[0] == t for k in keys)] for t in common], dtype=float)
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, len(common), size=(N_BOOT, len(common)))
    diffs = per_class[idx, 0].sum(axis=1) / per_class[idx, 1].sum(axis=1)
    low, high = np.percentile(diffs, [2.5, 97.5])
    diff = per_class[:, 0].sum() / per_class[:, 1].sum()
    print(f"  {name_b} vs {name_a} on {len(keys)} methods of {len(common)} classes: "
          f"passes only in {name_b} {only_b}, only in {name_a} {only_a}, McNemar p = {p:.3f}; "
          f"difference {diff:+.1%}, 95% bootstrap interval [{low:+.1%}, {high:+.1%}]")


def sample_disagreements(name, results, n):
    rows = [r for r in judge_rows(results) if (r["verdict"] == "OK") != bool(r["passed"])]
    chosen = random.Random(SEED).sample(rows, min(n, len(rows)))
    out = ROOT / "runs" / f"error_analysis_{name}.csv"
    fields = ["task_id", "method_name", "verdict", "tests_first", "reason", "revised", "tests_final",
              "type", "who_is_right"]
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in chosen:
            writer.writerow({"task_id": r["task_id"], "method_name": r["method_name"], "verdict": r["verdict"],
                             "tests_first": "pass" if r["passed"] else "fail", "reason": r["reason"],
                             "revised": r["revised"], "tests_final": "pass" if r["passed_final"] else "fail",
                             "type": "", "who_is_right": ""})
    print(f"  {len(chosen)} of {len(rows)} disagreements of {name} -> {out.relative_to(ROOT)}")


def main():
    parser = argparse.ArgumentParser(description="Pass rates, judge scores and comparisons between runs.")
    parser.add_argument("runs", nargs="+", help="folders in runs/, such as C0 C1-v2-medium C2-v2-medium")
    parser.add_argument("--classes", choices=["dev", "test", "all"], default="test",
                        help="dev: the 10 development classes; test: the other 61 (default); all: the 71")
    parser.add_argument("--sample", type=int, default=0, help="disagreements to write for the error analysis")
    args = parser.parse_args()

    task_ids, weak = class_ids(args.classes), weak_methods()
    runs = {name: load_run(name, task_ids) for name in args.runs}
    print(f"{args.classes} classes: {len(task_ids)}")
    for name, results in runs.items():
        if not results:
            print(f"\n{name}: no results on these classes")
            continue
        describe(name, results, weak)
    print("\nCOMPARISONS (method by method, classes present in both runs)")
    for (name_a, a), (name_b, b) in combinations([(n, r) for n, r in runs.items() if r], 2):
        compare(name_a, a, name_b, b)
    if args.sample:
        print("\nERROR ANALYSIS")
        for name, results in runs.items():
            if judge_rows(results):
                sample_disagreements(name, results, args.sample)


if __name__ == "__main__":
    main()
