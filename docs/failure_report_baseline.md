# Failure Mode Report — `baseline_v1`

Population: 200 sessions (8 personas).

## Overall failing dimensions

| Dimension | Value | Failure mode (PRD 13) | Recommendation |
|---|---|---|---|
| `transfer_score` | 0.252 (higher=better) | Curriculum: Transfer Gap (13.2) | Add varied practice and require justification on novel items. |
| `misconception_persistence` | 1.000 (lower=better) | Curriculum: Misconception Survival (13.2) | Diagnose the specific error and remediate it directly. |
| `avoidance_recovery_rate` | 0.055 (higher=better) | Tutor: Off-Task Tolerance (13.1) | Add explicit redirect / refuse / re-engage moves. |
| `answer_giving_rate` | 0.820 (lower=better) | Tutor: Answer-Giving + Hint Cascade (13.1) | Withhold answers; cap hints; require an attempt. |
| `scaffolding_independence` | 0.101 (higher=better) | Curriculum: Scaffolding Trap (13.2) | Fade scaffolding; cap hints per item. |
| `shallow_compliance_rate` | 1.000 (lower=better) | Tutor: Shallow Compliance Acceptance (13.1) | Replace 'do you understand?' with a justification probe. |

## Failure clusters (persona × dimension)

| Persona | Failing dimensions |
|---|---|
| shortcut_seeker | `transfer_score`, `misconception_persistence`, `avoidance_recovery_rate`, `answer_giving_rate`, `scaffolding_independence`, `shallow_compliance_rate` |
| confident_guesser | `learning_gain`, `transfer_score`, `misconception_persistence`, `avoidance_recovery_rate`, `answer_giving_rate`, `scaffolding_independence`, `shallow_compliance_rate` |
| anxious_learner | `learning_gain`, `transfer_score`, `misconception_persistence`, `avoidance_recovery_rate`, `answer_giving_rate`, `scaffolding_independence`, `shallow_compliance_rate` |
| memorizer | `transfer_score`, `avoidance_recovery_rate`, `answer_giving_rate` |
| distractible_student | `learning_gain`, `avoidance_recovery_rate`, `answer_giving_rate`, `scaffolding_independence`, `shallow_compliance_rate` |
| i_get_it | `transfer_score`, `misconception_persistence`, `avoidance_recovery_rate`, `answer_giving_rate`, `scaffolding_independence`, `shallow_compliance_rate` |
| over_hinter | `transfer_score`, `avoidance_recovery_rate`, `answer_giving_rate`, `scaffolding_independence`, `shallow_compliance_rate` |
| adversarial_learner | `learning_gain`, `avoidance_recovery_rate`, `answer_giving_rate`, `scaffolding_independence`, `shallow_compliance_rate` |
