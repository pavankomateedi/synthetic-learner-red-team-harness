# Decision Log

*Deliverable 8 / chronological record of design decisions and their rationale.*

Each entry records the *call*, the *alternatives considered*, and *why* —
because the PRD evaluates whether the system avoids self-deception and
acknowledges trade-offs.

---

## D1 — Subject domain: 7th-grade fractions

**Alternatives considered.** SAT reading, AP biology, algebra, US history.

**Why fractions.** The PRD requires persona behaviors "grounded in documented
real student behavior" (§6.3). Fractions have the densest documented
misconception literature of any topic in K-12 math (Siegler, Ashlock, Ni &
Zhou). Every persona's wrong answer can be tied to a specific, cited error
pattern, which is what makes the synthetic learners credible critics.

## D2 — Rule-based agents, not LLM-driven

**Alternatives considered.** Claude-backed learners + Claude-backed tutor;
hybrid (LLM tutor, rule-based learners); fully rule-based.

**Why rule-based.** Three reasons:
1. **Quality gates must be deterministic.** Golden sets and regression checks
   can't depend on stochastic external services. The PRD explicitly permits
   rule-based simulations (§10.2) and says "quality of reasoning matters more
   than scale."
2. **The improvement loop must be falsifiable.** A baseline tutor with
   stochastic answer-giving makes "did V2 fix it?" unanswerable. V1 is
   *consistently* bad in documented ways, so V2's fixes can be attributed.
3. **No API key required**, which means the harness ships and runs anywhere,
   including CI.

An optional LLM mode is in scope as future work (`pyproject.toml [llm]`
extra). It would replace either side without disturbing the eval contract.

## D3 — The learner's answer is mathematically graded, not string-matched

**Trade-off.** Value-based grading lets `4/8` count as correct for `1/2`,
which is pedagogically right. But it broke the original `eq_t2` ("reduce 6/8
to lowest terms" — `6/8` is value-equal to `3/4`, so the misconception
distractor was indistinguishable from the right answer).

**Resolution.** Replaced `eq_t2` with a scale-up transfer item where the
correct and misconception answers differ in value. Documented here because it
demonstrates the test suite catching a real design bug before it could ship.

## D4 — Resolution quality as a single scalar, not a vector

**Alternatives considered.** Per-dimension quality scores (e.g. independence
quality vs. understanding quality).

**Why scalar.** The learner's `resolve()` only needs a single weight on its
mastery delta and misconception clearance probability. Adding more knobs
would not change behavior in any measurable way given the current persona
parameter ranges. Recorded so future me knows not to redesign this.

## D5 — Counter-metrics live in the comparator, not the evaluator

**Why.** Counter-metrics are inherently *relational* — they ask "*if* X
changed, did Y change too?" That makes them ill-defined for a single tutor.
Putting them in `comparator.py` keeps `evaluator.py` clean and makes the
comparator the single source of "real improvement vs. gaming?" verdicts.

## D6 — Per-persona regression check, not just overall

**Why.** Aggregate metrics can hide that a fix made one persona worse while
helping others. The harness flags this and surfaced exactly one such case —
`anxious_learner / scaffolding_independence` — which is reported honestly in
`docs/baseline_vs_improved.md`. The PRD calls this out as a counter-metric
discipline requirement (§14.6).

## D7 — Golden set lives in code (`slh/goldenset.py`), not prose

**Why.** The PRD's continuous-improvement requirement only works if every
future change can be re-checked against the same contract. Code is
re-runnable; prose decays. `docs/golden_set.md` is the human-readable
companion, but the authoritative spec is the data structure imported by the
tests.

## D8 — Tracking `item.remediated` on the tutor, not as a separate event log

**Why.** The PRD distinguishes "tutor remediated a misconception" from
"tutor gave a hint." Modelling that as one flag set by V2 when it issues a
remediation hint (after a misconception-flagged probe) keeps the learner's
`resolve()` interface uniform between V1 and V2 — V1 never sets it, V2 does.
Cleaner than threading move-type-specific flags through the resolver.

## D9 — Per-item turn budget of 6

**Why.** Long enough to allow a hint cascade in V1 (`HINT, HINT, GIVE_ANSWER`)
and a probe-remediate-probe loop in V2; short enough that adversarial loops
don't dominate session cost. Documented so a future change knows what's
calibrated.

## D10 — Eight personas, not the minimum six

**Why.** The PRD requires ≥6 (§6.2). I added two more — `i_get_it` and
`over_hinter` — because shallow-compliance and scaffolding-trap failures are
specifically called out in the failure taxonomy (§13) but would not be
exercised by the other six. Eight maps better onto the failure taxonomy
without bloating the test surface.
