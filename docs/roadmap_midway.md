# Roadmap to the midway report (Thursday 19 November 2026)

For the midway report our proposal promises a working judge, setups C0, C1 and C2 run on the 72
classes, and a first answer to RQ1. Tick a box by changing `[ ]` into `[x]` when a step is done.

![Architecture](architecture.png)

The diagram is also in `architecture.svg`, which can be edited by hand.

## Already done

- [x] **Data download.** `scripts/download_data.sh` puts ClassEval and benchmarks+ in `data/raw/`.
- [x] **Class selection (option A).** `scripts/select_classes.py` keeps 72 classes and 295 methods.
- [x] **Method order.** `scripts/order_methods.py` fixes the order of the methods in each class.

## Week 1 (3 to 8 November): setup and pilot

- [ ] **API check** (4 Nov). Send one short request to GPT-6 Luna through the OpenAI project and one
  to Qwen through OpenRouter. On OpenRouter, pick the cheapest non-quantized provider with good
  uptime. Then tell Alessandro that the access works.
- [ ] **Test harness** (5 Nov). Put a class together from the methods written so far and run the
  ClassEval tests of each method in a subprocess with a timeout. As a sanity check, the reference
  solutions of all 295 methods must pass. A method that fails with its own reference solution goes
  back to the selection.
- [ ] **Coder, setup C0** (6 Nov). The coder writes one method per request, in the order of
  `data/selection/method_order.csv`. It sees the class skeleton and the methods written so far,
  never the tests.
- [ ] **Judge v1** (6 Nov). For each new method the judge reads the class description, the method
  docstring and the code written so far. It answers OK or NOT OK with a short reason, in JSON.
- [ ] **Pilot** (8 Nov). Run C0 and the judge on 8 classes and answer two questions before going on.
  First, is the judge clearly better than chance against the tests? We look at Cohen's kappa and at
  how often it says OK to code that fails. Second, does one method cost few enough tokens for C0 to
  C2 on 72 classes to fit in the two budgets of 10 dollars? If the judge is close to chance, we change
  the model before the full runs.

## Week 2 (9 to 15 November): C1, C2 and the full runs

- [ ] **Setups C1 and C2** (10 Nov). In C1 the judge gives its verdict on the finished class and the
  coder may revise once. In C2 the verdict comes after each method, again with one revision of that
  method.
- [ ] **Full runs** (11 to 13 Nov). Run C0, C1 and C2 on the 72 classes with low reasoning effort.
  Log tokens and cost after every class, and stop if either budget reaches 70 percent.
- [ ] **Analysis** (14 to 16 Nov). Report the share of methods and of classes that pass their tests,
  and for the judge its accuracy, kappa and rate of false OK verdicts. Compare C2 with C0 and with C1
  using McNemar tests and bootstrap confidence intervals.
- [ ] **Error analysis** (14 to 16 Nov). Read 20 cases where the judge and the tests disagree and
  group them into a few types.

## 17 to 19 November: midway presentation

- [ ] **Slides** (17 Nov). The idea in one slide; the setup (72 classes, method order, models,
  budget); the pilot; the results of C0 to C2 as a first answer to RQ1; what went wrong and the plan
  for C3 and C4.
- [ ] **Rehearsal** (18 Nov).

## Open decisions

- [ ] **Which Qwen model writes the code.** Candidates are qwen3.6-27b, qwen3.8-27b or a smaller
  model. The pilot decides, because a coder that already passes almost every test leaves no room for
  feedback.
- [ ] **What "the same budget" means across setups.** A simple rule is at most one revision per
  method in C2 and one per class in C1, with the tokens of every setup reported next to the results.
- [ ] **The note "classes with the 1st methods implemented"** from the lab session. We should ask
  Alessandro what he meant.
- [ ] **Order by fields.** The dependencies cover calls between methods, not fields. A method that
  reads a field may make more sense after the method that fills it. We read the 72 classes once and
  record any manual change in `scripts/order_methods.py`.
