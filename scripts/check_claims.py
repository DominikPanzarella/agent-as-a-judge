"""Pilot, question 2: are the concrete claims in the judge's reasons true?

We took every NOT OK verdict of the four judges (v1 and v2, low and medium effort) on run C0 of
the 10 development classes. OK verdicts rarely say anything concrete, so they are left out. For
each claim about what the code returns, prints or raises, we wrote a short snippet by hand and run
it on the class the judge saw. A claim is true when the snippet prints what the judge said.

The script sends no request. It writes runs/pilot_claims.csv and prints, for each judge, how many
of its claims are true.

    .venv/bin/python scripts/check_claims.py
"""
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "runs/pilot_claims.csv"
JUDGES = ["v1-low", "v2-low", "v1-medium", "v2-medium"]

OUT_OF_STOCK = ("import io, contextlib\nvm = VendingMachine()\n"
                "vm.inventory = {'Coke': {'price': 1.25, 'quantity': 0}}\nvm.balance = 5\n"
                "buf = io.StringIO()\nwith contextlib.redirect_stdout(buf):\n"
                "    r = vm.purchase_item('Coke')\nprint(repr(buf.getvalue()), r)")


def raises(call):
    return f"try:\n    {call}\n    print('no error')\nexcept Exception as e:\n    print(type(e).__name__)"


# id, task, method, judges that make the claim, claim, snippet, what the claim says it prints
CLAIMS = [
    ("A", "ClassEval_55", "palindromic_length", ["v1-low"],
     "the docstring example returns 0, not 2",
     "print(Manacher('ababa').palindromic_length(2, 1, 'a|b|a|b|a'))", "0"),
    ("B", "ClassEval_55", "palindromic_string", ["v1-low"],
     "'abba' gives an empty string",
     "print(repr(Manacher('abba').palindromic_string()))", "''"),
    ("C", "ClassEval_55", "palindromic_string", ["v2-low"],
     "'a|a' gives 'aa'",
     "print(repr(Manacher('a|a').palindromic_string()))", "'aa'"),
    ("D", "ClassEval_55", "palindromic_string", ["v1-medium", "v2-medium"],
     "'|' gives an empty string",
     "print(repr(Manacher('|').palindromic_string()))", "''"),
    ("E", "ClassEval_16", "calculate", ["v1-low"],
     "'1x+2' gives 3.0", "print(Calculator().calculate('1x+2'))", "3.0"),
    ("F", "ClassEval_16", "calculate", ["v2-low", "v1-medium"],
     "'1 2' gives 2.0", "print(Calculator().calculate('1 2'))", "2.0"),
    ("G", "ClassEval_16", "calculate", ["v1-medium"],
     "'1abc2' gives 2.0", "print(Calculator().calculate('1abc2'))", "2.0"),
    ("H", "ClassEval_16", "calculate", ["v2-medium"],
     "'1a+2' gives 3.0", "print(Calculator().calculate('1a+2'))", "3.0"),
    ("I", "ClassEval_16", "apply_operator", ["v2-low", "v1-medium", "v2-medium"],
     "the docstring example leaves ['+'] on the operator stack",
     "print(Calculator().apply_operator([1, 2, 3], ['+', '-']))", "([1, -1], ['+'])"),
    ("J", "ClassEval_40", "condition_judge", JUDGES,
     "the docstring example returns 0, not -1",
     "print(FitnessTracker(1.8, 70, 20, 'male').condition_judge())", "0"),
    ("K", "ClassEval_40", "condition_judge", ["v1-medium", "v2-medium"],
     "a sex other than male or female raises UnboundLocalError",
     raises("FitnessTracker(1.8, 70, 20, 'other').condition_judge()"), "UnboundLocalError"),
    ("L", "ClassEval_40", "calculate_calorie_intake", ["v1-low"],
     "the docstring example returns 556.0",
     "print(FitnessTracker(1.8, 70, 20, 'male').calculate_calorie_intake())", "556.0"),
    ("M", "ClassEval_40", "calculate_calorie_intake", ["v2-low", "v1-medium", "v2-medium"],
     "the docstring example returns 862.75",
     "print(FitnessTracker(1.8, 70, 20, 'male').calculate_calorie_intake())", "862.75"),
    ("N", "ClassEval_40", "calculate_calorie_intake", ["v2-low"],
     "the user of the example is underweight (condition -1)",
     "print(FitnessTracker(1.8, 70, 20, 'male').condition_judge())", "-1"),
    ("O", "ClassEval_57", "mrr", ["v1-low", "v2-low"],
     "an empty list raises ZeroDivisionError",
     raises("MetricsCalculator2.mrr([])"), "ZeroDivisionError"),
    ("P", "ClassEval_57", "map", ["v1-medium"],
     "an empty list raises ZeroDivisionError",
     raises("MetricsCalculator2.map([])"), "ZeroDivisionError"),
    ("Q", "ClassEval_57", "map", ["v1-medium"],
     "a ground truth num of 0 raises ZeroDivisionError",
     raises("MetricsCalculator2.map(([1, 0, 1], 0))"), "ZeroDivisionError"),
    ("R", "ClassEval_85", "simulate_operation", ["v1-low", "v1-medium", "v2-medium"],
     "the docstring example returns 18 and ends at 38.4",
     "t = Thermostat(20.4, 37.5, 'cool')\nr = t.simulate_operation()\n"
     "print(r, round(t.current_temperature, 1))", "18 38.4"),
    ("S", "ClassEval_94", "purchase_item", ["v1-low", "v1-medium", "v2-medium"],
     "an out-of-stock item prints nothing and returns False", OUT_OF_STOCK, "'' False"),
    ("T", "ClassEval_94", "display_items", ["v1-low", "v1-medium"],
     "with two products it returns a list",
     "vm = VendingMachine()\nvm.inventory = {'Coke': {'price': 1.25, 'quantity': 10}, "
     "'Pizza': {'price': 1.25, 'quantity': 10}}\nprint(type(vm.display_items()).__name__)", "list"),
    ("U", "ClassEval_94", "display_items", ["v2-medium"],
     "with one product it returns a str",
     "vm = VendingMachine()\nvm.inventory = {'Coke': {'price': 1.25, 'quantity': 10}}\n"
     "print(type(vm.display_items()).__name__)", "str"),
    ("V", "ClassEval_20", "send_message", ["v1-medium", "v2-medium"],
     "a message to oneself is stored twice",
     "c = Chat()\nc.users = {'John': []}\nc.send_message('John', 'John', 'Hi')\n"
     "print(len(c.users['John']))", "2"),
]
# NOT OK verdicts whose reason makes no claim that can be run.
NO_CLAIM = {"v2-low": ["ClassEval_85 simulate_operation (the reason is only 'NOT OK')"]}


