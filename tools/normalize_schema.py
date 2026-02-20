#!/usr/bin/env python3
"""
Schema Normalizer: Unifies all marker YAML variants into a single canonical schema.

INPUT:  build/markers_rated/{1_approved,2_good}/{ATO,SEM,CLU,MEMA}/*.yaml
OUTPUT: build/markers_normalized/{ATO,SEM,CLU,MEMA}/*.yaml
        build/markers_normalized/marker_registry.json

Unified Schema (v5.1):
  id: str                    # e.g. "ATO_ABSOLUTIZER"
  schema: "LeanDeep"
  version: "5.1"
  layer: str                 # ATO | SEM | CLU | MEMA
  lang: str                  # de | en | bilingual
  description: str           # Human-readable purpose
  frame:
    signal: list[str]
    concept: str
    pragmatics: str
    narrative: str
  patterns: list[dict]       # [{type: "regex", value: "...", flags: []}]
  examples:
    positive: list[str]
    negative: list[str]
  tags: list[str]
  rating: int                # 1 or 2 (from quality tier)

  # Optional (preserved when present):
  composed_of: list[str]     # Constituent marker IDs
  requires: dict             # Complex dependency spec (CLU/MEMA)
  activation: dict           # Activation rules
  scoring: dict              # Scoring config
  window: dict               # Window config
  gates: dict                # Gating rules
  ingredients: dict          # Required marker combos (CLU)
  negative_evidence: dict    # Inhibitory markers
  emits: dict                # Index effects
  conflicts_with: list[str]  # Conflicting markers
  detect_class: str          # MEMA detection class
  criteria: dict             # MEMA detection criteria
  semiotic: dict             # Semiotic analysis
  metadata: dict             # Pass-through metadata
"""

import json
import re
import sys
from pathlib import Path
from ruamel.yaml import YAML

yaml_reader = YAML()
yaml_reader.preserve_quotes = True
yaml_reader.allow_duplicate_keys = True

yaml_writer = YAML()
yaml_writer.default_flow_style = False
yaml_writer.width = 200
yaml_writer.allow_unicode = True

REPO = Path("/Users/benjaminpoersch/Projects/Marker- entbiazed/WTME_ALL_Marker-LD3.4.1-5.1")
INPUT_DIR = REPO / "build" / "markers_rated"
OUTPUT_DIR = REPO / "build" / "markers_normalized"
REGISTRY_PATH = OUTPUT_DIR / "marker_registry.json"

# Create output dirs
for layer in ["ATO", "SEM", "CLU", "MEMA"]:
    (OUTPUT_DIR / layer).mkdir(parents=True, exist_ok=True)


def infer_layer(marker_id):
    """Infer layer from marker ID prefix."""
    for prefix in ["ATO_", "SEM_", "CLU_", "MEMA_"]:
        if marker_id.startswith(prefix):
            return prefix.rstrip("_")
    return "UNKNOWN"


def normalize_id(data, filename):
    """Extract canonical marker ID."""
    mid = data.get("id") or data.get("name") or filename.replace(".yaml", "")
    return str(mid).strip()


def normalize_lang(data, examples):
    """Detect language from data and examples."""
    lang = data.get("lang", "")
    if lang and lang in ("de", "en"):
        return lang

    # Check if examples have both _de and _en keys
    raw_ex = data.get("examples", {})
    if isinstance(raw_ex, dict):
        has_de = any(k.endswith("_de") for k in raw_ex.keys())
        has_en = any(k.endswith("_en") for k in raw_ex.keys())
        if has_de and has_en:
            return "bilingual"
        if has_de:
            return "de"

    # Check languages field
    langs = data.get("languages", [])
    if isinstance(langs, list):
        if "de" in langs and "en" in langs:
            return "bilingual"
        if "de" in langs:
            return "de"
        if "en" in langs:
            return "en"

    # Heuristic from examples content
    all_text = " ".join(str(e) for e in examples.get("positive", [])[:3])
    if re.search(r'\b(ich|du|wir|nicht|und|das|ist|ein|der|die|mein)\b', all_text, re.IGNORECASE):
        return "de"
    return "en"


def normalize_description(data):
    """Extract description from various fields."""
    desc = data.get("description") or data.get("intent") or data.get("meaning") or ""
    return str(desc).strip()


