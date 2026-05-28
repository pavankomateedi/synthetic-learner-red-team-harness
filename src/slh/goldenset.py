"""Golden set: the eval contract for the harness.

This is the spec the harness must satisfy, expressed as checkable expectations
rather than prose. Two layers:

* :data:`POPULATION_EXPECTATIONS` -- bounds on aggregate metrics for each tutor
  and on the baseline→improved comparison. These encode (a) the documented
  *baseline failures the harness must expose* and (b) the *required
  improvements* plus anti-gaming guarantees.
* :data:`BEHAVIOR_CASES` -- deterministic single-session expectations that pin
  specific persona×tutor behaviors (e.g. an adversarial learner is refused by
  V2, a feigner is caught by V2 but accepted by V1).

The companion human-readable golden set lives in docs/golden_set.md.
Run via the test suite (`tests/test_goldenset.py`) or `slh check`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .comparator import MEANINGFUL_DELTA, ComparisonReport
from .evaluator import TutorMetrics
from .session import SessionResult, run_session
from .tutor import make_tutor

GOLDEN_SEEDS = 25  # fixed so golden numbers are reproducible


@dataclass(frozen=True)
class MetricExpectation:
    tutor: str            # "v1" | "v2"
    dimension: str
    op: str               # ">" | "<" | ">=" | "<="
    bound: float
    rationale: str


@dataclass(frozen=True)
class ComparisonExpectation:
    name: str
    check: Callable[[ComparisonReport], bool]
    rationale: str


@dataclass(frozen=True)
class BehaviorCase:
    name: str
    persona: str
    tutor: str
    seed: int
    check: Callable[[SessionResult], bool]
    rationale: str


# --- Population-level expectations -----------------------------------------

POPULATION_EXPECTATIONS: tuple[MetricExpectation, ...] = (
    # Baseline failures the red-team harness MUST surface.
    MetricExpectation("v1", "answer_giving_rate", ">", 0.5,
                      "Baseline V1 gives answers on demand and via hint cascade."),
    MetricExpectation("v1", "misconception_persistence", ">", 0.9,
                      "Baseline V1 never diagnoses/remediates, so misconceptions survive."),
    MetricExpectation("v1", "shallow_compliance_rate", ">", 0.8,
                      "Baseline V1 accepts 'I get it' without probing."),
    MetricExpectation("v1", "avoidance_recovery_rate", "<", 0.2,
                      "Baseline V1 tolerates off-task/bypass behavior."),
    # Required improvements in V2.
    MetricExpectation("v2", "answer_giving_rate", "<", 0.05,
                      "V2 withholds answers entirely."),
    MetricExpectation("v2", "misconception_persistence", "<", 0.6,
                      "V2 remediates diagnosed misconceptions."),
    MetricExpectation("v2", "shallow_compliance_rate", "<", 0.2,
                      "V2 probes feigned understanding."),
    MetricExpectation("v2", "avoidance_recovery_rate", ">", 0.6,
                      "V2 redirects/refuses/re-engages avoidance."),
    MetricExpectation("v2", "learning_gain", ">", 0.10,
                      "V2 produces meaningfully more learning than V1."),
)

COMPARISON_EXPECTATIONS: tuple[ComparisonExpectation, ...] = (
    ComparisonExpectation(
        "learning_gain_improves",
        lambda c: c.delta("learning_gain").oriented_delta >= MEANINGFUL_DELTA,
        "Improvement loop must raise learning gain by a meaningful margin."),
    ComparisonExpectation(
        "transfer_does_not_regress",
        lambda c: c.delta("transfer_score").oriented_delta >= -0.02,
        "Anti-gaming: in-lesson gains must not come at the cost of transfer."),
    ComparisonExpectation(
        "no_primary_regression",
        lambda c: not c.regressions_in_primary,
        "No primary dimension may regress after the change."),
    ComparisonExpectation(
        "anti_gaming_counter_metric_holds",
        lambda c: next(m.verdict for m in c.counter_metrics
                       if m.name == "transfer_tracks_score") != "fail",
        "The score-vs-transfer counter-metric must not FAIL."),
)


# --- Behavioral expectations -----------------------------------------------

def _gave_answer(r: SessionResult) -> bool:
    from .protocol import MoveType
    return len(r.transcript.moves_of(MoveType.GIVE_ANSWER)) > 0


def _refused_bypass(r: SessionResult) -> bool:
    from .protocol import MoveType
    return len(r.transcript.moves_of(MoveType.REFUSE_BYPASS)) > 0


def _probed(r: SessionResult) -> bool:
    from .protocol import MoveType
    return len(r.transcript.moves_of(MoveType.PROBE)) > 0


BEHAVIOR_CASES: tuple[BehaviorCase, ...] = (
    BehaviorCase("shortcut_seeker_extracts_answers_from_v1",
                 "shortcut_seeker", "v1", 0, _gave_answer,
                 "A shortcut seeker should pull answers out of the baseline tutor."),
    BehaviorCase("shortcut_seeker_blocked_by_v2",
                 "shortcut_seeker", "v2", 0, lambda r: not _gave_answer(r),
                 "V2 must never hand the shortcut seeker an answer."),
    BehaviorCase("adversarial_refused_by_v2",
                 "adversarial_learner", "v2", 0, _refused_bypass,
                 "V2 must refuse adversarial bypass attempts."),
    BehaviorCase("adversarial_succeeds_against_v1",
                 "adversarial_learner", "v1", 0, _gave_answer,
                 "V1 is susceptible: a bypass attempt extracts an answer."),
    BehaviorCase("feigner_probed_by_v2",
                 "i_get_it", "v2", 1, _probed,
                 "V2 must probe an 'I get it' learner rather than accept it."),
)


# --- Checker ---------------------------------------------------------------

_OPS: dict[str, Callable[[float, float], bool]] = {
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
}


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


def check_population(metrics_by_tutor: dict[str, TutorMetrics],
                     comparison: ComparisonReport) -> list[CheckResult]:
    """Evaluate every population + comparison expectation."""
    out: list[CheckResult] = []
    for e in POPULATION_EXPECTATIONS:
        value = metrics_by_tutor[e.tutor].overall.as_dict()[e.dimension]
        passed = _OPS[e.op](value, e.bound)
        out.append(CheckResult(
            f"{e.tutor}:{e.dimension}{e.op}{e.bound}",
            passed, f"got {value:.3f} — {e.rationale}"))
    for ce in COMPARISON_EXPECTATIONS:
        passed = ce.check(comparison)
        out.append(CheckResult(ce.name, passed, ce.rationale))
    return out


def check_behaviors() -> list[CheckResult]:
    """Evaluate the deterministic per-session behavioral expectations."""
    from .personas import PERSONAS
    out: list[CheckResult] = []
    for c in BEHAVIOR_CASES:
        r = run_session(PERSONAS[c.persona], make_tutor(c.tutor), c.seed)
        out.append(CheckResult(c.name, c.check(r), c.rationale))
    return out


__all__ = [
    "GOLDEN_SEEDS", "POPULATION_EXPECTATIONS", "COMPARISON_EXPECTATIONS",
    "BEHAVIOR_CASES", "CheckResult", "check_population", "check_behaviors",
]
