"""Setups C1 and C2: the coder writes a class, the judge reviews it, the coder may revise once.

C2, feedback on every method. For each method, in the fixed order, the coder writes it as in C0
and the judge reviews it. If the verdict is NOT OK, the coder reads the judge's reason and writes
the method again, once. The new version replaces the first one, and the next methods see it.

C1, feedback on the finished class. The coder writes the whole class as in C0, one method at a
time. The judge reviews the finished class once. If the verdict is NOT OK, the coder reads the
reason and writes the whole class again, once. From that reply we take each method; a method that
is missing from it, or does not compile, keeps its first version.

In both setups a reply without a usable method is neither reviewed nor revised, as in C0, so the
judge's feedback is the only difference with C0. The judge can be v1 or v2 (it can run code), with
low or medium effort.

At the end the harness runs the tests twice: on the first version of every method and on the
final one. The first run tells how good the judge's verdicts were, the second whether the
feedback helped. Each class goes to runs/<name>/<task_id>.json, where the name is, for example,
C2-v2-medium. Every request goes to runs/cost_log.csv.

    .venv/bin/python scripts/loop.py C2 --judge v2 --effort medium --dry-run ClassEval_19
    .venv/bin/python scripts/loop.py C2 --judge v2 --effort medium ClassEval_19 ClassEval_55
    .venv/bin/python scripts/loop.py C1 --judge v1 --all
"""
import argparse
import json
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

import budget
import coder
import harness
import judge

ROOT = harness.ROOT
SETUPS = ["C1", "C2"]

CLASS_SYSTEM = (
    "You are revising a Python class. Write the whole class again, with every method, in a "
    "single ```python code block, and write nothing outside the block. Use the imports of the "
    "skeleton; if you need another module, import it inside the method."
)


def method_feedback(name, reason):
    return (f"A reviewer read your method `{name}` and answered NOT OK: {reason}\n\n"
            f"Write the method `{name}` again, taking the review into account.")


def class_revision_prompt(task, source, reason):
    return "\n".join([f"This is the skeleton of the class {task['class_name']}:", "",
                      "```python", coder.skeleton(task), "```", "",
                      "This is the class you wrote:", "", "```python", source, "```", "",
                      f"A reviewer read the class and answered NOT OK: {reason}", "",
                      "Write the class again, taking the review into account."])


def usable(code):
    return code is not None and harness.as_class_member(code) is not None


class Run:
    """The two clients and the settings of one run, plus the calls that log their cost."""

    def __init__(self, coder_client, judge_client, setup, name, model, version, effort):
        self.coder_client, self.judge_client = coder_client, judge_client
        self.setup, self.name, self.model = setup, name, model
        self.version, self.effort = version, effort

    def write(self, task, messages, method_name, role, max_tokens=coder.MAX_TOKENS):
        r = coder.ask(self.coder_client, messages, self.model, max_tokens)
        budget.log(setup=self.name, task_id=task["task_id"], method_name=method_name, role=role,
                   service="openrouter", model=self.model, **r)
        return r

    def logged(self, task, method_name, review):
        for request in review["requests"]:
            budget.log(setup=self.name, task_id=task["task_id"], method_name=method_name,
                       role=f"judge-{self.version}", service="openai", model=judge.MODEL, **request)
        return review

    def first_version(self, task, written, name):
        messages = [{"role": "system", "content": coder.SYSTEM},
                    {"role": "user", "content": coder.prompt(task, written, name)}]
        r = self.write(task, messages, name, "coder")
        code = coder.extract_method(r["reply"], name)
        return messages, {"code": code, "valid": usable(code), **r}


def run_c2(run, task, steps):
    written, records = {}, []
    for name in steps:
        messages, first = run.first_version(task, written, name)
        record = {"method_name": name, "first": first, "review": None, "revision": None,
                  "final_code": first["code"] if first["valid"] else None}
        if first["valid"]:
            review_method = judge.judge_method if run.version == "v1" else judge.judge_method_with_tools
            review = run.logged(task, name, review_method(run.judge_client, task, written, name,
                                                          first["code"], run.effort))
            record["review"] = review
            if review["verdict"] == "NOT OK":
                messages += [{"role": "assistant", "content": first["reply"]},
                             {"role": "user", "content": method_feedback(name, review["reason"])}]
                r = run.write(task, messages, name, "coder-revision")
                code = coder.extract_method(r["reply"], name)
                record["revision"] = {"code": code, "valid": usable(code), **r}
                if usable(code):
                    record["final_code"] = code  # an unusable revision keeps the first version
        if record["final_code"] is not None:
            written[name] = record["final_code"]
        records.append(record)
    return records, {}


def run_c1(run, task, steps):
    written, records = {}, []
    for name in steps:
        _, first = run.first_version(task, written, name)
        if first["valid"]:
            written[name] = first["code"]
        records.append({"method_name": name, "first": first,
                        "final_code": first["code"] if first["valid"] else None})
    review = run.logged(task, "", judge.judge_class(run.judge_client, task, written, run.version, run.effort))
    revision = None
    if review["verdict"] == "NOT OK":
        messages = [{"role": "system", "content": CLASS_SYSTEM},
                    {"role": "user", "content": class_revision_prompt(task, harness.build_class(task, written),
                                                                      review["reason"])}]
        # A whole class needs more room than one method. In C2 each revised method can use
        # MAX_TOKENS, so here the class gets MAX_TOKENS for each of its methods. With MAX_TOKENS
        # alone, the first run of ClassEval_55 spent them all on reasoning and wrote no code.
        r = run.write(task, messages, "", "coder-revision", coder.MAX_TOKENS * len(records))
        replaced = []
        for record in records:
            # Only methods that were usable at first can change, as in C2. A method the coder
            # copied unchanged does not count as rewritten.
            code = coder.extract_method(r["reply"], record["method_name"])
            if record["final_code"] is not None and usable(code):
                if harness.as_class_member(code) != harness.as_class_member(record["final_code"]):
                    replaced.append(record["method_name"])
                record["final_code"] = code
        revision = {"replaced": replaced, **r}
    return records, {"review": review, "revision": revision}


