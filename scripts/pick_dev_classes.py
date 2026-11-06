"""Pick the development classes, the ones we use to try out and tune the coder and the judge.

ClassEval_19 and ClassEval_55 were the first trial. The pilot adds 8 classes drawn at random, with
a fixed seed, from the other kept classes. All 10 stay out of the final analysis, so that we do
not evaluate the setups on the classes we used to choose them. The result goes to
data/selection/dev_classes.csv.
"""
import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLASSES = ROOT / "data/selection/classes.csv"
DEV = ROOT / "data/selection/dev_classes.csv"
SEED = 2026
FIRST_TRIAL = ["ClassEval_19", "ClassEval_55"]
N_PILOT = 8


def number(task_id):
    return int(task_id.split("_")[1])


def main():
    with CLASSES.open(encoding="utf-8") as f:
        kept = {r["task_id"]: r for r in csv.DictReader(f) if r["kept"] == "1"}
    pool = sorted((t for t in kept if t not in FIRST_TRIAL), key=number)
    pilot = sorted(random.Random(SEED).sample(pool, N_PILOT), key=number)
    rows = ([{"task_id": t, "group": "first trial"} for t in FIRST_TRIAL]
            + [{"task_id": t, "group": "pilot"} for t in pilot])
    for row in rows:
        row.update(class_name=kept[row["task_id"]]["class_name"], n_methods=kept[row["task_id"]]["n_methods"])
    with DEV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "class_name", "n_methods", "group"])
        writer.writeheader()
        writer.writerows(rows)
    n_methods = sum(int(r["n_methods"]) for r in rows)
    print(f"{len(rows)} development classes with {n_methods} methods -> {DEV.relative_to(ROOT)}")
    for r in rows:
        print(f"  {r['task_id']:<13} {r['class_name']:<28} {r['n_methods']:>2} methods  ({r['group']})")
    print(f"the final analysis keeps {len(kept) - len(rows)} classes")


if __name__ == "__main__":
    main()
