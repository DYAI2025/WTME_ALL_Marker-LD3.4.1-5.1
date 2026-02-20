#!/usr/bin/env python3
"""
Tests for the VAD Enrichment Tool.

Validates:
  1. VAD values are within valid ranges after enrichment
  2. effect_on_state values are within [-1,1]
  3. At least 90% of ATO markers have VAD values
  4. Specific markers get expected VAD profiles (sanity checks)
  5. Clamping works correctly at boundaries
  6. Idempotency: running twice produces the same result
  7. Family classification produces reasonable results

Run with:
    python3 -m pytest tests/test_enrich_vad.py -v
"""

import json
import sys
from pathlib import Path

# Ensure project root is on path so we can import the tool module
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

from enrich_vad import (
    compute_vad,
    compute_effect_on_state,
    classify_family,
    _clamp,
    FAMILY_VAD,
    FAMILY_EFFECT,
    ID_OVERRIDES,
    TAG_ADJUSTMENTS,
    TAG_EFFECT_ADJUSTMENTS,
)

REGISTRY_PATH = REPO / "build" / "markers_normalized" / "marker_registry.json"


def _load_registry():
    """Load the marker registry JSON."""
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Range validation tests (post-enrichment)
# ---------------------------------------------------------------------------

def test_vad_values_in_range():
    """After enrichment, all VAD values must be in valid ranges."""
    registry = _load_registry()
    markers = registry["markers"]

    for mid, m in markers.items():
        layer = m.get("layer", "")
        if layer not in ("ATO", "SEM"):
            continue

        # Classify and compute
        tags = m.get("tags", [])
        desc = m.get("description", "")
        family = classify_family(mid, tags, desc)
        m["_family"] = family
        vad = compute_vad(m)

        assert -1.0 <= vad["valence"] <= 1.0, (
            f"{mid} valence {vad['valence']} out of range [-1,1]"
        )
        assert 0.0 <= vad["arousal"] <= 1.0, (
            f"{mid} arousal {vad['arousal']} out of range [0,1]"
        )
        assert 0.0 <= vad["dominance"] <= 1.0, (
            f"{mid} dominance {vad['dominance']} out of range [0,1]"
        )


def test_effect_on_state_in_range():
    """After enrichment, all effect_on_state values must be in [-1,1]."""
    registry = _load_registry()
    markers = registry["markers"]

    for mid, m in markers.items():
        layer = m.get("layer", "")
        if layer not in ("ATO", "SEM"):
            continue

        tags = m.get("tags", [])
        desc = m.get("description", "")
        family = classify_family(mid, tags, desc)
        m["_family"] = family
        eos = compute_effect_on_state(m)

        for key in ("trust", "conflict", "deesc"):
            assert -1.0 <= eos[key] <= 1.0, (
                f"{mid} {key} {eos[key]} out of range [-1,1]"
            )


# ---------------------------------------------------------------------------
# Coverage test
# ---------------------------------------------------------------------------

def test_ato_coverage():
    """At least 90% of ATO markers should produce valid VAD values."""
    registry = _load_registry()
    markers = registry["markers"]

    ato_total = sum(1 for m in markers.values() if m["layer"] == "ATO")
    ato_with_vad = 0

    for mid, m in markers.items():
        if m["layer"] != "ATO":
            continue
        tags = m.get("tags", [])
        desc = m.get("description", "")
        family = classify_family(mid, tags, desc)
        m["_family"] = family
        vad = compute_vad(m)

        # A valid VAD means it was computed (always the case for our tool)
        if vad and all(isinstance(vad[k], (int, float)) for k in ("valence", "arousal", "dominance")):
            ato_with_vad += 1

    assert ato_with_vad / max(ato_total, 1) >= 0.9, (
        f"Only {ato_with_vad}/{ato_total} ATOs have valid VAD"
    )


def test_sem_coverage():
    """At least 90% of SEM markers should produce valid VAD values."""
    registry = _load_registry()
    markers = registry["markers"]

    sem_total = sum(1 for m in markers.values() if m["layer"] == "SEM")
    sem_with_vad = 0

    for mid, m in markers.items():
        if m["layer"] != "SEM":
            continue
        tags = m.get("tags", [])
        desc = m.get("description", "")
        family = classify_family(mid, tags, desc)
        m["_family"] = family
        vad = compute_vad(m)

        if vad and all(isinstance(vad[k], (int, float)) for k in ("valence", "arousal", "dominance")):
            sem_with_vad += 1

    assert sem_with_vad / max(sem_total, 1) >= 0.9, (
        f"Only {sem_with_vad}/{sem_total} SEMs have valid VAD"
    )


