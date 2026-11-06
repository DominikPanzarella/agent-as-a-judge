# Roadmap to the midway report (Thursday 19 November 2026) and beyond

The midway report is a written report of at most 2 pages, submitted on iCorsi by midnight of
19 November. There is no presentation in class. It must contain the title, the team, the changes to
the original plan, the status of the project with explicit numbers, and a detailed schedule until
16 December that explains why each step is feasible. Tick a box by changing `[ ]` into `[x]`.

![Architecture](architecture.png)

The diagram is also in `architecture.svg`, which can be edited by hand.

## Course dates

- Thursday 12 and Monday 16 November: labs, where we can ask questions.
- Thursday 19 November: midway report, by midnight.
- Monday 23 and Thursday 26 November: 1-to-1 meetings, for the groups the instructors call.
- Monday 14 December: last lab for feedback.
- Wednesday 16 December: final report, at most 10 pages plus 2 for references.
- Thursday 17 December: 5-minute presentation in class.

## Already done

- [x] **Data download.** `scripts/download_data.sh` puts ClassEval and benchmarks+ in `data/raw/`.
- [x] **Class selection (option A).** `scripts/select_classes.py` keeps 71 classes and 289 methods.
- [x] **Method order.** `scripts/order_methods.py` fixes the order of the methods in each class.
- [x] **Test harness** (5 Nov). `scripts/harness.py` runs the tests of each method in a subprocess.
  The reference solutions pass all 289 methods; 4 methods pass even as empty stubs and are listed
  in `data/selection/weak_tests.csv`.

## Week 1 (5 to 8 November): setup and pilot

- [x] **API check** (6 Nov). `scripts/check_api.py` sends one tiny request to GPT-6 Luna and one to
  Qwen, on the cheapest OpenRouter provider that serves the model in full precision. Both work.
  qwen3.6-27b has no provider in bf16 or fp16, so the coder is now qwen3.8-27b, served in bf16 by
  DeepInfra (0.15 dollars per million input tokens, 1.875 per million output tokens).
- [x] **Coder, setup C0** (6 Nov). `scripts/coder.py` writes one method per request, in the order
  of `data/selection/method_order.csv`. It sees the class skeleton and the methods written so far,
  never the tests. First real run on ClassEval_19 and ClassEval_55: 3 of 4 methods pass, about
  1500 tokens and 0.0018 dollars per method.
- [x] **Judge v1** (6 Nov). For each new method the judge reads the class description, the
  method docstring and the code written so far. It answers OK or NOT OK with a short reason, in JSON.
  On the first four methods it agrees with the tests three times, but every concrete claim in its
  reasons is false: it cannot run code. This makes it the "judge without tools" control.
- [ ] **Judge v2 with a tool** (to decide). Before the verdict the judge may run a few lines of
  Python on the class written so far, for example the docstring examples, in a subprocess with a
  timeout. The hidden tests stay hidden.
- [ ] **Pilot** (by Sunday 8 Nov). Run C0 on 8 classes and judge their methods with judge v1 (and v2,
  if we build it), with low and with medium effort. Three questions before going on. Is the judge
  clearly better than chance against the tests? We look at Cohen's kappa and at how often it says
  OK to code that fails or NOT OK to code that passes. Are the concrete claims in its reasons true?
  We check a sample by running the code. Does one method cost few enough tokens for C0 to C2 on 71
  classes to fit in the two budgets of 10 dollars? The first estimate is about 0.0018 dollars per
  method for the coder. We also run C0 a second time on the same 8 classes, to see how many methods
  change result by chance alone. If the judge is close to chance, we change it before the full runs.

## Week 2 (9 to 15 November): C1, C2 and the full runs

- [ ] **Setups C1 and C2** (10 Nov). In C1 the judge gives its verdict on the finished class and the
  coder may revise once. In C2 the verdict comes after each method, again with one revision of that
  method.
- [ ] **Full runs** (11 to 13 Nov). Run C0, C1 and C2 on the 71 classes, the coder with low
  reasoning effort and the judge with the effort chosen in the pilot.
  Log tokens and cost after every class, and stop if either budget reaches 70 percent. The lab of
  12 November is a good moment to show the first numbers to the instructors.
- [ ] **Analysis** (14 to 15 Nov). Report the share of methods and of classes that pass their tests,
  with and without the 4 weak methods, and for the judge its accuracy, kappa and rate of false OK
  verdicts. Compare C2 with C0 and with C1 using McNemar tests and bootstrap confidence intervals.
- [ ] **Error analysis** (14 to 15 Nov). Read 20 cases where the judge and the tests disagree and
  group them into a few types.

## 16 to 19 November: midway report

- [ ] **Draft** (16 Nov). Write the 2 pages and bring them to the lab for feedback. The changes to
  the plan so far: the models run through the course APIs instead of locally (the coder is
  qwen3.8-27b, because qwen3.6-27b has no full-precision provider), we use 71 of the 100 classes,
  the order of the methods is fixed and documented, and, if we build it, the judge can run code.
- [ ] **Submission** (19 Nov, before midnight). Final read and upload on iCorsi.

## After the midway (20 November to 17 December)

- [ ] **1-to-1 meeting** (23 or 26 Nov), if the instructors call us.
- [ ] **Setup C3, the flywheel** (20 to 29 Nov). Split the 71 classes into three rounds. After each
  round the judge learns which of its verdicts the tests proved wrong and keeps them in memory.
- [ ] **Setup C4 and the two controls** (30 Nov to 6 Dec). C4 gives the coder the real test results.
  The controls are the judge without tools (judge v1, already written) and a coder that judges its
  own code (self-refine).
- [ ] **Full analysis** (7 to 11 Dec). Answer RQ1, RQ2 and RQ3 with the same tests as above.
- [ ] **Final report** (7 to 15 Dec). At most 10 pages plus 2 of references; bring a draft to the lab
  of 14 December.
- [ ] **Submission of the final report** (16 Dec).
- [ ] **5-minute presentation** (17 Dec).

## Open decisions

- [ ] **Which Qwen model writes the code.** For now qwen3.8-27b, since qwen3.6-27b has no
  full-precision provider. The pilot can still change it: a coder that already passes almost every
  test leaves no room for feedback, and then a smaller model such as qwen3.5-9b (bf16 on DeepInfra)
  would be the better choice.
- [ ] **What "the same budget" means across setups.** A simple rule is at most one revision per
  method in C2 and one per class in C1, with the tokens of every setup reported next to the results.
- [ ] **The note "classes with the 1st methods implemented"** from the lab session. We should ask
  Alessandro what he meant, at the lab of 12 November at the latest.
- [ ] **Order by fields.** The dependencies cover calls between methods, not fields. A method that
  reads a field may make more sense after the method that fills it. We read the 71 classes once and
  record any manual change in `scripts/order_methods.py`. This has to happen before the full runs
  of 11 November, because it changes the prompts.
- [ ] **Reasoning effort of the judge.** On the first four methods low and medium effort gave the
  same verdicts. Medium costs about three times more, about 0.1 dollars for all 289 methods. The
  pilot decides.
