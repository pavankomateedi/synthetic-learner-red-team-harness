"""Tutor policy tests: baseline failures vs. improved fixes."""

import random

from slh.curriculum import PROBLEMS_BY_ID
from slh.protocol import Action, ActionType, ItemState, MoveType
from slh.tutor import TutorV1, TutorV2, make_tutor

RNG = random.Random(0)
EQ = "eq_i1"


def _item():
    return ItemState(EQ)


def test_make_tutor_aliases():
    assert make_tutor("v1").name == "baseline_v1"
    assert make_tutor("baseline").name == "baseline_v1"
    assert make_tutor("v2").name == "improved_v2"
    assert make_tutor("improved").name == "improved_v2"


def test_make_tutor_unknown_raises():
    import pytest
    with pytest.raises(ValueError):
        make_tutor("v3")


def test_v1_gives_answer_on_request():
    move = TutorV1().next_move(PROBLEMS_BY_ID[EQ],
                               Action(ActionType.ASK_ANSWER, EQ), _item(), RNG)
    assert move.type == MoveType.GIVE_ANSWER


def test_v1_is_susceptible_to_bypass():
    move = TutorV1().next_move(PROBLEMS_BY_ID[EQ],
                               Action(ActionType.BYPASS_ATTEMPT, EQ), _item(), RNG)
    assert move.type == MoveType.GIVE_ANSWER


def test_v1_hint_cascade_ends_in_answer():
    tutor, item = TutorV1(), _item()
    item.hints_given = 2
    move = tutor.next_move(PROBLEMS_BY_ID[EQ], Action(ActionType.ASK_HINT, EQ), item, RNG)
    assert move.type == MoveType.GIVE_ANSWER


def test_v1_accepts_shallow_compliance():
    move = TutorV1().next_move(PROBLEMS_BY_ID[EQ],
                               Action(ActionType.CLAIM_UNDERSTANDING, EQ, genuine=False),
                               _item(), RNG)
    assert move.type == MoveType.ADVANCE


def test_v1_tolerates_off_task():
    move = TutorV1().next_move(PROBLEMS_BY_ID[EQ],
                               Action(ActionType.SWITCH_TOPIC, EQ), _item(), RNG)
    assert move.type != MoveType.REDIRECT


def test_v2_refuses_bypass():
    move = TutorV2().next_move(PROBLEMS_BY_ID[EQ],
                               Action(ActionType.BYPASS_ATTEMPT, EQ), _item(), RNG)
    assert move.type == MoveType.REFUSE_BYPASS


def test_v2_withholds_answer_and_caps_hints():
    tutor, item = TutorV2(), _item()
    item.hints_given = TutorV2.MAX_HINTS
    move = tutor.next_move(PROBLEMS_BY_ID[EQ], Action(ActionType.ASK_ANSWER, EQ), item, RNG)
    assert move.type == MoveType.PROBE  # never GIVE_ANSWER


def test_v2_redirects_off_task():
    move = TutorV2().next_move(PROBLEMS_BY_ID[EQ],
                               Action(ActionType.SWITCH_TOPIC, EQ), _item(), RNG)
    assert move.type == MoveType.REDIRECT


def test_v2_probes_claim_of_understanding():
    move = TutorV2().next_move(PROBLEMS_BY_ID[EQ],
                               Action(ActionType.CLAIM_UNDERSTANDING, EQ, genuine=False),
                               _item(), RNG)
    assert move.type == MoveType.PROBE


def test_v2_remediates_diagnosed_misconception():
    tutor, item = TutorV2(), _item()
    wrong = Action(ActionType.ANSWER, EQ, correct=False, misconception="same_digits_only")
    move = tutor.next_move(PROBLEMS_BY_ID[EQ], wrong, item, RNG)
    assert move.type == MoveType.PROBE
    assert item.remediated is True


def test_resolution_quality_ordering():
    v1, v2 = TutorV1(), TutorV2()
    given = ItemState(EQ, answer_given=True)
    verified = ItemState(EQ, verified_understanding=True)
    assert v1.resolution_quality(given) < v2.resolution_quality(verified)
