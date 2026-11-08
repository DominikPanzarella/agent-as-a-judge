"""Three checks on the pilot, from saved results. Sends no request.

1. Resampling. The methods that the judge calls NOT OK in one C0 run are replaced by the same
   method from an independent C0 run, written without feedback. C2 has to do better than this to
   show that the judge's reason helps, and not just a second attempt.
2. The judge on more failing methods. TPR and TNR of judge v2 with medium effort, pooled over the
   27B and 9B runs, with 95% Wilson intervals. The 9B runs contain more failing methods.
3. Power. How often an exact McNemar test on the 251 test methods detects a gain, simulated.

    .venv/bin/python scripts/pilot_controls.py
"""
import json
import math

import numpy as np
from scipy.stats import binomtest

import analyze
import harness
import judge
import pilot_report

ROOT = harness.ROOT
# (run whose NOT OK methods are replaced, independent run with the same coder)
PAIRS = [("C0", "C0-r2"), ("C0-9b", "C0-9b-r2"), ("C0-9b-r2", "C0-9b")]
JUDGES = [("v1", "low"), ("v1", "medium"), ("v2", "low"), ("v2", "medium")]


def methods(folder, task_ids):
    return {(t, m["method_name"]): m for t, r in pilot_report.load(folder, task_ids).items()
            for m in r["methods"]}


def wilson(k, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - half, centre + half


def resampling(task_ids):
    print("RESAMPLING: the judge's NOT OK methods replaced by an independent run, without feedback")
    rows = []
    for run, other in PAIRS:
        first, second = methods(ROOT / "runs" / run, task_ids), methods(ROOT / "runs" / other, task_ids)
        for version, effort in JUDGES:
            folder = judge.folder(run, version, effort)
            if not folder.exists():
                continue
            verdicts = methods(folder, task_ids)
            flagged = [k for k, m in verdicts.items() if not m.get("auto") and m["verdict"] == "NOT OK"]
            fixed = sum(not first[k]["passed"] and second[k]["passed"] for k in flagged)
            broken = sum(first[k]["passed"] and not second[k]["passed"] for k in flagged)
            rows.append({"run": run, "judge": f"{version}-{effort}", "not_ok": len(flagged),
                         "fixed": fixed, "broken": broken})
            print(f"  {run:<9} judge {version}-{effort:<7} {len(flagged):>2} NOT OK -> fixed {fixed}, broken {broken}")
    c2 = [m for r in analyze.load_run("C2-v2-medium", task_ids).values() for m in r["methods"]]
    print(f"  for comparison, C2 with judge v2-medium: {sum(m['revision'] is not None for m in c2)} "
          f"revisions -> fixed {sum(not m['passed_first'] and m['passed'] for m in c2)}, broken "
          f"{sum(m['passed_first'] and not m['passed'] for m in c2)} (all methods, as in analyze.py)")
    return rows


def pooled_judge(task_ids):
    print("\nJUDGE v2-medium ON MORE FAILING METHODS (TPR and TNR with 95% Wilson intervals)")
    # None stands for the judge's reviews inside C2, on its first versions.
    sources = {"27B, C0": "C0", "27B, C2 first versions": None, "9B, run 1": "C0-9b",
               "9B, run 2": "C0-9b-r2"}
    pooled, table = [], {}
    for label, run in sources.items():
        if run is None:
            rows = analyze.judge_rows(analyze.load_run("C2-v2-medium", task_ids))
        elif judge.folder(run, "v2", "medium").exists():
            rows = [m for m in methods(judge.folder(run, "v2", "medium"), task_ids).values()
                    if not m.get("auto")]
        else:
            print(f"  {label}: not judged yet")
            continue
        table[label] = rows
        pooled += rows
    table["all pooled"] = pooled

    result = {}
    for label, rows in table.items():
        a = judge.agreement(rows)
        tp = round(a["tpr"] * a["n_passing"])
        tn = round(a["tnr"] * a["n_failing"])
        result[label] = {"n_passing": a["n_passing"], "n_failing": a["n_failing"], "tpr": a["tpr"],
                         "tpr_ci": wilson(tp, a["n_passing"]), "tnr": a["tnr"],
                         "tnr_ci": wilson(tn, a["n_failing"]), "kappa": a["kappa"]}
        r = result[label]
        print(f"  {label:<24} TPR {r['tpr']:.2f} [{r['tpr_ci'][0]:.2f}, {r['tpr_ci'][1]:.2f}] of "
              f"{r['n_passing']:>3} passing   TNR {r['tnr']:.2f} [{r['tnr_ci'][0]:.2f}, "
              f"{r['tnr_ci'][1]:.2f}] of {r['n_failing']:>2} failing   kappa {r['kappa']:.2f}")
    print("  The pooled runs share the same 10 classes, so the intervals are somewhat too narrow.")
    return result


def power(n_methods=251, reps=4000):
    """Share of simulated runs in which McNemar finds a gain at the 5% level. Each method is fixed
    with probability p_fix and broken with p_broken, independently; with repetitions the methods
    are treated as independent, so that number is optimistic."""
    print(f"\nPOWER of the exact McNemar test on {n_methods} methods ({reps} simulations each)")
    rng = np.random.default_rng(analyze.SEED)
    result = []
    for fixed, broken, label in [(3, 2, "as in the pilot, 3 fixed and 2 broken per 38"),
                                 (4, 1, "3 more methods per 38, about 8 points")]:
        row = {"effect": label}
        for runs in (1, 3):
            n, hits = n_methods * runs, 0
            for _ in range(reps):
                u = rng.random(n)
                b = int((u < fixed / 38).sum())
                c = int(((u >= fixed / 38) & (u < (fixed + broken) / 38)).sum())
                hits += b > c and binomtest(b, b + c, 0.5).pvalue < 0.05
            row[f"{runs}_runs"] = hits / reps
        result.append(row)
        print(f"  {label:<46} one run {row['1_runs']:.2f}, three runs {row['3_runs']:.2f}")
    return result


def main():
    task_ids = pilot_report.dev_classes()
    out = {"resampling": resampling(task_ids), "judge_v2_medium": pooled_judge(task_ids),
           "power": power()}
    path = ROOT / "runs/pilot_controls.json"
    path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\n-> {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
