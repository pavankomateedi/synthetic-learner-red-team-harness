# Synthetic Learner Design Doc

*Deliverable 2 / PRD §6.*

## Design principles

Each persona is a **frozen disposition** plus a **mutable learner state**. The
disposition is encoded as numeric dimensions so persona differentiation (PRD
6.3) is enforced by a test, not a paragraph:
`test_personas.py::test_persona_pairs_differ_in_at_least_three_dimensions`.

The synthetic learner is deliberately **rule-based and seeded**, not LLM-driven.
Three reasons (see `docs/decision_log.md` for the full case):
1. **Quality gates must be deterministic.** Property tests, golden sets, and
   regression checks can't depend on stochastic external services.
2. **Failure modes must be inspectable.** A red-team learner that's a black
   box is just a different black box. Rule-based agents let us *prove* a
   specific persona produces a specific misconception answer on a specific
   problem (`test_learner.py::test_generate_answer_uses_held_misconception`).
3. **No API key required** for the harness or its quality gates.

## The five required facets (PRD 6.1)

| Facet | How it's encoded |
|---|---|
| Knowledge State | `prior_mastery: dict[concept, float]` plus a set of `misconceptions` (IDs into the curriculum catalog). |
| Motivation Profile | `curiosity`, `performance_orientation`, `social_motivation`, `avoidance_tendency` ∈ [0, 1]. |
| Behavioral Patterns | `effort`, `persistence`, `hint_solicitation`, `feigns_understanding`, `topic_switch`, `guess_confidence`, `adversarial`. |
| Memory Model | `retention` (how much learning sticks), `consolidation_noise` (chance of mis-consolidating a new misconception), `transfer_penalty` (extra mastery loss on novel items). |
| Avoidance Signature | A human-readable label plus the combination of behavioral dims that dominate. |

The per-turn decision policy reads these and the current `LearnerState`:

```
respond(move) ->
  if move is COMPREHENSION_CHECK:  feign or honestly ask
  if move is PROBE:                produce a sound or unsound EXPLAIN (mastery-gated)
  if move is GIVE_ANSWER:          claim understanding (genuine iff really mastered)
  otherwise (attempt-class):       gate adversarial -> give-up -> topic-switch
                                       -> ask-answer/hint -> attempt
```

Mastery updates only at item resolution, weighted by the tutor's
`resolution_quality` and the learner's `retention`. Misconceptions clear with
probability ∝ quality only when the tutor explicitly remediated.

## The eight archetypes

All eight rows below map onto the PRD 6.2 reference table. Numeric dimensions
are tuned so each persona triggers a specific tutor weakness on the chosen
domain.

| ID | Archetype | Educational risk |
|---|---|---|
| `shortcut_seeker` | Shortcut Seeker | Tutor gives answers without teaching. |
| `confident_guesser` | Confident Guesser | False positive on assessment. |
| `anxious_learner` | Anxious Learner | Tutor fails to scaffold and emotionally recover. |
| `memorizer` | Memorizer | Curriculum confuses recall with learning. |
| `distractible_student` | Distractible Student | Tutor fails to redirect without losing rapport. |
| `i_get_it` | "I Get It" Student | Tutor fails to probe for real understanding. |
| `over_hinter` | Over-Hinter | Hints erode independence. |
| `adversarial_learner` | Adversarial Learner | Tutor susceptible to prompt injection. |

Research grounding for each persona is stored on the persona itself
(`research_grounding` field) and summarised in `docs/research_notes.md`.

## Differentiation (PRD 6.3)

Every pair of personas differs in ≥ 3 measurable dimensions. The check counts
numeric dimensions whose values differ by > 0.15, plus a point each for
distinct misconception sets and distinct mastery profiles. Enforced by
`test_personas.py::test_persona_pairs_differ_in_at_least_three_dimensions`.

## Memory model details

- `resolve(problem, quality, remediate, rng)` runs at item resolution.
- Mastery delta = `quality * retention * 0.4`, clamped to [0, 1].
- If `remediate=True`, each held misconception relevant to the problem clears
  with probability `quality`.
- With probability `consolidation_noise * (1 - quality)`, the learner adds a
  new misconception associated with that problem — modelling *mis-*
  consolidation. Anxious and distractible learners have elevated noise.

## What the design intentionally does *not* model

See `docs/limitations.md`. Headlines: no natural-language production, no
emotional state continuity across sessions, no peer effects, no diurnal
attention.
