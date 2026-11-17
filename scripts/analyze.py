"""Analysis of the runs: pass rates, judge scores and comparisons between setups. Sends no request.

For each run: methods and classes passing (with and without the weak methods) and, when there is a
judge, its agreement, kappa, TPR and TNR on the first versions, and the final versions against
the first ones. For each pair of runs, and for final against first versions: an exact McNemar
test and a bootstrap interval over classes. --sample N writes N disagreements per run to
runs/error_analysis_<run>.csv, to classify by hand. --pool takes the repetitions of each setup
(<prefix>-r1, -r2, ...) together and compares the setups on all of them.

    .venv/bin/python scripts/analyze.py --classes dev C0 C2-v2-medium
    .venv/bin/python scripts/analyze.py --classes test C2-9b C3-9b
    .venv/bin/python scripts/analyze.py --classes test C2-9b --sample 20
    .venv/bin/python scripts/analyze.py --classes test --pool C2-9b-8k C3-9b-8k C2n-9b-8k
"""
import argparse
import csv
import json
import random
from collections import Counter
from itertools import combinations

import numpy as np
from scipy.stats import binomtest

import harness
import judge

ROOT = harness.ROOT
SEED = 2026
N_BOOT = 10000


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


def first_outcomes(results):
    """(task_id, method_name) -> True if the first version passes its tests."""
    return {(t, m["method_name"]): bool(m["passed_first"]) for t, r in results.items() for m in r["methods"]}


def share(values):
    return f"{sum(values)} of {len(values)} ({sum(values) / len(values):.1%})" if values else "none"


def judge_rows(results):
    """The judge's verdicts on first versions, with the tests on the same versions."""
    rows = []
    for t, r in results.items():
        if r.get("setup") in ("C2", "C3"):
            rows += [{"task_id": t, "method_name": m["method_name"], "verdict": m["review"]["verdict"],
                      "passed": m["passed_first"], "reason": m["review"]["reason"],
                      "revised": m["revision"] is not None, "passed_final": m["passed"]}
                     for m in r["methods"] if m.get("review")]
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
    a = judge.agreement(rows)
    print(f"  judge on first versions ({a['n']} methods): agreement {a['accuracy']:.2f}, kappa {a['kappa']:.2f}, "
          f"TPR {a['tpr']:.2f} of {a['n_passing']} passing, TNR {a['tnr']:.2f} of {a['n_failing']} failing")
    first = first_outcomes(results)
    fixed = sum(not first[k] and out[k] for k in out)
    broken = sum(first[k] and not out[k] for k in out)
    print(f"  revisions: {sum(r['revised'] for r in rows)} after a NOT OK; methods fixed {fixed}, broken {broken}")
    paired("first versions", first, "final versions", out)


def compare(name_a, a, name_b, b):
    common = set(a) & set(b)
    paired(name_a, outcomes({t: a[t] for t in common}), name_b, outcomes({t: b[t] for t in common}))


def difference(oa, ob):
    """The same methods under two conditions, b against a: exact McNemar test and bootstrap over
    classes of the difference in the share of passing methods."""
    keys = sorted(set(oa) & set(ob))
    common = sorted({k[0] for k in keys})
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
    return {"n_methods": len(keys), "n_classes": len(common), "only_a": only_a, "only_b": only_b,
            "p": p, "diff": diff, "low": low, "high": high}


def paired(name_a, oa, name_b, ob):
    d = difference(oa, ob)
    p = f"p = {d['p']:.3f}" if d["p"] >= 0.001 else "p < 0.001"
    print(f"  {name_b} vs {name_a} on {d['n_methods']} methods of {d['n_classes']} classes: "
          f"passes only in {name_b} {d['only_b']}, only in {name_a} {d['only_a']}, McNemar {p}; "
          f"difference {d['diff']:+.1%}, 95% bootstrap interval [{d['low']:+.1%}, {d['high']:+.1%}]")


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


def repetitions(prefix):
    """The runs of one setup that differ only in the repetition: <prefix>-r1, <prefix>-r2, ..."""
    return sorted(f.name for f in (ROOT / "runs").glob(f"{prefix}-r[0-9]*") if f.is_dir())


def pooled(names, task_ids):
    """The repetitions of one setup as one set of outcomes. The class stays the unit of the
    bootstrap, so the repetition goes into the method name."""
    first, final, runs = {}, {}, []
    for i, name in enumerate(names, start=1):
        results = load_run(name, task_ids)
        runs.append(results)
        first.update({(t, f"{m}#{i}"): v for (t, m), v in first_outcomes(results).items()})
        final.update({(t, f"{m}#{i}"): v for (t, m), v in outcomes(results).items()})
    return first, final, runs


