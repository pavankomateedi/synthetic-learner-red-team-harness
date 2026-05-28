"""Shared interaction protocol between the tutor and the synthetic learner.

A session is a sequence of turns. On each turn the tutor emits a :class:`Move`
and the learner replies with an :class:`Action`. Keeping these types in one
module avoids a tutor<->learner import cycle and gives the evaluator a single,
stable vocabulary to score against.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class MoveType(StrEnum):
    PRESENT_PROBLEM = "present_problem"   # pose the current problem
    GIVE_HINT = "give_hint"               # scaffold toward the answer
    GIVE_ANSWER = "give_answer"           # reveal the answer (a tutor failure)
    COMPREHENSION_CHECK = "comprehension_check"  # "do you understand?" (shallow)
    PROBE = "probe"                       # ask the learner to justify (deep check)
    REDIRECT = "redirect"                 # bring an off-task learner back
    ENCOURAGE = "encourage"               # emotional scaffolding
    ADVANCE = "advance"                   # mark item resolved, move on
    REFUSE_BYPASS = "refuse_bypass"       # decline an adversarial request


class ActionType(StrEnum):
    ANSWER = "answer"                     # attempt the problem
    ASK_HINT = "ask_hint"                 # request a hint
    ASK_ANSWER = "ask_answer"             # solicit the answer directly
    CLAIM_UNDERSTANDING = "claim_understanding"  # "I get it" (maybe feigned)
    EXPLAIN = "explain"                   # justify reasoning (answer to a probe)
    SWITCH_TOPIC = "switch_topic"         # go off-task
    GIVE_UP = "give_up"                   # disengage
    BYPASS_ATTEMPT = "bypass_attempt"     # adversarial manipulation


@dataclass
class Move:
    """A tutor utterance directed at the learner."""

    type: MoveType
    problem_id: str | None = None
    hint_level: int = 0
    text: str = ""


@dataclass
class Action:
    """A learner response to the tutor's move."""

    type: ActionType
    problem_id: str | None = None
    response: str = ""        # the literal answer string, if ANSWER/EXPLAIN
    correct: bool | None = None    # filled by the session runner after grading
    misconception: str | None = None  # diagnosed misconception id, if any
    genuine: bool | None = None    # for CLAIM_UNDERSTANDING: is it real?
    text: str = ""


@dataclass
class Turn:
    """One tutor move paired with the learner's reply."""

    index: int
    move: Move
    action: Action


@dataclass
class ItemState:
    """Per-problem working state the tutor and runner share within a session."""

    problem_id: str
    attempts: int = 0
    hints_given: int = 0
    off_task: int = 0
    bypass_attempts: int = 0
    last_correct: bool | None = None
    last_misconception: str | None = None
    claimed_understanding: bool = False
    verified_understanding: bool = False
    gave_up: bool = False
    answer_given: bool = False        # tutor revealed the answer this item
    # Set by the tutor when it decides to ADVANCE:
    resolution_quality: float = 0.0   # instructional soundness of the resolution
    remediated: bool = False          # did the tutor target a misconception?


@dataclass
class Transcript:
    """The full record of a session, plus the problems that were resolved."""

    learner_id: str
    tutor_name: str
    turns: list[Turn] = field(default_factory=list)
    resolved: dict[str, bool] = field(default_factory=dict)  # problem_id -> mastered-at-resolution

    def actions_of(self, *types: ActionType) -> list[Action]:
        return [t.action for t in self.turns if t.action.type in types]

    def moves_of(self, *types: MoveType) -> list[Move]:
        return [t.move for t in self.turns if t.move.type in types]
