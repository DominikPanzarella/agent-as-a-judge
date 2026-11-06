# Agent-As-a-Judge
Neural Code Analysis Course Paper Presentation and Project

**Project: Can a Judge Agent Make a Coding Agent Better?** (Dominik Panzarella, Daniele Buser)

We test the future work of Agent-as-a-Judge (Zhuge et al., ICML 2025). A judge agent gives feedback
after every method while a coding agent writes a class. We run this on ClassEval (Du et al., 2023),
whose tests tell us who is right.

![Architecture](docs/architecture.png)

The plan up to the midway report, with what is done and what is still open, is in
[docs/roadmap_midway.md](docs/roadmap_midway.md).

## Setup

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env                     # add the API keys, never commit .env
./scripts/download_data.sh               # ClassEval + benchmarks+ into data/raw/ (not tracked)
.venv/bin/python scripts/benchmark_stats.py
.venv/bin/python scripts/select_classes.py
.venv/bin/python scripts/order_methods.py
.venv/bin/python scripts/harness.py      # reference solutions must pass, stubs must fail
.venv/bin/python scripts/check_api.py    # one tiny request to each API
.venv/bin/python scripts/budget.py       # dollars spent so far on each API
.venv/bin/python scripts/coder.py --dry-run ClassEval_19   # print a coder prompt, send nothing
```

## Data

- ClassEval: https://github.com/FudanSELab/ClassEval (CC BY-NC 4.0)
- benchmarks+ from "Examining Benchmark Quality in Code Generation":
  https://doi.org/10.5281/zenodo.21031875 (CC BY 4.0), used to drop trivial and problematic tasks

## Class selection

`scripts/select_classes.py` writes `data/selection/classes.csv`, one row per class with the reason for
each drop. We drop a class when benchmarks+ marks one of its methods as problematic, since its tests
then cannot say whether the code is right. This removes 27 classes. We also drop the one class whose
methods are all trivial: all nine models tested in benchmarks+ solve them. Finally we drop
ClassEval_49, whose helper method `matches_requirements` has its own tests but is not among the
methods to write, so its reference solution fails in our harness. The remaining 71 classes have 289
methods.

## Method order

`scripts/order_methods.py` writes `data/selection/method_order.csv`. The coder writes the methods of a
class in the order of its skeleton, which we take as the logical order chosen by the ClassEval
authors. We change that order only where a method calls another method of the same class: the called
method comes first. This changes the position of 48 of the 289 methods, in 15 classes. One ClassEval
annotation is wrong. In ClassEval_63, `process_data` does not call `process`, so we remove that
dependency, which would otherwise create a cycle.

## Test harness

`scripts/harness.py` puts a class together from single methods and runs each ClassEval test class
in its own subprocess, in a temporary folder and with a 10 second timeout. A method that is missing,
or that does not compile, becomes a stub that returns None, so it fails only its own tests. Some
ClassEval methods lose their decorator (such as `@staticmethod`), so the harness takes it back from
the class skeleton.

Run as a script, the harness checks itself. The reference solutions pass all 289 methods and all 71
classes. With stubs only, 4 methods still pass, because their tests cannot tell a no-op from a
solution. They are listed in `data/selection/weak_tests.csv` and we report results with and without
them.

## Coder (setup C0)

`scripts/coder.py` asks Qwen (qwen3.8-27b on OpenRouter, served in bf16) for one method at a time,
in the order of `data/selection/method_order.csv`. The prompt holds the class skeleton, the methods
written so far and the name of the next method, never the tests. From the reply we keep only that
method. If it is missing or does not compile, the method stays a stub and we do not ask again, so
every setup sends the coder the same number of requests. Each class is saved in
`runs/C0/<task_id>.json` with the code, tokens, cost and test result of every method.

`scripts/budget.py` writes one line per request to `runs/cost_log.csv`. Before each class it checks
the budgets and stops the run when a service has spent 70 percent of its 10 dollars. For OpenRouter
it also asks the service how much the key has spent, because both of us use the same key.

## The judge

`scripts/judge.py` asks GPT-6 Luna whether a method does what its docstring says. The judge sees the
class skeleton, the methods written before and the new method, never the tests. Its answer is a
JSON object with a short reason and a verdict, OK or NOT OK; the reason is the feedback the coder
will get in C1 and C2. On a finished run the script compares the verdicts with the tests (agreement,
Cohen's kappa, OK given to failing methods, NOT OK given to passing ones). Verdicts go to
`runs/judge/<setup>-<version>-<effort>/`. OpenAI does not return the cost of a request, so the
script computes it from the standard prices.

Judge v1 only reads the code. On the first four methods its verdicts agree with the tests three
times out of four, with low and with medium reasoning effort, but every concrete claim in its
reasons was false when we ran the code: it tries to execute the code in its head and gets it wrong.
Judge v1 is therefore the "judge without tools" of our plan.

Judge v2 can also run Python before it answers, up to 5 times per method, with the tool
`run_python`. The code runs after the class written so far, in a separate process, in a temporary
folder and with a 10 second limit, as in the test harness. The judge can try the docstring
examples or a case it doubts, and the reason must report what it saw. The tests stay hidden. In
its first runs the judge copied the class into its own code, so it could end up testing a copy
instead of the coder's code; now the prompt asks it to call the class directly, and code that
redefines the class is not run.

On the same four methods every claim of judge v2 about what the code returns was true. It agrees
with the tests on two methods. The other two disagreements are problems of ClassEval rather than of
the judge. The docstring of `palindromic_length` does not say whether the result counts from `diff`
or from the center, and the tests expect the reading the coder did not choose. `palindromic_string`
breaks when the input contains `|`, its own separator, and no test checks that case. So in the
analysis a disagreement with the tests does not always mean that the judge is wrong.

Both versions use the OpenAI Responses API with the same settings, so they differ only in the tool;
the older Chat Completions API does not accept tools together with a reasoning effort for GPT-6
Luna.

```bash
.venv/bin/python scripts/judge.py C0 --version v1 --effort medium ClassEval_19 ClassEval_55
.venv/bin/python scripts/judge.py C0 --version v2 --effort medium ClassEval_19 ClassEval_55
.venv/bin/python scripts/judge.py C0 --version v2 --effort medium --summary
```
