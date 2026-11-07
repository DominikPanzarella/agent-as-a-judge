# Agent-As-a-Judge
Neural Code Analysis Course Paper Presentation and Project

**Project: Can a Judge Agent Make a Coding Agent Better?**
Dominik Panzarella and Daniele Buser, Neural Code Analysis, USI, autumn 2026.

A coding agent writes a Python class one method at a time, and a judge agent reviews the work. We
measure whether the judge's feedback makes the code pass more tests, and how often the judge itself
is wrong. The tasks come from ClassEval (Du et al., 2023), whose tests stay hidden from both
agents, so they give an independent check on each of them.

## Table of contents

1. [Introduction](#1-introduction)
2. [How it works](#2-how-it-works)
3. [Status](#3-status)
4. [Getting started](#4-getting-started)
5. [Usage](#5-usage)
6. [Project layout](#6-project-layout)
7. [Method details](#7-method-details)
8. [Output files](#8-output-files)
9. [Results so far](#9-results-so-far)
10. [Known issues](#10-known-issues)
11. [References](#11-references)
12. [Data and licenses](#12-data-and-licenses)
13. [Authors and acknowledgments](#13-authors-and-acknowledgments)

## 1. Introduction

In the course we presented Agent-as-a-Judge (Zhuge et al., ICML 2025), where an agent judges the
work of another agent step by step. In its future work the paper suggests two ideas. The judge's
verdicts could be used as feedback while the work is still going on. Judge and worker could also
improve each other over time, a loop the paper calls a flywheel. Our project tests both ideas on
tasks where the right answer comes from real tests, not from the judge.

We ask three questions:

- RQ1: Does the coder write better code when the judge gives feedback after every method, rather
  than only at the end or not at all?
- RQ2: If the judge remembers the mistakes the tests caught in earlier rounds, does it get better
  over time, and does the coder get better with it?
- RQ3: How often is the judge wrong while it works inside the loop? And does the coder start
  writing code that pleases the judge but fails the tests?

## 2. How it works

![Architecture](docs/architecture.png)

The diagram is also in `docs/architecture.svg`, which can be edited by hand.

Work goes through three blocks. First the data scripts download ClassEval, drop the classes whose
tests or descriptions are unreliable and fix the order in which the methods are written. Then the
coder (Qwen through OpenRouter) writes each class one method at a time, while the judge (GPT-6 Luna
through OpenAI) reviews the code. Finally the test harness runs the ClassEval tests on the result
and the analysis compares the setups. Every request is logged with its cost, and a run stops before
either course budget is used up.

We keep the coder and the tasks the same and change only the feedback:

| Setup | Feedback to the coder | Answers | Status |
|---|---|---|---|
| C0 | none (baseline) | RQ1 | code ready, piloted |
| C1 | the judge reviews the finished class, one revision of the class | RQ1 | code ready |
| C2 | the judge reviews each method right after it is written, one revision of that method | RQ1, RQ3 | code ready |
| C3 | as C2, with the classes split into three rounds; after each round the judge learns which of its verdicts the tests proved wrong | RQ2 | planned |
| C4 | the coder sees the real test results after each method (best case) | upper bound | planned |

The plan also has two controls: judge v1, which cannot run code (the "judge without tools"), and a
coder that reviews its own code (self-refine).

## 3. Status

| Step | State |
|---|---|
| Data download, class selection, method order | done |
| Test harness, checked on the reference solutions | done |
| Check of the docstring examples | done |
| API access (OpenAI project and OpenRouter key from the course) | done |
| Coder, setup C0 | done, piloted on 10 classes |
| Judge v1 and v2 | done, piloted on 10 classes |
| Setups C1 and C2 | code ready and tested offline; runs wait for the instructors' advice |
| Setups C3, C4, self-refine control | planned after the midway report |
| Midway report (2 pages) | due 19 November 2026 |
| Final report and 5-minute talk | due 16 and 17 December 2026 |

The plan with dates is in [docs/roadmap_midway.md](docs/roadmap_midway.md). Up to now the project
has spent about 0.11 dollars on OpenRouter and 0.04 dollars on OpenAI, out of 10 dollars each.

## 4. Getting started

### 4.1 Requirements

- Python 3.13 (we use 3.13.2 on macOS).
- An OpenAI API key for the course project and an OpenRouter API key. The course provides both,
  each with a 10 dollar budget.
- An internet connection for the data download and the API calls. Everything else runs locally.

### 4.2 Installation

```bash
git clone https://github.com/DominikPanzarella/agent-as-a-judge.git
cd agent-as-a-judge
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

`requirements.txt` has the two API clients (`openai`, which also talks to OpenRouter, and
`python-dotenv`), the libraries that the ClassEval classes import (`numpy`, `pandas`, `pillow`,
`gensim`) and the statistics libraries for the analysis (`scipy`, `statsmodels`).

### 4.3 API keys

```bash
cp .env.example .env
```

Then open `.env` and write the two keys after `OPENAI_API_KEY=` and `OPENROUTER_API_KEY=`. Git
ignores `.env`, so the keys never reach a commit. Do not paste them anywhere else.

### 4.4 Data

```bash
./scripts/download_data.sh
```

The script downloads `ClassEval_data.json` from the ClassEval repository and the benchmarks+
archive from Zenodo into `data/raw/`. Git does not track that folder. Run the script once after
cloning; everything we derive from the raw data is already in `data/selection/`, which is tracked.

## 5. Usage

All commands run from the repository root. The scripts that run the models (`coder.py`, `judge.py`
and `loop.py`) have a `--dry-run` option that prints the prompt and sends nothing. They also skip
the classes they have already done, unless you pass `--force`.

### 5.1 Prepare the classes

```bash
.venv/bin/python scripts/benchmark_stats.py     # counts of trivial and problematic methods in benchmarks+
.venv/bin/python scripts/select_classes.py      # keeps 71 classes -> data/selection/classes.csv
.venv/bin/python scripts/order_methods.py       # order of the methods -> data/selection/method_order.csv
.venv/bin/python scripts/pick_dev_classes.py    # 10 development classes -> data/selection/dev_classes.csv
```

The outputs are already in the repository. Run these again only if you change the selection rules.

### 5.2 Check the tests and the docstrings

```bash
.venv/bin/python scripts/harness.py                   # reference solutions must pass, stubs must fail
.venv/bin/python scripts/check_docstring_examples.py  # runs every docstring example on the reference
```

The harness writes `data/selection/reference_check.csv` (empty when every reference passes) and
`data/selection/weak_tests.csv`. The docstring check writes `data/selection/docstring_examples.csv`;
the examples we checked by hand are in `data/selection/wrong_docstring_examples.csv`.

### 5.3 Check the APIs and the budget

```bash
.venv/bin/python scripts/check_api.py   # one tiny request to each API, prints tokens and cost
.venv/bin/python scripts/budget.py      # dollars spent so far on each API
```

### 5.4 Setup C0: the coder alone

```bash
.venv/bin/python scripts/coder.py --dry-run ClassEval_19            # show the first prompt
.venv/bin/python scripts/coder.py ClassEval_19 ClassEval_55         # run two classes
.venv/bin/python scripts/coder.py --all                             # every kept class
.venv/bin/python scripts/coder.py --name C0-r2 ClassEval_19         # a second run in runs/C0-r2/
.venv/bin/python scripts/coder.py --model qwen/qwen3.5-9b --name C0-9b ClassEval_19   # another coder
```

### 5.5 The judge on a finished run

```bash
.venv/bin/python scripts/judge.py C0 --version v2 --effort medium --dry-run ClassEval_55
.venv/bin/python scripts/judge.py C0 --version v1 --effort low ClassEval_19 ClassEval_55
.venv/bin/python scripts/judge.py C0 --version v2 --effort medium --all
.venv/bin/python scripts/judge.py C0 --version v2 --effort medium --summary   # compare with the tests
```

The first argument is the run to judge, that is a folder in `runs/`. `--version v1` only reads
the code, while `--version v2` can also run it. `--effort` is `low` or `medium`, as the course
allows.

### 5.6 Setups C1 and C2: coder and judge together

```bash
.venv/bin/python scripts/loop.py C2 --judge v2 --effort medium --dry-run ClassEval_19
.venv/bin/python scripts/loop.py C2 --judge v2 --effort medium ClassEval_19 ClassEval_55
.venv/bin/python scripts/loop.py C1 --judge v1 --all
```

`--model` changes the coder and `--name` the output folder, which by default is
`runs/<setup>-<judge>-<effort>/`.

### 5.7 Summary of the pilot

```bash
.venv/bin/python scripts/pilot_report.py
```

It prints the tables of [section 9](#9-results-so-far) from the saved results and writes
`runs/pilot_disagreements.csv`. It sends no request.

## 6. Project layout

```
.env.example                     # names of the two API keys; copy it to .env
requirements.txt                 # Python dependencies
docs/
  architecture.svg, .png         # the diagram in section 2
  roadmap_midway.md              # plan and dates up to the final report, with checkboxes
scripts/
  download_data.sh               # ClassEval and benchmarks+ -> data/raw/
  benchmark_stats.py             # prints the benchmarks+ counts behind the selection
  select_classes.py              # which classes we keep and why -> data/selection/classes.csv
  order_methods.py               # order of the methods in each class -> method_order.csv
  pick_dev_classes.py            # the 10 development classes, drawn with seed 2026
  harness.py                     # builds a class from single methods and runs the ClassEval tests
  check_docstring_examples.py    # runs the docstring examples on the reference solutions
  check_api.py                   # one tiny request to OpenAI and one to OpenRouter
  budget.py                      # cost log and the stop at 70 percent of a budget
  coder.py                       # setup C0: Qwen writes a class one method at a time
  judge.py                       # judge v1 and v2, on one method or on a whole class
  loop.py                        # setups C1 and C2: judge feedback and one revision
  pilot_report.py                # tables of the pilot from the saved results
data/
  raw/                           # downloaded data, not tracked
  selection/
    classes.csv                  # every ClassEval class: kept or not, and the reason
    method_order.csv             # the step at which each method is written, and its calls
    dev_classes.csv              # development classes, kept out of the final analysis
    weak_tests.csv               # methods whose tests also pass with an empty stub
    reference_check.csv          # reference methods that fail our harness (none)
    docstring_examples.csv       # outcome of every docstring example, one row per method
    wrong_docstring_examples.csv # docstring examples checked by hand: wrong or not
runs/
  C0/, C0-r2/                    # two runs of the coder with qwen3.8-27b
  C0-9b/, C0-9b-r2/              # two runs of the coder with qwen3.5-9b
  judge/<run>-<version>-<effort>/  # verdicts of the judge on a finished run
  judge/*-before-fix, *-before-guard/  # first verdicts, kept to document two fixes of the judge
  cost_log.csv                   # one row per API request
  pilot_disagreements.csv        # methods where a judge and the tests disagree
  pilot_adjudication.csv         # our reading of each disagreement: who is right
```

## 7. Method details

### 7.1 Class selection

ClassEval has 100 classes with 410 methods. `scripts/select_classes.py` drops a class when
benchmarks+ (the dataset of "Examining Benchmark Quality in Code Generation") marks one of its
methods as problematic, because its tests then cannot say whether the code is right. This removes
27 classes. It also drops ClassEval_7, the one class whose methods are all trivial: all nine models
tested in benchmarks+ solve them. Finally it drops ClassEval_49, whose helper method
`matches_requirements` has its own tests but is not among the methods to write, so its reference
solution fails in our harness. The remaining 71 classes have 289 methods.

Ten of the 71 classes are development classes (`scripts/pick_dev_classes.py`): ClassEval_19 and
ClassEval_55 from the first trial, plus ClassEval_16, 20, 40, 57, 60, 85, 94 and 95, drawn at random
with seed 2026. We use them to try out and tune the coder and the judge, so the final analysis
leaves them out and works on 61 classes.

### 7.2 Method order

`scripts/order_methods.py` keeps the order of the class skeleton, which we take as the logical order
chosen by the ClassEval authors. It changes that order only where a method calls another method of
the same class: the called method comes first. This moves 48 of the 289 methods, in 15 classes. One
ClassEval annotation is wrong. In ClassEval_63, `process_data` does not call `process`, so we remove
that dependency, which would otherwise create a cycle.

### 7.3 Test harness

`scripts/harness.py` puts a class together from single methods and runs each ClassEval test class
in its own subprocess, in a temporary folder and with a 10 second timeout. A method that is missing,
or that does not compile, becomes a stub that returns None, so it fails only its own tests. Some
ClassEval methods lose their decorator (`@staticmethod`), so the harness takes it back from the
class skeleton.

Run as a script, the harness checks itself. The reference solutions pass all 289 methods and all 71
classes. With stubs only, 4 methods still pass, because their tests cannot tell an empty method from
a solution. They are listed in `data/selection/weak_tests.csv`, and we report results with and
without them.

### 7.4 Coder

The coder is `qwen/qwen3.8-27b` on OpenRouter, with low reasoning effort and at most 4000 output
tokens per request. The course asks for the cheapest provider that serves a model in full precision,
so the requests ask OpenRouter to sort providers by price and to accept only bf16, fp16 or fp32.
`qwen3.6-27b` has no such provider, which is why we use 3.8.

For each method the prompt holds the class skeleton, the methods written so far and the name of the
next method, never the tests. From the reply we keep only that method, even when the model sends
back the whole class. If the method is missing or does not compile, it stays a stub and we do not
ask again, so every setup sends the coder the same number of requests.

### 7.5 Judge v1 and v2

The judge is `gpt-6-luna` in the course's OpenAI project, with low or medium reasoning effort. It
sees the class skeleton, the methods written before and the method under review, never the tests.
Its answer is a JSON object with a short reason and a verdict, OK or NOT OK; the reason comes first,
so the verdict follows from it. In C1 and C2 the reason is the feedback the coder gets.

Judge v1 only reads the code. Judge v2 can also run Python before it answers, up to 5 times per
method, with the tool `run_python`. Its code runs after the class written so far, in a separate
process, in a temporary folder and with a 10 second limit, as in the harness. With it the judge can
try the docstring examples or a case it doubts, and the reason must report what it saw. In its first
runs the judge copied the class into its own code and could end up testing the copy. Now the prompt
asks it to call the class directly, and code that redefines the class is not run.

We added v2 because v1, on the first methods, described results that the code does not produce.
Both use the OpenAI Responses API with the same settings, so only the tool differs. The older Chat
Completions API was not an option for v2, because for this model it does not accept tools together
with a reasoning effort.

### 7.6 Setups C1 and C2

`scripts/loop.py` runs the two setups with feedback. In C2 the judge reviews every method right
after the coder writes it. After a NOT OK the coder reads the reason in the same conversation and
writes that method again, once, and the next methods see the new version. C1 works on the finished
class instead: the coder writes the whole class first, the judge reviews it once, and after a NOT
OK the coder writes the whole class again, once. Neither setup reviews or revises a reply without a
usable method, as in C0, so the feedback is the only difference with C0.

The harness runs the tests twice, on the first version and on the final version of every method.
The first run tells how good the verdicts were, the second whether the feedback helped.

### 7.7 Costs and budget

| Model | Provider | Input | Cached input | Output |
|---|---|---|---|---|
| qwen/qwen3.8-27b (coder) | DeepInfra, bf16 | 0.15 | 0.0375 | 1.875 |
| qwen/qwen3.5-9b (tested coder) | PrimeIntellect, bf16 | 0.075 | 0.068 | 0.11 |
| gpt-6-luna (judge) | OpenAI, standard tier | 0.10 | 0.01 | 0.50 |

Prices are in dollars per million tokens, as listed on 6 November 2026. OpenRouter returns the cost
of each request. OpenAI does not, so `scripts/judge.py` computes it from the prices above; the
OpenAI dashboard has the real spend. `scripts/budget.py` logs every request in `runs/cost_log.csv`
and, before each class, stops the run when a service has spent 70 percent of its 10 dollars. For
OpenRouter it also asks the service how much the key has spent, because both of us use the same key.

## 8. Output files

Every run of `coder.py` writes one JSON file per class in `runs/<name>/<task_id>.json`. It holds the
task, the model, and for each method the extracted `code`, whether it was `valid`, the raw `reply`,
the `finish_reason`, the provider, the token counts, the `cost` and whether it `passed` its tests.
The file also has `class_passed`, the result of every test class (`tests`) and the full `source`
that the harness ran.

The judge writes `runs/judge/<run>-<version>-<effort>/<task_id>.json`. For each method it holds the
`verdict`, the `reason`, whether the method `passed` its tests, the code the judge ran with its
output (`runs`, v2 only), and the tokens and cost of every request. `auto` is true when the coder's
reply had no usable method, so the judge was not asked.

`loop.py` writes `runs/<setup>-<judge>-<effort>/<task_id>.json`. For each method it keeps the
`first` version, the `review`, the `revision` if any, the `final_code`, and `passed_first` and
`passed` for the two test runs. In C1 the `review` and the `revision` belong to the whole class, and
`revision.replaced` lists the methods the coder actually changed.

`runs/cost_log.csv` has one row per request, with time, run, class, method, role (`coder`,
`coder-revision`, `judge-v1` or `judge-v2`), service, model, provider, tokens and cost.

## 9. Results so far

These numbers come from the pilot on the 10 development classes (38 methods) and are not the
results of the study. Run `scripts/pilot_report.py` to print them again.

The coder, two identical runs per model:

| Coder | Methods passing (run 1 / run 2) | Classes passing | Methods that change between runs | Cost per method |
|---|---|---|---|---|
| qwen3.8-27b | 31 / 32 of 38 | 6 / 5 of 10 | 3 | 0.0012 $ |
| qwen3.5-9b | 26 / 23 of 38 | 3 / 2 of 10 | 7 | 0.0002 $ |

The four judges on the first run of qwen3.8-27b, compared with the tests (7 methods fail, 31 pass):

| Judge | Agreement | Cohen's kappa | OK to a failing method | NOT OK to a passing method | Cost per method |
|---|---|---|---|---|---|
| v1, low effort | 0.74 | 0.21 | 4 of 7 | 6 of 31 | 0.00015 $ |
| v1, medium effort | 0.66 | 0.02 | 5 of 7 | 8 of 31 | 0.00024 $ |
| v2, low effort | 0.68 | -0.05 | 6 of 7 | 6 of 31 | 0.00022 $ |
| v2, medium effort | 0.63 | -0.10 | 6 of 7 | 8 of 31 | 0.00030 $ |

Against the tests all four judges are close to chance. We read the 15 methods on which at least one
judge and the tests disagree, ran the code and compared it with the docstring and the reference
solution (`runs/pilot_adjudication.csv`). In 5 of them the tests require something the docstring
does not say. For 3 others the docstring example contradicts the reference solution. The judge
finds a real bug that no test checks in 3 methods. Only 2 are coder bugs that the tests catch; the
last 2 are edge cases outside the docstring, where the judge is stricter than the specification.

## 10. Known issues

- ClassEval tests and docstrings do not always agree, even after the benchmarks+ filter. Running
  the 671 docstring examples on the reference solutions gives 5 wrong examples in 4 classes
  (`data/selection/wrong_docstring_examples.csv`). This is a lower bound: 153 examples raise an
  error and 25 cannot be compared automatically.
- Agreement with the tests alone does not measure the judge well, so we also classify the
  disagreements by hand.
- The coder is not deterministic. Between two identical runs 3 of 38 methods change result with
  qwen3.8-27b, and 7 with qwen3.5-9b.
- qwen3.5-9b reasons for longer, and 2 or 3 of its replies per run hit the limit of 4000 tokens.
- The choice of coder, the handling of the classes with conflicting tests and the number of
  repetitions are open questions that we have asked the instructors about.

## 11. References

- Zhuge et al., "Agent-as-a-Judge: Evaluate Agents with Agents", ICML 2025.
  https://arxiv.org/abs/2410.10934
- Du et al., "ClassEval: A Manually-Crafted Benchmark for Evaluating LLMs on Class-level Code
  Generation", 2023. https://arxiv.org/abs/2308.01861
- "Examining Benchmark Quality in Code Generation", data set benchmarks+.
  https://doi.org/10.5281/zenodo.21031875

## 12. Data and licenses

- ClassEval: https://github.com/FudanSELab/ClassEval, CC BY-NC 4.0.
- benchmarks+: https://doi.org/10.5281/zenodo.21031875, CC BY 4.0.

Neither data set is stored in this repository; `scripts/download_data.sh` fetches them. The files in
`data/selection/` and `runs/` contain class names, method names and short excerpts derived from
them.

## 13. Authors and acknowledgments

Dominik Panzarella and Daniele Buser, students of the Neural Code Analysis course at USI, taught by
Prof. Gabriele Bavota with Alessandro Giagnorio as teaching assistant. The course provided the
OpenAI project and the OpenRouter key used for every model call.
