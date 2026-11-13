"""Setups C2 and C3: coder and judge together, with one revision.

C2: the judge reviews each method; after a NOT OK the coder rewrites that method once, and the
next methods see the new version. C3: as C2, and the judge also reads its earlier reviews of the
same class, its memory. The tests run on the first and on the final version of every method.
Results go to runs/<name>/<task_id>.json; without --name the folder is <setup>-<judge>-<effort>.

--reuse takes from another run every first version and review whose input is the same, so two
setups differ only where the judge does, and not because the coder writes a method differently.

The defaults are the study's: coder qwen3.5-9b, judge v1 with medium effort.

    .venv/bin/python scripts/loop.py C3 --dry-run ClassEval_19
    .venv/bin/python scripts/loop.py C2 --name C2-9b --classes test
    .venv/bin/python scripts/loop.py C3 --name C3-9b --reuse C2-9b --classes test
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
SETUPS = ["C2", "C3"]
# The study's settings, decided with the instructors on 11 and 12 November.
CODER = "qwen/qwen3.5-9b"
EFFORT = "medium"

def method_feedback(name, reason):
    return (f"A reviewer read your method `{name}` and answered NOT OK: {reason}\n\n"
            f"Write the method `{name}` again, taking the review into account.")


def usable(code):
    return code is not None and harness.as_class_member(code) is not None


class Run:
    """The two clients and the settings of one run, plus the calls that log their cost."""

    def __init__(self, coder_client, judge_client, setup, name, model, version, effort,
                 confidence=False, min_confidence=None, reuse=None):
        self.coder_client, self.judge_client = coder_client, judge_client
        self.setup, self.name, self.model = setup, name, model
        self.version, self.effort = version, effort
        self.confidence, self.min_confidence = confidence, min_confidence
        self.reuse = reuse  # name of the run to take equal first versions and reviews from

    def settings(self):
        """What must be equal in another run before one of its results can be reused."""
        return {"coder_model": self.model, "judge": self.version, "effort": self.effort,
                "confidence": self.confidence, "min_confidence": self.min_confidence}

    def earlier(self, task, written, name):
        """The record of this method in the reused run, if it was written after the same methods."""
        f = ROOT / "runs" / (self.reuse or "") / f"{task['task_id']}.json"
        if not self.reuse or not f.exists():
            return None
        old = json.loads(f.read_text(encoding="utf-8"))
        if any(old.get(k) != v for k, v in self.settings().items()):
            return None
        before = {}
        for record in old["methods"]:
            if record["method_name"] == name:
                return record if before == written else None
            if record["final_code"] is not None:
                before[record["method_name"]] = record["final_code"]
        return None

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
        old = self.earlier(task, written, name)
        if old:
            return messages, {**old["first"], "cost": 0.0, "reused": self.reuse}
        r = self.write(task, messages, name, "coder")
        code = coder.extract_method(r["reply"], name)
        return messages, {"code": code, "valid": usable(code), **r}

    def review(self, task, written, name, code, memory):
        """The judge on one method. Without a memory the judge's input is the one of C2, so an
        equal review of the reused run is taken as it is."""
        old = self.earlier(task, written, name)
        if old and not memory and old["review"] and old["first"]["code"] == code:
            return {**old["review"], "cost": 0.0, "reused": self.reuse}
        return self.logged(task, name, judge.judge_any(
            self.judge_client, task, written, name, code, self.version, self.effort,
            memory if self.setup == "C3" else None, self.confidence, self.min_confidence))


def write_class(run, task, steps):
    """One class, method by method. In C3 `memory` holds the judge's reviews of the methods so far."""
    written, records, memory = {}, [], []
    for name in steps:
        messages, first = run.first_version(task, written, name)
        record = {"method_name": name, "first": first, "review": None, "revision": None,
                  "final_code": first["code"] if first["valid"] else None}
        if first["valid"]:
            review = run.review(task, written, name, first["code"], memory)
            record["review"] = review
            if review["verdict"] == "NOT OK":
                messages += [{"role": "assistant", "content": first["reply"]},
                             {"role": "user", "content": method_feedback(name, review["reason"])}]
                r = run.write(task, messages, name, "coder-revision")
                code = coder.extract_method(r["reply"], name)
                record["revision"] = {"code": code, "valid": usable(code), **r}
                if usable(code):
                    record["final_code"] = code  # an unusable revision keeps the first version
            if run.setup == "C3" and review["verdict"] in ("OK", "NOT OK"):
                memory.append(judge.memory_line(name, review, record["final_code"] != first["code"]))
        if record["final_code"] is not None:
            written[name] = record["final_code"]
        records.append(record)
    return records


