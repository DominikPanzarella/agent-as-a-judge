"""Cost log of every request, and the stop at 70 percent of the two course budgets.

The coder and the judge add one line to runs/cost_log.csv for each request. check() is
called before each class: it raises BudgetReached when a service has used 70 percent of its
10 dollars. For OpenRouter it also asks the service how much the key has spent, because the
key is shared with the other team member and our own log only sees this machine.

Run as a script, it prints how much each service has spent so far.
"""
import csv
import json
import os
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "runs/cost_log.csv"
BUDGET = {"openrouter": 10.0, "openai": 10.0}  # dollars, set by the course
STOP_AT = 0.7
FIELDS = ["time", "setup", "task_id", "method_name", "role", "service", "model", "provider",
          "prompt_tokens", "cached_tokens", "completion_tokens", "reasoning_tokens", "cost"]


class BudgetReached(Exception):
    pass


def log(**row):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    new = not LOG.exists()
    with LOG.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        if new:
            writer.writeheader()
        writer.writerow({"time": time.strftime("%Y-%m-%d %H:%M:%S"), **row})


def spent_in_log(service):
    if not LOG.exists():
        return 0.0
    with LOG.open(encoding="utf-8") as f:
        return sum(float(r["cost"] or 0) for r in csv.DictReader(f) if r["service"] == service)


def openrouter_key_usage(key):
    """Dollars spent by the key and its limit (None if the key has no limit)."""
    request = urllib.request.Request("https://openrouter.ai/api/v1/key",
                                     headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.load(response)["data"]
    return float(data["usage"]), data.get("limit")


def status(service):
    """Dollars spent and the budget of a service, from the service itself when it can tell us."""
    spent, limit = spent_in_log(service), BUDGET[service]
    key = os.getenv("OPENROUTER_API_KEY")
    if service == "openrouter" and key:
        try:
            remote, remote_limit = openrouter_key_usage(key)
            spent, limit = max(spent, remote), float(remote_limit or limit)
        except Exception:  # the log is enough if the service does not answer
            pass
    return spent, limit


def check(service):
    spent, limit = status(service)
    if spent >= STOP_AT * limit:
        raise BudgetReached(f"{service} has spent {spent:.2f} of {limit:.2f} dollars")
    return spent, limit


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    for service in BUDGET:
        spent, limit = status(service)
        print(f"{service}: {spent:.4f} of {limit:.2f} dollars spent, stop at {STOP_AT * limit:.2f}")