def same_inputs(runs_a, runs_b):
    """Two setups where the second reuses the first: what changes on the methods they share."""
    rejected = Counter()
    reviews = changed = 0
    for a, b in zip(runs_a, runs_b):
        old = {(t, m["method_name"]): m for t, r in a.items() for m in r["methods"]}
        for t, r in b.items():
            for m in r["methods"]:
                o, review = old[(t, m["method_name"])], m["review"] or {}
                if review.get("reused") and review["verdict"] == "NOT OK":
                    rejected["failing" if not o["passed_first"] else "passing"] += 1
                    for label, x in (("a", o), ("b", m)):
                        rejected[f"fixed_{label}"] += bool(not x["passed_first"] and x["passed"])
                        rejected[f"broken_{label}"] += bool(x["passed_first"] and not x["passed"])
                elif (review and o["review"] and not review.get("reused") and m["first"]["valid"]
                      and o["first"]["valid"] and m["first"]["code"] == o["first"]["code"]):
                    reviews += 1
                    changed += review["verdict"] != o["review"]["verdict"]
    return rejected, reviews, changed


def pool(prefixes, task_ids):
    """The repetitions of each setup together, and the setups against each other."""
    print("\nREPETITIONS TOGETHER (bootstrap over classes)")
    pools = {}
    for prefix in prefixes:
        names = repetitions(prefix)
        if not names:
            print(f"  {prefix}: no folder runs/{prefix}-r1, -r2, ...")
            continue
        first, final, runs = pooled(names, task_ids)
        pools[prefix] = (final, runs)
        print(f"  {prefix}: {len(names)} runs, methods passing {share(list(first.values()))} in the first versions, "
              f"{share(list(final.values()))} in the final ones")
        paired("first versions", first, "final versions", final)
    for (name_a, (a, runs_a)), (name_b, (b, runs_b)) in combinations(pools.items(), 2):
        paired(name_a, a, name_b, b)
        if all(r and next(iter(r.values())).get("reuse", "").startswith(name_a) for r in runs_b):
            rejected, reviews, changed = same_inputs(runs_a, runs_b)
            kind = next(iter(runs_b[0].values()))
            if kind.get("feedback") == "verdict":
                print(f"    rejected by the same review in both: {rejected['failing'] + rejected['passing']} methods; "
                      f"of the {rejected['failing']} failing ones, fixed {rejected['fixed_a']} in {name_a} and "
                      f"{rejected['fixed_b']} in {name_b}; of the {rejected['passing']} passing ones, broken "
                      f"{rejected['broken_a']} and {rejected['broken_b']}")
            if kind["setup"] == "C3":
                print(f"    new reviews of the same code in {name_b}: {reviews}, verdict changed in {changed}")


def main():
    parser = argparse.ArgumentParser(description="Pass rates, judge scores and comparisons between runs.")
    parser.add_argument("runs", nargs="*", help="folders in runs/, such as C2-9b C3-9b")
    parser.add_argument("--pool", nargs="+", default=[], metavar="PREFIX",
                        help="setups whose repetitions are analysed together, such as C2-9b-8k C2n-9b-8k")
    parser.add_argument("--classes", choices=["dev", "test", "all"], default="test",
                        help="dev: the 10 development classes; test: the other 61 (default); all: the 71")
    parser.add_argument("--sample", type=int, default=0, help="disagreements to write for the error analysis")
    args = parser.parse_args()

    task_ids, weak = harness.class_ids(args.classes), weak_methods()
    runs = {name: load_run(name, task_ids) for name in args.runs}
    print(f"{args.classes} classes: {len(task_ids)}")
    for name, results in runs.items():
        if not results:
            print(f"\n{name}: no results on these classes")
            continue
        describe(name, results, weak)
    if len(runs) > 1:
        print("\nCOMPARISONS (method by method, classes present in both runs)")
    for (name_a, a), (name_b, b) in combinations([(n, r) for n, r in runs.items() if r], 2):
        compare(name_a, a, name_b, b)
    if args.pool:
        pool(args.pool, task_ids)
    if args.sample:
        print("\nERROR ANALYSIS")
        for name, results in runs.items():
            if judge_rows(results):
                sample_disagreements(name, results, args.sample)


if __name__ == "__main__":
    main()