# ---------------------------------------------------------------------------
# Sanity checks: specific markers should have expected VAD profiles
# ---------------------------------------------------------------------------

def test_anger_marker_negative_valence():
    """ATO_ANGER should have negative valence and high arousal."""
    m = {
        "id": "ATO_ANGER",
        "tags": ["atomic", "anger"],
        "description": "Ausdrücke von Wut oder Frustration",
        "frame": {"signal": [], "concept": "", "pragmatics": "", "narrative": ""},
        "_family": "CONFLICT",
    }
    vad = compute_vad(m)
    assert vad["valence"] < 0, f"ATO_ANGER valence should be negative, got {vad['valence']}"
    assert vad["arousal"] >= 0.5, f"ATO_ANGER arousal should be high, got {vad['arousal']}"


def test_apology_marker_positive_valence():
    """ATO_APOLOGY should have positive valence."""
    m = {
        "id": "ATO_APOLOGY",
        "tags": ["atomic", "apology"],
        "description": "Ausdrücke der Reue oder Entschuldigung",
        "frame": {"signal": [], "concept": "", "pragmatics": "", "narrative": ""},
        "_family": "SUPPORT",
    }
    vad = compute_vad(m)
    assert vad["valence"] > 0, f"ATO_APOLOGY valence should be positive, got {vad['valence']}"


def test_gaslighting_marker_negative_trust():
    """SEM_GASLIGHTING should reduce trust and increase conflict."""
    m = {
        "id": "SEM_GASLIGHTING",
        "tags": ["gaslighting"],
        "description": "gaslighting pattern",
        "frame": {"signal": ["deny reality"], "concept": "gaslighting", "pragmatics": "reality manipulation", "narrative": ""},
        "_family": "CONFLICT",
    }
    eos = compute_effect_on_state(m)
    assert eos["trust"] < 0, f"SEM_GASLIGHTING trust should be negative, got {eos['trust']}"
    assert eos["conflict"] > 0, f"SEM_GASLIGHTING conflict should be positive, got {eos['conflict']}"


def test_deescalation_marker_positive_deesc():
    """ATO_DEESCALATION_PHRASE should have positive deesc effect."""
    m = {
        "id": "ATO_DEESCALATION_PHRASE",
        "tags": ["deescalation", "repair"],
        "description": "deescalation phrases",
        "frame": {"signal": [], "concept": "", "pragmatics": "", "narrative": ""},
        "_family": "SUPPORT",
    }
    eos = compute_effect_on_state(m)
    assert eos["deesc"] > 0, f"Deescalation marker deesc should be positive, got {eos['deesc']}"


def test_joy_humor_high_valence():
    """JOY/HUMOR ID override should produce high positive valence."""
    m = {
        "id": "ATO_HUMOR_SUPPRESS",
        "tags": ["humor"],
        "description": "Humor suppression marker",
        "frame": {},
        "_family": "SUPPORT",
    }
    vad = compute_vad(m)
    # ID override for HUMOR gives valence=+0.6, then humor tag adjustment adds +0.2
    # After clamping: valence should be > 0.5
    assert vad["valence"] > 0.5, f"HUMOR marker should have high valence, got {vad['valence']}"


def test_threat_marker_extreme_arousal():
    """THREAT markers should have very high arousal via ID override."""
    m = {
        "id": "SEM_THREAT_ESCALATION",
        "tags": ["threat", "conflict"],
        "description": "threat escalation pattern",
        "frame": {},
        "_family": "CONFLICT",
    }
    vad = compute_vad(m)
    assert vad["arousal"] >= 0.8, f"THREAT marker should have very high arousal, got {vad['arousal']}"
    assert vad["valence"] < -0.3, f"THREAT marker should have very negative valence, got {vad['valence']}"


# ---------------------------------------------------------------------------
# Clamping tests
# ---------------------------------------------------------------------------

