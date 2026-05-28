"""Session runner: drives a multi-turn learner <-> tutor interaction and
captures everything the evaluator needs (PRD 7.2, 10.1).

Measurement design:
  * A **pre-assessment** snapshots knowledge on assessment + transfer items
    *before* any teaching (no learning is applied).
  * The **lesson** teaches instruction + assessment items in curriculum order.
  * A **post-assessment** re-measures assessment items (learning gain) and
    transfer items (transfer score) *after* teaching.

Assessment attempts are pure: they read the learner's knowledge but never
mutate it, so pre/post comparisons are clean.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .curriculum import (
    LESSON_SEQUENCE,
    PROBLEMS_BY_ID,
    Problem,
    problems_for,
)
from .learner import SyntheticLearner
from .personas import Persona
from .protocol import ActionType, ItemState, MoveType, Transcript, Turn
from .tutor import PER_ITEM_TURN_BUDGET, TutorPolicy


@dataclass
class SessionResult:
    learner_id: str
    tutor_name: str
    transcript: Transcript
    items: list[ItemState]
    pre_assessment: dict[str, bool]
    post_assessment: dict[str, bool]
    post_transfer: dict[str, bool]
    initial_misconceptions: set[str]
    final_misconceptions: set[str]
    mastery_before: dict[str, float] = field(default_factory=dict)
    mastery_after: dict[str, float] = field(default_factory=dict)


def lesson_problems() -> list[Problem]:
    """Instruction + assessment items, ordered by the curriculum sequence."""
    out: list[Problem] = []
    for concept in LESSON_SEQUENCE:
        out += problems_for("instruction", concept)
        out += problems_for("assessment", concept)
    return out


def _assess(learner: SyntheticLearner, problems: list[Problem],
            rng: random.Random) -> dict[str, bool]:
    """A pure attempt at each problem; reads knowledge, never mutates it."""
    result: dict[str, bool] = {}
    for p in problems:
        action = learner._generate_answer(p, rng)  # noqa: SLF001 - intentional internal use
        result[p.id] = p.is_correct(action.response)
    return result


def run_item(learner: SyntheticLearner, tutor: TutorPolicy, problem: Problem,
             transcript: Transcript, rng: random.Random,
             budget: int = PER_ITEM_TURN_BUDGET) -> ItemState:
    """Run a single problem to resolution (or budget exhaustion)."""
    item = ItemState(problem.id)
    move = tutor.open_item(problem)
    turns = 0
    while move.type != MoveType.ADVANCE:
        action = learner.respond(move, rng)
        if action.type == ActionType.ANSWER and action.response:
            action.correct = problem.is_correct(action.response)
            action.misconception = problem.diagnose(action.response)
            learner.record_grade(bool(action.correct))
        elif action.type == ActionType.EXPLAIN:
            action.misconception = (
                problem.diagnose(action.response) if action.response else None
            )
        tutor.observe(action, item)
        transcript.turns.append(Turn(turns, move, action))
        turns += 1
        if turns >= budget:
            break
        move = tutor.next_move(problem, action, item, rng)

    quality = tutor.resolution_quality(item)
    learner.resolve(problem, quality, item.remediated, rng)
    transcript.resolved[problem.id] = learner.effective_mastery(problem) >= 0.7
    return item


def run_session(persona: Persona, tutor: TutorPolicy, seed: int) -> SessionResult:
    """Run one full teaching session for one persona against one tutor."""
    rng = random.Random(seed)
    learner = SyntheticLearner(persona)

    init_mis = set(learner.state.misconceptions)
    mastery_before = dict(learner.state.mastery)

    assess_items = problems_for("assessment") + problems_for("transfer")
    pre = _assess(learner, assess_items, rng)

    transcript = Transcript(learner.id, tutor.name)
    items: list[ItemState] = []
    for problem in lesson_problems():
        items.append(run_item(learner, tutor, problem, transcript, rng))

    post = _assess(learner, problems_for("assessment"), rng)
    post_transfer = _assess(learner, problems_for("transfer"), rng)

    return SessionResult(
        learner_id=learner.id,
        tutor_name=tutor.name,
        transcript=transcript,
        items=items,
        pre_assessment=pre,
        post_assessment=post,
        post_transfer=post_transfer,
        initial_misconceptions=init_mis,
        final_misconceptions=set(learner.state.misconceptions),
        mastery_before=mastery_before,
        mastery_after=dict(learner.state.mastery),
    )


__all__ = ["SessionResult", "run_session", "run_item", "lesson_problems", "PROBLEMS_BY_ID"]
