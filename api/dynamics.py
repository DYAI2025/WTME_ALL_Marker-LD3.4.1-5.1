"""
Emotion dynamics computation for LeanDeep marker system.

Computes UED (Utterance Emotion Dynamics) metrics from VAD sequences
and relationship state indices from marker effect_on_state annotations.
"""

from __future__ import annotations
import math


def compute_ued_metrics(vad_sequence: list[dict]) -> dict | None:
    """Compute UED metrics from a sequence of per-message VAD values.

    Requires at least 3 messages. Returns None if insufficient data.

    Metrics:
        home_base: Mean valence/arousal/dominance (emotional center of gravity)
        variability: Std deviation of valence/arousal (emotional range)
        instability: Mean absolute successive difference (emotional volatility)
        rise_rate: Avg positive arousal delta after negative valence (escalation tendency)
        recovery_rate: Avg negative arousal delta after arousal peak (calming ability)
        density: Proportion of emotionally charged utterances (|valence|>0.2 or arousal>0.3)
    """
    if len(vad_sequence) < 3:
        return None

    n = len(vad_sequence)
    vals = [v["valence"] for v in vad_sequence]
    aros = [v["arousal"] for v in vad_sequence]
    doms = [v["dominance"] for v in vad_sequence]

    # Home base: mean
    home_base = {
        "valence": round(sum(vals) / n, 3),
        "arousal": round(sum(aros) / n, 3),
        "dominance": round(sum(doms) / n, 3),
    }

    # Variability: std deviation
    def std(xs):
        mean = sum(xs) / len(xs)
        variance = sum((x - mean) ** 2 for x in xs) / len(xs)
        return math.sqrt(variance)

    variability = {
        "valence": round(std(vals), 3),
        "arousal": round(std(aros), 3),
    }

    # Instability: mean absolute successive difference
    val_diffs = [abs(vals[i + 1] - vals[i]) for i in range(n - 1)]
    aro_diffs = [abs(aros[i + 1] - aros[i]) for i in range(n - 1)]
    instability = {
        "valence": round(sum(val_diffs) / len(val_diffs), 3),
        "arousal": round(sum(aro_diffs) / len(aro_diffs), 3),
    }

    # Rise rate: avg positive arousal delta after negative valence messages
    rise_deltas = []
    for i in range(n - 1):
        if vals[i] < -0.1:  # Negative valence message
            delta_a = aros[i + 1] - aros[i]
            if delta_a > 0:  # Arousal rising
                rise_deltas.append(delta_a)
    rise_rate = round(sum(rise_deltas) / max(len(rise_deltas), 1), 3)

    # Recovery rate: avg negative arousal delta after arousal peak
    recovery_deltas = []
    for i in range(1, n - 1):
        if aros[i] > aros[i - 1] and aros[i] > 0.4:  # Local peak above threshold
            delta_a = aros[i + 1] - aros[i]
            if delta_a < 0:  # Arousal dropping (recovery)
                recovery_deltas.append(abs(delta_a))
    recovery_rate = round(sum(recovery_deltas) / max(len(recovery_deltas), 1), 3)

    # Density: proportion of emotionally charged utterances
    charged = sum(1 for v in vad_sequence if abs(v["valence"]) > 0.2 or v["arousal"] > 0.3)
    density = round(charged / n, 3)

    return {
        "home_base": home_base,
        "variability": variability,
        "instability": instability,
        "rise_rate": rise_rate,
        "recovery_rate": recovery_rate,
        "density": density,
    }


def compute_state_indices(detections: list, markers: dict) -> dict:
    """Aggregate effect_on_state from all detections into relationship state indices.

    Args:
        detections: List of Detection objects with marker_id
        markers: Dict of marker_id -> MarkerDef objects

    Returns:
        {trust, conflict, deesc, contributing_markers} clamped to [-1, 1]
    """
    trust = 0.0
    conflict = 0.0
    deesc = 0.0
    count = 0

    for d in detections:
        mdef = markers.get(d.marker_id)
        if mdef and mdef.effect_on_state:
            eos = mdef.effect_on_state
            trust += eos.get("trust", 0)
            conflict += eos.get("conflict", 0)
            deesc += eos.get("deesc", 0)
            count += 1

    return {
        "trust": round(max(-1.0, min(1.0, trust)), 3),
        "conflict": round(max(-1.0, min(1.0, conflict)), 3),
        "deesc": round(max(-1.0, min(1.0, deesc)), 3),
        "contributing_markers": count,
    }
