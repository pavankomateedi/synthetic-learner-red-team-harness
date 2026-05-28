# Limitations Memo

*Deliverable 10 / PRD §16. Required honest disclosure.*

This harness is a useful critic, not an oracle. Below is what it cannot do,
where it may mislead, and what a human would need to trust its findings.

## 1. Real student behaviors the synthetic learners cannot approximate

- **Natural language.** Learners emit action *types* and canonical answer
  strings, not free-form student writing. Real misreadings, partial
  explanations, and novel wrong answers are not generated. The
  `low_reading_comprehension` archetype from the PRD table is therefore *not*
  implemented — literacy conflation can't be exercised without real text.
- **Emotional dynamics over time.** Anxiety is a static dimension that raises
  give-up probability; it does not accumulate, spike, or recover the way a real
  student's affect does within or across sessions.
- **Strategic, adaptive adversarial behavior.** The `adversarial_learner` tries
  one scripted bypass pattern. A real adversary (or a jailbreak-seeking
  student) adapts to refusals; ours does not escalate creatively.
- **Genuine partial knowledge.** Mastery is a scalar per concept. Real partial
  understanding is structured (a student may handle like-denominators but not
  unlike) — we approximate this only at the granularity of the four concepts.

## 2. How the chosen domain limits generalizability

- Findings are about **7th-grade fraction arithmetic** with four concepts and
  ~17 items. A tutor that handles fractions well may fail completely on, say,
  proof-based geometry or essay feedback. None of the numbers transfer across
  subjects.
- The misconception catalog is small (5 misconceptions). Real fraction
  instruction must contend with many more. The harness will not surface a
  failure tied to a misconception it doesn't model.

## 3. Can the loop distinguish real learning from synthetic overfit?

**Partially, and that's the honest answer.**

- The `synthetic_overfit` counter-metric checks that transfer gain (on unseen
  items) tracks in-lesson gain. In our run transfer gain (+0.139) exceeded
  in-lesson gain (+0.091), which is genuine evidence against overfit *within
  this synthetic population*.
- But the transfer items are still authored by the same person who authored
  the instruction items and the personas. There is a shared-author bias: the
  whole closed world could be internally consistent and still wrong about real
  students. **The harness cannot detect overfit to its own worldview.** Only a
  human-representative held-out population can, and we don't have one.

## 4. What a human educator would need to validate these findings

1. **Confirm the misconception distractors are the ones real 7th-graders
   actually produce** (we cite the literature, but didn't run real students).
2. **Confirm V2's pedagogy is sound, not just metric-improving** — e.g., that
   capping hints at 1 doesn't abandon students who genuinely need more
   scaffolding. The `educator_agreement` counter-metric is a *proxy rubric*,
   explicitly labelled as needing human signoff.
3. **Validate the transfer items are truly novel** relative to instruction and
   not solvable by the same surface procedure.
4. **Sanity-check the one reported regression** (`anxious_learner /
   scaffolding_independence`): is V2 genuinely worse for anxious students, or
   is "independence = zero hints" the wrong proxy for them? We suspect the
   latter — for an anxious learner, *appropriate* scaffolding is not a failure
   — which is itself a limitation of the independence metric.

## 5. Known limitations of the evaluation method

- **`scaffolding_independence` conflates "needed no help" with "got no help."**
  An anxious learner who is correctly given supportive hints scores as
  *less independent*, penalising good pedagogy. This is why V2 shows a
  regression on that persona; the metric, not the tutor, is arguably at fault.
- **Misconception persistence excludes learners who started with none**, so the
  denominator varies by persona. This is correct (you can't persist what you
  never had) but means the metric is noisier for low-misconception personas.
- **Single session per learner.** No spacing, no forgetting curve, no
  re-test-after-delay. Retention is modelled only as an immediate discount on
  the learning gain, not as decay over time.
- **The tutor is rule-based.** Real LLM tutors fail in ways a finite policy
  cannot enumerate (hallucinated math, inconsistent persona, context-window
  drift). This harness tests the *documented* failure taxonomy, not the long
  tail of LLM-specific failures. The optional `[llm]` mode is the path to
  testing those, and is not yet exercised.

## 6. One-line honest summary

The harness credibly shows V2 fixes the documented failure modes of V1 on
synthetic fraction learners, with disciplined anti-gaming checks — but it
cannot, by itself, prove those gains would hold for real students, and it
correctly flags one place where its own metric is suspect.
