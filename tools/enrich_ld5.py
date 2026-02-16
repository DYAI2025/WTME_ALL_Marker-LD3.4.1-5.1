#!/usr/bin/env python3
"""
LeanDeep 5.0 Enrichment: Adds LD5 engine metadata to normalized markers.

Adds:
  - CLU: family classification + multiplier + hypothesis lifecycle defaults
  - MEMA: detect_class inference + ARS config
  - SEM: activation defaults for markers missing them
  - All layers: window/cooldown defaults per LD5 spec

Reads from:  build/markers_normalized/{ATO,SEM,CLU,MEMA}/*.yaml
              build/markers_normalized/marker_registry.json
Writes to:   same files (in-place update)
"""

import json
import sys
from pathlib import Path
from ruamel.yaml import YAML

yaml_rw = YAML()
yaml_rw.default_flow_style = False
yaml_rw.width = 200
yaml_rw.allow_unicode = True

REPO = Path("/Users/benjaminpoersch/Projects/Marker- entbiazed/WTME_ALL_Marker-LD3.4.1-5.1")
NORM_DIR = REPO / "build" / "markers_normalized"
REGISTRY_PATH = NORM_DIR / "marker_registry.json"

# ---------------------------------------------------------------------------
# CLU Family Classification (from ARCHITECTURE_LD5.md §4)
# ---------------------------------------------------------------------------

# Keywords in marker ID that map to a family
CLU_FAMILY_RULES = [
    # CONFLICT family (multiplier 2.0)
    (["CONFLICT", "ESCALATION", "HEATED", "TOXICITY", "HOSTILE", "GASLIGHTING",
      "GOTTMAN", "DESTRUCTIVE", "OFFENSIVE", "DEAD_KNOCK", "PREEMPTIVE_VICTIM",
      "COVERT_RESPONSIBILITY", "GOALPOST", "MINIMIZATION", "CIRCULAR_REASONING",
      "SUPERIORITY", "CONTROL_PATTERN", "DIGITAL_MANIPULATION", "PSYCHOLOGICAL_DIGITAL"],
     "CONFLICT", 2.0),

    # GRIEF family (multiplier 2.0)
    (["GRIEF", "EMPTINESS", "SHUTDOWN", "DISSOCIATION", "DYSREGULATION",
      "RUMINATION", "SHAME", "NEEDINESS_GUILT"],
     "GRIEF", 2.0),

    # SUPPORT family (multiplier 1.75)
    (["SUPPORT", "REPAIR", "BINDING", "SUSTAINED_CONTACT", "POSITIVE_AFFECT",
      "PRESENCE_BINDING", "TRUST", "TECH_REPAIR", "AGREE_TO_DISAGREE",
      "VALUE_REFRAME", "FRIENDSHIP", "FLIRTING", "INTIMACY", "SECRET_BONDING",
      "DRIFT_TO_PRESENCE", "SYMBOLIC_SLOW", "NARRATIVE_DEEPENING"],
     "SUPPORT", 1.75),

    # COMMITMENT family (multiplier 1.5)
    (["COMMITMENT", "BUSINESS_READINESS", "FUNDRAISING", "ACHIEVEMENT_MOTIVE",
      "POWER_MOTIVE", "SAFETY_MOTIVE", "AUTONOMOUS_FIELD"],
     "COMMITMENT", 1.5),

    # UNCERTAINTY family (multiplier 1.5)
    (["UNCERTAINTY", "INCONSISTENCY", "CONTRADICTION", "CONSISTENCY",
      "DISSONANCE", "INCONGRUENCE", "MISALIGNMENT", "MISUNDERSTANDING",
      "TOPIC_DRIFT", "MODE_SWITCH", "SOFT_REJECTION", "SUSPICIOUS",
      "SVT_MESSAGE"],
     "UNCERTAINTY", 1.5),
]

# Persona/Spiral markers get their own family
CLU_PERSONA_KEYWORDS = ["PERSONA", "SPIRAL", "SD_STAGE", "LL_PROFILE",
                        "IDENTITY", "TEMPORAL_IDENTITY", "INDIVIDUATION"]
CLU_INTUITION_KEYWORDS = ["INTUITION"]


