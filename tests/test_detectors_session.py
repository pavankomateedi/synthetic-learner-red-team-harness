"""Detector + session-runner tests."""

from slh.detectors import detect
from slh.personas import PERSONAS
from slh.protocol import Action, ActionType, Move, MoveType, Transcript, Turn
from slh.session import lesson_problems, run_session
from slh.tutor import make_tutor


def _t(move_type, action_type, pid="p", **akw):
    return Turn(0, Move(move_type, pid), Action(action_type, pid, **akw))


def test_detect_counts_avoidance():
    tr = Transcript("x", "v1")
    tr.turns = [
        _t(MoveType.PRESENT_PROBLEM, ActionType.BYPASS_ATTEMPT),
        _t(MoveType.PRESENT_PROBLEM, ActionType.ASK_ANSWER),
        _t(MoveType.PRESENT_PROBLEM, ActionType.SWITCH_TOPIC),
        _t(MoveType.PRESENT_PROBLEM, ActionType.GIVE_UP),
    ]
    f = detect(tr)
    assert f.bypass_attempts == 1
    assert f.answer_solicitations == 1
    assert f.topic_switches == 1
    assert f.give_ups == 1
    assert f.total_avoidance == 4


def test_detect_recovery_pairs_next_move():
    tr = Transcript("x", "v2")
    tr.turns = [
        Turn(0, Move(MoveType.PRESENT_PROBLEM, "p"), Action(ActionType.SWITCH_TOPIC, "p")),
        Turn(1, Move(MoveType.REDIRECT, "p"), Action(ActionType.ANSWER, "p")),
    ]
    f = detect(tr)
    assert f.avoidance_events == 1
    assert f.avoidance_recovered == 1
    assert f.recovery_rate == 1.0


def test_detect_shallow_accepted_when_not_probed():
    tr = Transcript("x", "v1")
    tr.turns = [
        Turn(0, Move(MoveType.COMPREHENSION_CHECK, "p"),
             Action(ActionType.CLAIM_UNDERSTANDING, "p", genuine=False)),
    ]
    f = detect(tr)
    assert f.feigned_understanding == 1
    assert f.shallow_accepted == 1


def test_detect_shallow_caught_when_probed():
    tr = Transcript("x", "v2")
    tr.turns = [
        Turn(0, Move(MoveType.COMPREHENSION_CHECK, "p"),
             Action(ActionType.CLAIM_UNDERSTANDING, "p", genuine=False)),
        Turn(1, Move(MoveType.PROBE, "p"), Action(ActionType.EXPLAIN, "p", correct=False)),
    ]
    f = detect(tr)
    assert f.shallow_accepted == 0


def test_recovery_rate_is_one_when_no_events():
    assert detect(Transcript("x", "v1")).recovery_rate == 1.0


def test_run_session_is_deterministic():
    p = PERSONAS["confident_guesser"]
    r1 = run_session(p, make_tutor("v1"), 7)
    r2 = run_session(p, make_tutor("v1"), 7)
    assert [t.action.type for t in r1.transcript.turns] == \
           [t.action.type for t in r2.transcript.turns]
    assert r1.post_assessment == r2.post_assessment


def test_run_session_shapes():
    r = run_session(PERSONAS["memorizer"], make_tutor("v2"), 0)
    assert len(r.items) == len(lesson_problems())
    assert r.pre_assessment and r.post_assessment and r.post_transfer
    assert r.mastery_before and r.mastery_after
