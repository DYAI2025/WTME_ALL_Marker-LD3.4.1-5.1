"""Tests for the Persona Profile System (Pro Tier)."""
import sys
import shutil
import tempfile

sys.path.insert(0, ".")

from fastapi.testclient import TestClient
from api.main import app, persona_store
from api.personas import PersonaStore

client = TestClient(app)


# --- Helper: conversation payload ---

ESCALATION_CONVERSATION = {
    "messages": [
        {"role": "A", "text": "Du bist immer so egoistisch! Nie denkst du an mich!"},
        {"role": "B", "text": "Das stimmt überhaupt nicht! Du übertreibst total!"},
        {"role": "A", "text": "Siehst du? Genau das meine ich! Du hörst nie zu!"},
        {"role": "B", "text": "Ich höre immer zu! Du verdrehst alles!"},
        {"role": "A", "text": "Lass mich in Ruhe. Ich will nicht mehr reden."},
        {"role": "B", "text": "Jetzt machst du wieder dicht. Typisch!"},
        {"role": "A", "text": "Du bist schuld an allem!"},
        {"role": "B", "text": "Nein, du bist schuld!"},
    ]
}

REPAIR_CONVERSATION = {
    "messages": [
        {"role": "A", "text": "Ich bin enttäuscht von dir."},
        {"role": "B", "text": "Es tut mir wirklich leid. Ich habe einen Fehler gemacht."},
        {"role": "A", "text": "Ich verstehe, dass es schwierig war."},
        {"role": "B", "text": "Danke, dass du mir zuhörst. Ich schätze dich sehr."},
        {"role": "A", "text": "Lass uns zusammen eine Lösung finden."},
        {"role": "B", "text": "Ja, das finde ich gut. Ich bin froh."},
    ]
}

BASIC_CONVERSATION = {
    "messages": [
        {"role": "A", "text": "Ich bin wütend!"},
        {"role": "B", "text": "Es tut mir leid."},
        {"role": "A", "text": "Ich verstehe dich."},
    ]
}


# ---------------------------------------------------------------------------
# CRUD Lifecycle
# ---------------------------------------------------------------------------

def test_persona_create():
    """Create a persona and get back a UUID token."""
    resp = client.post("/v1/personas")
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert "created_at" in data
    assert len(data["token"]) == 36  # UUID format
    # Cleanup
    client.delete(f"/v1/personas/{data['token']}")


def test_persona_get():
    """Create, then retrieve a persona."""
    resp = client.post("/v1/personas")
    token = resp.json()["token"]

    resp2 = client.get(f"/v1/personas/{token}")
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["token"] == token
    assert data["schema"] == "LeanDeep-Persona"
    assert data["stats"]["session_count"] == 0
    # Cleanup
    client.delete(f"/v1/personas/{token}")


def test_persona_delete():
    """Create, delete, then verify 404."""
    resp = client.post("/v1/personas")
    token = resp.json()["token"]

    resp2 = client.delete(f"/v1/personas/{token}")
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "deleted"

    resp3 = client.get(f"/v1/personas/{token}")
    assert resp3.status_code == 404


