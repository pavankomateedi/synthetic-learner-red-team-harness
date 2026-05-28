# Tutor & Curriculum Documentation

*Deliverable 3 / PRD §7.*

## Subject domain

**7th-grade rational-number (fraction) arithmetic** — equivalence, comparison,
addition with like and unlike denominators. Chosen because fraction reasoning
has the deepest documented-misconception literature in mathematics education
(Siegler et al., 2011; Ashlock, 2010; Ni & Zhou, 2005), which makes every
persona's wrong answer *diagnostic* rather than random noise.

## Item bank

| Concept | Instruction | Assessment | Transfer |
|---|---|---|---|
| equivalence | 2 | 1 | 2 |
| comparison | 2 | 1 | 2 |
| addition_like | 2 | 1 | 0 |
| addition_unlike | 1 | 1 | 2 |

Each `Problem` carries a `misconception_answers` map — the specific wrong
answer a learner holding that misconception will produce. This is what lets the
evaluator *diagnose* an error, not just grade it.

Transfer items use **unseen numbers and unseen direction of equivalence** so
correctness on them genuinely measures transfer rather than memorisation. The
intentional weakness baked into the curriculum is that `addition_unlike` is
under-instructed relative to its difficulty — exposing a sequencing failure
the red-team harness can surface.

## Tutor interaction protocol

Tutor and learner alternate via `Move` / `Action` types (`slh/protocol.py`):

| Tutor move | Learner action |
|---|---|
| `PRESENT_PROBLEM`, `GIVE_HINT`, `REDIRECT`, `ENCOURAGE` | `ANSWER`, `ASK_HINT`, `ASK_ANSWER`, `SWITCH_TOPIC`, `GIVE_UP`, `BYPASS_ATTEMPT` |
| `COMPREHENSION_CHECK` | `CLAIM_UNDERSTANDING` (possibly feigned) |
| `PROBE` | `EXPLAIN` (sound iff genuine mastery) |
| `GIVE_ANSWER` | `CLAIM_UNDERSTANDING` |
| `REFUSE_BYPASS` | no immediate action |
| `ADVANCE` | item resolved |

The session runner caps each item at `PER_ITEM_TURN_BUDGET = 6` turns. The
tutor exposes `resolution_quality(item) → [0, 1]`, which the runner feeds into
`learner.resolve()` so learning happens uniformly whether the item ended by
advancement or by budget exhaustion.

## TutorV1 — Baseline (intentionally flawed)

V1 embodies the PRD §13.1 failure modes so the harness has something real to
expose:

| Failure (PRD 13.1) | How V1 realizes it |
|---|---|
| Answer-Giving | Hands over the answer on any `ASK_ANSWER` or `BYPASS_ATTEMPT`. |
| Hint Cascade | After two hints, just gives the answer. |
| Off-Task Tolerance | Does not emit `REDIRECT` on `SWITCH_TOPIC`. |
| Rapport-Preservation Bias | On `GIVE_UP`, hands over the answer to move on. |
| Shallow Compliance Acceptance | Uses `COMPREHENSION_CHECK`, advances on any `CLAIM_UNDERSTANDING`. |

V1's `resolution_quality` is low (0.10–0.45) and `remediated` is never set —
so misconceptions held at the start survive instruction. Hence the headline
result `misconception_persistence = 1.000` for V1.

## TutorV2 — Improved (proposed by the recursive loop)

V2 was proposed after reading V1's failure report:

| Failure addressed | V2 mechanism |
|---|---|
| Answer-Giving | `MAX_HINTS = 1`; never emits `GIVE_ANSWER`. |
| Hint Cascade | Hint cap; further hint requests are converted to a `PROBE` requiring an attempt. |
| Off-Task Tolerance | `SWITCH_TOPIC` → explicit `REDIRECT`. |
| Rapport-Preservation Bias | `GIVE_UP` → `ENCOURAGE`, never the answer. |
| Shallow Compliance Acceptance | `COMPREHENSION_CHECK` replaced with `PROBE`; advances only on a sound `EXPLAIN`. |
| Misconception Survival | Wrong answers diagnosed as misconceptions trigger a probe + targeted remediation; `remediated=True` so `learner.resolve()` clears the misconception. |
| Bypass Susceptibility | `BYPASS_ATTEMPT` → `REFUSE_BYPASS`. |

V2's `resolution_quality` is higher when verified (0.85) or correct (0.6), and
0.35 even when unresolved — because productive struggle still teaches
something, unlike answer-giving.

## Why two rule-based policies rather than a single LLM tutor

The PRD permits "LLM-powered agents", "rule-based learner simulations", or
"hand-authored learner scripts" (§10.2) and says "quality of reasoning matters
more than scale." Two reasons we chose rule-based policies:

1. **The failure modes must be controllable.** A baseline tutor with
   *unpredictable* answer-giving makes the improvement loop unfalsifiable. V1
   is deliberately and consistently bad in the documented ways, so when V2
   fixes them we know exactly what changed.
2. **Reproducibility is the gate.** A seeded rule-based system gives identical
   numbers run to run, which is what makes the golden set meaningful.

An optional Claude-backed mode could replace either side as a future extension
(see the `[llm]` extras in `pyproject.toml`); the current core does not depend
on it.
