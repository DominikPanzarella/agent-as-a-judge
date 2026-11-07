"""Does a method come before the method that fills a field it reads?

The method order follows the calls between methods, not the fields. This script reads the
reference solution of each kept class and lists every pair in which a method reads a field
(self.x) that a later method writes: an assignment, an item assignment, or a call such as append
or update. A pair is "new field" when the field is not set in __init__, so the coder could not
know it exists; otherwise the field is already in the skeleton and the pair is "fills".

On the 71 classes there are 43 pairs, all of kind "fills", so the order stays as it is. The pairs
go to data/selection/field_order_check.csv.

    .venv/bin/python scripts/check_field_order.py
"""
import ast
import csv

import coder
import harness

OUT = harness.ROOT / "data/selection/field_order_check.csv"
MUTATING = {"append", "extend", "insert", "remove", "pop", "clear", "update", "add", "setdefault",
            "discard", "popitem", "appendleft", "sort", "reverse"}


def self_field(node):
    """The name x of self.x, also inside self.x[...] or self.x.y; None for anything else."""
    while isinstance(node, (ast.Subscript, ast.Attribute)):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
            return node.attr
        node = node.value
    return None


def fields(function):
    """The fields a method writes and the fields it reads."""
    written, read = set(), set()
    for node in ast.walk(function):
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            for target in node.targets if isinstance(node, ast.Assign) else [node.target]:
                for t in target.elts if isinstance(target, ast.Tuple) else [target]:
                    if self_field(t):
                        written.add(self_field(t))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in MUTATING:
            if self_field(node.func.value):
                written.add(self_field(node.func.value))
        if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self"
                and isinstance(node.ctx, ast.Load)):
            read.add(node.attr)
    return written, read


def main():
    order, rows = coder.method_order(), []
    for task in harness.load_tasks():
        tree = ast.parse(task["solution_code"])
        cls = next(c for c in tree.body if isinstance(c, ast.ClassDef) and c.name == task["class_name"])
        functions = {f.name: f for f in cls.body if isinstance(f, ast.FunctionDef)}
        in_init = fields(functions["__init__"])[0] if "__init__" in functions else set()
        steps = order[task["task_id"]]
        for i, name in enumerate(steps):
            read = fields(functions[name])[1] - set(functions)
            for j, later in enumerate(steps[i + 1:], start=i + 2):
                for field in sorted(read & fields(functions[later])[0]):
                    rows.append({"task_id": task["task_id"], "reader": name, "reader_step": i + 1,
                                 "writer": later, "writer_step": j, "field": field,
                                 "kind": "fills" if field in in_init else "new field"})
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    new = [r for r in rows if r["kind"] == "new field"]
    print(f"{len(rows)} pairs in {len({r['task_id'] for r in rows})} classes, {len(new)} with a field "
          f"that __init__ does not set -> {OUT.relative_to(harness.ROOT)}")
    for r in new:
        print(f"  {r['task_id']}: {r['reader']} reads {r['field']}, which only {r['writer']} creates")


if __name__ == "__main__":
    main()