def run(source, snippet):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "claim.py"
        path.write_text(source + "\n\n" + snippet + "\n", encoding="utf-8")
        try:
            p = subprocess.run([sys.executable, "-I", str(path)], capture_output=True, text=True,
                               timeout=10, cwd=tmp)
        except subprocess.TimeoutExpired:
            return "timeout"
    return (p.stdout.strip() or p.stderr.strip().splitlines()[-1]) if (p.stdout or p.stderr) else ""


def main():
    rows = []
    for cid, task_id, method, judges, claim, snippet, claimed in CLAIMS:
        source = json.loads((ROOT / "runs/C0" / f"{task_id}.json").read_text(encoding="utf-8"))["source"]
        observed = run(source, snippet)
        rows.append({"claim_id": cid, "task_id": task_id, "method_name": method,
                     "judges": " ".join(judges), "claim": claim, "snippet": snippet,
                     "claimed": claimed, "observed": observed, "true": observed == claimed})
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    for r in rows:
        print(f"{r['claim_id']} {r['task_id'][10:]:>3} {r['method_name']:<25} "
              f"{'TRUE ' if r['true'] else 'FALSE'} {r['claim']} (observed: {r['observed']})")
    print()
    for j in JUDGES:
        mine = [r for r in rows if j in r["judges"].split()]
        print(f"{j:<10} {sum(r['true'] for r in mine)} of {len(mine)} claims true"
              + (f"; NOT OK without a claim: {len(NO_CLAIM[j])}" if j in NO_CLAIM else ""))
    print(f"\n{len(rows)} claims -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