def run_class(run, task, steps):
    records, extra = (run_c1 if run.setup == "C1" else run_c2)(run, task, steps)
    firsts = {r["method_name"]: r["first"]["code"] for r in records if r["first"]["valid"]}
    finals = {r["method_name"]: r["final_code"] for r in records if r["final_code"] is not None}
    source_first, source = harness.build_class(task, firsts), harness.build_class(task, finals)
    tests_first, tests = harness.run_tests(task, source_first), harness.run_tests(task, source)
    passed_first, passed = harness.method_passed(task, tests_first), harness.method_passed(task, tests)
    for r in records:
        r["passed_first"], r["passed"] = passed_first[r["method_name"]], passed[r["method_name"]]
    return {"task_id": task["task_id"], "class_name": task["class_name"], "setup": run.setup,
            "name": run.name, "coder_model": run.model, "judge": run.version, "effort": run.effort,
            "methods": records, **extra,
            "class_passed_first": harness.class_passed(tests_first),
            "class_passed": harness.class_passed(tests),
            "tests_first": tests_first, "tests": tests, "source_first": source_first, "source": source}


def costs(result):
    """Coder and judge dollars of one class."""
    coder_cost = judge_cost = 0.0
    for r in result["methods"]:
        coder_cost += r["first"].get("cost") or 0
        coder_cost += (r.get("revision") or {}).get("cost") or 0
        judge_cost += (r.get("review") or {}).get("cost") or 0
    coder_cost += (result.get("revision") or {}).get("cost") or 0
    judge_cost += (result.get("review") or {}).get("cost") or 0
    return coder_cost, judge_cost


def main():
    parser = argparse.ArgumentParser(description="Setups C1 and C2: coder, judge and one revision.")
    parser.add_argument("setup", choices=SETUPS)
    parser.add_argument("tasks", nargs="*", help="task ids, such as ClassEval_19")
    parser.add_argument("--all", action="store_true", help="every kept class")
    parser.add_argument("--judge", choices=judge.VERSIONS, default="v2", help="v2 can run code")
    parser.add_argument("--effort", choices=judge.EFFORTS, default=judge.EFFORT, help="reasoning effort of the judge")
    parser.add_argument("--model", default=coder.MODEL, help="OpenRouter model of the coder")
    parser.add_argument("--name", help="name of the run and of its folder in runs/ (default: setup-judge-effort)")
    parser.add_argument("--dry-run", action="store_true", help="print the feedback prompts and send nothing")
    parser.add_argument("--force", action="store_true", help="run again classes that already have a result")
    args = parser.parse_args()
    name = args.name or f"{args.setup}-{args.judge}-{args.effort}"

    tasks = {t["task_id"]: t for t in harness.load_tasks()}
    order = coder.method_order()
    chosen = list(tasks) if args.all else args.tasks
    unknown = [t for t in chosen if t not in tasks]
    if not chosen or unknown:
        parser.error(f"give kept task ids or --all (not kept or unknown: {unknown})")

    if args.dry_run:
        task = tasks[chosen[0]]
        if args.setup == "C2":
            print("After a NOT OK, the coder's conversation goes on with this message:\n")
            print(method_feedback(order[task["task_id"]][0], "<the judge's reason>"))
        else:
            print("After a NOT OK on the class, the coder gets:\n\nSYSTEM:\n" + CLASS_SYSTEM + "\n\nUSER:\n"
                  + class_revision_prompt(task, "<the class written by the coder>", "<the judge's reason>"))
        return

    load_dotenv(ROOT / ".env")
    run = Run(OpenAI(api_key=os.environ["OPENROUTER_API_KEY"], base_url="https://openrouter.ai/api/v1", max_retries=5),
              OpenAI(api_key=os.environ["OPENAI_API_KEY"], max_retries=5),
              args.setup, name, args.model, args.judge, args.effort)
    out_dir = ROOT / "runs" / name
    out_dir.mkdir(parents=True, exist_ok=True)
    for task_id in chosen:
        out = out_dir / f"{task_id}.json"
        if out.exists() and not args.force:
            print(f"{task_id}: already done, skipped")
            continue
        try:
            budget.check("openrouter")
            budget.check("openai")
        except budget.BudgetReached as stop:
            print(f"Stopped before {task_id}: {stop}")
            sys.exit(1)
        result = run_class(run, tasks[task_id], order[task_id])
        out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        ms = result["methods"]
        coder_cost, judge_cost = costs(result)
        if run.setup == "C2":
            feedback = (f"{sum((r['review'] or {}).get('verdict') == 'NOT OK' for r in ms)} NOT OK, "
                        f"{sum(r['revision'] is not None for r in ms)} revisions")
        else:
            feedback = f"class {result['review']['verdict']}, {len((result['revision'] or {}).get('replaced', []))} methods rewritten"
        print(f"{task_id}: {feedback}; methods passing {sum(r['passed_first'] for r in ms)} -> "
              f"{sum(r['passed'] for r in ms)} of {len(ms)}; coder {coder_cost:.5f} $, judge {judge_cost:.5f} $")


if __name__ == "__main__":
    main()
