import sys
sys.path.insert(0, ".")

def test_state_indices_from_conversation():
    from api.engine import MarkerEngine
    eng = MarkerEngine()
    eng.load()
    messages = [
        {"text": "Du bist immer so egoistisch!", "speaker": "A"},
        {"text": "Das stimmt nicht, ich tue mein Bestes.", "speaker": "B"},
        {"text": "Lass uns in Ruhe darüber reden.", "speaker": "A"},
    ]
    result = eng.analyze_conversation(messages, threshold=0.3)
    assert "state_indices" in result
    si = result["state_indices"]
    assert "trust" in si and "conflict" in si and "deesc" in si
    assert isinstance(si["contributing_markers"], int)

def test_state_indices_values_bounded():
    """State index values should always be in [-1, 1] range."""
    from api.engine import MarkerEngine
    eng = MarkerEngine()
    eng.load()
    messages = [
        {"text": "Du bist schuld!", "speaker": "A"},
        {"text": "Nein, du bist schuld!", "speaker": "B"},
        {"text": "Immer das gleiche mit dir!", "speaker": "A"},
        {"text": "Ich hasse das!", "speaker": "B"},
        {"text": "Ich auch!", "speaker": "A"},
    ]
    result = eng.analyze_conversation(messages, threshold=0.3)
    si = result["state_indices"]
    assert -1.0 <= si["trust"] <= 1.0
    assert -1.0 <= si["conflict"] <= 1.0
    assert -1.0 <= si["deesc"] <= 1.0

def test_two_message_conversation_no_ued():
    """With only 2 messages, ued_metrics should be None."""
    from api.engine import MarkerEngine
    eng = MarkerEngine()
    eng.load()
    messages = [
        {"text": "Hallo.", "speaker": "A"},
        {"text": "Hallo.", "speaker": "B"},
    ]
    result = eng.analyze_conversation(messages, threshold=0.3)
    assert result["ued_metrics"] is None
    assert "message_vad" in result
    assert len(result["message_vad"]) == 2