def normalize_frame(data):
    """Normalize frame to consistent structure."""
    frame = data.get("frame", {})
    if not frame or not isinstance(frame, dict):
        return {"signal": [], "concept": "", "pragmatics": "", "narrative": ""}

    signal = frame.get("signal", [])
    if isinstance(signal, str):
        signal = [signal]
    elif signal is None:
        signal = []
    signal = [str(s) for s in signal]

    return {
        "signal": signal,
        "concept": str(frame.get("concept", "") or ""),
        "pragmatics": str(frame.get("pragmatics", "") or ""),
        "narrative": str(frame.get("narrative", "") or ""),
    }


def normalize_patterns(data):
    """Normalize all pattern variants to unified format."""
    result = []

    # Check 'pattern' field (singular)
    pattern = data.get("pattern")
    if pattern:
        if isinstance(pattern, list):
            for p in pattern:
                if isinstance(p, str):
                    result.append({"type": "regex", "value": p})
                elif isinstance(p, dict):
                    result.append(dict(p))
        elif isinstance(pattern, dict):
            # pattern: {regex: "...", flags: [...]}
            regex = pattern.get("regex", "")
            flags = pattern.get("flags", [])
            if regex:
                result.append({"type": "regex", "value": str(regex), "flags": list(flags) if flags else []})
        elif isinstance(pattern, str):
            result.append({"type": "regex", "value": pattern})

    # Check 'patterns' field (plural)
    patterns = data.get("patterns")
    if patterns and isinstance(patterns, list):
        for p in patterns:
            if isinstance(p, dict):
                result.append(dict(p))
            elif isinstance(p, str):
                result.append({"type": "regex", "value": p})

    return result


def normalize_examples(data):
    """Normalize examples to {positive: [...], negative: [...]}."""
    raw = data.get("examples")
    positive = []
    negative = []

    if raw is None:
        pass
    elif isinstance(raw, dict):
        # Collect positives from all keys
        for key in ["positive", "positive_de", "positive_en", "pos"]:
            val = raw.get(key, [])
            if val:
                positive.extend([str(v).strip() for v in val if v])

        # Collect negatives from all keys
        for key in ["negative", "negative_de", "negative_en", "neg"]:
            val = raw.get(key, [])
            if val:
                negative.extend([str(v).strip() for v in val if v])
    elif isinstance(raw, list):
        # Flat list = all positives
        positive = [str(e).strip() for e in raw if e]

    # Also check top-level 'negatives' field
    top_neg = data.get("negatives")
    if top_neg and isinstance(top_neg, list):
        negative.extend([str(n).strip() for n in top_neg if n])

    # Deduplicate while preserving order
    positive = list(dict.fromkeys(positive))
    negative = list(dict.fromkeys(negative))

    return {"positive": positive, "negative": negative}


def normalize_tags(data):
    """Normalize tags to flat list of strings."""
    tags = data.get("tags", [])
    if isinstance(tags, list):
        return [str(t).strip() for t in tags if t]
    elif isinstance(tags, str):
        return [t.strip() for t in tags.split(",") if t.strip()]
    return []


def normalize_composed_of(data):
    """Extract composition info."""
    comp = data.get("composed_of") or data.get("ingredients")
    if isinstance(comp, list):
        return [str(c) for c in comp]
    if isinstance(comp, dict):
        # ingredients: {require: [...], k_of_n: {...}}
        return comp
    return None


def normalize_marker(data, filename, tier):
    """Normalize a single marker to unified schema."""
    marker_id = normalize_id(data, filename)
    layer = infer_layer(marker_id)
    examples = normalize_examples(data)

    normalized = {
        "id": marker_id,
        "schema": "LeanDeep",
        "version": "5.1",
        "layer": layer,
        "lang": normalize_lang(data, examples),
        "description": normalize_description(data),
        "frame": normalize_frame(data),
        "patterns": normalize_patterns(data),
        "examples": examples,
        "tags": normalize_tags(data),
        "rating": 1 if tier == "1_approved" else 2,
    }

    # Optional fields - preserve when present
    comp = normalize_composed_of(data)
    if comp:
        normalized["composed_of"] = comp

    for field in ["requires", "activation", "scoring", "window", "gates",
                   "ingredients", "negative_evidence", "emits", "conflicts_with",
                   "detect_class", "criteria", "gating_conflict", "policy",
                   "absence_sets", "emit", "evidence_capture", "fire_when",
                   "semiotic", "temperature_semantics", "meta_logic",
                   "compositionality", "vad_estimate", "effect_on_state"]:
        val = data.get(field)
        if val is not None:
            normalized[field] = val

    # Metadata: merge metadata + meta
    meta = {}
    if data.get("metadata"):
        meta.update(dict(data["metadata"]) if hasattr(data["metadata"], "items") else {})
    if data.get("meta"):
        meta["source"] = dict(data["meta"]) if hasattr(data["meta"], "items") else data["meta"]
    if data.get("label"):
        meta["label"] = str(data["label"])
    if meta:
        normalized["metadata"] = meta

    return normalized


