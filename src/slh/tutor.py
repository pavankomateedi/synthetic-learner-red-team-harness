"""The tutor / curriculum engine under test (PRD section 7).

Two policies share one interface so the harness can run an identical synthetic
population against each and compare:

* :class:`TutorV1` -- the *baseline*. It deliberately embodies the documented
  tutor failures from PRD section 13.1 (answer-giving, hint cascade, shallow
  compliance acceptance, off-task tolerance, rapport-preservation, bypass
  susceptibility). These flaws are real and are what the red-team harness
  exists to surface.

* :class:`TutorV2` -- the *improved* policy proposed by the recursive loop. It
  withholds answers, caps hints, probes for genuine understanding, remediates
  diagnosed misconceptions, redirects off-task behavior, and refuses bypass
  attempts.

A move is chosen from the learner's last action plus the per-item state; the
session runner owns the loop. ``next_move`` mutates ``ItemState``; the tutor
also exposes ``resolution_quality`` so the runner can resolve learning uniformly
whether the item ended by advancing or by exhausting its turn budget.
"""

from __future__ import annotations

import random

from .curriculum import PROBLEMS_BY_ID, Problem
from .protocol import Action, ActionType, ItemState, Move, MoveType

PER_ITEM_TURN_BUDGET = 6


class TutorPolicy:
    """Base tutor: shared bookkeeping; subclasses define the reaction policy."""

    name = "base"

    def open_item(self, problem: Problem) -> Move:
        return Move(MoveType.PRESENT_PROBLEM, problem.id, text=problem.prompt)

    def observe(self, action: Action, item: ItemState) -> None:
        """Fold the learner's action into per-item counters."""
        if action.type == ActionType.ANSWER:
            item.attempts += 1
            item.last_correct = action.correct
            item.last_misconception = action.misconception
        elif action.type == ActionType.SWITCH_TOPIC:
            item.off_task += 1
        elif action.type == ActionType.BYPASS_ATTEMPT:
            item.bypass_attempts += 1
        elif action.type == ActionType.GIVE_UP:
            item.gave_up = True
        elif action.type == ActionType.CLAIM_UNDERSTANDING:
            item.claimed_understanding = True
            item.verified_understanding = bool(action.genuine)
        elif action.type == ActionType.EXPLAIN:
            item.verified_understanding = bool(action.correct)

    def next_move(self, problem: Problem, action: Action, item: ItemState,
                  rng: random.Random) -> Move:  # pragma: no cover - abstract
        raise NotImplementedError

    def resolution_quality(self, item: ItemState) -> float:  # pragma: no cover - abstract
        """Instructional soundness (0..1) of how this item was resolved."""
        raise NotImplementedError

    @staticmethod
    def _advance(item: ItemState) -> Move:
        return Move(MoveType.ADVANCE, item.problem_id)


class TutorV1(TutorPolicy):
    """Baseline tutor with the documented failure modes."""

    name = "baseline_v1"

    def next_move(self, problem: Problem, action: Action, item: ItemState,
                  rng: random.Random) -> Move:
        t = action.type

        # Bypass susceptibility: complies and hands over the answer.
        if t == ActionType.BYPASS_ATTEMPT:
            return self._give_answer(problem, item)
        # Answer-giving: any request for the answer is granted.
        if t == ActionType.ASK_ANSWER:
            return self._give_answer(problem, item)
        # Hint cascade: hint, hint, then just give the answer.
        if t == ActionType.ASK_HINT:
            if item.hints_given >= 2:
                return self._give_answer(problem, item)
            item.hints_given += 1
            return Move(MoveType.GIVE_HINT, problem.id, hint_level=item.hints_given,
                        text="here's a hint...")
        # Off-task tolerance: does not redirect; weakly re-presents.
        if t == ActionType.SWITCH_TOPIC:
            return Move(MoveType.PRESENT_PROBLEM, problem.id, text="anyway, back to this")
        # Rapport-preservation bias: a frustrated learner is simply given the answer.
        if t == ActionType.GIVE_UP:
            return self._give_answer(problem, item)
        # Shallow compliance acceptance: "I get it" is taken at face value.
        if t == ActionType.CLAIM_UNDERSTANDING:
            return self._advance(item)
        # Answer attempts.
        if t == ActionType.ANSWER:
            if action.correct:
                if not item.claimed_understanding:
                    return Move(MoveType.COMPREHENSION_CHECK, problem.id,
                                text="great -- you understand this, right?")
                return self._advance(item)
            # Wrong: validate and escalate hints; never diagnoses the misconception.
            if item.hints_given >= 2:
                return self._give_answer(problem, item)
            item.hints_given += 1
            return Move(MoveType.GIVE_HINT, problem.id, hint_level=item.hints_given,
                        text="good try! here's a hint...")
        return Move(MoveType.PRESENT_PROBLEM, problem.id, text=problem.prompt)

    def _give_answer(self, problem: Problem, item: ItemState) -> Move:
        item.answer_given = True
        item.hints_given += 1
        return Move(MoveType.GIVE_ANSWER, problem.id, text=f"the answer is {problem.answer}")

    def resolution_quality(self, item: ItemState) -> float:
        # Answer-giving teaches almost nothing; an unverified correct answer a little
        # more; nothing here remediates misconceptions.
        if item.answer_given:
            return 0.15
        if item.last_correct:
            return 0.45
        return 0.1