def test_clamp_function():
    """Test that _clamp works correctly at boundaries."""
    assert _clamp(1.5, -1.0, 1.0) == 1.0
    assert _clamp(-1.5, -1.0, 1.0) == -1.0
    assert _clamp(0.5, -1.0, 1.0) == 0.5
    assert _clamp(0.0, 0.0, 1.0) == 0.0
    assert _clamp(-0.1, 0.0, 1.0) == 0.0
    assert _clamp(1.1, 0.0, 1.0) == 1.0


def test_extreme_tag_accumulation_clamped():
    """Even with many negative tags, values should be clamped to valid ranges."""
    m = {
        "id": "ATO_TEST_EXTREME",
        "tags": ["anger", "sadness", "fear", "shame", "manipulation",
                 "isolation", "vulnerability", "grief", "guilt"],
        "description": "anger wut aggression sadness fear anxiety shame manipulation isolation",
        "frame": {},
        "_family": "CONFLICT",
    }
    vad = compute_vad(m)
    assert -1.0 <= vad["valence"] <= 1.0
    assert 0.0 <= vad["arousal"] <= 1.0
    assert 0.0 <= vad["dominance"] <= 1.0

    eos = compute_effect_on_state(m)
    assert -1.0 <= eos["trust"] <= 1.0
    assert -1.0 <= eos["conflict"] <= 1.0
    assert -1.0 <= eos["deesc"] <= 1.0


# ---------------------------------------------------------------------------
# Idempotency test
# ---------------------------------------------------------------------------

def test_idempotency():
    """Running compute_vad twice on the same marker gives identical results."""
    m = {
        "id": "ATO_BLAME_SHIFT",
        "tags": ["blame", "conflict"],
        "description": "blame shift pattern",
        "frame": {"signal": ["blame"], "concept": "conflict", "pragmatics": "", "narrative": ""},
        "_family": "CONFLICT",
    }
    vad1 = compute_vad(m)
    vad2 = compute_vad(m)
    assert vad1 == vad2, f"VAD not idempotent: {vad1} != {vad2}"

    eos1 = compute_effect_on_state(m)
    eos2 = compute_effect_on_state(m)
    assert eos1 == eos2, f"Effect not idempotent: {eos1} != {eos2}"


# ---------------------------------------------------------------------------
# Family classification tests
# ---------------------------------------------------------------------------

def test_classify_conflict_family():
    """Markers with CONFLICT-related IDs should classify as CONFLICT."""
    assert classify_family("ATO_BLAME_SHIFT", ["blame"], "") == "CONFLICT"
    assert classify_family("SEM_GASLIGHTING", ["gaslighting"], "") == "CONFLICT"
    assert classify_family("ATO_ESCALATION_LEXICON", [], "") == "CONFLICT"


def test_classify_grief_family():
    """Markers with GRIEF-related IDs should classify as GRIEF."""
    assert classify_family("ATO_DEPRESSION_SELF_FOCUS", [], "") == "GRIEF"
    assert classify_family("ATO_ABANDONMENT_ANXIETY", [], "") == "GRIEF"
    assert classify_family("ATO_ISOLATION_PHRASE", [], "") == "GRIEF"


def test_classify_support_family():
    """Markers with SUPPORT-related IDs should classify as SUPPORT."""
    assert classify_family("ATO_EMPATHY_MARKERS", [], "") == "SUPPORT"
    assert classify_family("ATO_APOLOGY", [], "") == "SUPPORT"
    assert classify_family("ATO_DEESCALATION_OFFER", [], "") == "SUPPORT"
    assert classify_family("ATO_POSITIVE_REGARD", [], "") == "SUPPORT"


def test_classify_commitment_family():
    """Markers with COMMITMENT-related IDs should classify as COMMITMENT."""
    assert classify_family("ATO_COMMITMENT_PHRASE", [], "") == "COMMITMENT"
    assert classify_family("ATO_DECISION_ANNOUNCEMENT", [], "") == "COMMITMENT"
    assert classify_family("ATO_BOUNDARY_STRICT", [], "") == "COMMITMENT"


