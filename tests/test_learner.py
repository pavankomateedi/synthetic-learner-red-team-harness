"""Synthetic learner behavior & memory-model tests."""

import random

from slh.curriculum import PROBLEMS_BY_ID, problems_for
from slh.learner import SyntheticLearner
from slh.personas import PERSONAS
from slh.protocol import ActionType, Move, MoveType


def _learner(pid="shortcut_seeker"):
    return SyntheticLearner(PERSONAS[pid])


def test_transfer_penalty_lowers_effective_mastery():
    learner = _learner("memorizer")
    instr = problems_for("instruction", "addition_unlike")[0]
    transfer = problems_for("transfer", "addition_unlike")[0]
    assert learner.effective_mastery(transfer) < learner.effective_mastery(instr)


def test_generate_answer_uses_held_misconception():
    learner = _learner("confident_guesser")  # holds bigger_denom_bigger
    cmp = PROBLEMS_BY_ID["cmp_i1"]
    rng = random.Random(0)
    saw_misconception = False
    for _ in range(50):
        a = learner._generate_answer(cmp, rng)
        if a.response == cmp.misconception_answers["bigger_denom_bigger"]:
            saw_misconception = True
            break
    assert saw_misconception


def test_resolve_increases_mastery():
    learner = _learner("i_get_it")
    addl = problems_for("instruction", "addition_like")[0]
    before = learner.state.mastery["addition_like"]
    learner.resolve(addl, quality=1.0, remediate=False, rng=random.Random(0))
    assert learner.state.mastery["addition_like"] > before


def test_remediation_clears_misconception_deterministically():
    learner = _learner("i_get_it")
    addl = problems_for("instruction", "addition_like")[0]
    # quality=1.0 -> removal probability 1.0
    learner.resolve(addl, quality=1.0, remediate=True, rng=random.Random(0))
    assert "add_across" not in learner.state.misconceptions


def test_record_grade_tracks_consecutive_errors():
    learner = _learner()
    learner.record_grade(False)
    learner.record_grade(False)
    assert learner.state.consecutive_errors == 2
    learner.record_grade(True)
    assert learner.state.consecutive_errors == 0


def test_adversarial_learner_attempts_bypass():
    learner = _learner("adversarial_learner")
    move = Move(MoveType.PRESENT_PROBLEM, "eq_i1")
    rng = random.Random(0)
    actions = {learner.respond(move, rng).type for _ in range(20)}
    assert ActionType.BYPASS_ATTEMPT in actions


def test_probe_response_is_unsound_for_low_mastery():
    learner = _learner("i_get_it")  # mastery 0.4, holds add_across
    addl = problems_for("instruction", "addition_like")[0]
    action = learner.respond(Move(MoveType.PROBE, addl.id), random.Random(0))
    assert action.type == ActionType.EXPLAIN
    assert action.correct is False


def test_comprehension_check_can_be_feigned():
    learner = _learner("i_get_it")  # feigns_understanding 0.9
    addl = problems_for("instruction", "addition_like")[0]
    rng = random.Random(0)
    claims = [learner.respond(Move(MoveType.COMPREHENSION_CHECK, addl.id), rng)
              for _ in range(20)]
    feigned = [c for c in claims
               if c.type == ActionType.CLAIM_UNDERSTANDING and c.genuine is False]
    assert feigned  # at least one feigned "I get it"
