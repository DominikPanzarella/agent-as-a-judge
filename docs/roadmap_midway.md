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
- [x] **Judge v2 with a tool** (6 Nov). Before the verdict the judge may run Python up to 5 times
  on the class written so far, for example the docstring examples, in a subprocess with a timeout.
  The hidden tests stay hidden. On the first four methods all its claims about the code are true;
  its two disagreements with the tests come from an ambiguous docstring and from a bug the tests do
  not check.
- [x] **Pilot** (by Sunday 8 Nov). Run C0 on 8 classes and judge their methods with judge v1 (and v2,
  if we build it), with low and with medium effort. Three questions before going on. Is the judge
  clearly better than chance against the tests? We look at Cohen's kappa and at how often it says
  OK to code that fails or NOT OK to code that passes. Are the concrete claims in its reasons true?
  We check a sample by running the code. Does one method cost few enough tokens for C0 to C2 on 71
  classes to fit in the two budgets of 10 dollars? The first estimate is about 0.0018 dollars per
  method for the coder. We also run C0 a second time on the same 8 classes, to see how many methods
  change result by chance alone. If the judge is close to chance, we change it before the full runs.

  Results (6 and 7 Nov, `scripts/pilot_report.py`, 10 development classes, 38 methods). The coder
  passes 31 and 32 methods in two identical runs, and 3 methods change result by chance. Against the
  tests the judges are close to chance, with kappa between -0.10 and 0.21. We then read the 15
  methods on which a judge and the tests disagree (`runs/pilot_adjudication.csv`). In 5 of them the
  tests ask for behaviour that the docstring does not describe, in 3 the docstring example is wrong,
  and in 3 the judge finds a real bug that no test checks. Against these corrected labels, with the
  5 unclear methods left out, kappa rises to 0.60 for v1-low and to 0.47 for v1-medium and
  v2-medium. Most of the gap comes from the tests, so we keep the judge as it is.
  `scripts/check_claims.py` runs the 22 concrete claims found in the NOT OK reasons. Several judges
  make the same claim; counted per judge, 23 of 23 claims are true with medium effort and 12 of 16
  with low effort. Costs are small: about 0.0012 dollars per method for
  the coder and 0.0003 for judge v2-medium, so a whole setup on 289 methods costs well under one
  dollar.

## Week 2 (9 to 15 November): C1, C2 and the full runs

- [x] **Setups C1 and C2** (10 Nov). In C1 the judge gives its verdict on the finished class and the
  coder may revise once. In C2 the verdict comes after each method, again with one revision of that
  method. The code is ready (`scripts/loop.py`, 6 Nov). On 7 Nov we ran both on the 10 development
  classes, with judge v2 and medium effort. In C2 the revisions fixed 3 methods and broke 2. The
  two broken methods were correct, and the judge asked for behaviour the docstring does not
  describe. In C1 the class revisions changed no test result. Both setups end below C0 (27 and 29
  methods against 31), but their first versions were already worse, so the gap comes from the
  coder's randomness before any feedback. The first C1 run of ClassEval_55 exposed a bug: a whole
  class with only 4000 tokens ran out during reasoning and wrote no code. The class revision now
  gets 4000 tokens per method of the class, as in C2 (old result in `runs/C1-v2-medium-before-fix`).
  Cost on 289 methods: about 0.6 dollars for the coder and 0.1 for the judge in each setup. The
  full runs wait for the instructors' answer on coder, classes, repetitions and the proposals of
  the next section.
- [ ] **Full runs** (11 to 13 Nov). Run C0, C1 and C2 on the 71 classes, the coder with low
  reasoning effort and the judge with the effort chosen in the pilot.
  Log tokens and cost after every class, and stop if either budget reaches 70 percent. The lab of
  12 November is a good moment to show the first numbers to the instructors.
- [ ] **Analysis** (14 to 15 Nov). Report the share of methods and of classes that pass their tests,
  with and without the 4 weak methods, and for the judge its accuracy, kappa and rate of false OK
  verdicts. Compare C2 with C0 and with C1 using McNemar tests and bootstrap confidence intervals.
  `scripts/analyze.py` does all of this and already works on the development runs.
- [ ] **Error analysis** (14 to 15 Nov). Read 20 cases where the judge and the tests disagree and
  group them into a few types (`scripts/analyze.py --sample 20` draws them). For each case we also decide who is right, since the first runs
  already show disagreements caused by ambiguous docstrings and by bugs the tests do not check.

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

