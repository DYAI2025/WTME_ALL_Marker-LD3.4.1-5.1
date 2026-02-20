import sys
sys.path.insert(0, ".")

def test_ued_metrics_from_vad_sequence():
    from api.dynamics import compute_ued_metrics
    vad_seq = [
        {"valence": -0.5, "arousal": 0.8, "dominance": 0.3},
        {"valence": -0.3, "arousal": 0.6, "dominance": 0.4},
        {"valence": 0.2, "arousal": 0.3, "dominance": 0.5},
        {"valence": -0.4, "arousal": 0.7, "dominance": 0.2},
        {"valence": 0.1, "arousal": 0.4, "dominance": 0.5},
    ]
    metrics = compute_ued_metrics(vad_seq)
    assert metrics is not None
    assert "home_base" in metrics
    assert "variability" in metrics
    assert "instability" in metrics
    assert "rise_rate" in metrics
    assert "recovery_rate" in metrics
    assert "density" in metrics
    # Home base = mean
    expected_v = round(sum(v["valence"] for v in vad_seq) / 5, 3)
    assert metrics["home_base"]["valence"] == expected_v

def test_ued_too_few_messages():
    from api.dynamics import compute_ued_metrics
    assert compute_ued_metrics([{"valence": 0, "arousal": 0, "dominance": 0}]) is None
    assert compute_ued_metrics([{"valence": 0, "arousal": 0, "dominance": 0}] * 2) is None

def test_ued_density():
    from api.dynamics import compute_ued_metrics
    vad_seq = [
        {"valence": 0.0, "arousal": 0.1, "dominance": 0.5},  # neutral
        {"valence": -0.5, "arousal": 0.8, "dominance": 0.3},  # charged
        {"valence": 0.01, "arousal": 0.15, "dominance": 0.5},  # neutral
    ]
    metrics = compute_ued_metrics(vad_seq)
    assert metrics["density"] == round(1/3, 3)  # 1 of 3 is charged

def test_ued_instability():
    from api.dynamics import compute_ued_metrics
    vad_seq = [
        {"valence": 0.0, "arousal": 0.0, "dominance": 0.5},
        {"valence": 1.0, "arousal": 1.0, "dominance": 0.5},
        {"valence": 0.0, "arousal": 0.0, "dominance": 0.5},
    ]
    metrics = compute_ued_metrics(vad_seq)
    # Mean absolute successive difference: (1.0 + 1.0) / 2 = 1.0
    assert metrics["instability"]["valence"] == 1.0
    assert metrics["instability"]["arousal"] == 1.0

def test_state_indices_basic():
    from api.dynamics import compute_state_indices
    from dataclasses import dataclass, field

    @dataclass
    class MockMarkerDef:
        effect_on_state: dict | None = None

    @dataclass
    class MockDetection:
        marker_id: str = ""

    markers = {
        "ATO_ANGER": MockMarkerDef(effect_on_state={"trust": -0.3, "conflict": 0.4, "deesc": -0.2}),
        "ATO_APOLOGY": MockMarkerDef(effect_on_state={"trust": 0.2, "conflict": -0.2, "deesc": 0.3}),
    }
    detections = [MockDetection(marker_id="ATO_ANGER"), MockDetection(marker_id="ATO_APOLOGY")]

    si = compute_state_indices(detections, markers)
    assert si["trust"] == round(-0.3 + 0.2, 3)
    assert si["conflict"] == round(0.4 + -0.2, 3)
    assert si["deesc"] == round(-0.2 + 0.3, 3)
    assert si["contributing_markers"] == 2

def test_state_indices_clamping():
    from api.dynamics import compute_state_indices
    from dataclasses import dataclass

    @dataclass
    class MockMarkerDef:
        effect_on_state: dict | None = None

    @dataclass
    class MockDetection:
        marker_id: str = ""

    markers = {"M1": MockMarkerDef(effect_on_state={"trust": -0.9, "conflict": 0.9, "deesc": -0.9})}
    detections = [MockDetection(marker_id="M1"), MockDetection(marker_id="M1")]
    si = compute_state_indices(detections, markers)
    assert si["trust"] >= -1.0
    assert si["conflict"] <= 1.0

def test_state_indices_empty():
    from api.dynamics import compute_state_indices
    si = compute_state_indices([], {})
    assert si["trust"] == 0.0
    assert si["conflict"] == 0.0
    assert si["deesc"] == 0.0
    assert si["contributing_markers"] == 0
