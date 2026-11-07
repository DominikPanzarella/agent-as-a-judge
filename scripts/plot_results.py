"""Charts of the pilot for the README, from saved results. Sends no request.

One chart per question, in docs/figures/: the judges' kappa (judge_kappa.png), their claims
(judge_claims.png), why judge and tests disagree (disagreements.png), and the methods passing
before and after the feedback (setups_first_final.png). The colors are checked for color
blindness, and every mark carries its value.

    .venv/bin/python scripts/plot_results.py
"""
import csv
import json
from collections import Counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import harness  # noqa: E402
import judge  # noqa: E402
import pilot_report  # noqa: E402

ROOT = harness.ROOT
OUT = ROOT / "docs/figures"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK_2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#ffffff"
JUDGES = [("v1", "low"), ("v1", "medium"), ("v2", "low"), ("v2", "medium")]

plt.rcParams.update({
    "font.family": ["Helvetica", "Arial", "DejaVu Sans"], "font.size": 11,
    "text.color": INK, "axes.labelcolor": INK_2, "xtick.color": INK_2, "ytick.color": INK,
    "axes.edgecolor": GRID, "axes.facecolor": SURFACE, "figure.facecolor": SURFACE,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.grid": True, "axes.grid.axis": "x", "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.axisbelow": True, "legend.frameon": False,
})


def figure(title, subtitle, height):
    fig, ax = plt.subplots(figsize=(8, height), dpi=200)
    fig.text(0.02, 0.97, title, fontsize=14, fontweight="bold", va="top")
    fig.text(0.02, 0.97 - 0.42 / height, subtitle, fontsize=10.5, color=INK_2, va="top")
    ax.tick_params(axis="y", length=0)
    return fig, ax


def save(fig, name, top, left=0.2):
    fig.subplots_adjust(left=left, right=0.95, top=top, bottom=0.14)
    fig.savefig(OUT / name)
    plt.close(fig)
    print(f"docs/figures/{name}")


