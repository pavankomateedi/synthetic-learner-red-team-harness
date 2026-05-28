"""Evaluator + comparator tests, including counter-metric failure paths."""

from slh.comparator import DIMENSIONS, compare
from slh.evaluator import DimensionScores, TutorMetrics, evaluate
from slh.harness import run_population


def _metrics(name, **scores):
    transfer_gain = scores.pop("_transfer_gain", 0.0)
    base = dict.fromkeys(DIMENSIONS, 0.0)
    base.update(scores)
    return TutorMetrics(tutor_name=name, overall=DimensionScores(**base),
                        transfer_gain=transfer_gain)


def test_evaluate_produces_all_dimensions_in_range():
    metrics = evaluate(run_population("v1", n_seeds=4))
    d = metrics.overall.as_dict()
    assert set(d) == set(DIMENSIONS)
    assert metrics.per_persona  # per-persona breakdown present
    for v in d.values():
        assert -1.0 <= v <= 1.0


def test_evaluate_empty_raises():
    import pytest
    with pytest.raises(ValueError):
        evaluate([])


def test_compare_detects_improvement():
    base = _metrics("v1", learning_gain=0.05, transfer_score=0.30, answer_giving_rate=0.8)
    imp = _metrics("v2", learning_gain=0.20, transfer_score=0.45, answer_giving_rate=0.0)
    rep = compare(base, imp)
    assert rep.delta("learning_gain").improved_flag
    assert rep.delta("answer_giving_rate").improved_flag  # lower is better
    assert not rep.regressions_in_primary
    assert rep.overall_improved


def test_compare_flags_regression():
    base = _metrics("v1", transfer_score=0.50)
    imp = _metrics("v2", transfer_score=0.30, learning_gain=0.20)
    rep = compare(base, imp)
    assert "transfer_score" in rep.regressions
    assert rep.regressions_in_primary


def test_counter_metric_can_fail_on_gaming():
    # Scores up but transfer collapses -> benchmark gaming.
    base = _metrics("v1", learning_gain=0.05, transfer_score=0.50)
    imp = _metrics("v2", learning_gain=0.25, transfer_score=0.20)
    rep = compare(base, imp)
    cm = next(m for m in rep.counter_metrics if m.name == "transfer_tracks_score")
    assert cm.verdict == "fail"


def test_counter_metric_passes_when_transfer_tracks():
    base = _metrics("v1", learning_gain=0.05, transfer_score=0.30)
    imp = _metrics("v2", learning_gain=0.20, transfer_score=0.45, _transfer_gain=0.15)
    rep = compare(base, imp)
    cm = next(m for m in rep.counter_metrics if m.name == "transfer_tracks_score")
    assert cm.verdict == "pass"
    assert len(rep.counter_metrics) == 5  # all five PRD 8.2 counter-metrics present
