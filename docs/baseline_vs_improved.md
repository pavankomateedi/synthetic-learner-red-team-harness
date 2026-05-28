# Baseline vs. Improved — `baseline_v1` → `improved_v2`

## Primary + supporting metrics

| Dimension | Baseline | Improved | Δ (better-oriented) | Status |
|---|---|---|---|---|
| `learning_gain` | 0.068 | 0.159 | +0.091 | 🟢 improved |
| `transfer_score` | 0.252 | 0.343 | +0.091 | 🟢 improved |
| `misconception_persistence` | 1.000 | 0.360 | +0.640 | 🟢 improved |
| `avoidance_recovery_rate` | 0.055 | 0.863 | +0.808 | 🟢 improved |
| `answer_giving_rate` | 0.820 | 0.000 | +0.820 | 🟢 improved |
| `scaffolding_independence` | 0.101 | 0.165 | +0.063 | 🟢 improved |
| `shallow_compliance_rate` | 1.000 | 0.000 | +1.000 | 🟢 improved |

## Regression check

Regressions detected:
- `anxious_learner/scaffolding_independence`

## Counter-metrics (anti-gaming, PRD 8.2)

| Counter-metric | Question | Verdict | Detail |
|---|---|---|---|
| `transfer_tracks_score` | If scores improve, did transfer also improve? | ✅ pass | Scores up and transfer up (+0.091). |
| `hints_vs_independence` | If the tutor gives more hints, did independence decline? | ✅ pass | Hint usage delta -1.71/item; independence delta +0.063. |
| `synthetic_overfit` | If synthetic learners perform better, did the system overfit? | ✅ pass | Transfer gain +0.139 vs in-lesson gain +0.091. |
| `educator_agreement` | If the evaluator reports improvement, would a human educator agree? | ✅ pass | Changes are pedagogically sound by proxy rubric (less answer-giving, fewer surviving misconceptions, better recovery). PROXY ONLY -- requires human educator sign-off. |
| `agency_preserved` | If off-topic behavior is redirected, is agency/rapport preserved? | ✅ pass | Redirection improved without resorting to answer-giving (rapport-preserving recovery). |

## Interpretation

**Verdict: real improvement.** 7 dimension(s) improved meaningfully; 1 regression(s).
