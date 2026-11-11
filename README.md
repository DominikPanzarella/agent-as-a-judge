# Agent-As-a-Judge
Neural Code Analysis Course Paper Presentation and Project

**Project: Can a Judge Agent Make a Coding Agent Better?**
Dominik Panzarella and Daniele Buser, Neural Code Analysis, USI, autumn 2026.

A coding agent writes a Python class one method at a time, and a judge agent reviews the work. We
measure whether the judge's feedback makes the code pass more tests, and how often the judge is
wrong. The tasks come from ClassEval. Neither agent sees the tests: the judge works only with what
exists when the code is written (the docstring and the code so far), and the tests only give the
grade.

## Contents

1. [Idea](#1-idea)
2. [How it works](#2-how-it-works)
3. [Quick start](#3-quick-start)
4. [Usage](#4-usage)
5. [Project layout](#5-project-layout)
6. [Results so far](#6-results-so-far)
7. [References and data](#7-references-and-data)

## 1. Idea

Agent-as-a-Judge (Zhuge et al., ICML 2025) uses an agent to judge another agent step by step. Its
future work suggests using the judge's verdicts as feedback during the work, and letting judge and
worker improve each other (a "flywheel"). We test both ideas on tasks with real tests:

- RQ1: Does the judge's feedback after every method make the coder write better code?
- RQ2: If the judge remembers its past mistakes, do judge and coder improve over time?
- RQ3: How often is the judge wrong inside the loop?

## 2. How it works

![Architecture](docs/architecture_base.png)

Solid parts are built and were tried in the pilot; orange, dashed parts are planned.
The first diagram, from before the pilot, is in `docs/architecture.svg`.

Both setups have a coder and a judge:

| Setup | Feedback to the coder | Status |
|---|---|---|
| C2 | after each method the judge reviews it; one revision of that method, then the next method | piloted |
| C3 | as C2, in rounds of classes; from the second round the judge has a memory of its mistakes that we confirm by hand | planned, if time and budget allow |

C1, with one review of the finished class, was piloted but is dropped (11 November): the study is
about feedback given step by step.

There is no setup without the judge: the baseline is inside each setup, in the first version of
each method, written before any feedback.

**One method in C2.** (1) The coder writes the method. (2) The judge gets the skeleton with the
docstrings, the methods written so far and the new one, never the tests; v2 may also run code of its
own on the class written so far. (3) It answers OK or NOT OK with a reason. (4) After a NOT OK the
coder gets the reason in the same conversation and rewrites the method once. (5) The final version
joins the methods already written, and the next method starts. When the class is finished, the
harness runs all its tests on the first and on the final versions: that is the grade.

**Built**

- **Class selection.** 71 of the 100 ClassEval classes (289 methods): we drop the classes that
  benchmarks+ marks as problematic, plus two with trivial or broken methods. 10 are development
  classes for the pilot; the analysis uses the other 61. Methods follow the skeleton, except that a
  called method comes before its caller.
- **Prompt.** The class skeleton with all the docstrings, the methods written so far and the name
  of the next method.
- **Coder.** `qwen/qwen3.5-9b` on OpenRouter (chosen on 11 November; the pilot also used
  `qwen3.8-27b`, which already passes 82% of the methods), with low reasoning effort and 4000 output
  tokens per request. It writes one method at a time and rewrites it after a NOT OK, without ever
  seeing the tests or running code.
- **Judge.** `gpt-6-luna` on OpenAI, with medium effort. It answers OK or NOT OK with a reason, and
  the reason is the feedback. v1 only reads the code; v2 can also run it up to 5 times. It never sees
  the tests.
- **Test harness.** Each ClassEval test class runs in its own process. A missing method becomes a
  stub, so it fails only its own tests. 4 methods pass even as stubs; we report results with and
  without them.
- **Judge vs tests.** Not part of the loop: after a run, the judge's verdict on each first version is
  set next to the grade of the same version. It gives TPR, TNR and Cohen's kappa, and the list of
  disagreements that we check by hand.
- **Analysis.** McNemar tests paired by method and bootstrap intervals over classes.

**Plan after the instructors' answer** (11 November)

- **First, the judge.** On the 10 pilot classes, which stay out of the study, we grade the 9B's
  methods with the tests and measure the judge on them (TPR, TNR, kappa), trying prompt variants
  until it works as well as it can with only the docstring and the code.
- **Then one full run of C2** on the 61 test classes, and a report of the budget spent before
  deciding on repetitions.
- **C3** if time and budget allow.

Later variants (judge v3, our labels, controls, other ways to fill the judge's memory) are in the
[roadmap](docs/roadmap_midway.md).

## 3. Quick start

Python 3.13, plus the OpenAI and OpenRouter keys from the course.

```bash
git clone https://github.com/DominikPanzarella/agent-as-a-judge.git
cd agent-as-a-judge
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env          # then write the two keys in .env (git ignores it)
./scripts/download_data.sh    # ClassEval and benchmarks+ -> data/raw/
```

## 4. Usage

Run everything from the repository root. The scripts that call a model accept `--dry-run` (print
the prompt, send nothing) and skip classes already done unless you pass `--force`.

```bash
# prepare and check the classes (outputs are already in data/selection/)
.venv/bin/python scripts/select_classes.py
.venv/bin/python scripts/order_methods.py
.venv/bin/python scripts/harness.py                    # references must pass, stubs must fail

# check the APIs and the budget
.venv/bin/python scripts/check_api.py
.venv/bin/python scripts/budget.py

# the coder alone (setup C0 of the pilot, now only the first versions)
.venv/bin/python scripts/coder.py ClassEval_19 ClassEval_55
.venv/bin/python scripts/coder.py --all

# the judge on a finished run (v1 reads, v2 can also run code)
.venv/bin/python scripts/judge.py C0 --version v2 --effort medium --all

# C2: coder and judge together (C1 was only piloted)
.venv/bin/python scripts/loop.py C2 --judge v2 --effort medium --all

# results
.venv/bin/python scripts/pilot_report.py               # tables of the pilot
.venv/bin/python scripts/pilot_controls.py             # resampling control, judge TNR, power
.venv/bin/python scripts/plot_results.py               # charts -> docs/figures/
.venv/bin/python scripts/analyze.py --classes test C0 C2-v2-medium --sample 20
```

`analyze.py` reports pass rates, the judge's TPR and TNR, McNemar tests and bootstrap intervals
between runs; `--sample 20` draws disagreements for the error analysis.

## 5. Project layout

```
docs/          diagrams, charts (figures/) and the roadmap
scripts/
  download_data.sh, select_classes.py, order_methods.py, pick_dev_classes.py   data
  harness.py, check_docstring_examples.py, check_field_order.py               checks
  coder.py, judge.py, loop.py, budget.py, check_api.py                         runs
  pilot_report.py, pilot_controls.py, check_claims.py, plot_results.py,
  analyze.py                                                                   results
data/selection/  the kept classes, method order, development classes, weak tests
runs/            one folder per run with a JSON file per class, plus cost_log.csv
```

Each JSON file in `runs/` holds, per method, the code, the judge's review and revision when there
is one, the token counts, the cost and the test result.

## 6. Results so far

[TODO] Completing...

## 7. References and data

- Zhuge et al., "Agent-as-a-Judge: Evaluate Agents with Agents", ICML 2025.
  https://arxiv.org/abs/2410.10934
- Du et al., "ClassEval: A Manually-Crafted Benchmark for Evaluating LLMs on Class-level Code
  Generation", 2023. https://arxiv.org/abs/2308.01861 (data: CC BY-NC 4.0)
- benchmarks+, from "Examining Benchmark Quality in Code Generation".
  https://doi.org/10.5281/zenodo.21031875 (data: CC BY 4.0)

The data sets are not stored here; `scripts/download_data.sh` fetches them.

Course: Neural Code Analysis, USI, Prof. Gabriele Bavota, with Alessandro Giagnorio as teaching
assistant. The course provided the OpenAI project and the OpenRouter key.
