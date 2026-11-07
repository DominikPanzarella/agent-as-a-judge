"""Fix the order in which the coder writes the methods of each class.

We keep the skeleton order and move a method only so that the methods it calls come first. Methods
in a dependency cycle are flagged. Output: data/selection/method_order.csv.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLASSEVAL = ROOT / "data/raw/classeval/ClassEval_data.json"
CLASSES = ROOT / "data/selection/classes.csv"
OUT = ROOT / "data/selection/method_order.csv"

# Dependencies in ClassEval that the reference solution does not have, found by reading the code.
# ClassEval_63: process_data never calls process, so the annotation creates a false cycle.
FALSE_DEPENDENCIES = {("ClassEval_63", "process_data", "process")}


def order(names, deps):
    """Skeleton order, with each method preceded by the methods it calls."""
    done, cycle, visiting = [], [], set()

    def visit(n):
        if n in done:
            return
        if n in visiting:
            cycle.append(n)
            return
        visiting.add(n)
        for d in deps[n]:
            visit(d)
        visiting.discard(n)
        if n not in done:
            done.append(n)

    for n in names:
        visit(n)
    return done, sorted(set(cycle), key=names.index)


kept = {r["task_id"] for r in csv.DictReader(CLASSES.open(encoding="utf-8")) if r["kept"] == "1"}
tasks = [t for t in json.loads(CLASSEVAL.read_text(encoding="utf-8")) if t["task_id"] in kept]

rows, moved_classes, cycle_classes = [], [], []
for t in tasks:
    names = [m["method_name"] for m in t["methods_info"]]
    deps = {
        m["method_name"]: [
            d for d in m["dependencies"]["method_dependencies"]
            if d != m["method_name"] and (t["task_id"], m["method_name"], d) not in FALSE_DEPENDENCIES
        ]
        for m in t["methods_info"]
    }
    sequence, cycle = order(names, deps)
    if sequence != names:
        moved_classes.append(t["task_id"])
    if cycle:
        cycle_classes.append(t["task_id"])
    for step, n in enumerate(sequence, start=1):
        rows.append({
            "task_id": t["task_id"],
            "class_name": t["class_name"],
            "step": step,
            "method_name": n,
            "skeleton_position": names.index(n) + 1,
            "depends_on": " ".join(deps[n]),
            "in_cycle": int(n in cycle),
        })

with OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

print(f"{len(tasks)} classes, {len(rows)} methods -> {OUT.relative_to(ROOT)}")
print(f"order differs from the skeleton in {len(moved_classes)} classes: {' '.join(moved_classes)}")
print(f"classes with a dependency cycle: {len(cycle_classes)} {' '.join(cycle_classes)}")