def run_class(run, task, steps):
    records = write_class(run, task, steps)
    firsts = {r["method_name"]: r["first"]["code"] for r in records if r["first"]["valid"]}
    finals = {r["method_name"]: r["final_code"] for r in records if r["final_code"] is not None}
    source_first, source = harness.build_class(task, firsts), harness.build_class(task, finals)
    tests_first, tests = harness.run_tests(task, source_first), harness.run_tests(task, source)
    passed_first, passed = harness.method_passed(task, tests_first), harness.method_passed(task, tests)
    for r in records:
        r["passed_first"], r["passed"] = passed_first[r["method_name"]], passed[r["method_name"]]
    return {"task_id": task["task_id"], "class_name": task["class_name"], "setup": run.setup,
            "name": run.name, **run.settings(), "reuse": run.reuse, "methods": records,
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
    return coder_cost, judge_cost


def main():
    parser = argparse.ArgumentParser(description="Setups C2 and C3: coder, judge and one revision.")
    parser.add_argument("setup", choices=SETUPS)
    parser.add_argument("tasks", nargs="*", help="task ids, such as ClassEval_19")
    parser.add_argument("--classes", choices=["dev", "test"],
                        help="dev: the 10 development classes; test: the other 61, the ones of the study")
    parser.add_argument("--all", action="store_true", help="every kept class, development ones included")
    parser.add_argument("--judge", choices=judge.VERSIONS, default="v1",
                        help="v1 only reads the code (the judge of the study), as v6 and v7; v2 to v5 can run it")
    parser.add_argument("--effort", choices=judge.EFFORTS, default=EFFORT, help="reasoning effort of the judge")
    parser.add_argument("--model", default=CODER, help="OpenRouter model of the coder")
    parser.add_argument("--name", help="name of the run and of its folder in runs/ (default: setup-judge-effort)")
    parser.add_argument("--confidence", action="store_true", help="the judge also says how sure it is, 0 to 100")
    parser.add_argument("--min-confidence", type=int, help="below this confidence the judge looks again")
    parser.add_argument("--reuse", help="run to take equal first versions and reviews from, such as C2-9b")
    parser.add_argument("--dry-run", action="store_true", help="print the feedback prompts and send nothing")
    parser.add_argument("--force", action="store_true", help="run again classes that already have a result")
    args = parser.parse_args()
    name = args.name or f"{args.setup}-{args.judge}-{args.effort}"

    tasks = {t["task_id"]: t for t in harness.load_tasks()}
    order = coder.method_order()
    chosen = harness.class_ids(args.classes) if args.classes else list(tasks) if args.all else args.tasks
    unknown = [t for t in chosen if t not in tasks]
    if not chosen or unknown:
        parser.error(f"give kept task ids, --classes or --all (not kept or unknown: {unknown})")

    if args.dry_run:
        task = tasks[chosen[0]]
        print("After a NOT OK, the coder's conversation goes on with this message:\n")
        print(method_feedback(order[task["task_id"]][0], "<the judge's reason>"))
        if args.setup == "C3" and len(order[task["task_id"]]) > 1:
            first, second = order[task["task_id"]][:2]
            memory = [judge.memory_line(first, {"verdict": "NOT OK", "reason": "<the judge's reason>"}, True)]
            print("\nFrom the second method, the judge's message has its earlier reviews:\n")
            print(judge.prompt(task, {first: f"<the final version of {first}>"}, second,
                               f"<the first version of {second}>", memory))
        return

    load_dotenv(ROOT / ".env")
    run = Run(OpenAI(api_key=os.environ["OPENROUTER_API_KEY"], base_url="https://openrouter.ai/api/v1", max_retries=5),
              OpenAI(api_key=os.environ["OPENAI_API_KEY"], max_retries=5),
              args.setup, name, args.model, args.judge, args.effort,
              args.confidence or args.min_confidence is not None, args.min_confidence, args.reuse)
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
        feedback = (f"{sum((r['review'] or {}).get('verdict') == 'NOT OK' for r in ms)} NOT OK, "
                    f"{sum(r['revision'] is not None for r in ms)} revisions")
        print(f"{task_id}: {feedback}; methods passing {sum(r['passed_first'] for r in ms)} -> "
              f"{sum(r['passed'] for r in ms)} of {len(ms)}; coder {coder_cost:.5f} $, judge {judge_cost:.5f} $")


if __name__ == "__main__":
    main()
