#!/usr/bin/env python3
"""
Fix ALL remaining broken composed_of references across ALL layers.

Previous fix_clu_refs.py handled CLU/MEMA → 0 broken.
This script handles SEM→ATO and UNKNOWN layer refs.

Strategy:
  1. Curated semantic mapping (manual, high-quality matches)
  2. Suffix variants (_MARKER, _TEXT, _PROSODY)
  3. Strip prefixes / annotations
  4. Remove unmappable refs (log for audit)

Reads/writes: build/markers_normalized/**/*.yaml + marker_registry.json
"""

import json
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
# Curated ATO mapping: broken_ref → best existing ATO
# Only maps where semantic overlap is strong enough to preserve detection quality
# ---------------------------------------------------------------------------
ATO_SEMANTIC_MAP = {
    # --- Clear matches (suffix/naming variants) ---
    "ATO_FIRSTTIME_CLAUSE": "ATO_FIRSTTIME_CLAUSE_MARKER",
    "ATO_SARCASM_MARKER": "ATO_SARCASM",
    "ATO_SARCASM_MARKERS": "ATO_SARCASM",
    "ATO_SARCASM_SUBTILE": "ATO_SARCASM_CUES",
    "ATO_HUMOR_SIGNAL": "ATO_HUMOR_LIGHT",
    "ATO_PLAYFUL_TONE": "ATO_HUMOR_LIGHT",
    "ATO_METAPHOR_CUE": "ATO_METAPHOR",
    "ATO_SPIRAL_TERMS": "ATO_SPIRAL",
    "ATO_SELF_REF": "ATO_SELF_REFLECTION",
    "ATO_SELF_OBSERVATION": "ATO_SELF_REFLECTION",
    "ATO_FULL_STRESS": "ATO_STRESS",
    "ATO_STATUS_TERMS": "ATO_STATUS_SIGNALING",
    "ATO_CULTURAL_ELEMENT": "ATO_CULTURE_TOKEN",
    "ATO_CRITIQUE_ELEMENT": "ATO_CRITICISM",
    "ATO_MORAL_LANGUAGE": "ATO_MORAL_AUTHORITY",

    # --- Strong semantic matches ---
    "ATO_ACCUSATION_PHRASE": "ATO_DIRECT_ACCUSATION",
    "ATO_YOUR_FAULT_PHRASE": "ATO_BLAME_SHIFT_MARKER",
    "ATO_FAULT_REFERENCE": "ATO_BLAME_SHIFT",
    "ATO_ANGER_EXPRESSION": "ATO_ANGER",
    "ATO_ANXIETY_TERMS": "ATO_FEAR_ANXIETY",
    "ATO_CONTROL_MARKERS": "ATO_CONTROL_PHRASES",
    "ATO_POWER_LANGUAGE": "ATO_POWER_ASSERTION",
    "ATO_DELAYING_PHRASES": "ATO_DELAY_WORD",
    "ATO_COMPARISON_OBJECT": "ATO_COMPARISON_MANIPULATION",
    "ATO_DESIRE_VERB": "ATO_WANT_TERM",
    "ATO_DREHEN_IM_KREIS": "ATO_SPIRAL",
    "ATO_HELPLESSNESS_DEPENDENCY": "ATO_LEARNED_HELPLESSNESS",
    "ATO_LONG_RESPONSE_GAP": "ATO_PAUSE_LONG",
    "ATO_MICRO_DISMISSAL": "ATO_MINIMIZATION",
    "ATO_MOCKING_LEXICON": "ATO_PUTDOWN_TEMPLATE",
    "ATO_OUTRAGE_MARKERS": "ATO_ANGER_RAGE",
    "ATO_PREMATURE_CLOSURE": "ATO_SUBJECT_CLOSED",
    "ATO_UNDERSTATEMENT": "ATO_SOFTENING",
    "ATO_WE_PLAN": "ATO_JOINT_PLANNING",
    "ATO_INVITING_RESONANCE": "ATO_POSITIVE_RESONANCE",
    "ATO_SUPPORTIVE_LANGUAGE": "ATO_SUPPORT_PHRASE",
    "ATO_FLIRTING_PHRASE": "ATO_ROMANTIC_SIGNAL_DIRECT",
    "ATO_THREAT_ESCALATION": "ATO_THREAT_LANGUAGE",
    "ATO_TOXIC_TOKENS": "ATO_ESCALATION_LEXICON",
    "ATO_SWEAR_WORD": "ATO_ESCALATION_LEXICON",

    # --- Reasonable semantic matches ---
    "ATO_EMOTIONAL_WITHDRAWAL": "ATO_DISENGAGEMENT_LANGUAGE",
    "ATO_OFFENDED_SILENCE": "ATO_SILENT_TREATMENT_INDICATORS",
    "ATO_SILENCE": "ATO_PAUSE_LONG",
    "ATO_INDIFFERENT": "ATO_AFFECT_FLAT",
    "ATO_KEINE_LOESUNG": "ATO_GIVING_UP_PHRASE",
    "ATO_NO_MOTIVATION": "ATO_ENERGY_LOW",
    "ATO_BOUNDARY_CROSS": "ATO_BOUNDARY_NEGOTIATION",
    "ATO_AUTHORITY_PHRASE": "ATO_POWER_ASSERTION",
    "ATO_APPEAL_TO_AUTHORITY_EXPERT": "ATO_MORAL_AUTHORITY",
    "ATO_APPEAL_TO_AUTHORITY_STUDY": "ATO_MORAL_AUTHORITY",
    "ATO_ROUTINE_CONTEXT": "ATO_RITUAL",
    "ATO_FUTURE_IDEA": "ATO_PROACTIVE_INTENTION",
    "ATO_DOUBLE_BIND_EXPRESSIONS": "ATO_DOUBLE_ENTENDRE",

    # --- SEM cross-layer refs in SEM composed_of ---
    "SEM_ANXIETY_LANGUAGE": "ATO_FEAR_ANXIETY",
    "SEM_RELIABILITY_CONCERN": "ATO_TRUST_DEFICIT_STATEMENT",
    "SEM_RISK_FORECAST": "ATO_RISK_AVERSION_PHRASE",
}