def classify_clu_family(marker_id):
    """Classify a CLU marker into its LD5 family."""
    upper = marker_id.upper()

    # Check intuition markers first — they carry the family name in their ID
    if "INTUITION_" in upper:
        suffix = upper.split("INTUITION_", 1)[1]
        for keywords, family, mult in CLU_FAMILY_RULES:
            for kw in keywords:
                if kw in suffix:
                    return family, mult
        # Intuition markers that don't match a rule
        if any(kw in suffix for kw in ["BIAS", "IRONY", "MORALITY", "DIGNITY",
                                        "NARION", "PARASITIC", "SELF_EFFICACY",
                                        "SHUTDOWN"]):
            return "UNCERTAINTY", 1.5
        return "PROCESS", 1.0

    # Persona/spiral system
    if any(kw in upper for kw in CLU_PERSONA_KEYWORDS):
        return "PERSONA", 1.0

    # Check family rules
    for keywords, family, mult in CLU_FAMILY_RULES:
        for kw in keywords:
            if kw in upper:
                return family, mult

    # Analytical/process markers
    if any(kw in upper for kw in ["SCENE_SHIFT", "QA_RIDDLE", "MAXIM",
                                   "AUTHORITY_SHIFT", "EXAMPLE", "RISK_LEVEL",
                                   "INFORMATION", "SIBLING", "FAMILY_HIERARCHY",
                                   "HOUSEHOLD"]):
        return "PROCESS", 1.0

    return "UNCLASSIFIED", 1.0


# ---------------------------------------------------------------------------
# MEMA detect_class inference (from ARCHITECTURE_LD5.md §6)
# ---------------------------------------------------------------------------

def infer_detect_class(marker_id, data):
    """Infer MEMA detect_class from marker ID and existing fields."""
    if data.get("detect_class"):
        return data["detect_class"]

    upper = marker_id.upper()

    # Absence markers → absence_meta
    if "ABSENCE_" in upper:
        return "absence_meta"

    # Trend markers → trend_analysis
    if "TREND" in upper or "DRIFT" in upper or "SPIRAL" in upper:
        return "trend_analysis"

    # Cycle markers → cycle_detection
    if "CYCLE" in upper or "LOOP" in upper or "CASCADE" in upper:
        return "cycle_detection"

    # Pattern markers → pattern_detection
    if "PATTERN" in upper:
        return "pattern_detection"

    # Profile/composite markers → profile_composite
    if "PROFILE" in upper or "MARKER" in upper.split("MEMA_", 1)[-1]:
        return "profile_composite"

    # Archetype roles → archetype_composite
    if any(kw in upper for kw in ["CONTROLLER", "GASLIGHTER", "MEDIATOR",
                                   "MINIMIZER", "RUMINATOR", "MANIPULATIVE"]):
        return "archetype_composite"

    # Complex composites (multi-CLU wechselwirkung)
    if data.get("composed_of") and isinstance(data["composed_of"], list) and len(data["composed_of"]) >= 2:
        return "composite_meta"

    return "composite_meta"


# ---------------------------------------------------------------------------
# Default LD5 fields
# ---------------------------------------------------------------------------

# Hypothesis lifecycle defaults (CLU §4)
HYPOTHESIS_LIFECYCLE = {
    "provisional": {"rule": "AT_LEAST 2 DISTINCT SEMs IN 5 messages"},
    "confirm_window": 10,
    "decay_window": 15,
}

# Cooldown defaults (Bias Protection §5.2)
COOLDOWN_DEFAULTS = {
    "standard": 5,
    "UNCERTAINTY": 4,
}

# ARS config (§6)
ARS_CONFIG = {
    "scale": [0.0, 5.0],
    "decay_lambda": 0.85,
    "decay_unit": "24h",
}


def enrich_sem(marker_id, data):
    """Add LD5 defaults to SEM marker."""
    changes = {}

    # Default activation if missing
    if not data.get("activation"):
        if data.get("composed_of") and isinstance(data["composed_of"], list):
            n = len(data["composed_of"])
            if n >= 2:
                changes["activation"] = {"rule": f"ANY 2 IN 4 messages"}
            else:
                changes["activation"] = {"rule": "ANY 1"}
        else:
            changes["activation"] = {"rule": "ANY 1"}

    # Default scoring if missing
    if not data.get("scoring"):
        changes["scoring"] = {"base": 1.0, "weight": 1.0, "formula": "logistic"}

    # Default window if missing
    if not data.get("window"):
        changes["window"] = {"messages": 4}

    return changes


def enrich_clu(marker_id, data):
    """Add LD5 family, multiplier, and hypothesis lifecycle to CLU marker."""
    changes = {}

    family, multiplier = classify_clu_family(marker_id)
    changes["ld5_family"] = family
    changes["ld5_multiplier"] = multiplier

    # Hypothesis lifecycle for intuition markers
    if "INTUITION_" in marker_id.upper():
        if not data.get("ld5_hypothesis"):
            changes["ld5_hypothesis"] = dict(HYPOTHESIS_LIFECYCLE)

    # Cooldown
    cooldown = COOLDOWN_DEFAULTS.get(family, COOLDOWN_DEFAULTS["standard"])
    changes["ld5_cooldown"] = cooldown

    # Default activation if missing
    if not data.get("activation"):
        changes["activation"] = {
            "rule": "AT_LEAST 2 DISTINCT SEMs IN 5 messages",
            "window": 5
        }

    # Default scoring if missing
    if not data.get("scoring"):
        changes["scoring"] = {"base": 1.0, "weight": 1.0, "multiplier": multiplier}
    elif data.get("scoring") and isinstance(data["scoring"], dict):
        # Add multiplier to existing scoring
        if "multiplier" not in data["scoring"]:
            changes.setdefault("scoring", dict(data["scoring"]))
            changes["scoring"]["multiplier"] = multiplier

    # Default window if missing
    if not data.get("window"):
        changes["window"] = {"messages": 6}

    return changes


