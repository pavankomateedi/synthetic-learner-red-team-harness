"""Synthetic Learner Red Team Harness.

A red-team harness that populates research-grounded synthetic learners, runs
them through an AI fractions tutor, surfaces educational failure modes, and
recursively improves the tutor while guarding against benchmark gaming.
"""

from .comparator import compare
from .evaluator import evaluate
from .harness import LoopResult, run_improvement_loop, run_population
from .personas import all_personas
from .session import run_session
from .tutor import make_tutor

__version__ = "1.0.0"

__all__ = [
    "run_improvement_loop", "run_population", "LoopResult",
    "run_session", "evaluate", "compare", "make_tutor", "all_personas",
    "__version__",
]
