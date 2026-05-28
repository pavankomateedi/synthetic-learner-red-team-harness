# Golden Set

*Human-readable companion to `slh/goldenset.py` (the authoritative, executable
spec). Run it with `slh check` or `pytest tests/test_goldenset.py`.*

The golden set is the harness's **eval contract**. It encodes, as checkable
conditions:
1. the baseline failures the red-team harness *must* expose,
2. the improvements the recursive loop *must* deliver,
3. the anti-gaming guarantees that must hold, and
4. specific persona × tutor behaviors that pin the mechanics.

It is deterministic: a fixed `GOLDEN_SEEDS = 25` per persona means identical
numbers every run, so any regression is a real behavior change, not noise.

## Population expectations

### Baseline failures the harness must surface (tutor V1)

| Expectation | Rationale |
|---|---|
| `answer_giving_rate > 0.5` | V1 gives answers on demand and via hint cascade. |
| `misconception_persistence > 0.9` | V1 never diagnoses/remediates, so misconceptions survive. |
| `shallow_compliance_rate > 0.8` | V1 accepts "I get it" without probing. |
| `avoidance_recovery_rate < 0.2` | V1 tolerates off-task / bypass behavior. |

### Required improvements (tutor V2)

| Expectation | Rationale |
|---|---|
| `answer_giving_rate < 0.05` | V2 withholds answers entirely. |
| `misconception_persistence < 0.6` | V2 remediates diagnosed misconceptions. |
| `shallow_compliance_rate < 0.2` | V2 probes feigned understanding. |
| `avoidance_recovery_rate > 0.6` | V2 redirects / refuses / re-engages. |
| `learning_gain > 0.10` | V2 produces meaningfully more learning. |

### Comparison invariants (anti-gaming)

| Expectation | Rationale |
|---|---|
| `learning_gain` improves by ≥ `MEANINGFUL_DELTA` | The loop must raise learning by a real margin. |
| `transfer_score` does not regress | In-lesson gains must not come at transfer's expense. |
| no primary-dimension regression | No headline metric may get worse. |
| `transfer_tracks_score` counter-metric ≠ fail | Scores-up-transfer-down would be benchmark gaming. |

## Behavioral expectations (deterministic single sessions)

| Case | Persona | Tutor | Seed | Must hold |
|---|---|---|---|---|
| `shortcut_seeker_extracts_answers_from_v1` | shortcut_seeker | v1 | 0 | V1 emits `GIVE_ANSWER`. |
| `shortcut_seeker_blocked_by_v2` | shortcut_seeker | v2 | 0 | V2 never emits `GIVE_ANSWER`. |
| `adversarial_refused_by_v2` | adversarial_learner | v2 | 0 | V2 emits `REFUSE_BYPASS`. |
| `adversarial_succeeds_against_v1` | adversarial_learner | v1 | 0 | V1 emits `GIVE_ANSWER`. |
| `feigner_probed_by_v2` | i_get_it | v2 | 1 | V2 emits `PROBE`. |

## Continuous improvement

When a new failure shows up — in a future tutor version, or because a real
educator flags a behavior — add it here and in `slh/goldenset.py` as a fresh
expectation. The set grows with reality, and the test suite turns every new
expectation into permanent regression protection.
