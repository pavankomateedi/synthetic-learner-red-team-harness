"""Avoidance & shallow-compliance detector (PRD 10.1 "Avoidance Detector",
13.1 failure taxonomy).

Operates purely on a :class:`Transcript`. It flags bypass attempts, answer
solicitation, topic-switching, give-ups, and feigned understanding, and -- by
looking at the tutor's *next* move on the same item -- whether each avoidance
event was successfully recovered (redirected / refused / re-engaged).
"""

from __future__ import annotations

from dataclasses import dataclass

from .protocol import ActionType, MoveType, Transcript

# Which tutor move counts as "recovering" each avoidance action.
_RECOVERY_MOVE: dict[ActionType, MoveType] = {
    ActionType.SWITCH_TOPIC: MoveType.REDIRECT,
    ActionType.GIVE_UP: MoveType.ENCOURAGE,
    ActionType.BYPASS_ATTEMPT: MoveType.REFUSE_BYPASS,
}

_AVOIDANCE_ACTIONS = frozenset(_RECOVERY_MOVE) | {ActionType.ASK_ANSWER}


@dataclass
class AvoidanceFlags:
    bypass_attempts: int = 0
    answer_solicitations: int = 0
    topic_switches: int = 0
    give_ups: int = 0
    hint_solicitations: int = 0
    feigned_understanding: int = 0       # CLAIM_UNDERSTANDING that was not genuine
    shallow_accepted: int = 0            # feigned claims the tutor accepted (no probe)
    avoidance_events: int = 0            # events that *could* be recovered
    avoidance_recovered: int = 0         # events the tutor actually recovered

    @property
    def recovery_rate(self) -> float:
        if self.avoidance_events == 0:
            return 1.0  # nothing to recover from
        return self.avoidance_recovered / self.avoidance_events

    @property
    def total_avoidance(self) -> int:
        return (self.bypass_attempts + self.answer_solicitations
                + self.topic_switches + self.give_ups)


def detect(transcript: Transcript) -> AvoidanceFlags:
    """Scan a transcript and tally avoidance behavior + tutor recovery."""
    f = AvoidanceFlags()
    turns = transcript.turns
    for i, turn in enumerate(turns):
        a = turn.action
        if a.type == ActionType.BYPASS_ATTEMPT:
            f.bypass_attempts += 1
        elif a.type == ActionType.ASK_ANSWER:
            f.answer_solicitations += 1
        elif a.type == ActionType.SWITCH_TOPIC:
            f.topic_switches += 1
        elif a.type == ActionType.GIVE_UP:
            f.give_ups += 1
        elif a.type == ActionType.ASK_HINT:
            f.hint_solicitations += 1
        elif a.type == ActionType.CLAIM_UNDERSTANDING and a.genuine is False:
            f.feigned_understanding += 1
            # Accepted shallow compliance: a feigned "I get it" that the tutor
            # did NOT challenge with a probe on the same item.
            nxt = turns[i + 1] if i + 1 < len(turns) else None
            caught = (nxt is not None
                      and nxt.move.problem_id == turn.move.problem_id
                      and nxt.move.type == MoveType.PROBE)
            if not caught:
                f.shallow_accepted += 1

        # Recoverable avoidance events: look at the tutor's next move on this item.
        if a.type in _RECOVERY_MOVE:
            f.avoidance_events += 1
            want = _RECOVERY_MOVE[a.type]
            nxt = turns[i + 1] if i + 1 < len(turns) else None
            if (nxt is not None
                    and nxt.move.problem_id == turn.move.problem_id
                    and nxt.move.type == want):
                f.avoidance_recovered += 1
    return f


__all__ = ["AvoidanceFlags", "detect"]
