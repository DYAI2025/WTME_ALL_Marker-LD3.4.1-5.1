"""Tests for the /v1/analyze/dynamics API endpoint."""
import sys
sys.path.insert(0, ".")

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_dynamics_endpoint_basic():
    resp = client.post("/v1/analyze/dynamics", json={
        "messages": [
            {"role": "A", "text": "Ich bin wütend!"},
            {"role": "B", "text": "Es tut mir leid."},
            {"role": "A", "text": "Ich verstehe dich."},
        ]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "message_vad" in data
    assert "ued_metrics" in data
    assert "state_indices" in data
    assert "markers" in data
    assert "meta" in data
    assert len(data["message_vad"]) == 3


def test_dynamics_vad_structure():
    resp = client.post("/v1/analyze/dynamics", json={
        "messages": [
            {"role": "A", "text": "Du bist immer so egoistisch!"},
            {"role": "B", "text": "Das stimmt nicht!"},
            {"role": "A", "text": "Lass uns in Ruhe reden."},
        ]
    })
    data = resp.json()
    for mv in data["message_vad"]:
        assert "valence" in mv
        assert "arousal" in mv
        assert "dominance" in mv


def test_dynamics_state_indices_structure():
    resp = client.post("/v1/analyze/dynamics", json={
        "messages": [
            {"role": "A", "text": "Du bist schuld!"},
            {"role": "B", "text": "Ich entschuldige mich."},
        ]
    })
    data = resp.json()
    si = data["state_indices"]
    assert "trust" in si
    assert "conflict" in si
    assert "deesc" in si
    assert "contributing_markers" in si


def test_dynamics_ued_with_few_messages():
    """UED should be None with fewer than 3 messages."""
    resp = client.post("/v1/analyze/dynamics", json={
        "messages": [
            {"role": "A", "text": "Hallo."},
            {"role": "B", "text": "Hi."},
        ]
    })
    data = resp.json()
    assert data["ued_metrics"] is None


def test_dynamics_threshold():
    resp = client.post("/v1/analyze/dynamics", json={
        "messages": [
            {"role": "A", "text": "Ich bin so traurig."},
            {"role": "B", "text": "Ich verstehe dich."},
            {"role": "A", "text": "Danke dir."},
        ],
        "threshold": 0.3,
    })
    assert resp.status_code == 200
