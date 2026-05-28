# Evaluation Method

*Deliverable 4 / PRD §8.*

## Primary metrics (PRD §8.1)

All seven required dimensions are computed by `slh.evaluator.evaluate()`,
both aggregated across the population and broken down per persona. Direction
("higher" or "lower" is better) is recorded in `slh.evaluator.DIMENSIONS` so the
comparator can do regression checks generically.

| Dimension | What it measures | How it's computed | Direction |
|---|---|---|---|
| `learning_gain` | Pre/post knowledge state change | mean(post-assessment score − pre-assessment score) over assessment items | higher better |
| `transfer_score` | Performance on novel items not seen during instruction | mean fraction correct on transfer items, post-instruction | higher better |
| `misconception_persistence` | Specific misconceptions surviving instruction | fraction of initially-held misconceptions still held post (excluding learners with none) | lower better |
| `avoidance_recovery_rate` | Tutor's success at redirecting avoidance | `recovered / recoverable` events from the detector | higher better |
| `answer_giving_rate` | Frequency the tutor gives answers | `count(GIVE_ANSWER) / lesson_items` | lower better |
| `scaffolding_independence` | Whether hint reliance declines | fraction of items resolved with zero hints | higher better |
| `shallow_compliance_rate` | "I get it" accepted without verification | feigned claims not immediately followed by a `PROBE`, divided by total feigned claims | lower better |

## Counter-metrics (PRD §8.2)

Computed by `slh.comparator.compare()`. Each yields an explicit
**pass / warn / fail** verdict with the numbers behind it. They can — by
design — return WARN or FAIL, so the system cannot only ever flatter itself.

| Counter-metric | Question | Failure trigger |
|---|---|---|
| `transfer_tracks_score` | If scores improve, did transfer also improve? | Scores up but transfer down beyond `REGRESSION_EPS`. |
| `hints_vs_independence` | If the tutor gives more hints, did independence decline? | Hint usage up AND independence down. |
| `synthetic_overfit` | If synthetic learners perform better, did the system overfit to them? | In-lesson gain > `MEANINGFUL_DELTA` but transfer gain ≤ `REGRESSION_EPS`. |
| `educator_agreement` | Would a human educator agree? | Proxy rubric — pedagogically sound iff answer-giving down, misconception persistence down, recovery up. **Proxy only; needs human validation.** |
| `agency_preserved` | If off-topic behavior is redirected, is agency/rapport preserved? | Recovery up but answer-giving also up (coerced redirection). |

## Thresholds

| Constant | Value | Used for |
|---|---|---|
| `MEANINGFUL_DELTA` | 0.05 | Below this, a per-dimension change is treated as noise rather than improvement. |
| `REGRESSION_EPS` | 0.02 | A wrong-direction move beyond this triggers a regression flag (overall or per persona). |

The "failure" thresholds for marking a tutor as failing on a given dimension
live in `slh.report.FAILURE_THRESHOLDS`:

| Dimension | Failing if |
|---|---|
| `learning_gain` | < 0.05 |
| `transfer_score` | < 0.40 |
| `misconception_persistence` | > 0.50 |
| `avoidance_recovery_rate` | < 0.50 |
| `answer_giving_rate` | > 0.30 |
| `scaffolding_independence` | < 0.40 |
| `shallow_compliance_rate` | > 0.30 |

## Human educator agreement check

The `educator_agreement` counter-metric is a **proxy rubric**, not a real
human signoff. It passes when:
- answer-giving rate did not regress,
- misconception persistence did not regress,
- avoidance recovery rate did not regress.

These were chosen because they encode "the tutor stopped doing the things
educators flag as problematic" rather than "scores went up." The PRD requires
explicit human review; this proxy is what the harness can compute
automatically. A real educator review is listed as an outstanding requirement
in `docs/limitations.md`.

## How to re-run

```powershell
slh check          # the golden set + behavior expectations (the gate)
slh compare        # full loop + generate reports under docs/
pytest             # all tests, fails if coverage < 85%
```