class TutorV2(TutorPolicy):
    """Improved tutor proposed by the recursive improvement loop."""

    name = "improved_v2"
    MAX_HINTS = 1  # cap scaffolding to protect independence

    def next_move(self, problem: Problem, action: Action, item: ItemState,
                  rng: random.Random) -> Move:
        t = action.type

        # Refuse bypass attempts outright.
        if t == ActionType.BYPASS_ATTEMPT:
            return Move(MoveType.REFUSE_BYPASS, problem.id,
                        text="I won't do that -- let's work through it together.")
        # Withhold direct answers; convert a request into one conceptual hint
        # then require an attempt.
        if t in (ActionType.ASK_ANSWER, ActionType.ASK_HINT):
            if item.hints_given >= self.MAX_HINTS:
                return Move(MoveType.PROBE, problem.id,
                            text="give it a try first -- what's your thinking?")
            item.hints_given += 1
            return Move(MoveType.GIVE_HINT, problem.id, hint_level=item.hints_given,
                        text="think about the size of each piece...")
        # Redirect off-task behavior while preserving rapport.
        if t == ActionType.SWITCH_TOPIC:
            return Move(MoveType.REDIRECT, problem.id,
                        text="we can chat after -- first, back to the fractions.")
        # Recover a disengaged learner with encouragement + scaffolding, not the answer.
        if t == ActionType.GIVE_UP:
            return Move(MoveType.ENCOURAGE, problem.id,
                        text="you've got this -- let's take it one step at a time.")
        # Never accept "I get it" at face value: probe for justification.
        if t == ActionType.CLAIM_UNDERSTANDING:
            if item.verified_understanding:
                return self._advance(item)
            return Move(MoveType.PROBE, problem.id,
                        text="great -- explain how you'd get it so I can check.")
        # A probe reply (EXPLAIN) is the real comprehension gate.
        if t == ActionType.EXPLAIN:
            if action.correct:
                return self._advance(item)
            item.remediated = True  # targeted at the underlying misconception
            return Move(MoveType.GIVE_HINT, problem.id, hint_level=item.hints_given,
                        text="let's fix the idea underneath that...")
        # Answer attempts.
        if t == ActionType.ANSWER:
            if action.correct:
                # Verify with a probe before advancing (guards against luck).
                return Move(MoveType.PROBE, problem.id, text="nice -- can you explain why?")
            if action.misconception is not None:
                # Surface and remediate the specific misconception.
                item.remediated = True
                return Move(MoveType.PROBE, problem.id,
                            text="interesting -- walk me through your reasoning.")
            if item.hints_given >= self.MAX_HINTS:
                return Move(MoveType.PROBE, problem.id, text="what step felt unsure?")
            item.hints_given += 1
            return Move(MoveType.GIVE_HINT, problem.id, hint_level=item.hints_given,
                        text="close -- reconsider the denominators.")
        return Move(MoveType.PRESENT_PROBLEM, problem.id, text=problem.prompt)

    def resolution_quality(self, item: ItemState) -> float:
        if item.verified_understanding:
            return 0.85
        if item.last_correct:
            return 0.6
        # Even an unresolved item involved productive struggle, never answer-giving.
        return 0.35


def make_tutor(name: str) -> TutorPolicy:
    if name in ("v1", "baseline", TutorV1.name):
        return TutorV1()
    if name in ("v2", "improved", TutorV2.name):
        return TutorV2()
    raise ValueError(f"unknown tutor: {name!r}")


__all__ = ["TutorPolicy", "TutorV1", "TutorV2", "make_tutor", "PER_ITEM_TURN_BUDGET",
           "PROBLEMS_BY_ID"]
