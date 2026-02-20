#!/usr/bin/env python3
"""
VAD Enrichment Tool for LeanDeep Marker System.

Computes Valence-Arousal-Dominance (VAD) estimates and effect_on_state deltas
for ATO and SEM markers using rules-based mapping from ld5_family, tags, frame,
description, and ID prefix.

Reads from:  build/markers_normalized/marker_registry.json
Writes to:   build/markers_rated/{1_approved,2_good}/{ATO,SEM}/*.yaml

Usage:
    python3 tools/enrich_vad.py              # dry-run (default), print stats
    python3 tools/enrich_vad.py --apply      # write VAD to source YAML files
    python3 tools/enrich_vad.py --stats      # print distribution tables only
"""

import argparse
import json
import sys
from pathlib import Path
from collections import defaultdict

from ruamel.yaml import YAML

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO / "build" / "markers_normalized" / "marker_registry.json"
RATED_DIR = REPO / "build" / "markers_rated"
TIER_MAP = {1: "1_approved", 2: "2_good"}

# ---------------------------------------------------------------------------
# YAML setup (matches project convention: ruamel.yaml v0.19.1)
# ---------------------------------------------------------------------------

yaml_rw = YAML()
yaml_rw.preserve_quotes = True
yaml_rw.allow_duplicate_keys = True
yaml_rw.default_flow_style = None
yaml_rw.width = 200
yaml_rw.allow_unicode = True

# ---------------------------------------------------------------------------
# Family classification for ATO/SEM markers
# (Mirrors the CLU rules from enrich_ld5.py, extended to ATO/SEM scope)
# ---------------------------------------------------------------------------

FAMILY_RULES = [
    # CONFLICT family
    (["CONFLICT", "ESCALATION", "HEATED", "TOXICITY", "HOSTILE", "GASLIGHTING",
      "GOTTMAN", "DESTRUCTIVE", "OFFENSIVE", "DEAD_KNOCK", "PREEMPTIVE_VICTIM",
      "COVERT_RESPONSIBILITY", "GOALPOST", "MINIMIZATION", "CIRCULAR_REASONING",
      "SUPERIORITY", "CONTROL_PATTERN", "DIGITAL_MANIPULATION", "PSYCHOLOGICAL_DIGITAL",
      "BLAME", "ACCUSATION", "CRITICISM", "ATTACK", "STONEWALLING", "CONTEMPT",
      "DEVALUING", "DEFENSIVENESS", "REBUTTAL", "BURDEN_SHIFT", "COMPARISON_MANIPULATION",
      "THREAT", "ULTIMATUM", "MANIPULATION", "DOUBLE_BIND", "GATEKEEPING",
      "FORMAT_POLICING", "COMPETITIVE", "AGGRESSIVE", "COLD_LABEL"],
     "CONFLICT"),

    # GRIEF family
    (["GRIEF", "EMPTINESS", "SHUTDOWN", "DISSOCIATION", "DYSREGULATION",
      "RUMINATION", "SHAME", "NEEDINESS_GUILT", "DEPRESSION", "SADNESS",
      "SUFFERING", "PAIN", "NEGATIVE_SELF", "FLAT", "APATHETIC", "OVERWHELM",
      "ABANDONMENT", "FEAR", "ANXIETY", "ISOLATION", "WITHDRAWAL", "LONELINESS",
      "HELPLESS", "VULNERABILITY"],
     "GRIEF"),

    # SUPPORT family
    (["SUPPORT", "REPAIR", "BINDING", "SUSTAINED_CONTACT", "POSITIVE_AFFECT",
      "PRESENCE_BINDING", "TRUST", "TECH_REPAIR", "AGREE_TO_DISAGREE",
      "VALUE_REFRAME", "FRIENDSHIP", "FLIRTING", "INTIMACY", "SECRET_BONDING",
      "DRIFT_TO_PRESENCE", "SYMBOLIC_SLOW", "NARRATIVE_DEEPENING",
      "EMPATHY", "COMPASSION", "CARE", "POSITIVE_REGARD", "DEESCALATION",
      "APOLOGY", "COMPROMISE", "ACCEPTANCE", "INCLUSION", "CONNECTION",
      "CONSENSUS", "AFFILIATION", "ENCOURAGEMENT", "HUMOR", "JOY", "GRATITUDE",
      "LOVE", "DEVOTION", "AFFECTION", "ROMANTIC"],
     "SUPPORT"),

    # COMMITMENT family
    (["COMMITMENT", "BUSINESS_READINESS", "FUNDRAISING", "ACHIEVEMENT",
      "POWER_MOTIVE", "SAFETY_MOTIVE", "AUTONOMOUS_FIELD",
      "DECISION", "ACTION_ORIENT", "BOUNDARY_SET", "BOUNDARY_STRICT",
      "CERTAINTY", "DIRECTIVE", "EXCELLENCE", "INFLUENCE", "LEADERSHIP"],
     "COMMITMENT"),

    # UNCERTAINTY family
    (["UNCERTAINTY", "INCONSISTENCY", "CONTRADICTION", "DISSONANCE",
      "INCONGRUENCE", "MISALIGNMENT", "MISUNDERSTANDING", "TOPIC_DRIFT",
      "MODE_SWITCH", "SOFT_REJECTION", "SUSPICIOUS", "SVT_MESSAGE",
      "AMBIVALENCE", "AMBIVALENZ", "AMBIGUITY", "HESITATION", "AVOIDANCE", "DENIAL",
      "QUESTION", "CONDITION_CUE", "DELAY", "CONTEXT_SWITCH"],
     "UNCERTAINTY"),

    # INTIMACY family (subset of SUPPORT but distinct VAD profile)
    (["INTIMACY", "ROMANTIC", "LOVE", "DEVOTION", "AFFECTION", "FLIRTING"],
     "INTIMACY"),
]


