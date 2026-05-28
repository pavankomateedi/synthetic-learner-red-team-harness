"""Persona design tests (PRD 6)."""

import itertools

from slh.curriculum import MISCONCEPTIONS
from slh.personas import _NUMERIC_DIMS, PERSONAS, all_personas


def test_at_least_six_personas():
    assert len(PERSONAS) >= 6


def test_all_personas_document_required_facets():
    for p in all_personas():
        assert p.archetype and p.description
        assert p.educational_risk and p.research_grounding
        assert p.avoidance_signature
        assert p.prior_mastery  # knowledge state
        for mid in p.misconceptions:
            assert mid in MISCONCEPTIONS


def test_numeric_dimensions_in_unit_range():
    for p in all_personas():
        for d in _NUMERIC_DIMS:
            v = getattr(p, d)
            assert 0.0 <= v <= 1.0, (p.id, d, v)


def test_persona_pairs_differ_in_at_least_three_dimensions():
    """PRD 6.3: each persona must differ in >= 3 measurable dimensions."""
    for a, b in itertools.combinations(all_personas(), 2):
        assert a.dimensions_differing(b) >= 3, (a.id, b.id, a.dimensions_differing(b))


def test_persona_ids_unique():
    ids = [p.id for p in all_personas()]
    assert len(ids) == len(set(ids))
