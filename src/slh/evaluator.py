"""Outcome evaluator (PRD section 8.1).

Turns a population of :class:`SessionResult` into the seven required evaluation
dimensions, both aggregated and broken down per persona (for the failure-cluster
report). Counter-metrics (8.2) live in :mod:`slh.comparator` because they are
inherently comparative.

Metric direction is recorded in :data:`DIMENSIONS` (+1 = higher is better,
-1 = lower is better) so the comparator can do regression checks generically.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .curriculum import problems_for
from .detectors import detect
from .protocol import MoveType
from .session import SessionResult

# Direction of "better" for each dimension.
DIMENSIONS: dict[str, int] = {
    "learning_gain": +1,
    "transfer_score": +1,
    "misconception_persistence": -1,
    "avoidance_recovery_rate": +1,
    "answer_giving_rate": -1,
    "scaffolding_independence": +1,
    "shallow_compliance_rate": -1,
}

_ASSESSMENT_IDS = [p.id for p in problems_for("assessment")]
_TRANSFER_IDS = [p.id for p in problems_for("transfer")]


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


@dataclass
class DimensionScores:
    learning_gain: float = 0.0
    transfer_score: float = 0.0
    misconception_persistence: float = 0.0
    avoidance_recovery_rate: float = 0.0
    answer_giving_rate: float = 0.0
    scaffolding_independence: float = 0.0
    shallow_compliance_rate: float = 0.0

    def as_dict(self) -> dict[str, float]:
        return {k: getattr(self, k) for k in DIMENSIONS}


@dataclass
class TutorMetrics:
    tutor_name: str
    overall: DimensionScores
    per_persona: dict[str, DimensionScores] = field(default_factory=dict)
    # Supporting raw numbers for counter-metrics / transparency.
    pre_assessment_score: float = 0.0
    post_assessment_score: float = 0.0
    pre_transfer_score: float = 0.0
    transfer_gain: float = 0.0
    mean_hints_first_half: float = 0.0
    mean_hints_second_half: float = 0.0
    n_sessions: int = 0


# --- per-session derived quantities ---------------------------------------


def _score(d: dict[str, bool], ids: list[str] | None = None) -> float:
    items = [d[i] for i in (ids or d.keys()) if i in d]
    return _mean([1.0 if v else 0.0 for v in items])


def _session_learning_gain(r: SessionResult) -> float:
    return _score(r.post_assessment, _ASSESSMENT_IDS) - _score(r.pre_assessment, _ASSESSMENT_IDS)


def _session_transfer(r: SessionResult) -> float:
    return _score(r.post_transfer, _TRANSFER_IDS)


def _session_misconception_persistence(r: SessionResult) -> float | None:
    if not r.initial_misconceptions:
        return None  # nothing could persist; excluded from the mean
    survived = r.initial_misconceptions & r.final_misconceptions
    return len(survived) / len(r.initial_misconceptions)


def _session_answer_giving_rate(r: SessionResult) -> float:
    n_items = len(r.items) or 1
    given = len(r.transcript.moves_of(MoveType.GIVE_ANSWER))
    return given / n_items


def _session_independence(r: SessionResult) -> float:
    if not r.items:
        return 1.0
    zero_hint = sum(1 for it in r.items if it.hints_given == 0)
    return zero_hint / len(r.items)


def _session_shallow_rate(r: SessionResult) -> float | None:
    f = detect(r.transcript)
    if f.feigned_understanding == 0:
        return None
    return f.shallow_accepted / f.feigned_understanding


def _hint_halves(r: SessionResult) -> tuple[float, float]:
    n = len(r.items)
    if n == 0:
        return 0.0, 0.0
    mid = n // 2 or 1
    first = _mean([float(it.hints_given) for it in r.items[:mid]])
    second = _mean([float(it.hints_given) for it in r.items[mid:]]) if r.items[mid:] else first
    return first, second


def _dimension_scores(results: list[SessionResult]) -> DimensionScores:
    persistences = [p for r in results if (p := _session_misconception_persistence(r)) is not None]
    shallow = [s for r in results if (s := _session_shallow_rate(r)) is not None]
    recoveries = [detect(r.transcript).recovery_rate for r in results]
    return DimensionScores(
        learning_gain=_mean([_session_learning_gain(r) for r in results]),
        transfer_score=_mean([_session_transfer(r) for r in results]),
        misconception_persistence=_mean(persistences),
        avoidance_recovery_rate=_mean(recoveries),
        answer_giving_rate=_mean([_session_answer_giving_rate(r) for r in results]),
        scaffolding_independence=_mean([_session_independence(r) for r in results]),
        shallow_compliance_rate=_mean(shallow),
    )


def evaluate(results: list[SessionResult]) -> TutorMetrics:
    """Aggregate a population of session results into tutor-level metrics."""
    if not results:
        raise ValueError("no session results to evaluate")
    tutor_name = results[0].tutor_name

    per_persona: dict[str, DimensionScores] = {}
    by_persona: dict[str, list[SessionResult]] = {}
    for r in results:
        by_persona.setdefault(r.learner_id, []).append(r)
    for pid, rs in by_persona.items():
        per_persona[pid] = _dimension_scores(rs)

    halves = [_hint_halves(r) for r in results]
    return TutorMetrics(
        tutor_name=tutor_name,
        overall=_dimension_scores(results),
        per_persona=per_persona,
        pre_assessment_score=_mean([_score(r.pre_assessment, _ASSESSMENT_IDS) for r in results]),
        post_assessment_score=_mean([_score(r.post_assessment, _ASSESSMENT_IDS) for r in results]),
        pre_transfer_score=_mean([_score(r.pre_assessment, _TRANSFER_IDS) for r in results]),
        transfer_gain=_mean([
            _session_transfer(r) - _score(r.pre_assessment, _TRANSFER_IDS) for r in results
        ]),
        mean_hints_first_half=_mean([h[0] for h in halves]),
        mean_hints_second_half=_mean([h[1] for h in halves]),
        n_sessions=len(results),
    )


__all__ = ["DIMENSIONS", "DimensionScores", "TutorMetrics", "evaluate"]