def classify_family(marker_id: str, tags: list, description: str) -> str:
    """Classify an ATO/SEM marker into an ld5_family for VAD computation.

    Priority: check marker ID first, then tags, then description keywords.
    Returns the first matching family, or empty string if unclassified.
    """
    upper = marker_id.upper()

    # Priority overrides: compound words that contain substrings of other
    # families' keywords (e.g. DEESCALATION contains ESCALATION).
    # Check these explicitly before the general loop.
    PRIORITY_OVERRIDES = {
        "DEESCALATION": "SUPPORT",
        "DEESC": "SUPPORT",
    }
    for prefix, family in PRIORITY_OVERRIDES.items():
        if prefix in upper:
            return family

    # Check ID keywords first (strongest signal)
    for keywords, family in FAMILY_RULES:
        for kw in keywords:
            if kw in upper:
                return family

    # Check tags
    tags_upper = " ".join(t.upper() for t in tags)
    for keywords, family in FAMILY_RULES:
        for kw in keywords:
            if kw in tags_upper:
                return family

    # Check description keywords
    desc_upper = description.upper()
    for keywords, family in FAMILY_RULES:
        for kw in keywords:
            if kw in desc_upper:
                return family

    return ""


# ---------------------------------------------------------------------------
# VAD Mapping Tables
# ---------------------------------------------------------------------------

# Family-based VAD base values: {family: (valence, arousal, dominance)}
FAMILY_VAD = {
    "CONFLICT":    (-0.5,  0.8,  0.6),
    "GRIEF":       (-0.6,  0.3,  0.2),
    "SUPPORT":     (+0.3,  0.3,  0.5),
    "COMMITMENT":  (+0.2,  0.3,  0.5),
    "UNCERTAINTY": (-0.2,  0.5,  0.3),
    "INTIMACY":    (+0.4,  0.4,  0.4),
}
FAMILY_VAD_DEFAULT = (0.0, 0.3, 0.5)

# ID prefix overrides: if marker ID contains keyword, use these values as base
# (overrides family base entirely). Checked in order; first match wins.
ID_OVERRIDES = [
    (["JOY", "HUMOR", "GRATITUDE"],              (+0.6,  0.5,  0.5)),
    (["ANGER", "WUT", "RAGE"],                    (-0.6,  0.85, 0.6)),
    (["SADNESS", "DEPRESSION"],                   (-0.7,  0.25, 0.15)),
    (["FEAR", "ANXIETY"],                         (-0.5,  0.7,  0.15)),
    (["LOVE", "DEVOTION", "AFFECTION"],           (+0.5,  0.45, 0.4)),
    (["BLAME", "ACCUSATION"],                     (-0.5,  0.75, 0.7)),
    (["APOLOGY", "REPAIR"],                       (+0.3,  0.2,  0.35)),
    (["GASLIGHT", "MANIPULATION"],                (-0.4,  0.6,  0.8)),
    (["ISOLATION", "WITHDRAWAL"],                 (-0.4,  0.2,  0.2)),
    (["THREAT", "ULTIMATUM"],                     (-0.6,  0.9,  0.85)),
    (["SUPPORT", "ENCOURAGE"],                    (+0.4,  0.35, 0.5)),
    (["GUILT", "SHAME"],                          (-0.5,  0.4,  0.15)),
    (["SUFFERING", "PAIN"],                       (-0.65, 0.5,  0.15)),
    (["HESITATION", "UNCERTAINTY"],               (-0.1,  0.3,  0.25)),
    (["MODAL", "QUESTION", "STRUCTURAL"],         (0.0,   0.2,  0.5)),
]

