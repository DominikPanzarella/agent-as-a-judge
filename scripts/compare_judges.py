"""The prompt variants of the judge on the pilot classes, from saved verdicts. Sends no request.

Every judge found in runs/judge for both pilot runs of the 9B (C0-9b and C0-9b-r2) is compared
with the tests: TPR, TNR, kappa and cost. Each judge is also compared with v2 on the same methods:
how many methods only one of the two gets right, with an exact McNemar test. The repeat of v2
(tag r2) shows how much v2 changes on its own, the noise a variant has to beat. For a judge that
gives a confidence, it also says whether the confidence is lower on the verdicts the tests
contradict. Disagreements with the tests go to runs/judge_variants_disagreements.csv, to read by
hand; the chart goes to docs/figures/judge_variants.png.

    .venv/bin/python scripts/compare_judges.py
"""
import csv

from scipy.stats import binomtest

import harness
import judge
import pilot_report
import plot_results as plot

ROOT = harness.ROOT
RUNS = ["C0-9b", "C0-9b-r2"]
BASE = "v2-medium"
DISAGREEMENTS = ROOT / "runs/judge_variants_disagreements.csv"


def test_methods():
    """Methods of the 61 test classes, for the cost of one pass of the judge in the study."""
    dev = set(pilot_report.dev_classes())
    with (ROOT / "data/selection/method_order.csv").open(encoding="utf-8") as f:
        return sum(r["task_id"] not in dev for r in csv.DictReader(f))


def judges():
    """Names such as v2-medium or v2-medium-r2 that have verdicts for both runs."""
    found = {}
    for run in RUNS:
        for d in (ROOT / "runs/judge").glob(f"{run}-v*"):
            found.setdefault(d.name[len(run) + 1:], set()).add(run)
    return sorted(name for name, runs in found.items() if runs == set(RUNS))


def verdicts(name):
    out = {}
    for run in RUNS:
        for t, r in pilot_report.load(ROOT / "runs/judge" / f"{run}-{name}", pilot_report.dev_classes()).items():
            for m in r["methods"]:
                if not m.get("auto") and m["verdict"] in ("OK", "NOT OK"):
                    out[(run, t, m["method_name"])] = m
    return out


def right(m):
    return (m["verdict"] == "OK") == bool(m["passed"])


def confidence(name, v):
    """Is the judge less sure of the verdicts the tests contradict? Printed only if it gave a confidence."""
    scored = [(m["confidence"], right(m)) for m in v.values() if m.get("confidence") is not None]
    good, bad = [c for c, r in scored if r], [c for c, r in scored if not r]
    if not good or not bad:
        return
    pairs = [(g > b) + 0.5 * (g == b) for g in good for b in bad]
    again = [m for m in v.values() if len(m.get("looks", [])) > 1]
    changed = sum(m["looks"][0]["verdict"] != m["verdict"] for m in again)
    print(f"  {name}: confidence {min(good + bad)} to {max(good + bad)}; mean {sum(good) / len(good):.0f} on the "
          f"{len(good)} verdicts the tests confirm, {sum(bad) / len(bad):.0f} on the {len(bad)} they contradict; "
          f"the confirmed one has the higher confidence in {sum(pairs) / len(pairs):.0%} of the pairs (50% is chance)"
          + (f"; looked again at {len(again)} methods, {changed} verdicts changed" if again else ""))


def chart(rows):
    height = 1.5 + 0.5 * len(rows)
    low, high = min(r["kappa"] for r in rows), max(r["kappa"] for r in rows)
    fig, ax = plot.figure(f"Every prompt of the judge has a kappa between {low:.2f} and {high:.2f}",
                          "The 9B's methods of the two pilot runs; TPR: passing methods called OK, "
                          "TNR: failing methods called NOT OK", height)
    for y, r in enumerate(reversed(rows)):
        for key, color, dy, label in [("tpr", plot.BLUE, 0.12, "TPR"), ("tnr", plot.ORANGE, -0.12, "TNR")]:
            ax.scatter([r[key]], [y + dy], s=60, color=color, edgecolor=plot.SURFACE, linewidth=1.5,
                       zorder=3, label=label if y == 0 else None)
            ax.text(r[key] + 0.02, y + dy, f"{r[key]:.2f}", va="center", fontsize=8.5, color=plot.INK_2)
        ax.text(1.08, y, f"kappa {r['kappa']:.2f}", va="center", fontsize=9, color=plot.INK)
    ax.set_yticks(range(len(rows)), [r["judge"] for r in reversed(rows)])
    ax.set_xlim(0, 1.3)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_xlabel("share of methods")
    ax.legend(loc="lower right", fontsize=9.5, ncol=2, bbox_to_anchor=(1.0, 1.0), handletextpad=0.3)
    plot.OUT.mkdir(parents=True, exist_ok=True)
    plot.save(fig, "judge_variants.png", 1 - 1.05 / height, left=0.2)


def main():
    names = judges()
    if BASE not in names:
        print(f"no verdicts of {BASE} for {', '.join(RUNS)}")
        return
    base, n_test = verdicts(BASE), test_methods()
    print(f"Judges on the 9B's methods of {' and '.join(RUNS)}, against the tests")
    print(f"  {'judge':<14} {'methods':>7} {'TPR':>5} {'TNR':>5} {'kappa':>6} {'runs/m':>7} {'$/method':>9} "
          f"{f'$ for {n_test}':>10}   vs {BASE}: only it right / only {BASE} right, McNemar p")
    rows, wrong = [], []
    for name in names:
        v = verdicts(name)
        a = judge.agreement(list(v.values()))
        cost = sum(m.get("cost") or 0 for m in v.values()) / len(v)
        runs = sum(m.get("n_runs", 0) for m in v.values()) / len(v)
        common = [k for k in v if k in base]
        only_it = sum(right(v[k]) and not right(base[k]) for k in common)
        only_base = sum(right(base[k]) and not right(v[k]) for k in common)
        p = binomtest(min(only_it, only_base), only_it + only_base).pvalue if only_it + only_base else 1.0
        versus = "" if name == BASE else f"{only_it:>3} / {only_base:<3} p = {p:.2f}"
        print(f"  {name:<14} {a['n']:>7} {a['tpr']:>5.2f} {a['tnr']:>5.2f} {a['kappa']:>6.2f} {runs:>7.1f} "
              f"{cost:>9.5f} {cost * n_test:>10.3f}   {versus}")
        rows.append({"judge": name, **a})
        wrong += [{"judge": name, "run": run, "task_id": t, "method_name": n, "verdict": m["verdict"],
                   "tests": "pass" if m["passed"] else "fail", "n_runs": m.get("n_runs", 0), "reason": m["reason"]}
                  for (run, t, n), m in v.items() if not right(m)]
    with DISAGREEMENTS.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(wrong[0]))
        writer.writeheader()
        writer.writerows(wrong)
    print(f"  {len(wrong)} disagreements with the tests -> {DISAGREEMENTS.relative_to(ROOT)}")
    per_method = {}
    for w in wrong:
        per_method.setdefault((w["run"], w["task_id"], w["method_name"]), set()).add(w["judge"])
    shared = sorted(k for k, js in per_method.items() if len(js) == len(names))
    print(f"  {len(shared)} of {len(per_method)} methods with a disagreement are wrong for every judge:")
    for run, t, n in shared:
        print(f"    {run} {t}.{n}")
    for name in names:
        confidence(name, verdicts(name))
    chart(rows)


if __name__ == "__main__":
    main()
