#!/usr/bin/env python3
"""Rename clinical diagnostic labels to behavioral descriptors.
Updates filename, internal id/name field, description, and tags."""
from pathlib import Path
import re

QUALITY_DIR = Path("/Users/benjaminpoersch/Projects/Marker- entbiazed/WTME_ALL_Marker-LD3.4.1-5.1/build/markers_rated")

RENAMES = {
    # ATO layer
    "ATO_ADHD_DISORGANIZED_THOUGHTS": "ATO_DISORGANIZED_THOUGHT_PATTERN",
    "ATO_AUTISM_LITERAL_LANGUAGE": "ATO_LITERAL_LANGUAGE_PATTERN",
    "ATO_BIPOLAR_MANIC_SPEECH": "ATO_MANIC_SPEECH_PATTERN",
    "ATO_BPD_FEAR_OF_ABANDONMENT": "ATO_ABANDONMENT_ANXIETY",
    "ATO_BPD_INTENSE_EMOTIONS": "ATO_INTENSE_EMOTION_SWING",
    "ATO_DEPRESSIVE_NEGATIVE_TALK": "ATO_NEGATIVE_SELF_TALK",
    "ATO_OCD_REPETITIVE_LANGUAGE": "ATO_REPETITIVE_CHECKING_LANGUAGE",
    "ATO_PTSD_AVOIDANCE_LANGUAGE": "ATO_TRAUMA_AVOIDANCE_LANGUAGE",
    "ATO_SCHIZOPHRENIA_DISORGANIZED_SPEECH": "ATO_DISORGANIZED_SPEECH_PATTERN",
    # CLU layer
    "CLU_DEPRESSIVE_TRIAD": "CLU_NEGATIVE_COGNITIVE_TRIAD",
    # MEMA layer
    "MEMA_DISSOCIATIVE_COMPARTMENTALIZATION": "MEMA_EMOTIONAL_COMPARTMENTALIZATION",
    "MEMA_DEPRESSIVE_LANGUAGE_PROFILE": "MEMA_NEGATIVE_LANGUAGE_PROFILE",
}

# Tags to remove
REMOVE_TAGS = {"diagnostic", "psychiatric", "clinical", "disorder"}

renamed = 0
for yaml_file in sorted(QUALITY_DIR.rglob("*.yaml")):
    old_id = yaml_file.stem
    if old_id not in RENAMES:
        continue

    new_id = RENAMES[old_id]
    new_filename = new_id + ".yaml"
    new_path = yaml_file.parent / new_filename

    content = yaml_file.read_text(encoding='utf-8', errors='replace')

    # Replace all occurrences of old id with new id
    content = content.replace(old_id, new_id)

    # Remove diagnostic/psychiatric tags
    for tag in REMOVE_TAGS:
        # Handle YAML list format: - diagnostic
        content = re.sub(rf'\n\s*-\s*{tag}\s*(?=\n)', '', content)
        # Handle inline format: [atomic, diagnostic, ...]
        content = re.sub(rf',\s*{tag}', '', content)
        content = re.sub(rf'{tag}\s*,\s*', '', content)

    # Add behavioral_pattern tag if not present
    if 'behavioral_pattern' not in content:
        # Inline list format
        content = re.sub(
            r'(tags:\s*\[)',
            r'\1behavioral_pattern, ',
            content
        )
        # Block list format
        if re.search(r'^tags:\s*$', content, re.MULTILINE):
            content = re.sub(
                r'(tags:\s*\n)',
                r'\1- behavioral_pattern\n',
                content
            )

    yaml_file.write_text(content, encoding='utf-8')
    yaml_file.rename(new_path)
    print(f"RENAMED: {old_id} -> {new_id}")
    renamed += 1

print(f"\nRenamed {renamed} clinical labels to behavioral descriptors.")
