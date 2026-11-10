# Roadmap to the midway report (19 November 2026) and beyond

The midway report is at most 2 pages, uploaded on iCorsi by midnight of 19 November. It needs the
title, the team, the changes to the plan, the status with numbers, and a schedule until
16 December. Tick a box by changing `[ ]` into `[x]`.

![Architecture](architecture_base.png)

Solid parts are built. Orange parts are new in the base version, or planned when dashed. The
source is `architecture_base.svg`.

## Course dates

- 12 and 16 November: labs.
- 19 November: midway report, by midnight.
- 23 or 26 November: 1-to-1 meetings, if the instructors call us.
- 14 December: last lab.
- 16 December: final report, at most 10 pages plus 2 for references.
- 17 December: 5-minute presentation.

## Done

- [x] **Data and classes.** 71 of the 100 ClassEval classes, 289 methods (`select_classes.py`).
- [x] **Method order** (`order_methods.py`). Checked against the fields too: no change needed.
- [x] **Test harness** (5 Nov). References pass all 289 methods; 4 methods pass even as stubs.
- [x] **APIs** (6 Nov). Coder qwen3.8-27b in bf16 (qwen3.6-27b has no full-precision provider),
  judge GPT-6 Luna.
- [x] **Coder, setup C0** (6 Nov). One method per request, never seeing the tests.
- [x] **Judge v1 and v2** (6 Nov). v1 reads the code; v2 can also run it, up to 5 times.
- [x] **Pilot** (7 Nov, 10 development classes, 38 methods). Against the tests the judge looks close
  to chance (kappa at most 0.21). Against our labels of the 15 disputed methods it reaches 0.60,
  because the tests often check things the docstring does not say. With medium effort all the
  judge's concrete claims were true, so we keep the judge with medium effort.
- [x] **Setups C1 and C2 on the development classes** (7 Nov). C2: 3 methods fixed, 2 broken. C1:
  no change. Both start from worse first versions than C0, so the coder's randomness hides the
  effect of the feedback.
- [x] **Checks after the literature review** (8 Nov, `pilot_controls.py`). Rewriting the rejected
  methods without feedback does about as well as C2's revisions. The judge catches 15 of 22 failing
  methods of the 9B and 5 of 19 of the 27B, whose failures are mostly hidden requirements.

## Week 2 (9 to 15 November)

- [ ] **Base judge** (10 to 12 Nov). `judge.py` gets the tests of the method and a tool that runs
  them on the class written so far, next to `run_python`; `loop.py` tells the judge which methods
  are still missing. A dry run on the development classes first.
- [ ] **Full runs** (12 to 13 Nov). C1 and C2 on the 71 classes, after the instructors' answer.
- [ ] **Analysis** (14 to 15 Nov). Pass rates with and without the weak methods, the judge's TPR
  and TNR, McNemar tests and bootstrap intervals (`analyze.py`).
- [ ] **Error analysis** (14 to 15 Nov). 20 disagreements between judge and tests, grouped into
  kinds, deciding each time who is right (`analyze.py --sample 20`).

## 16 to 19 November: midway report

- [ ] **Draft** (16 Nov), to bring to the lab.
- [ ] **Submission** (19 Nov).

## After the midway (20 November to 17 December)

- [ ] **C3, the flywheel** (20 to 29 Nov). Three rounds of classes; between rounds the judge keeps
  a memory of its mistakes.
- [ ] **Later variants** (30 Nov to 6 Dec), the ones the instructors accept.
- [ ] **Full analysis** (7 to 11 Dec), answering RQ1, RQ2 and RQ3.
- [ ] **Final report** (7 to 16 Dec), with a draft at the lab of 14 December.
- [ ] **Presentation** (17 Dec).

## Base version (decided on 9 and 10 November)

- [ ] **Coder unchanged.** It writes one method at a time, never sees the tests and runs no code;
  it improves only inside the conversation, after the judge's feedback.
- [ ] **Judge with the tests.** The judge gets the docstring and all the ClassEval tests of the
  method, runs the method and the tests on the class written so far, and checks what the tests do
  not cover. In practice tests exist but are incomplete, and this is the case we want to study.
- [ ] **Methods not written yet.** The tests of 14 of the 289 methods call a method that comes
  later in the order (68 call some other method of the class). The judge is told which methods are
  still stubs.
- [ ] **Feedback after every method (C2) and at the end of the class (C1)**, as for RQ1. The grade is
  always all the ClassEval tests on the finished class.
- [ ] **Always a coder and a judge** (10 Nov). C0 and C4 are dropped. The baseline is the first
  version of each method, written before any feedback, against the final one.

## Later variants, to discuss with the instructors

Each comes with its reason and source.

- [ ] **A memory for the coder.** In the base version the coder carries nothing from one class to
  the next. A short list of the corrections it received, in its prompt, would let it improve over
  time (Reflexion, Shinn et al. 2023).
- [ ] **A coder that runs its own code**, on the docstring examples and without the ClassEval tests,
  before handing the method in (Self-Debug, Chen, Lin et al. 2024). Whether the coder may also see
  the tests is a question for the instructors.