def judge_kappa(task_ids):
    with pilot_report.ADJUDICATION.open(encoding="utf-8") as f:
        decided = {(r["task_id"], r["method_name"]): r["who_is_right"] for r in csv.DictReader(f)}
    rows = []
    for version, effort in JUDGES:
        results = pilot_report.load(judge.folder("C0", version, effort), task_ids)
        judged = [dict(m, task_id=t) for t, r in results.items() for m in r["methods"] if not m.get("auto")]
        corrected = []
        for m in judged:
            who = decided.get((m["task_id"], m["method_name"]), "tests")
            if who != "unclear":
                corrected.append(dict(m, passed=bool(m["passed"]) != (who == "judge")))
        rows.append((f"{version}, {effort}", judge.agreement(judged)["kappa"],
                     judge.agreement(corrected)["kappa"]))

    fig, ax = figure("Against our corrected labels the judges agree much more",
                     "Cohen's kappa of each judge on the 38 methods of the pilot; 5 unclear methods "
                     "are left out of the corrected labels", 3.6)
    for y, (name, k_tests, k_labels) in enumerate(reversed(rows)):
        ax.plot([k_tests, k_labels], [y, y], color=GRID, linewidth=3, zorder=1)
        ax.scatter([k_tests], [y], s=90, color=BLUE, edgecolor=SURFACE, linewidth=2, zorder=3,
                   label="against the tests" if y == 0 else None)
        ax.scatter([k_labels], [y], s=90, color=ORANGE, edgecolor=SURFACE, linewidth=2, zorder=3,
                   label="against our corrected labels" if y == 0 else None)
        ax.annotate(f"{k_tests:.2f}", (k_tests, y), xytext=(-12, 0), textcoords="offset points",
                    ha="right", va="center", fontsize=9.5, color=INK_2)
        ax.annotate(f"{k_labels:.2f}", (k_labels, y), xytext=(12, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=9.5, color=INK_2)
    ax.axvline(0, color=INK_2, linewidth=1, linestyle=(0, (3, 3)))
    ax.text(0.01, len(rows) - 0.45, "chance", fontsize=9.5, color=INK_2)
    ax.set_yticks(range(len(rows)), [r[0] for r in reversed(rows)])
    ax.set_xlim(-0.3, 0.8)
    ax.set_ylim(-0.6, len(rows) - 0.3)
    ax.set_xlabel("Cohen's kappa (0 = chance, 1 = perfect agreement)")
    ax.legend(loc="lower right", fontsize=9.5, ncol=2, bbox_to_anchor=(1.0, 1.0), handletextpad=0.3)
    save(fig, "judge_kappa.png", 0.72)


def judge_claims():
    with (ROOT / "runs/pilot_claims.csv").open(encoding="utf-8") as f:
        claims = list(csv.DictReader(f))
    rows = []
    for version, effort in JUDGES:
        mine = [c for c in claims if f"{version}-{effort}" in c["judges"].split()]
        true = sum(c["true"] == "True" for c in mine)
        rows.append((f"{version}, {effort}", true, len(mine) - true))

    fig, ax = figure("With medium effort every claim we ran was true",
                     "Concrete claims in the NOT OK reasons of each judge, checked by running the code",
                     3.4)
    for y, (name, true, false) in enumerate(reversed(rows)):
        ax.barh(y, true, height=0.5, color=BLUE, edgecolor=SURFACE, linewidth=1.5,
                label="true" if y == 0 else None)
        ax.barh(y, false, left=true, height=0.5, color=ORANGE, edgecolor=SURFACE, linewidth=1.5,
                label="false" if y == 0 else None)
        ax.text(true + false + 0.3, y, f"{true} of {true + false} true", va="center", fontsize=9.5,
                color=INK_2)
    ax.set_yticks(range(len(rows)), [r[0] for r in reversed(rows)])
    ax.set_xlim(0, 16)
    ax.set_xlabel("claims")
    ax.legend(loc="lower right", fontsize=9.5, ncol=2, bbox_to_anchor=(1.0, 1.0), handletextpad=0.3)
    save(fig, "judge_claims.png", 0.72)


def disagreements():
    with pilot_report.ADJUDICATION.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    names = {"hidden requirement": "the tests ask for something\nthe docstring does not say",
             "wrong docstring example": "the docstring example\nis wrong",
             "bug the tests miss": "a real bug that\nno test checks",
             "coder bug": "a coder bug that\nthe tests catch",
             "edge case outside the docstring": "an edge case outside\nthe docstring"}
    who_color = {"tests": (BLUE, "the tests are right"), "judge": (ORANGE, "the judge is right"),
                 "unclear": (AQUA, "unclear")}
    counts = Counter((r["category"], r["who_is_right"]) for r in rows)
    order = sorted(counts, key=lambda k: -counts[k])

    fig, ax = figure("Most disagreements are not the judge's fault",
                     f"The {len(rows)} pilot methods on which a judge and the tests disagree, read by hand",
                     3.9)
    seen = set()
    for y, (category, who) in enumerate(reversed(order)):
        color, label = who_color[who]
        ax.barh(y, counts[(category, who)], height=0.5, color=color,
                label=None if who in seen else label)
        seen.add(who)
        ax.text(counts[(category, who)] + 0.08, y, str(counts[(category, who)]), va="center",
                fontsize=9.5, color=INK_2)
    ax.set_yticks(range(len(order)), [names[c] for c, _ in reversed(order)], fontsize=10)
    ax.set_xlim(0, 6)
    ax.set_xticks(range(0, 7))
    ax.set_xlabel("methods")
    handles, labels = ax.get_legend_handles_labels()
    keep = [labels.index(who_color[w][1]) for w in ("tests", "judge", "unclear") if who_color[w][1] in labels]
    ax.legend([handles[i] for i in keep], [labels[i] for i in keep], loc="lower right", fontsize=9.5,
              ncol=3, bbox_to_anchor=(1.0, 1.0), handletextpad=0.3)
    save(fig, "disagreements.png", 0.74, left=0.3)


def setups_first_final(task_ids):
    runs = [("C0, run 1", "C0"), ("C0, run 2", "C0-r2"), ("C1", "C1-v2-medium"), ("C2", "C2-v2-medium")]
    rows = []
    for label, name in runs:
        results = pilot_report.load(ROOT / "runs" / name, task_ids)
        methods = [m for r in results.values() for m in r["methods"]]
        first = sum(m.get("passed_first", m["passed"]) for m in methods)
        rows.append((label, first, sum(m["passed"] for m in methods), len(methods)))

    fig, ax = figure("The first versions vary more than the feedback changes them",
                     "Methods passing their tests out of 38, before and after the judge's feedback "
                     "(10 development classes)", 3.6)
    for y, (label, first, final, n) in enumerate(reversed(rows)):
        ax.plot([first, final], [y, y], color=GRID, linewidth=3, zorder=1)
        ax.scatter([first], [y], s=90, color=BLUE, edgecolor=SURFACE, linewidth=2, zorder=3,
                   label="first versions" if y == 0 else None)
        ax.scatter([final], [y], s=90, color=ORANGE, edgecolor=SURFACE, linewidth=2, zorder=4,
                   label="final versions" if y == 0 else None)
        note = "no feedback" if label.startswith("C0") else f"{first} → {final}"
        ax.annotate(note, (max(first, final), y), xytext=(12, 0), textcoords="offset points",
                    va="center", fontsize=9.5, color=INK_2)
    ax.set_yticks(range(len(rows)), [r[0] for r in reversed(rows)])
    ax.set_xlim(20, 38)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_xlabel("methods passing (of 38)")
    ax.legend(loc="lower right", fontsize=9.5, ncol=2, bbox_to_anchor=(1.0, 1.0), handletextpad=0.3)
    save(fig, "setups_first_final.png", 0.74)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    task_ids = pilot_report.dev_classes()
    judge_kappa(task_ids)
    judge_claims()
    disagreements()
    setups_first_final(task_ids)


if __name__ == "__main__":
    main()
