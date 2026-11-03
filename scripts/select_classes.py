"""Choose the ClassEval classes we use (option A).

A class is dropped if benchmarks+ marks at least one of its methods as problematic,
because its tests can no longer tell us whether the code is right. A class is also
dropped if all of its methods are trivial, because feedback has nothing to improve.
Writes data/selection/classes.csv with one row per class and the reason for each drop.
"""
import collections
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUGMENTED = ROOT / "data/raw/benchmarks_plus/benchmarks+/classeval_augmented.jsonl"
OUT = ROOT / "data/selection/classes.csv"

methods = [json.loads(line) for line in AUGMENTED.open(encoding="utf-8") if line.strip()]
by_class = collections.defaultdict(list)
for m in methods:
    by_class[m["task_id"]].append(m)

rows = []
for task_id, ms in sorted(by_class.items(), key=lambda kv: int(kv[0].split("_")[1])):
    problematic = [m for m in ms if m["is_problematic"]]
    n_trivial = sum(bool(m["is_trivial"]) for m in ms)
    if problematic:
        issues = sorted({i for m in problematic for i in m["issues_found"]})
        names = ", ".join(m["method_name"] for m in problematic)
        reason = f"problematic: {names} ({'; '.join(issues)})"
    elif n_trivial == len(ms):
        reason = "all methods trivial"
    else:
        reason = ""
    rows.append({
        "task_id": task_id,
        "class_name": ms[0]["class_name"],
        "n_methods": len(ms),
        "n_trivial": n_trivial,
        "n_problematic": len(problematic),
        "kept": int(not reason),
        "reason": reason,
    })

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

kept = [r for r in rows if r["kept"]]
print(f"kept {len(kept)} of {len(rows)} classes, {sum(r['n_methods'] for r in kept)} methods -> {OUT.relative_to(ROOT)}")