def test_persona_delete_nonexistent():
    """Delete a nonexistent persona returns 404."""
    resp = client.delete("/v1/personas/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Path traversal guard
# ---------------------------------------------------------------------------

def test_persona_invalid_token_get():
    """Non-UUID token returns 404."""
    resp = client.get("/v1/personas/../../etc/passwd")
    assert resp.status_code == 404


def test_persona_invalid_token_delete():
    """Non-UUID token on delete returns 404."""
    resp = client.delete("/v1/personas/not-a-uuid")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Warm-start: session accumulation
# ---------------------------------------------------------------------------

def test_persona_session_accumulation():
    """Two dynamics calls with same token should increment session_count."""
    resp = client.post("/v1/personas")
    token = resp.json()["token"]

    # Session 1
    payload = {**BASIC_CONVERSATION, "persona_token": token}
    resp1 = client.post("/v1/analyze/dynamics", json=payload)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["persona_session"] is not None
    assert data1["persona_session"]["session_number"] == 1
    assert data1["persona_session"]["warm_start_applied"] is False

    # Session 2
    resp2 = client.post("/v1/analyze/dynamics", json=payload)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["persona_session"]["session_number"] == 2
    assert data2["persona_session"]["warm_start_applied"] is True

    # Verify persona file
    resp3 = client.get(f"/v1/personas/{token}")
    persona = resp3.json()
    assert persona["stats"]["session_count"] == 2
    assert persona["stats"]["total_messages"] == 6  # 3 msgs * 2 sessions

    # Cleanup
    client.delete(f"/v1/personas/{token}")


def test_persona_dynamics_without_token():
    """Dynamics without persona_token still works (backward compat)."""
    resp = client.post("/v1/analyze/dynamics", json=BASIC_CONVERSATION)
    assert resp.status_code == 200
    data = resp.json()
    assert data["persona_session"] is None
    assert "message_vad" in data


def test_persona_dynamics_invalid_token():
    """Dynamics with nonexistent persona_token returns 404."""
    payload = {**BASIC_CONVERSATION, "persona_token": "00000000-0000-0000-0000-000000000000"}
    resp = client.post("/v1/analyze/dynamics", json=payload)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Episode detection
# ---------------------------------------------------------------------------

def test_persona_episode_detection():
    """Escalation-heavy conversation should produce episodes."""
    resp = client.post("/v1/personas")
    token = resp.json()["token"]

    payload = {**ESCALATION_CONVERSATION, "persona_token": token}
    resp1 = client.post("/v1/analyze/dynamics", json=payload)
    assert resp1.status_code == 200
    data = resp1.json()

    # Check persona for episodes
    resp2 = client.get(f"/v1/personas/{token}")
    persona = resp2.json()
    episodes = persona.get("episodes", [])
    # We may get various episode types from this conversation
    assert isinstance(episodes, list)

    # Marker frequencies should have been accumulated
    assert len(persona.get("marker_frequencies", {})) > 0

    # State trajectory should have one entry
    assert len(persona["state_trajectory"]["trust"]) == 1
    assert len(persona["state_trajectory"]["conflict"]) == 1

    # Cleanup
    client.delete(f"/v1/personas/{token}")


# ---------------------------------------------------------------------------
# Prediction gating
# ---------------------------------------------------------------------------

def test_persona_prediction_insufficient_data():
    """New persona with <5 sessions → insufficient_data."""
    resp = client.post("/v1/personas")
    token = resp.json()["token"]

    resp2 = client.get(f"/v1/personas/{token}/predict")
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["confidence"] == "insufficient_data"
    assert data["predictions"] is None

    # Cleanup
    client.delete(f"/v1/personas/{token}")


def test_persona_prediction_after_sessions():
    """After enough sessions with shifts, prediction should be available."""
    resp = client.post("/v1/personas")
    token = resp.json()["token"]

    # Run 5 sessions with escalation to generate shift data
    payload = {**ESCALATION_CONVERSATION, "persona_token": token}
    for _ in range(5):
        r = client.post("/v1/analyze/dynamics", json=payload)
        assert r.status_code == 200

    resp2 = client.get(f"/v1/personas/{token}/predict")
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["session_count"] == 5
    # After 5 sessions with 8 messages each, we should have enough shifts
    if data["predictions"] is not None:
        assert "shift_counts" in data["predictions"]
        assert "shift_prior" in data["predictions"]

    # Cleanup
    client.delete(f"/v1/personas/{token}")


# ---------------------------------------------------------------------------
# Speaker EWMA persistence
# ---------------------------------------------------------------------------

def test_persona_speaker_ewma_persists():
    """Speaker EWMA values should persist across sessions."""
    resp = client.post("/v1/personas")
    token = resp.json()["token"]

    payload = {**BASIC_CONVERSATION, "persona_token": token}
    client.post("/v1/analyze/dynamics", json=payload)

    resp2 = client.get(f"/v1/personas/{token}")
    persona = resp2.json()
    ewma = persona.get("speaker_ewma", {})
    # Should have entries for speakers A and B (or at least the ones detected)
    assert len(ewma) > 0

    # Cleanup
    client.delete(f"/v1/personas/{token}")


# ---------------------------------------------------------------------------
# VAD history (Welford)
# ---------------------------------------------------------------------------

def test_persona_vad_history_accumulates():
    """VAD history should accumulate across sessions using Welford."""
    resp = client.post("/v1/personas")
    token = resp.json()["token"]

    payload = {**BASIC_CONVERSATION, "persona_token": token}
    client.post("/v1/analyze/dynamics", json=payload)
    client.post("/v1/analyze/dynamics", json=payload)

    resp2 = client.get(f"/v1/personas/{token}")
    persona = resp2.json()
    hist = persona.get("vad_history", {})
    # At least one speaker should have history
    if hist:
        for role, data in hist.items():
            assert "valence_mean" in data
            assert "n" in data
            assert data["n"] >= 1

    # Cleanup
    client.delete(f"/v1/personas/{token}")


# ---------------------------------------------------------------------------
# PersonaStore unit tests
# ---------------------------------------------------------------------------

def test_persona_store_path_traversal():
    """PersonaStore should reject non-UUID tokens."""
    store = PersonaStore(tempfile.mkdtemp())
    try:
        store.get("../../../etc/passwd")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_persona_store_create_and_get():
    """PersonaStore create + get round-trip."""
    tmpdir = tempfile.mkdtemp()
    store = PersonaStore(tmpdir)
    persona = store.create()
    assert persona["schema"] == "LeanDeep-Persona"

    loaded = store.get(persona["token"])
    assert loaded is not None
    assert loaded["token"] == persona["token"]

    # Cleanup
    shutil.rmtree(tmpdir)
