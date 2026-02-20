import sys
sys.path.insert(0, ".")

def test_analyze_returns_vad():
    """analyze_text should return per-detection VAD when markers have vad_estimate."""
    from api.engine import MarkerEngine
    eng = MarkerEngine()
    eng.load()
    result = eng.analyze_text("Ich bin so wütend auf dich!", threshold=0.3)
    vad_dets = [d for d in result["detections"] if d.vad is not None]
    assert len(vad_dets) > 0, "Expected at least one detection with VAD"
    for d in vad_dets:
        assert "valence" in d.vad
        assert "arousal" in d.vad
        assert "dominance" in d.vad

def test_analyze_vad_can_be_none():
    """Detections from markers without vad_estimate should have vad=None."""
    from api.engine import MarkerEngine
    eng = MarkerEngine()
    eng.load()
    result = eng.analyze_text("Ich bin so wütend auf dich!", threshold=0.3)
    # At least some detections exist
    assert len(result["detections"]) > 0
    # VAD can be None for markers that don't have vad_estimate
    for d in result["detections"]:
        if d.vad is not None:
            assert isinstance(d.vad, dict)

def test_conversation_returns_message_vad():
    """analyze_conversation should return aggregated VAD per message."""
    from api.engine import MarkerEngine
    eng = MarkerEngine()
    eng.load()
    messages = [
        {"text": "Ich bin so wütend!", "speaker": "A"},
        {"text": "Das tut mir leid.", "speaker": "B"},
        {"text": "Lass uns darüber reden.", "speaker": "A"},
    ]
    result = eng.analyze_conversation(messages, threshold=0.3)
    assert "message_vad" in result
    assert len(result["message_vad"]) == 3
    for mv in result["message_vad"]:
        assert "valence" in mv
        assert "arousal" in mv
        assert "dominance" in mv

def test_conversation_returns_ued_metrics():
    """analyze_conversation with 3+ messages should return UED metrics."""
    from api.engine import MarkerEngine
    eng = MarkerEngine()
    eng.load()
    messages = [
        {"text": "Du bist immer so egoistisch!", "speaker": "A"},
        {"text": "Das stimmt nicht!", "speaker": "B"},
        {"text": "Ich fühle mich so allein.", "speaker": "A"},
        {"text": "Es tut mir leid.", "speaker": "B"},
    ]
    result = eng.analyze_conversation(messages, threshold=0.3)
    assert "ued_metrics" in result
    if result["ued_metrics"] is not None:
        assert "home_base" in result["ued_metrics"]
        assert "variability" in result["ued_metrics"]
        assert "density" in result["ued_metrics"]

def test_conversation_returns_state_indices():
    """analyze_conversation should return state indices."""
    from api.engine import MarkerEngine
    eng = MarkerEngine()
    eng.load()
    messages = [
        {"text": "Du bist schuld an allem!", "speaker": "A"},
        {"text": "Lass uns in Ruhe darüber reden.", "speaker": "B"},
    ]
    result = eng.analyze_conversation(messages, threshold=0.3)
    assert "state_indices" in result
    si = result["state_indices"]
    assert "trust" in si
    assert "conflict" in si
    assert "deesc" in si
    assert "contributing_markers" in si