# Tag/keyword adjustments (applied on top of base)
TAG_ADJUSTMENTS = [
    (["anger", "wut", "aggression"],              (-0.1,  +0.15, +0.1)),
    (["sadness", "trauer", "grief"],              (-0.1,  -0.1,  -0.1)),
    (["fear", "angst", "anxiety"],                (-0.1,  +0.1,  -0.15)),
    (["joy", "freude", "gratitude", "humor"],     (+0.2,  +0.1,  0.0)),
    (["shame", "scham", "guilt"],                 (-0.15, +0.05, -0.2)),
    (["love", "liebe", "devotion"],               (+0.2,  +0.1,  0.0)),
    (["control", "power", "dominance"],           (-0.05, +0.1,  +0.2)),
    (["vulnerability", "helpless"],               (-0.1,  +0.05, -0.2)),
    (["deescalation", "repair", "apology"],       (+0.15, -0.1,  0.0)),
    (["manipulation", "gaslighting"],             (-0.2,  +0.1,  +0.15)),
    (["isolation", "withdrawal"],                 (-0.15, -0.1,  -0.1)),
]


# ---------------------------------------------------------------------------
# Effect-on-state Mapping Tables
# ---------------------------------------------------------------------------

# Family-based effect_on_state: {family: (trust, conflict, deesc)}
FAMILY_EFFECT = {
    "CONFLICT":    (-0.3,  +0.4,  -0.2),
    "GRIEF":       (-0.1,  +0.1,  -0.05),
    "SUPPORT":     (+0.2,  -0.15, +0.2),
    "COMMITMENT":  (+0.25, -0.1,  +0.15),
    "UNCERTAINTY": (-0.1,  +0.1,  -0.05),
    "INTIMACY":    (+0.3,  -0.1,  +0.1),
}
FAMILY_EFFECT_DEFAULT = (0.0, 0.0, 0.0)

# Tag adjustments to effect_on_state
TAG_EFFECT_ADJUSTMENTS = [
    (["manipulation", "gaslighting"],             (-0.2,  +0.2,  -0.15)),
    (["deescalation", "repair", "apology"],       (+0.15, -0.15, +0.2)),
    (["blame", "accusation"],                     (-0.15, +0.2,  -0.1)),
    (["love", "devotion", "affection"],           (+0.15, -0.05, +0.05)),
    (["isolation", "withdrawal"],                 (-0.15, +0.1,  -0.1)),
    (["support", "encourage"],                    (+0.1,  -0.1,  +0.1)),
]


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def _clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def _scan_keywords(keywords: list, search_text: str) -> bool:
    """Check if any keyword from the list appears in the search text."""
    for kw in keywords:
        if kw in search_text:
            return True
    return False


def compute_vad(marker: dict) -> dict:
    """Compute VAD estimate for a marker.

    Algorithm:
      1. Check ID prefix overrides (strongest signal, replaces family base).
      2. If no ID override matched, use family base.
      3. Apply tag/keyword adjustments from tags + description.
      4. Clamp: valence [-1,1], arousal [0,1], dominance [0,1].

    Returns {"valence": float, "arousal": float, "dominance": float}.
    """
    mid = marker.get("id", "").upper()
    family = marker.get("_family", "").upper()
    tags = [t.lower() for t in marker.get("tags", [])]
    desc = marker.get("description", "").lower()
    frame = marker.get("frame", {})

    # Build combined search text for tag adjustments
    frame_signals = frame.get("signal", []) if isinstance(frame.get("signal"), list) else []
    frame_concept = frame.get("concept", "") if isinstance(frame.get("concept"), str) else ""
    frame_pragmatics = frame.get("pragmatics", "") if isinstance(frame.get("pragmatics"), str) else ""
    search_text = " ".join(tags) + " " + desc + " " + " ".join(
        str(s).lower() for s in frame_signals
    ) + " " + frame_concept.lower() + " " + frame_pragmatics.lower()

    # Step 1: Check ID prefix overrides
    v, a, d = None, None, None
    for id_keywords, (ov, oa, od) in ID_OVERRIDES:
        if any(kw in mid for kw in id_keywords):
            v, a, d = ov, oa, od
            break

    # Step 2: If no ID override, use family base
    if v is None:
        v, a, d = FAMILY_VAD.get(family, FAMILY_VAD_DEFAULT)

    # Step 3: Apply tag/keyword adjustments
    for adj_keywords, (dv, da, dd) in TAG_ADJUSTMENTS:
        if _scan_keywords(adj_keywords, search_text):
            v += dv
            a += da
            d += dd

    # Step 4: Clamp
    v = _clamp(v, -1.0, 1.0)
    a = _clamp(a, 0.0, 1.0)
    d = _clamp(d, 0.0, 1.0)

    return {"valence": round(v, 2), "arousal": round(a, 2), "dominance": round(d, 2)}


