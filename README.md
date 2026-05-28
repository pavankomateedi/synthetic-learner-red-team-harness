# Synthetic Learner Red Team Harness

A red-team harness that stress-tests an AI fractions tutor with a population of
research-grounded synthetic students, exposes its educational failure modes,
runs one full recursive improvement cycle, and verifies the improvement isn't
benchmark gaming.

Built to the PRD (`PRD_Synthetic_Learner_Red_Team_Harness.md`). Every quality
gate runs **fully offline** — no API key needed — because every learner and
tutor is a deterministic, seeded rule-based agent. See
[docs/decision_log.md](docs/decision_log.md) for why.

## Headline result (n = 200 sessions per tutor)

| Dimension | Baseline V1 | Improved V2 | Direction |
|---|---|---|---|
| Learning gain (pre→post) | 0.068 | **0.159** | higher=better |
| Transfer score | 0.252 | **0.343** | higher=better |
| Misconception persistence | 1.000 | **0.360** | lower=better |
| Avoidance recovery rate | 0.055 | **0.863** | higher=better |
| Answer-giving rate | 0.820 | **0.000** | lower=better |
| Scaffolding independence | 0.101 | **0.165** | higher=better |
| Shallow compliance accepted | 1.000 | **0.000** | lower=better |

All five PRD §8.2 counter-metrics **pass**, including the critical anti-gaming
check: transfer gain (+0.139) actually exceeds in-lesson gain (+0.091).
One honest regression is reported (`anxious_learner/scaffolding_independence`) —
see [docs/limitations.md](docs/limitations.md).

## Quickstart

```powershell
pip install -e .[dev]
slh check                 # run the golden-set quality gate
slh compare --out docs    # full baseline -> improved loop, writes reports
slh run --tutor v1        # evaluate one tutor in isolation
pytest                    # full test suite + coverage gate (>=85%)
ruff check src tests
```

## Architecture

```
slh/
  curriculum.py   # research-grounded misconception catalog + problem bank
  personas.py     # 8 archetypes; each differs in >=3 measurable dimensions
  learner.py      # SyntheticLearner agent: seeded RNG + evolving memory model
  protocol.py     # Move / Action / Turn / ItemState shared types
  tutor.py        # TutorV1 (flawed baseline) + TutorV2 (improved policy)
  session.py      # multi-turn runner: pre-assess -> teach -> post-assess
  detectors.py    # avoidance / shallow-compliance / recovery detection
  evaluator.py    # 7 PRD-8.1 dimensions, aggregate + per-persona
  comparator.py   # before/after deltas, regression check, PRD-8.2 counter-metrics
  report.py       # failure-mode + comparison Markdown renderers
  goldenset.py    # the eval contract (passes via `slh check`)
  harness.py      # orchestrates the recursive improvement loop
  cli.py          # `slh` entry point
```

## Deliverables (PRD §12)

| # | Deliverable | File |
|---|---|---|
| 1 | Working prototype | this repo + `slh` CLI |
| 2 | Synthetic learner design doc | [docs/synthetic_learner_design.md](docs/synthetic_learner_design.md) |
| 3 | Tutor/curriculum documentation | [docs/tutor_and_curriculum.md](docs/tutor_and_curriculum.md) |
| 4 | Evaluation method | [docs/evaluation_method.md](docs/evaluation_method.md) |
| 5 | Baseline vs. improved report | [docs/baseline_vs_improved.md](docs/baseline_vs_improved.md) |
| 6 | Failure mode reports | [docs/failure_report_baseline.md](docs/failure_report_baseline.md), [docs/failure_report_improved.md](docs/failure_report_improved.md) |
| 7 | Recursive improvement description | [docs/recursive_improvement.md](docs/recursive_improvement.md) |
| 8 | Decision log | [docs/decision_log.md](docs/decision_log.md) |
| 9 | Research notes | [docs/research_notes.md](docs/research_notes.md) |
| 10 | Limitations memo | [docs/limitations.md](docs/limitations.md) |
| + | Golden set companion | [docs/golden_set.md](docs/golden_set.md) |