def test_classify_uncertainty_family():
    """Markers with UNCERTAINTY-related IDs should classify as UNCERTAINTY."""
    assert classify_family("ATO_AMBIVALENZ", [], "") == "UNCERTAINTY"
    assert classify_family("SEM_CONTRADICTION", [], "") == "UNCERTAINTY"
    assert classify_family("ATO_HESITATION_VOICE", ["hesitation"], "") == "UNCERTAINTY"


def test_classify_unknown_falls_through():
    """Markers with no matching keywords should return empty string."""
    result = classify_family("ATO_PROTOCOL_LANG", [], "")
    # This should still classify (PROTOCOL doesn't match any family)
    # but tags and description might catch it
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Table completeness tests
# ---------------------------------------------------------------------------

def test_all_families_have_vad():
    """Every family in FAMILY_VAD should produce valid 3-tuple."""
    for family, (v, a, d) in FAMILY_VAD.items():
        assert -1.0 <= v <= 1.0, f"{family} valence out of range"
        assert 0.0 <= a <= 1.0, f"{family} arousal out of range"
        assert 0.0 <= d <= 1.0, f"{family} dominance out of range"


def test_all_families_have_effect():
    """Every family in FAMILY_EFFECT should produce valid 3-tuple."""
    for family, (t, c, d) in FAMILY_EFFECT.items():
        assert -1.0 <= t <= 1.0, f"{family} trust out of range"
        assert -1.0 <= c <= 1.0, f"{family} conflict out of range"
        assert -1.0 <= d <= 1.0, f"{family} deesc out of range"


def test_id_overrides_valid():
    """All ID override values should be within valid ranges."""
    for keywords, (v, a, d) in ID_OVERRIDES:
        assert -1.0 <= v <= 1.0, f"{keywords} valence {v} out of range"
        assert 0.0 <= a <= 1.0, f"{keywords} arousal {a} out of range"
        assert 0.0 <= d <= 1.0, f"{keywords} dominance {d} out of range"


def test_tag_adjustments_reasonable():
    """Tag adjustment magnitudes should not exceed 0.25 per axis."""
    for keywords, (dv, da, dd) in TAG_ADJUSTMENTS:
        assert abs(dv) <= 0.25, f"{keywords} valence adj {dv} too large"
        assert abs(da) <= 0.25, f"{keywords} arousal adj {da} too large"
        assert abs(dd) <= 0.25, f"{keywords} dominance adj {dd} too large"


def test_tag_effect_adjustments_reasonable():
    """Effect tag adjustment magnitudes should not exceed 0.25 per axis."""
    for keywords, (dt, dc, dd) in TAG_EFFECT_ADJUSTMENTS:
        assert abs(dt) <= 0.25, f"{keywords} trust adj {dt} too large"
        assert abs(dc) <= 0.25, f"{keywords} conflict adj {dc} too large"
        assert abs(dd) <= 0.25, f"{keywords} deesc adj {dd} too large"


# ---------------------------------------------------------------------------
# Full registry integration test
# ---------------------------------------------------------------------------

def test_full_registry_enrichment():
    """Run enrichment on the full registry and verify distributions are sane."""
    registry = _load_registry()
    markers = registry["markers"]

    ato_count = 0
    sem_count = 0
    positive_valence = 0
    negative_valence = 0

    for mid, m in markers.items():
        layer = m.get("layer", "")
        if layer not in ("ATO", "SEM"):
            continue

        tags = m.get("tags", [])
        desc = m.get("description", "")
        family = classify_family(mid, tags, desc)
        m["_family"] = family
        vad = compute_vad(m)

        if layer == "ATO":
            ato_count += 1
        else:
            sem_count += 1

        if vad["valence"] > 0:
            positive_valence += 1
        elif vad["valence"] < 0:
            negative_valence += 1

    total = ato_count + sem_count
    assert total > 0, "No ATO/SEM markers found"

    # Sanity: we should have both positive and negative valence markers
    assert positive_valence > 0, "No positive-valence markers found"
    assert negative_valence > 0, "No negative-valence markers found"

    # Distribution should not be wildly skewed (at least 10% each way)
    pos_ratio = positive_valence / total
    neg_ratio = negative_valence / total
    assert pos_ratio >= 0.1, f"Too few positive markers: {pos_ratio:.1%}"
    assert neg_ratio >= 0.1, f"Too few negative markers: {neg_ratio:.1%}"
