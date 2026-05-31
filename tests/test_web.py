"""FastAPI dashboard tests (TestClient over the in-process app)."""

import pytest
from fastapi.testclient import TestClient

from slh import web


@pytest.fixture(scope="module")
def client(monkeypatch_module):
    # Use the canonical golden seed count so the golden-set assertion holds
    # (the contract in goldenset.py is calibrated at 25 seeds). Use a
    # module-scoped monkeypatch so the env mutation is restored after this
    # module instead of leaking to subsequent test modules.
    monkeypatch_module.setenv("SLH_WEB_SEEDS", "25")
    web._loop.cache_clear()
    return TestClient(web.app)


@pytest.fixture(scope="module")
def monkeypatch_module():
    # pytest's built-in monkeypatch is function-scoped; for a module-scoped
    # fixture we need our own MonkeyPatch instance with manual teardown.
    from _pytest.monkeypatch import MonkeyPatch
    mp = MonkeyPatch()
    yield mp
    mp.undo()


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_dashboard_renders(client):
    r = client.get("/")
    assert r.status_code == 200
    body = r.text
    # Engineering view: friendly labels, no code identifiers.
    assert "Did the new tutor really teach better?" in body
    assert "Old Tutor" in body and "New Tutor" in body
    assert "Sanity checks" in body
    assert "Quality checks pass" in body
    assert "Did students actually learn more?" in body
    assert "answer_giving_rate" not in body
    # Friendly persona names — including the two new negative-result personas.
    assert "The Shortcut Seeker" in body
    assert "The Advanced Learner" in body
    assert "The Struggling Learner" in body
    assert "shortcut_seeker" not in body
    # Nav links to all three audience views.
    assert 'href="teacher.html"' in body and 'href="parents.html"' in body


def test_teacher_view_renders(client):
    r = client.get("/teacher.html")
    assert r.status_code == 200
    body = r.text
    # Pedagogy framing: practices list and big stats reframed pedagogically.
    assert "Does the AI tutor practice what we teach?" in body
    assert "Practices the new tutor adopts" in body
    assert "Of misconceptions it actually fixes" in body
    # Persona table reused with friendly names.
    assert "The Struggling Learner" in body


def test_parents_view_renders(client):
    r = client.get("/parents.html")
    assert r.status_code == 200
    body = r.text
    # Plain-language outcomes; no technical metric names.
    assert "Is the AI tutor actually helping kids learn?" in body
    assert "What the tutor does well" in body
    assert "Where it still struggles" in body
    # Big stat about answer-handing (yes/no/rarely/never word).
    assert "Does the tutor hand over answers?" in body
    # Parents view stays jargon-free.
    assert "counter-metric" not in body
    assert "transfer_score" not in body


def test_api_metrics_shape(client):
    """Structural assertion only.

    Does NOT assert passed == total: that would couple this test to every
    golden expectation passing, so a single noise-driven golden flake would
    also fail the web test and mask the real subsystem. The golden state
    itself is asserted in tests/test_goldenset.py where it belongs.
    """
    r = client.get("/api/metrics")
    assert r.status_code == 200
    data = r.json()
    assert set(data["baseline"]) == set(data["improved"])
    assert {"passed", "total"} <= set(data["golden"])
    assert isinstance(data["overall_improved"], bool)
    assert "transfer_tracks_score" in data["counter_metrics"]


def test_seeds_env_parsing(monkeypatch):
    monkeypatch.setenv("SLH_WEB_SEEDS", "not-a-number")
    assert web._seeds() == 25
    monkeypatch.setenv("SLH_WEB_SEEDS", "7")
    assert web._seeds() == 7