- [ ] **Test cases split between the judge and the grade.** Some test cases of each method go to the
  judge, the others give the grade (224 of the 289 methods have five), so the grade does not use
  the tests the judge has seen.

- [ ] **Same first versions in every setup.** C1 and C2 start from the same first versions, written
  once with the same prompt, since two identical runs differ by 3 methods, as much as the feedback.
- [ ] **Our labels next to the tests, with TPR and TNR.** The paper judges its judge against human
  experts, and our tests and docstrings often disagree. We write the labelling criteria first,
  because people change them while labelling (Shankar et al. 2024, "criteria drift").
- [ ] **Feedback with evidence.** The coder also gets the code the judge ran and its output.
  Grounded critiques work better (CRITIC, Gou et al. 2024), and the judge's medium-effort claims
  were all true.
- [ ] **Judge v3, one docstring requirement at a time**, like the paper's ask module, with a third
  verdict, NOT SPECIFIED, that never reaches the coder. Both methods broken in C2 were correct code
  rejected for behaviour the docstring does not describe. Telling an underspecified task apart from
  a wrong solution works better as a separate step (Edwards and Schuster 2026). v3 also writes its
  checks from the docstring before reading the code, because tests written by a model carry a bias
  that can mislead the feedback (Chen et al., ACL 2025).
- [ ] **A careful memory in C3**: only corrections we confirm by hand, at most about ten. The
  paper found its memory module harmful, because errors spread to later verdicts.
- [ ] **C3 without the manual check.** Every disagreement between the judge and the tests goes into
  the memory as it is, as in the paper's memory module. Against C3 with the manual check, it shows
  how much the check matters.
- [ ] **C3 with a third model as reviewer.** A model of a third family, neither Qwen nor GPT, reads
  each disagreement (docstring, tests, code, the judge's reason) and decides in our place who is
  right. On the development classes we first compare it with our labels. Models tend to favour
  their own outputs (Panickssery et al. 2024); a model that judges a judge is the meta-judge of
  Wu et al. 2024, and a panel of different models is the jury of Verga et al. 2024.
- [ ] **Two controls**: empty feedback (NOT OK without the reason) and resampling (the method
  written again without feedback). They separate the effect of the reason from that of a second
  attempt; in a placebo-controlled study resampling did as well as feedback (Iscan 2026).
- [ ] **Up to three revision rounds for RQ3**, on the development classes only, recording the
  judge's OK and the tests at each round. A coder learns to please a judge only under repeated
  feedback (Gao et al. 2023; Pan et al. 2024), and one revision is too little to show it.
- [ ] **Count the revisions that change behaviour.** The coder must always rewrite, so it also
  follows wrong reviews (sycophancy, Sharma et al. 2024).
- [ ] **The judge as an evaluator.** TPR and TNR from the development classes correct the judge's
  pass rate on the other 61 classes (Rogan and Gladen formula).
- [ ] **pass^k if we repeat runs**: the share of methods that pass in all k runs (from τ-bench).

Sources: Zhuge et al. 2025 (the paper); Panickssery et al. 2024 (arXiv 2404.13076); Wu et al. 2024
(Meta-Rewarding, arXiv 2407.19594); Verga et al. 2024 (juries, arXiv 2404.18796); Shinn et al. 2023
(Reflexion, arXiv 2303.11366); Chen, Lin et al. 2024 (Self-Debug, arXiv 2304.05128); Edwards and
Schuster 2026 (arXiv 2603.26233); Chen et al. 2025 (ACL, 2025.acl-long.881); Iscan 2026 (arXiv
2606.31511); Gao et al. 2023 (ICML); Pan et al. 2024 (arXiv 2402.06627); Sharma et al. 2024 (arXiv
2310.13548); phase 14 (lessons 03 and 05), 16.23 and 18.02 of AI Engineering from Scratch
(https://github.com/DominikPanzarella/ai-engineering-from-scratch); lectures 4, 5, 6 and 14 of
Engineering AI Systems, USI
(https://www.composablesystems.org/courses/engineering-ai-systems/fa2026/).

## Open decisions

- [ ] **Coder.** qwen3.8-27b passes 82% of the methods and leaves little room for feedback;
  qwen3.5-9b passes fewer but is less stable, and the judge catches more of its failures (15 of 22
  against 5 of 19).
- [ ] **Repetitions.** One run per setup, or two or three. A simulation on the 251 test methods: an
  effect like the pilot's (3 fixed and 2 broken per 38) is detected 16% of the time with one run
  and about 48% with three; an 8-point gain 94% of the time with one run.
- [ ] **Same budget across setups.** For now: one revision per method in C2, one per class in C1.
- [ ] **The lab note "classes with the 1st methods implemented".** To ask Alessandro.
- [ ] **Coder memory and tests for the coder** in the later versions. To ask the instructors.
- [x] **Judge effort** (7 Nov). Medium: its claims were all true.
