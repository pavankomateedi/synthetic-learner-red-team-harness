"""Curriculum & misconception-catalog integrity tests."""

import pytest

from slh.curriculum import (
    CONCEPTS,
    MISCONCEPTIONS,
    PROBLEMS,
    Fraction,
    parse_fraction,
    problems_for,
)


def test_fraction_value_reduce_equals():
    assert Fraction(2, 4).value == 0.5
    assert Fraction(6, 8).reduced() == Fraction(3, 4)
    assert Fraction(1, 2).equals(Fraction(2, 4))
    assert not Fraction(1, 2).equals(Fraction(1, 3))
    assert str(Fraction(2, 4)) == "2/4"


def test_fraction_zero_denominator_rejected():
    with pytest.raises(ValueError):
        Fraction(1, 0)


def test_parse_fraction_whitespace_tolerant():
    assert parse_fraction(" 3 / 4 ") == Fraction(3, 4)


def test_every_problem_grades_its_own_answer_correct():
    for p in PROBLEMS:
        assert p.is_correct(p.answer), p.id
        # The canonical correct answer is not diagnosed as a misconception.
        assert p.diagnose(p.answer) is None, p.id


def test_misconception_answers_are_wrong_and_diagnosable():
    for p in PROBLEMS:
        for mid, wrong in p.misconception_answers.items():
            assert mid in MISCONCEPTIONS, (p.id, mid)
            assert not p.is_correct(wrong), (p.id, mid)
            assert p.diagnose(wrong) == mid, (p.id, mid)


def test_misconceptions_reference_real_concepts():
    for m in MISCONCEPTIONS.values():
        for c in m.affected_concepts:
            assert c in CONCEPTS
        assert m.citation  # every misconception is cited


def test_problem_kinds_present():
    assert problems_for("instruction")
    assert problems_for("assessment")
    assert problems_for("transfer")


def test_comparison_grading_is_symbolic():
    cmp = problems_for("instruction", "comparison")[0]
    assert cmp.is_correct(cmp.answer)
    assert not cmp.is_correct("=")  # unless answer is "="