# Refs to completely remove (no semantic equivalent exists)
REMOVE_REFS = {
    "ATO_UNKNOWN",           # Placeholder
    "ATO_ADMISSION_CUE",     # No equivalent
    "ATO_AI_RIGHTS_FORDERUNG",  # Too specific / niche
    "ATO_CAUSAL_CHAIN",      # Abstract concept, no atomic match
    "ATO_COMMUNITY_TALK",    # No match
    "ATO_DELETE_TRACES",     # No match
    "ATO_FAKE_IDENTITY_STORY",  # No match
    "ATO_FICTION_TOKENS",    # No clear match
    "ATO_HOBBY_OBJECT",      # No match
    "ATO_MEMORY_TRIGGER",    # No match
    "ATO_OBJECT_OF_DESIRE",  # No match
    "ATO_SIGH",              # Prosodic only, no text equivalent
    "ATO_SVT_BEZIEHUNG_DU_BOTSCHAFT",  # Legacy schema ref
    "ATO_TITLE_WORD",        # No match
    "ATO_TWIST",             # Too vague
}


def fix_single_ref(ref: str, all_ids: set) -> str | None:
    """Fix a single reference string. Returns corrected ID or None to remove."""

    # Already valid
    if ref in all_ids:
        return ref

    # Explicit removal
    if ref in REMOVE_REFS or "<" in ref:
        return None

    # Curated semantic mapping
    if ref in ATO_SEMANTIC_MAP:
        mapped = ATO_SEMANTIC_MAP[ref]
        if mapped in all_ids:
            return mapped

    # Strip qualified prefix (ld34_text_social_grammar.SEM_X)
    if "." in ref and ref.count(".") == 1:
        stripped = ref.split(".")[-1]
        if stripped in all_ids:
            return stripped

    # Strip @annotation (CLU_LL_PROFILE@self)
    if "@" in ref:
        stripped = ref.split("@")[0]
        if stripped in all_ids:
            return stripped

    # Try adding/removing _MARKER suffix
    if ref.endswith("_MARKER"):
        base = ref[:-7]
        if base in all_ids:
            return base
    else:
        with_marker = ref + "_MARKER"
        if with_marker in all_ids:
            return with_marker

    # Try _TEXT suffix
    if not ref.endswith("_TEXT"):
        with_text = ref + "_TEXT"
        if with_text in all_ids:
            return with_text

    # ATO prefix for SEM_ refs
    if ref.startswith("SEM_"):
        ato_variant = "ATO_" + ref[4:]
        if ato_variant in all_ids:
            return ato_variant

    # No fix found → remove
    return None


def fix_composed_of(composed, all_ids: set):
    """Fix a composed_of field. Returns (fixed_value, fixed_refs, removed_refs)."""
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
    """Convert ruamel types to plain Python."""
    if hasattr(obj, "items"):
        return {str(k): to_plain(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [to_plain(i) for i in obj]
    elif obj is None:
        return None
    return obj


def main():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    all_ids = set(registry["markers"].keys())

    stats = {"fixed": 0, "removed": 0, "markers_updated": 0, "unchanged": 0}
    all_fixed = []
    all_removed = []

    # Process ALL layers (not just CLU/MEMA)
    for marker_id, data in registry["markers"].items():
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
        layer = data.get("layer", "UNKNOWN")
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
    print(f"\n=== All-Layer Reference Fix Complete ===")
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

    # Verify: count remaining broken refs across ALL layers
    broken_after = 0
    total_after = 0
    broken_detail = []
    for mid, m in registry["markers"].items():
        comp = m.get("composed_of")
        refs = []
        if isinstance(comp, list):
            for c in comp:
                if isinstance(c, str):
                    refs.append(c)
                elif isinstance(c, dict):
                    for rid in c.get("marker_ids", []):
                        refs.append(str(rid))
        elif isinstance(comp, dict):
            for key in ["require", "sem_pool", "all_of", "any_of"]:
                val = comp.get(key, [])
                if isinstance(val, list):
                    refs.extend([c for c in val if isinstance(c, str)])
        for ref in refs:
            total_after += 1
            if ref not in all_ids:
                broken_after += 1
                broken_detail.append(f"  {mid} [{m.get('layer','?')}] → {ref}")

    print(f"\n--- Verification ---")
    print(f"Total refs after: {total_after}")
    print(f"Broken refs after: {broken_after} ({broken_after*100//max(total_after,1)}%)")

    if broken_detail:
        print(f"\n--- Still broken ---")
        for d in broken_detail:
            print(d)


if __name__ == "__main__":
    main()
