#!/usr/bin/env python3
"""Fix known typos in marker filenames and update internal id fields."""
from pathlib import Path
import re

QUALITY_DIR = Path("/Users/benjaminpoersch/Projects/Marker- entbiazed/WTME_ALL_Marker-LD3.4.1-5.1/build/markers_rated")

RENAMES = {
    "ATO_SARCASAM_CUE.yaml": "ATO_SARCASM_CUE.yaml",
    "ATO_UNCERTAINY_PHRASE.yaml": "ATO_UNCERTAINTY_PHRASE.yaml",
    "SEM_APATHATICLU_REPLY.yaml": "SEM_APATHETIC_REPLY.yaml",
    "SEM_SIMU_LAVE_SCAM_SEMANTIC.yaml": "SEM_SIMU_LOVE_SCAM_SEMANTIC.yaml",
}

fixed = 0
for yaml_file in sorted(QUALITY_DIR.rglob("*.yaml")):
    if yaml_file.name in RENAMES:
        new_name = RENAMES[yaml_file.name]
        new_path = yaml_file.parent / new_name

        # Also fix internal id/name field
        content = yaml_file.read_text(encoding='utf-8', errors='replace')
        old_id = yaml_file.stem
        new_id = new_name.replace('.yaml', '')
        content = content.replace(old_id, new_id)

        yaml_file.write_text(content, encoding='utf-8')
        yaml_file.rename(new_path)
        print(f"FIXED: {yaml_file.name} -> {new_name}")
        fixed += 1

print(f"\nFixed {fixed} typos.")