def compute_effect_on_state(marker: dict) -> dict:
    """Compute effect_on_state for a marker.

    Algorithm:
      1. Use family base for trust/conflict/deesc.
      2. Apply tag adjustments from tags + description + ID.
      3. Clamp all to [-1, 1].

    Returns {"trust": float, "conflict": float, "deesc": float}.
    """
    family = marker.get("_family", "").upper()
    tags = [t.lower() for t in marker.get("tags", [])]
    desc = marker.get("description", "").lower()
    mid = marker.get("id", "").lower()

    search_text = " ".join(tags) + " " + desc + " " + mid

    # Family base
    trust, conflict, deesc = FAMILY_EFFECT.get(family, FAMILY_EFFECT_DEFAULT)

    # Tag adjustments
    for adj_keywords, (dt, dc, dd) in TAG_EFFECT_ADJUSTMENTS:
        if _scan_keywords(adj_keywords, search_text):
            trust += dt
            conflict += dc
            deesc += dd

    # Clamp
    trust = _clamp(trust, -1.0, 1.0)
    conflict = _clamp(conflict, -1.0, 1.0)
    deesc = _clamp(deesc, -1.0, 1.0)

    return {"trust": round(trust, 2), "conflict": round(conflict, 2), "deesc": round(deesc, 2)}


# ---------------------------------------------------------------------------
# YAML file I/O
# ---------------------------------------------------------------------------

def find_yaml_path(marker_id: str, layer: str, rating: int) -> Path | None:
    """Resolve the source YAML path for a marker in build/markers_rated/."""
    tier = TIER_MAP.get(rating)
    if tier is None:
        # Try both tiers
        for t in TIER_MAP.values():
            p = RATED_DIR / t / layer / f"{marker_id}.yaml"
            if p.exists():
                return p
        return None
    p = RATED_DIR / tier / layer / f"{marker_id}.yaml"
    if p.exists():
        return p
    # Fallback: search other tier
    for t in TIER_MAP.values():
        p = RATED_DIR / t / layer / f"{marker_id}.yaml"
        if p.exists():
            return p
    return None


