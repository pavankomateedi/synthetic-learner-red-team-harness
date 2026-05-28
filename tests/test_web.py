"""FastAPI dashboard tests (TestClient over the in-process app)."""

import pytest
from fastapi.testclient import TestClient

from slh import web


@pytest.fixture(scope="module")
def client():
    # Use the canonical golden seed count so the golden-set assertion holds
    # (the contract in goldenset.py is calibrated at 25 seeds). Still sub-second.
    import os
    os.environ["SLH_WEB_SEEDS"] = "25"
    web._loop.cache_clear()
    return TestClient(web.app)


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_dashboard_renders(client):
    r = client.get("/")
    assert r.status_code == 200
    body = r.text
    assert "Synthetic Learner Red Team Harness" in body
    assert "baseline_v1" in body and "improved_v2" in body
    assert "Counter-metrics" in body
    assert "golden checks" in body


def test_api_metrics_shape(client):
    r = client.get("/api/metrics")
    assert r.status_code == 200
    data = r.json()
    assert set(data["baseline"]) == set(data["improved"])
    assert data["golden"]["passed"] == data["golden"]["total"]  # all green
    assert data["overall_improved"] is True
    assert "transfer_tracks_score" in data["counter_metrics"]


def test_seeds_env_parsing(monkeypatch):
    monkeypatch.setenv("SLH_WEB_SEEDS", "not-a-number")
    assert web._seeds() == 25
    monkeypatch.setenv("SLH_WEB_SEEDS", "7")
    assert web._seeds() == 7
