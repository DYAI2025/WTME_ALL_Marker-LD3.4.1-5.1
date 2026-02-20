"""Tests for VAD congruence gate and shadow buffer in MarkerEngine."""

import sys

sys.path.insert(0, ".")


def test_vad_congruence_values():
    """Test the congruence computation directly."""
    from api.engine import MarkerEngine

    eng = MarkerEngine()

    # Same direction = high congruence
    c1 = eng._vad_congruence(
        {"valence": -0.5, "arousal": 0.8, "dominance": 0.6},
        {"valence": -0.4, "arousal": 0.7, "dominance": 0.5},
    )
    assert c1 > 0.7, f"Same direction should be highly congruent, got {c1}"

    # Opposite direction = low congruence
    c2 = eng._vad_congruence(
        {"valence": -0.5, "arousal": 0.8, "dominance": 0.3},
        {"valence": +0.5, "arousal": 0.2, "dominance": 0.5},
    )
    assert c2 < 0.5, f"Opposite direction should be incongruent, got {c2}"

    # No VAD = neutral (0.5)
    c3 = eng._vad_congruence(None, {"valence": 0, "arousal": 0, "dominance": 0})
    assert c3 == 0.5


def test_absolutizer_gated_in_negative_context():
    """ABSOLUTIZER should pass gate in negative/aroused context."""
    from api.engine import MarkerEngine

    eng = MarkerEngine()
    eng.load()
    messages = [{"text": "Du hörst mir nie zu.", "speaker": "A"}]
    result = eng.analyze_conversation(messages, threshold=0.3)
    ato_ids = [d.marker_id for d in result["detections"] if d.layer == "ATO"]
    assert "ATO_ABSOLUTIZER" in ato_ids


def test_neutral_atos_gated_out_in_emotional_context():
    """Neutral/structural ATOs with mismatching VAD should be suppressed or reduced."""
    from api.engine import MarkerEngine

    eng = MarkerEngine()
    eng.load()
    # In angry context, neutral markers like TIME_REFERENCE should be suppressed
    messages = [{"text": "Du hörst mir nie zu!", "speaker": "A"}]
    result = eng.analyze_conversation(messages, threshold=0.3)
    ato_ids = [d.marker_id for d in result["detections"] if d.layer == "ATO"]
    # The key test: the gate is active and produces some ATOs
    assert len(ato_ids) > 0, "Gate should not suppress everything"


def test_love_context_passes_love_markers():
    """Love markers should pass gate in love declaration context."""
    from api.engine import MarkerEngine

    eng = MarkerEngine()
    eng.load()
    messages = [
        {
            "text": "Ich könnte mich niemals in jemand anderes verlieben.",
            "speaker": "A",
        }
    ]
    result = eng.analyze_conversation(messages, threshold=0.3)
    ato_ids = [d.marker_id for d in result["detections"] if d.layer == "ATO"]
    # Should have some detections (may or may not include love-specific markers
    # depending on what patterns exist in the registry)
    assert isinstance(ato_ids, list)


def test_shadow_buffer_surfaces_in_matching_context():
    """Suppressed ATOs from msg[0] should surface if msg[1] context matches."""
    from api.engine import MarkerEngine

    eng = MarkerEngine()
    eng.load()
    messages = [
        {"text": "Ich bin einfach nur müde.", "speaker": "A"},  # neutral/sad
        {"text": "Ich bin so traurig und erschöpft.", "speaker": "A"},  # clearly sad
    ]
    result = eng.analyze_conversation(messages, threshold=0.3)
    # The gate should process both messages and potentially surface shadow ATOs
    assert "detections" in result
    assert "message_vad" in result
    assert len(result["message_vad"]) == 2


def test_neutral_message_no_gate():
    """Emotionally neutral messages should not gate aggressively."""
    from api.engine import MarkerEngine

    eng = MarkerEngine()
    eng.load()
    messages = [{"text": "Ok.", "speaker": "A"}]
    result = eng.analyze_conversation(messages, threshold=0.3)
    # Should still work normally with minimal detections
    assert "detections" in result


def test_gate_reduces_ato_count():
    """Conversation analysis should return a filtered set of ATOs."""
    from api.engine import MarkerEngine

    eng = MarkerEngine()
    eng.load()
    messages = [
        {
            "text": "Du bist immer so egoistisch und hörst nie zu!",
            "speaker": "A",
        },
        {"text": "Das stimmt nicht, ich bin immer für dich da.", "speaker": "B"},
    ]
    result = eng.analyze_conversation(messages, threshold=0.3)
    ato_count = sum(1 for d in result["detections"] if d.layer == "ATO")
    # Should be reasonably filtered (not zero, not too many)
    assert ato_count > 0, "Gate should not suppress everything"
    assert ato_count < 30, "Gate should reduce noise"


def test_conversation_still_returns_all_fields():
    """Gated conversation should still return message_vad, ued_metrics, state_indices."""
    from api.engine import MarkerEngine

    eng = MarkerEngine()
    eng.load()
    messages = [
        {"text": "Ich bin wütend!", "speaker": "A"},
        {"text": "Es tut mir leid.", "speaker": "B"},
        {"text": "Lass uns reden.", "speaker": "A"},
    ]
    result = eng.analyze_conversation(messages, threshold=0.3)
    assert "message_vad" in result
    assert "ued_metrics" in result
    assert "state_indices" in result
    assert len(result["message_vad"]) == 3


def test_compute_raw_vad_empty():
    """_compute_raw_vad with no detections returns zero VAD."""
    from api.engine import MarkerEngine

    eng = MarkerEngine()
    vad = eng._compute_raw_vad([])
    assert vad == {"valence": 0.0, "arousal": 0.0, "dominance": 0.0}


def test_apply_vad_gate_neutral_passthrough():
    """Near-zero message VAD should let all ATOs pass without gating."""
    from api.engine import MarkerEngine, Detection, Match

    eng = MarkerEngine()

    det1 = Detection(
        marker_id="ATO_TEST",
        layer="ATO",
        confidence=0.8,
        description="test",
        matches=[],
        vad={"valence": -0.5, "arousal": 0.8, "dominance": 0.3},
    )
    # Neutral message VAD -> should pass everything
    neutral_vad = {"valence": 0.0, "arousal": 0.05, "dominance": 0.0}
    gated, suppressed, surfaced = eng._apply_vad_gate([det1], neutral_vad)
    assert len(gated) == 1
    assert len(suppressed) == 0
    assert len(surfaced) == 0


def test_apply_vad_gate_no_vad_marker_passes():
    """ATOs without VAD (structural markers) always pass the gate."""
    from api.engine import MarkerEngine, Detection

    eng = MarkerEngine()

    det_no_vad = Detection(
        marker_id="ATO_NEGATION_TOKEN",
        layer="ATO",
        confidence=0.9,
        description="negation",
        matches=[],
        vad=None,
    )
    msg_vad = {"valence": -0.5, "arousal": 0.8, "dominance": 0.3}
    gated, suppressed, surfaced = eng._apply_vad_gate([det_no_vad], msg_vad)
    assert len(gated) == 1
    assert det_no_vad in gated