def write_vad_to_yaml(yaml_path: Path, vad: dict, effect: dict) -> bool:
    """Write vad_estimate and effect_on_state fields to a YAML file.

    Returns True if write succeeded, False on error.
    Handles single-document YAML files. Skips array-format files (some CLU
    archetype files store multiple markers in a list).
    """
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml_rw.load(f)
    except Exception as e:
        print(f"  WARNING: Could not read {yaml_path.name}: {e}", file=sys.stderr)
        return False

    # Skip array-format YAML files
    if isinstance(data, list):
        return False

    if data is None:
        return False

    # Write the fields (idempotent: overwrites previous values)
    data["vad_estimate"] = vad
    data["effect_on_state"] = effect

    try:
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml_rw.dump(data, f)
        return True
    except Exception as e:
        print(f"  WARNING: Could not write {yaml_path.name}: {e}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Statistics / Reporting
# ---------------------------------------------------------------------------

def print_summary(enriched: list, skipped: int, errors: int, not_found: int):
    """Print per-family VAD distribution table."""
    if not enriched:
        print("No markers enriched.")
        return

    # Group by family
    by_family = defaultdict(list)
    for item in enriched:
        by_family[item["family"]].append(item)

    header = f"{'Family':<16} {'Count':>5}  {'V mean':>7} {'V range':>12}  {'A mean':>7} {'A range':>12}  {'D mean':>7} {'D range':>12}"
    print("\n" + "=" * 100)
    print("VAD Distribution by Family")
    print("=" * 100)
    print(header)
    print("-" * 100)

    total = 0
    for family in sorted(by_family.keys()):
        items = by_family[family]
        total += len(items)
        vs = [i["vad"]["valence"] for i in items]
        as_ = [i["vad"]["arousal"] for i in items]
        ds = [i["vad"]["dominance"] for i in items]

        v_mean = sum(vs) / len(vs)
        a_mean = sum(as_) / len(as_)
        d_mean = sum(ds) / len(ds)

        print(f"{family:<16} {len(items):>5}  {v_mean:>+7.2f} [{min(vs):+.2f},{max(vs):+.2f}]  "
              f"{a_mean:>7.2f} [{min(as_):.2f},{max(as_):.2f}]  "
              f"{d_mean:>7.2f} [{min(ds):.2f},{max(ds):.2f}]")

    print("-" * 100)
    print(f"{'TOTAL':<16} {total:>5}")
    print()

    # Effect-on-state summary
    print("=" * 80)
    print("Effect-on-State Distribution by Family")
    print("=" * 80)
    header2 = f"{'Family':<16} {'Count':>5}  {'Trust':>7} {'Conflict':>9} {'Deesc':>7}"
    print(header2)
    print("-" * 80)

    for family in sorted(by_family.keys()):
        items = by_family[family]
        ts = [i["effect"]["trust"] for i in items]
        cs = [i["effect"]["conflict"] for i in items]
        ds = [i["effect"]["deesc"] for i in items]

        t_mean = sum(ts) / len(ts)
        c_mean = sum(cs) / len(cs)
        d_mean = sum(ds) / len(ds)

        print(f"{family:<16} {len(items):>5}  {t_mean:>+7.2f} {c_mean:>+9.2f} {d_mean:>+7.2f}")

    print("-" * 80)
    print()

    # Layer breakdown
    layer_counts = defaultdict(int)
    for item in enriched:
        layer_counts[item["layer"]] += 1
    print(f"Layer breakdown: {dict(layer_counts)}")
    print(f"Skipped (CLU/MEMA): {skipped}")
    print(f"YAML not found:     {not_found}")
    print(f"Write errors:       {errors}")
    print(f"Total enriched:     {total}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="VAD Enrichment Tool for LeanDeep Marker System"
    )
    parser.add_argument("--apply", action="store_true",
                        help="Write VAD values to source YAML files (default: dry-run)")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Dry-run mode: compute and print stats without writing (default)")
    parser.add_argument("--stats", action="store_true",
                        help="Print distribution tables only (no file writes)")
    args = parser.parse_args()

    # --apply overrides --dry-run
    if args.apply:
        args.dry_run = False

    # Load registry
    if not REGISTRY_PATH.exists():
        print(f"ERROR: Registry not found: {REGISTRY_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    markers = registry.get("markers", {})
    print(f"Loaded {len(markers)} markers from registry")

    enriched = []
    skipped = 0
    not_found = 0
    errors = 0
    written = 0

    for marker_id, data in markers.items():
        layer = data.get("layer", "")

        # Only enrich ATO and SEM markers
        if layer not in ("ATO", "SEM"):
            skipped += 1
            continue

        # Classify family for this marker
        tags = data.get("tags", [])
        description = data.get("description", "")
        family = classify_family(marker_id, tags, description)

        # Enrich the data dict with family for VAD computation
        data["_family"] = family

        # Compute VAD and effect_on_state
        vad = compute_vad(data)
        effect = compute_effect_on_state(data)

        enriched.append({
            "id": marker_id,
            "layer": layer,
            "family": family or "(none)",
            "vad": vad,
            "effect": effect,
        })

        # Write to YAML if --apply
        if args.apply and not args.stats:
            rating = data.get("rating", 1)
            yaml_path = find_yaml_path(marker_id, layer, rating)
            if yaml_path is None:
                not_found += 1
                if not args.stats:
                    print(f"  SKIP {marker_id}: YAML not found")
            else:
                ok = write_vad_to_yaml(yaml_path, vad, effect)
                if ok:
                    written += 1
                else:
                    errors += 1

    # Print summary
    print_summary(enriched, skipped, errors, not_found)

    if args.apply and not args.stats:
        print(f"\nWrote VAD to {written} YAML files.")
    elif not args.stats:
        print(f"\nDry-run: {len(enriched)} markers would be enriched. Use --apply to write.")


if __name__ == "__main__":
    main()
