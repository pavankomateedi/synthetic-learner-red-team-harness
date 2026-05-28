"""The headline gate: the golden set must pass in full.

This is the eval contract -- it encodes both the baseline failures the harness
must surface and the improvements the recursive loop must deliver, plus the
anti-gaming guarantees. If a future change breaks any expectation, this fails.
"""

import pytest

from slh.goldenset import (
    GOLDEN_SEEDS,
    check_behaviors,
    check_population,
)
from slh.harness import run_improvement_loop


@pytest.fixture(scope="module")
def loop():
    return run_improvement_loop(n_seeds=GOLDEN_SEEDS)


def test_population_golden_set_passes(loop):
    metrics = {"v1": loop.baseline, "v2": loop.improved}
    results = check_population(metrics, loop.comparison)
    failed = [r for r in results if not r.passed]
    assert not failed, "\n".join(f"{r.name}: {r.detail}" for r in failed)


def test_behavior_golden_set_passes():
    results = check_behaviors()
    failed = [r for r in results if not r.passed]
    assert not failed, "\n".join(f"{r.name}: {r.detail}" for r in failed)


def test_loop_is_reproducible():
    a = run_improvement_loop(n_seeds=6)
    b = run_improvement_loop(n_seeds=6)
    assert a.baseline.overall.as_dict() == b.baseline.overall.as_dict()
    assert a.improved.overall.as_dict() == b.improved.overall.as_dict()