def enrich_mema(marker_id, data):
    """Add LD5 detect_class, ARS config to MEMA marker."""
    changes = {}

    # detect_class
    dc = infer_detect_class(marker_id, data)
    if dc and not data.get("detect_class"):
        changes["detect_class"] = dc

    # ARS config
    if not data.get("ld5_ars"):
        changes["ld5_ars"] = dict(ARS_CONFIG)

    # Default activation if missing
    if not data.get("activation"):
        if dc == "absence_meta":
            changes["activation"] = {"rule": "absence_detection", "window": 30}
        else:
            changes["activation"] = {"rule": "composite_trigger", "window": 10}

    # Default scoring if missing
    if not data.get("scoring"):
        changes["scoring"] = {"base": 1.0, "weight": 1.0, "formula": "logistic"}

    # Default window if missing
    if not data.get("window"):
        if dc == "absence_meta":
            changes["window"] = {"messages": 30}
        elif dc == "trend_analysis":
            changes["window"] = {"messages": 20}
        else:
            changes["window"] = {"messages": 10}

    return changes


def to_plain(obj):
    """Convert to plain Python types."""
    if hasattr(obj, "items"):
        return {str(k): to_plain(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [to_plain(i) for i in obj]
    elif obj is None:
        return None
    else:
        return obj


def main():
    # Load registry
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    stats = {"sem": 0, "clu": 0, "mema": 0, "unchanged": 0}
    family_dist = {}

    for marker_id, data in registry["markers"].items():
        layer = data.get("layer", "")
        changes = {}

        if layer == "SEM":
            changes = enrich_sem(marker_id, data)
            if changes:
                stats["sem"] += 1
        elif layer == "CLU":
            changes = enrich_clu(marker_id, data)
            if changes:
                stats["clu"] += 1
                fam = changes.get("ld5_family", "?")
                family_dist[fam] = family_dist.get(fam, 0) + 1
        elif layer == "MEMA":
            changes = enrich_mema(marker_id, data)
            if changes:
                stats["mema"] += 1
        else:
            stats["unchanged"] += 1
            continue

        if not changes:
            stats["unchanged"] += 1
            continue

        # Apply changes to registry
        for k, v in changes.items():
            data[k] = v

        # Write updated YAML
        out_dir = NORM_DIR / layer
        out_path = out_dir / f"{marker_id}.yaml"
        if out_path.exists():
            with open(out_path, "r", encoding="utf-8") as f:
                yaml_data = yaml_rw.load(f) or {}

            for k, v in changes.items():
                yaml_data[k] = v

            with open(out_path, "w", encoding="utf-8") as f:
                yaml_rw.dump(to_plain(yaml_data), f)

    # Update registry version
    registry["version"] = "5.1-LD5"
    registry["ld5_engine"] = {
        "ewma": {"alpha": 0.2, "green": 0.70, "yellow": 0.50, "red_below": 0.50},
        "ars": ARS_CONFIG,
        "bias_protection": {
            "distinct_sems": True,
            "cooldown_standard": 5,
            "cooldown_uncertainty": 4,
        },
        "hypothesis_lifecycle": HYPOTHESIS_LIFECYCLE,
        "families": {
            "CONFLICT": {"multiplier": 2.0, "priority": "critical"},
            "GRIEF": {"multiplier": 2.0, "priority": "critical"},
            "SUPPORT": {"multiplier": 1.75, "priority": "medium-high"},
            "COMMITMENT": {"multiplier": 1.5, "priority": "process"},
            "UNCERTAINTY": {"multiplier": 1.5, "priority": "ambivalence"},
            "PERSONA": {"multiplier": 1.0, "priority": "developmental"},
            "PROCESS": {"multiplier": 1.0, "priority": "analytical"},
        },
        "decay_lambda": 0.85,
    }

    # Write updated registry
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    print(f"\n=== LeanDeep 5.0 Enrichment Complete ===")
    print(f"SEM enriched:  {stats['sem']}")
    print(f"CLU enriched:  {stats['clu']}")
    print(f"MEMA enriched: {stats['mema']}")
    print(f"Unchanged:     {stats['unchanged']}")
    print(f"\nCLU Family Distribution:")
    for fam, count in sorted(family_dist.items(), key=lambda x: -x[1]):
        mult = next((m for kws, f, m in CLU_FAMILY_RULES if f == fam), 1.0)
        print(f"  {fam:20s}: {count:3d} (×{mult})")
    print(f"\nRegistry: {REGISTRY_PATH}")


if __name__ == "__main__":
    main()
