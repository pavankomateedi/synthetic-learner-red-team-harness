# Research Notes

*Deliverable 9 / PRD §11.*

## What was learned and how it changed the design

### Misconception literature → the diagnostic distractors

| Persona / misconception | Source | What the design borrowed |
|---|---|---|
| `add_across` (1/2 + 1/3 → 2/5) | Ashlock, R. (2010). *Error Patterns in Computation.* | Distractors for addition problems map to specific wrong sums; `learner._generate_answer` emits these deterministically when the misconception is held. |
| `bigger_denom_bigger` (1/8 > 1/4) | Ni, Y. & Zhou, Y. (2005). *Teaching and learning fraction and rational numbers: the origins and implications of whole number bias.* | The `confident_guesser` persona holds this misconception; comparison problems carry the wrong-order distractor. |
| `gap_thinking` (3/4 = 5/6 because both 1 short) | Stafylidou, S. & Vosniadou, S. (2004). *The development of students' understanding of the numerical value of fractions.* | Transfer comparison item `cmp_t1` carries the gap-thinking distractor (`=`), distinct from whole-number-bias distractor (`>`). |
| `same_digits_only` (cannot see 1/2 = 2/4) | NCTM (2014). *Principles to Actions.* | Equivalence problems carry the "keep the original numerator" distractor. |
| `add_num_keep_denom` (1/2 + 1/3 = 2/3) | Ashlock (2010). | Distinct from `add_across`; held by `anxious_learner` to vary the population's misconception mix. |

### Tutoring best practices → the V2 policy

| Behavior | Source | V2 mechanism |
|---|---|---|
| Productive struggle / withholding answers | NCTM (2014); Kapur, M. (2008). *Productive failure.* | `MAX_HINTS = 1`; no `GIVE_ANSWER` path. |
| Scaffolding fade & "assistance dilemma" | Koedinger, K. R., & Aleven, V. (2007). *Exploring the assistance dilemma in experiments with cognitive tutors.* | Hint cap; further requests escalate to a probe, not a hint. |
| Diagnose-then-remediate | NCTM (2014); Bray, W. S. (2011). *A collective case study of the influence of teachers' beliefs and knowledge on error-handling practices during class discussion of mathematics.* | Wrong answers matching a misconception trigger `PROBE` + targeted remediation hint; `item.remediated=True`. |
| Probe-for-justification vs. "do you understand?" | Rozenblit, L. & Keil, F. (2002). *The misunderstood limits of folk science: an illusion of explanatory depth.* | `COMPREHENSION_CHECK` replaced with `PROBE` in V2; advance only on sound `EXPLAIN`. |
| Redirect off-task without coercion | Koedinger & Aleven (2007); engagement literature. | `SWITCH_TOPIC → REDIRECT`, not answer-giving. |

### Assessment design → pre/post + transfer

| Principle | Source | Realization |
|---|---|---|
| Transfer vs. recall distinction | Bransford, J. D., Brown, A. L., & Cocking, R. R. (eds., 2000). *How People Learn.* | Separate `kind="transfer"` items, never seen during instruction. |
| Pre-post measurement | Hake, R. R. (1998). *Interactive-engagement versus traditional methods: a six-thousand-student survey...* | Pure pre-assessment (no learning applied) and post-assessment baked into the session runner. |
| Misconception persistence as a metric | Smith, J. P. III, diSessa, A. A., & Roschelle, J. (1993). *Misconceptions reconceived.* | Tracked per-learner, reported as a population dimension. |

### Persona research → the eight archetypes

| Persona | Source(s) |
|---|---|
| `shortcut_seeker` | Baker, R. S., Corbett, A. T., Koedinger, K. R., & Wagner, A. Z. (2004). *Off-task behavior in the cognitive tutor classroom: when students "game the system."* |
| `confident_guesser` | Dunning, D. et al. (2003); Bjork on illusions of competence. |
| `anxious_learner` | Ashcraft, M. H. (2002). *Math anxiety: personal, educational, and cognitive consequences.* |
| `memorizer` | Skemp, R. R. (1976). *Relational understanding and instrumental understanding.* |
| `distractible_student` | Karweit & Slavin engagement literature. |
| `i_get_it` | Rozenblit & Keil (2002), illusion of explanatory depth. |
| `over_hinter` | Koedinger & Aleven (2007), assistance dilemma. |
| `adversarial_learner` | Recent LLM-tutor prompt-injection reports (industry sources, 2023–2025). |

### Cognitive-science concepts the harness uses

- **Desirable difficulties** (Bjork, 1994) — transfer items are intentionally
  harder and unseen, because making them easy would hide the transfer gap.
- **Spacing / interleaving** — not modelled in v1 (single session per
  learner); flagged in `docs/limitations.md`.
- **Retrieval practice** — V2's `PROBE` after correct answer is effectively a
  retrieval-with-justification check, not a re-presentation.

## What research did *not* change

Two things I considered modelling and chose not to:
- **Emotional state continuity across sessions** — would require multi-session
  memory beyond v1's scope.
- **Peer / group dynamics** — out of scope per PRD §4.2.

Both are listed in `docs/limitations.md` as known gaps.
