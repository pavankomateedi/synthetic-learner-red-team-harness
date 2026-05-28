"""Harness orchestration (PRD 9 recursive improvement loop, 10).

Runs an identical synthetic population against the baseline and improved tutors,
evaluates both, compares them with regression + counter-metric checks, and
emits the deliverable reports. Everything is seeded, so a given
``(personas, n_seeds)`` always yields identical numbers.
"""

from __future__ import annotations

from dataclasses import dataclass

from .comparator import ComparisonReport, compare
from .evaluator import TutorMetrics, evaluate
from .personas import Persona, all_personas
from .session import SessionResult, run_session
from .tutor import make_tutor

DEFAULT_SEEDS = 25


def run_population(tutor_name: str, personas: list[Persona] | None = None,
                   n_seeds: int = DEFAULT_SEEDS, seed_offset: int = 0) -> list[SessionResult]:
    """Run every persona x seed against one tutor and return raw session results."""
    personas = personas or all_personas()
    tutor = make_tutor(tutor_name)
    results: list[SessionResult] = []
    for persona in personas:
        for s in range(n_seeds):
            results.append(run_session(persona, tutor, seed_offset + s))
    return results


@dataclass
class LoopResult:
    """The full output of one recursive improvement cycle."""

    baseline: TutorMetrics
    improved: TutorMetrics
    comparison: ComparisonReport


def run_improvement_loop(personas: list[Persona] | None = None,
                         n_seeds: int = DEFAULT_SEEDS) -> LoopResult:
    """One complete cycle: baseline run -> improved run -> comparison."""
    base_results = run_population("v1", personas, n_seeds)
    imp_results = run_population("v2", personas, n_seeds)
    baseline = evaluate(base_results)
    improved = evaluate(imp_results)
    return LoopResult(baseline, improved, compare(baseline, improved))


__all__ = ["run_population", "run_improvement_loop", "LoopResult", "DEFAULT_SEEDS"]
