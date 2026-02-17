#!/usr/bin/env python3
"""
Fix broken CLU/MEMA composed_of references.

Strategy:
  1. Strip qualified prefixes (ld34_text_social_grammar.SEM_X → SEM_X)
  2. Strip @annotations (CLU_LL_PROFILE@self → CLU_LL_PROFILE)
  3. Extract marker_ids from dict-format refs ({marker_ids: [X], weight: Y} → X)
  4. Map to best semantic equivalent where a clear match exists
  5. Remove template/placeholder refs (SEM_<FAMILIE/ASPEKT>_*, SCN_*)
  6. Remove truly unmappable refs and log for future SEM creation

Reads/writes: build/markers_normalized/{CLU,MEMA}/*.yaml + marker_registry.json
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
# Semantic mapping: broken_ref → existing_marker_id
# ---------------------------------------------------------------------------
SEMANTIC_MAP = {
    # Uncertainty / Toning
    "SEM_UNCERTAINTY_TONING": "SEM_UNCERTAINTY_PROSODY",
    "SEM_PROBABILISTIC_LANGUAGE": "SEM_UNCERTAINTY_PROSODY",

    # Conflict / Escalation
    "SEM_ANGER_ESCALATION": "SEM_CONFLICT_ESCALATION",
    "SEM_ESCALATION_MOVE": "SEM_CONFLICT_ESCALATION",
    "SEM_CONTROL_ESCALATION": "SEM_CONFLICT_ESCALATION",
    "SEM_SARCASM_IRRITATION": "SEM_SARCASTIC_DRIFT",

    # Support / Emotion
    "SEM_SUPPORT_VALIDATION": "SEM_EMOTIONAL_ACCEPTANCE",
    "SEM_EMOTIONAL_SUPPORT": "SEM_EMOTIONAL_AWARENESS",

    # Commitment
    "SEM_CLEAR_COMMITMENT": "SEM_COMMITMENT_LOCKIN",
    "SEM_PROCRASTINATION_BEHAVIOR": "SEM_CONFLICT_AVOIDANCE",
    "SEM_DELAYING_MOVE": "SEM_CONFLICT_AVOIDANCE",

    # Accusation / Trust
    "SEM_DISTRUST_ACCUSATION": "SEM_ACCUSATION_MARKER",
    "SEM_RELIABILITY_CONCERN": "SEM_RESPECT_RELIABILITY_FRAME",
    "SEM_NEGATIVE_FEEDBACK": "SEM_ACCUSATION_MARKER",

    # Dignity / Status
    "SEM_STATUS_THREAT": "SEM_STATUS_RECOGNITION",
    "SEM_DEMEANING_LANGUAGE": "SEM_DEFENSIVENESS_SHIFT_MARKER",

    # Moral
    "SEM_MORAL_JUDGMENT": "SEM_MORAL_REFRAMING_GOOD_INTENT",
    "SEM_MORAL_OUTRAGE": "SEM_MORAL_REFRAMING_GOOD_INTENT",

    # Flirting / Style
    "SEM_FRIENDLY_FLIRTING": "SEM_OFFENSIVE_FLIRTING",
    "SEM_MIRRORED_STYLE": "SEM_STYLE_COMPARISON",
    "SEM_BOUNDARY_SHIFT": "SEM_BOUNDARY_SETTING",

    # Persona / Spiral
    "SEM_COMPETITIVE_DRIVE": "SEM_TASK_DRIVE",
    "SEM_KPI_FOCUS": "SEM_BUSINESS_FOCUS",
    "SEM_COMPARATIVE_CLAIM": "SEM_CERTAINTY_CLAIMS",
    "SEM_ECOLOGICAL_METAPHOR": "SEM_METAPHORICAL_COMMENT",
    "SEM_TRADEOFF_LANGUAGE": "SEM_ANALYTICAL_THINKING",

    # Double bind
    "SEM_DOUBLE_BIND_DISCLAIMER_BUT": "SEM_DOUBLE_BIND",

    # Self-reflection
    "SEM_SELF_CONSIST_PROBE_EXT": "SEM_CONSIST_EVAL_EXTERNAL",

    # Guilt
    "SEM_GUILT_FRAMING": "ATO_GUILT_TRIP",
    "SEM_GUILT_TRIPPING": "ATO_GUILT_TRIP",

    # CLU refs
    "CLU_EMOTIONAL_SUPPORT": "CLU_SUPPORT_EXCHANGE",
    "CLU_EMOTIONAL_DYSREGULATION": "CLU_DYSREGULATION_PATTERN",
    "CLU_PROCRASTINATION_LOOP": "CLU_RUMINATION_LOOP",
    "CLU_INDIRECT_CONFLICT_AVOIDANCE": "CLU_CONFLICT_ESCALATION",
}

# Refs to completely remove (templates, placeholders, non-existent concepts)
REMOVE_REFS = {
    "SEM_<FAMILIE/ASPEKT>_A",
    "SEM_<FAMILIE/ASPEKT>_B",
    "SEM_<FAMILIE/ASPEKT>_C",
    "SCN_*",
    "SEM_GENERIC_PATTERN",
    "HINT_POSITIVE_AFFECT",
}


def fix_single_ref(ref: str, all_ids: set) -> str | None:
    """Fix a single reference string. Returns corrected ID or None to remove."""

    # Already valid
    if ref in all_ids:
        return ref

    # Category 1: Strip qualified prefix (ld34_text_social_grammar.SEM_X)
    if "." in ref and ref.count(".") == 1:
        stripped = ref.split(".")[-1]
        if stripped in all_ids:
            return stripped

    # Category 2: Strip @annotation (CLU_LL_PROFILE@self)
    if "@" in ref:
        stripped = ref.split("@")[0]
        if stripped in all_ids:
            return stripped

    # Category 3: Template/placeholder → remove
    if ref in REMOVE_REFS or "<" in ref:
        return None

    # Category 4: Semantic mapping
    if ref in SEMANTIC_MAP:
        mapped = SEMANTIC_MAP[ref]
        if mapped in all_ids:
            return mapped
        # Map target also doesn't exist — try again without MARKER suffix
        base = mapped.replace("_MARKER", "")
        if base in all_ids:
            return base

    # Category 5: Try adding/removing _MARKER suffix
    if ref.endswith("_MARKER"):
        base = ref[:-7]
        if base in all_ids:
            return base
    else:
        with_marker = ref + "_MARKER"
        if with_marker in all_ids:
            return with_marker

    # Category 6: ATO prefix for SEM_ refs that might be ATOs
    if ref.startswith("SEM_"):
        ato_variant = "ATO_" + ref[4:]
        if ato_variant in all_ids:
            return ato_variant

    # No fix found → remove
    return None


def fix_composed_of(composed, all_ids: set) -> tuple[list | dict | None, list[str], list[str]]:
    """
    Fix a composed_of field. Returns (fixed_value, fixed_refs, removed_refs).
    """
    fixed_list = []
    fixed_refs = []
    removed_refs = []

    if isinstance(composed, list):
        for item in composed:
            if isinstance(item, str):
                result = fix_single_ref(item, all_ids)
                if result:
                    fixed_list.append(result)
                    if result != item:
                        fixed_refs.append(f"{item} → {result}")
                else:
                    removed_refs.append(item)
            elif isinstance(item, dict):
                # Dict format: {'marker_ids': ['SEM_X'], 'weight': 0.5}
                marker_ids = item.get("marker_ids", [])
                if isinstance(marker_ids, list):
                    new_ids = []
                    for mid in marker_ids:
                        result = fix_single_ref(str(mid), all_ids)
                        if result:
                            new_ids.append(result)
                            if result != mid:
                                fixed_refs.append(f"{mid} → {result}")
                        else:
                            removed_refs.append(str(mid))
                    if new_ids:
                        new_item = dict(item)
                        new_item["marker_ids"] = new_ids
                        fixed_list.append(new_item)
                else:
                    fixed_list.append(item)
            else:
                fixed_list.append(item)

        return fixed_list if fixed_list else None, fixed_refs, removed_refs

    elif isinstance(composed, dict):
        result_dict = dict(composed)
        for key in ["require", "sem_pool", "all_of", "any_of"]:
            if key in result_dict and isinstance(result_dict[key], list):
                new_list = []
                for ref in result_dict[key]:
                    if isinstance(ref, str):
                        result = fix_single_ref(ref, all_ids)
                        if result:
                            new_list.append(result)
                            if result != ref:
                                fixed_refs.append(f"{ref} → {result}")
                        else:
                            removed_refs.append(ref)
                    else:
                        new_list.append(ref)
                result_dict[key] = new_list

        return result_dict, fixed_refs, removed_refs

    return composed, [], []


def to_plain(obj):
    """Convert to plain Python types."""
    if hasattr(obj, "items"):
        return {str(k): to_plain(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [to_plain(i) for i in obj]
    elif obj is None:
        return None
    return obj


def main():
    # Load registry
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    all_ids = set(registry["markers"].keys())

    stats = {"fixed": 0, "removed": 0, "markers_updated": 0, "unchanged": 0}
    all_fixed = []
    all_removed = []

    for marker_id, data in registry["markers"].items():
        if data["layer"] not in ("CLU", "MEMA"):
            continue

        composed = data.get("composed_of")
        if not composed:
            continue

        fixed_composed, fixed_refs, removed_refs = fix_composed_of(composed, all_ids)

        if not fixed_refs and not removed_refs:
            stats["unchanged"] += 1
            continue

        stats["markers_updated"] += 1
        stats["fixed"] += len(fixed_refs)
        stats["removed"] += len(removed_refs)
        all_fixed.extend([(marker_id, f) for f in fixed_refs])
        all_removed.extend([(marker_id, r) for r in removed_refs])

        # Update registry
        if fixed_composed is not None:
            data["composed_of"] = fixed_composed
        else:
            data.pop("composed_of", None)

        # Update YAML file
        layer = data["layer"]
        yaml_path = NORM_DIR / layer / f"{marker_id}.yaml"
        if yaml_path.exists():
            with open(yaml_path, "r", encoding="utf-8") as f:
                yaml_data = yaml_rw.load(f) or {}

            if fixed_composed is not None:
                yaml_data["composed_of"] = to_plain(fixed_composed)
            else:
                yaml_data.pop("composed_of", None)

            with open(yaml_path, "w", encoding="utf-8") as f:
                yaml_rw.dump(to_plain(yaml_data), f)

    # Write updated registry
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    # Summary
    print(f"\n=== CLU/MEMA Reference Fix Complete ===")
    print(f"Markers updated: {stats['markers_updated']}")
    print(f"Refs fixed (remapped): {stats['fixed']}")
    print(f"Refs removed (unmappable): {stats['removed']}")
    print(f"Unchanged: {stats['unchanged']}")

    if all_fixed:
        print(f"\n--- Remapped ({len(all_fixed)}) ---")
        for mid, fix in all_fixed:
            print(f"  {mid}: {fix}")

    if all_removed:
        print(f"\n--- Removed ({len(all_removed)}) ---")
        for mid, ref in all_removed:
            print(f"  {mid}: {ref}")

    # Verify: count remaining broken refs
    broken_after = 0
    total_after = 0
    for mid, m in registry["markers"].items():
        comp = m.get("composed_of")
        refs = []
        if isinstance(comp, list):
            refs = [c for c in comp if isinstance(c, str)]
        elif isinstance(comp, dict):
            for key in ["require", "sem_pool", "all_of", "any_of"]:
                val = comp.get(key, [])
                if isinstance(val, list):
                    refs.extend([c for c in val if isinstance(c, str)])
        for ref in refs:
            total_after += 1
            if ref not in all_ids:
                broken_after += 1

    print(f"\n--- Verification ---")
    print(f"Total refs after: {total_after}")
    print(f"Broken refs after: {broken_after} ({broken_after*100//max(total_after,1)}%)")


if __name__ == "__main__":
    main()