def to_plain_dict(obj):
    """Convert ruamel.yaml objects to plain Python dicts for JSON serialization."""
    if hasattr(obj, "items"):
        return {str(k): to_plain_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_plain_dict(i) for i in obj]
    elif obj is None:
        return None
    else:
        return obj


def main():
    stats = {"total": 0, "success": 0, "errors": 0, "per_layer": {}, "per_tier": {}}
    registry = {}

    for tier in ["1_approved", "2_good"]:
        tier_dir = INPUT_DIR / tier
        if not tier_dir.exists():
            continue

        for layer_dir in sorted(tier_dir.iterdir()):
            if not layer_dir.is_dir():
                continue
            layer = layer_dir.name

            for yaml_file in sorted(layer_dir.glob("*.yaml")):
                stats["total"] += 1
                try:
                    with open(yaml_file, "r", encoding="utf-8") as f:
                        data = yaml_reader.load(f)

                    if data is None:
                        stats["errors"] += 1
                        print(f"SKIP (empty): {yaml_file.name}", file=sys.stderr)
                        continue

                    # Handle composite files (YAML array of markers)
                    markers_to_process = []
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get("id"):
                                markers_to_process.append(item)
                        if not markers_to_process:
                            stats["errors"] += 1
                            print(f"SKIP (list without ids): {yaml_file.name}", file=sys.stderr)
                            continue
                    else:
                        markers_to_process = [data]

                    for marker_data in markers_to_process:
                        normalized = normalize_marker(marker_data, yaml_file.name, tier)
                        marker_id = normalized["id"]
                        marker_layer = normalized["layer"]

                        # Write normalized YAML
                        out_layer = marker_layer if marker_layer != "UNKNOWN" else layer
                        out_dir = OUTPUT_DIR / out_layer
                        out_dir.mkdir(parents=True, exist_ok=True)
                        out_path = out_dir / f"{marker_id}.yaml"
                        with open(out_path, "w", encoding="utf-8") as f:
                            yaml_writer.dump(to_plain_dict(normalized), f)

                        # Add to registry (JSON-safe)
                        registry[marker_id] = to_plain_dict(normalized)

                        stats["success"] += 1
                        stats["per_layer"][out_layer] = stats["per_layer"].get(out_layer, 0) + 1
                        stats["per_tier"][tier] = stats["per_tier"].get(tier, 0) + 1

                except Exception as e:
                    stats["errors"] += 1
                    print(f"ERROR: {yaml_file.name}: {e}", file=sys.stderr)

                if stats["success"] % 100 == 0 and stats["success"] > 0:
                    print(f"  ...normalized {stats['success']} markers", file=sys.stderr)

    # Write registry JSON
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "schema": "LeanDeep",
            "version": "5.1",
            "total": len(registry),
            "layers": {
                layer: len([m for m in registry.values() if m["layer"] == layer])
                for layer in ["ATO", "SEM", "CLU", "MEMA"]
            },
            "markers": registry,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n=== Schema Normalization Complete ===")
    print(f"Total processed: {stats['total']}")
    print(f"Success: {stats['success']}")
    print(f"Errors: {stats['errors']}")
    print(f"\nPer layer: {stats['per_layer']}")
    print(f"Per tier: {stats['per_tier']}")
    print(f"\nOutput: {OUTPUT_DIR}")
    print(f"Registry: {REGISTRY_PATH} ({len(registry)} markers)")


if __name__ == "__main__":
    main()