## Proposals to discuss with the instructors (7 Nov)

These come from the pilot and from the Agent-as-a-Judge paper. Others come from the lessons on
Reflexion, Self-Refine and CRITIC in the ai-engineering-from-scratch course, and from lectures 4, 5
and 14 of Engineering AI Systems (USI, Fall 2026). In the diagram below, blue is what we built and
orange is proposed or planned.

![Proposed architecture](architecture_proposed.png)

- [ ] **Same first versions in every setup.** Two identical runs of C0 differ by up to 3 methods, as
  much as the effect we want to measure. C1 can start from the class written in C0. C2 can reuse
  the C0 version of a method as long as no earlier method was revised, because the prompt is then
  the same. The difference between setups would then come only from the feedback.
- [ ] **Human labels next to the tests.** The paper scores the judge against the majority vote of
  three experts, not against tests. We can label the disagreements independently, measure our
  agreement, and then settle each case together.
- [ ] **Feedback with evidence.** In C2 the coder could also receive the code the judge ran and its
  output, as in CRITIC. The paper notes that the judge is sensitive to noise and needs factual
  information, and the claims of v2 with medium effort were all true.
- [ ] **A judge that checks only what the docstring states.** Both methods broken in C2 were correct
  code that the judge rejected for behaviour the docstring does not describe. The paper's ask
  module judges one requirement at a time; a v3 could list the requirements of the docstring and
  check each.
- [ ] **Memory in C3.** The paper found its memory module harmful, because an error in one judgment
  spreads to the next ones. Our memory would hold the verdicts that the tests proved wrong, but in
  the pilot about one method in five had a conflict between test and docstring. We could keep only
  the corrections confirmed by hand, and cap their number.
- [ ] **TPR and TNR instead of agreement.** Engineering AI Systems reports a judge with two numbers:
  the share of passing outputs it accepts (TPR) and the share of failing ones it rejects (TNR). When
  most methods pass, as with our coder, a judge that accepts everything already agrees often.
  `scripts/analyze.py` now prints both. The lecture asks for 30 to 50 failures in the development
  set and as many in the test set, while our development classes have 7 failing methods in C0. The
  9B coder, which fails more often, would help here too.
- [ ] **Written criteria before the labels.** Shankar et al. (2024) show that people change their
  criteria while they label ("criteria drift"). We would write the rules for deciding who is right
  first, label a few cases together, and only then label alone. For the error analysis we would
  write a note on each case before naming the kinds of error (open coding, then axial coding).
- [ ] **The judge as an evaluator.** With TPR and TNR measured on the development classes, the
  formula of Rogan and Gladen turns the judge's share of OK verdicts on the other 61 classes into an
  estimate of the true pass rate. Comparing it with the tests shows whether the judge could replace
  them, which is the use the paper had in mind.
- [ ] **pass^k if we repeat the runs.** If each setup runs k times, the pass^k of τ-bench (the share
  of methods that pass in all k runs) shows how reliable the coder is, next to the average.
- [ ] **A control with empty feedback.** After a NOT OK, the coder is asked to write the method again
  without the reason. With self-refine, it separates the effect of the reason from the effect of a
  second attempt.

## Open decisions

- [ ] **Which Qwen model writes the code.** For now qwen3.8-27b, since qwen3.6-27b has no
  full-precision provider. The pilot can still change it: a coder that already passes almost every
  test leaves no room for feedback, and then a smaller model such as qwen3.5-9b (bf16 on DeepInfra)
  would be the better choice.
- [ ] **What "the same budget" means across setups.** A simple rule is at most one revision per
  method in C2 and one per class in C1, with the tokens of every setup reported next to the results.
- [ ] **The note "classes with the 1st methods implemented"** from the lab session. We should ask
  Alessandro what he meant, at the lab of 12 November at the latest.
- [x] **Order by fields** (7 Nov). The dependencies cover calls between methods, not fields.
  `scripts/check_field_order.py` lists every method that reads a field which a later method writes.
  There are 43 such pairs in 20 classes, and in all of them `__init__` already sets the field, so
  the coder sees it in the skeleton. The order stays as it is.
- [x] **Reasoning effort of the judge** (7 Nov). Medium. With low effort 4 of the 16 claims we
  could run were false, with medium effort none of 23. The coder reads these claims in C1 and C2,
  so they must be true, and medium costs only about 0.09 dollars for all 289 methods with v2.
