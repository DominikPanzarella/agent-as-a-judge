"""Summarise ClassEval as annotated by benchmarks+ (trivial / problematic methods) and its method dependencies."""
import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUGMENTED = ROOT / "data/raw/benchmarks_plus/benchmarks+/classeval_augmented.jsonl"
CLASSEVAL = ROOT / "data/raw/classeval/ClassEval_data.json"

methods = [json.loads(line) for line in AUGMENTED.open(encoding="utf-8") if line.strip()]
by_class = collections.defaultdict(list)
for m in methods:
    by_class[m["task_id"]].append(m)

print(f"methods: {len(methods)}, classes: {len(by_class)}")
for flag in ("is_trivial", "is_challenging", "is_genuinely_challenging", "is_problematic"):
    print(f"  {flag}: {sum(bool(m[flag]) for m in methods)}")

print("issues found:")
for issue, n in collections.Counter(i for m in methods for i in m["issues_found"] or []).most_common():
    print(f"  {n:3d}  {issue}")

problematic = {c for c, ms in by_class.items() if any(m["is_problematic"] for m in ms)}
all_trivial = {c for c, ms in by_class.items() if all(m["is_trivial"] for m in ms)}
kept = [c for c in by_class if c not in problematic | all_trivial]
print(f"classes with >=1 problematic method: {len(problematic)}")
print(f"classes with all methods trivial: {len(all_trivial)}")
print(f"kept if both are dropped: {len(kept)} classes, {sum(len(by_class[c]) for c in kept)} methods")

tasks = json.loads(CLASSEVAL.read_text(encoding="utf-8"))
deps = [m["dependencies"]["method_dependencies"] for t in tasks for m in t["methods_info"]]
print(f"methods calling other methods of the class: {sum(bool(d) for d in deps)} of {len(deps)}")
print(f"classes with >=1 such dependency: "
      f"{sum(any(m['dependencies']['method_dependencies'] for m in t['methods_info']) for t in tasks)}")
