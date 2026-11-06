"""Summary of the pilot on the development classes. It reads saved results and sends no request.

It answers the pilot's questions. How often does the coder pass, and how many methods change
result between two identical runs of C0, only by chance? How does each judge (v1 or v2, low or
medium effort) agree with the tests, and what does it cost? What would the full runs cost?

It also writes runs/pilot_disagreements.csv, with every method on which a judge and the tests
disagree. The column who_is_right is left empty: we fill it in by hand (judge, tests, or unclear).
"""
import csv
import json
from pathlib import Path

import judge

ROOT = Path(__file__).resolve().parent.parent
DEV = ROOT / "data/selection/dev_classes.csv"
DISAGREEMENTS = ROOT / "runs/pilot_disagreements.csv"
N_METHODS = 289  # all kept methods, for the cost projection
CONFIGS = [(v, e) for v in judge.VERSIONS for e in judge.EFFORTS]


def dev_classes():
    with DEV.open(encoding="utf-8") as f:
        return [r["task_id"] for r in csv.DictReader(f)]


def load(folder, task_ids):
    out = {}
    for t in task_ids:
        f = folder / f"{t}.json"
        if f.exists():
            out[t] = json.loads(f.read_text(encoding="utf-8"))
    return out


def coder_section(task_ids):
    runs = {name: load(ROOT / "runs" / name, task_ids) for name in ("C0", "C0-r2")}
    print("CODER (setup C0)")
    for name, results in runs.items():
        methods = [m for r in results.values() for m in r["methods"]]
        if not methods:
            print(f"  {name}: no results")
            continue
        cost = sum(m["cost"] or 0 for m in methods)
        tokens = sum(m["prompt_tokens"] + m["completion_tokens"] for m in methods)
        print(f"  {name}: {sum(m['passed'] for m in methods)} of {len(methods)} methods pass, "
              f"{sum(r['class_passed'] for r in results.values())} of {len(results)} classes pass, "
              f"{sum(not m['valid'] for m in methods)} invalid replies, "
              f"{tokens / len(methods):.0f} tokens and {cost / len(methods):.5f} $ per method")
    both = [t for t in task_ids if t in runs["C0"] and t in runs["C0-r2"]]
    flips = []
    for t in both:
        second = {m["method_name"]: m["passed"] for m in runs["C0-r2"][t]["methods"]}
        flips += [(t, m["method_name"], m["passed"], second[m["method_name"]])
                  for m in runs["C0"][t]["methods"] if m["passed"] != second[m["method_name"]]]
    n = sum(len(runs["C0"][t]["methods"]) for t in both)
    print(f"  methods that change result between the two runs: {len(flips)} of {n}")
    for t, name, first, second in flips:
        print(f"    {t} {name}: {'pass' if first else 'fail'} -> {'pass' if second else 'fail'}")
    methods = [m for r in runs["C0"].values() for m in r["methods"]]
    return sum(m["cost"] or 0 for m in methods) / max(len(methods), 1)


def judge_section(task_ids):
    print("\nJUDGE on run C0 (agreement with the tests)")
    print(f"  {'judge':<12} {'methods':>7} {'agree':>6} {'kappa':>6} {'OK to fail':>11} "
          f"{'NOT OK to pass':>15} {'runs/method':>12} {'$/method':>9}")
    rows, costs = [], {}
    for version, effort in CONFIGS:
        results = load(judge.folder("C0", version, effort), task_ids)
        judged = [dict(m, task_id=t) for t, r in results.items() for m in r["methods"] if not m.get("auto")]
        if not judged:
            print(f"  {version}-{effort:<9} no results")
            continue
        a = judge.agreement(judged)
        cost = sum(m.get("cost") or 0 for m in judged) / len(judged)
        costs[(version, effort)] = cost
        runs = sum(m.get("n_runs", 0) for m in judged) / len(judged)
        print(f"  {version + '-' + effort:<12} {a['n']:>7} {a['accuracy']:>6.2f} {a['kappa']:>6.2f} "
              f"{a['false_ok']:>5.2f} of {a['n_failing']:<3} {a['false_not_ok']:>8.2f} of {a['n_passing']:<4} "
              f"{runs:>12.1f} {cost:>9.5f}")
        for m in judged:
            if m["verdict"] in ("OK", "NOT OK") and (m["verdict"] == "OK") != bool(m["passed"]):
                rows.append({"judge": f"{version}-{effort}", "task_id": m["task_id"],
                             "method_name": m["method_name"], "verdict": m["verdict"],
                             "tests": "pass" if m["passed"] else "fail",
                             "reason": m["reason"], "who_is_right": ""})
    with DISAGREEMENTS.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["judge", "task_id", "method_name", "verdict", "tests",
                                               "reason", "who_is_right"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"  {len(rows)} disagreements -> {DISAGREEMENTS.relative_to(ROOT)} (column who_is_right to fill in by hand)")
    return costs


def main():
    task_ids = dev_classes()
    print(f"{len(task_ids)} development classes\n")
    coder_cost = coder_section(task_ids)
    judge_costs = judge_section(task_ids)
    print(f"\nPROJECTION for {N_METHODS} methods")
    print(f"  coder, one run of C0: {coder_cost * N_METHODS:.2f} $ (C2 can need up to twice as many requests)")
    for (version, effort), cost in judge_costs.items():
        print(f"  judge {version}-{effort}, one pass over all methods: {cost * N_METHODS:.2f} $")


if __name__ == "__main__":
    main()
