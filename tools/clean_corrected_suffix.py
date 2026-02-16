#!/usr/bin/env python3
"""Remove _corrected suffix from marker filenames and update internal ids."""
from pathlib import Path

QUALITY_DIR = Path("/Users/benjaminpoersch/Projects/Marker- entbiazed/WTME_ALL_Marker-LD3.4.1-5.1/build/markers_rated")

fixed = 0
for yaml_file in sorted(QUALITY_DIR.rglob("*_corrected.yaml")):
    new_name = yaml_file.name.replace("_corrected.yaml", ".yaml")
    new_path = yaml_file.parent / new_name

    if new_path.exists():
        # Base version exists -> compare sizes, keep larger
        if yaml_file.stat().st_size >= new_path.stat().st_size:
            new_path.unlink()
            print(f"REPLACED: {new_name} with corrected version (larger)")
        else:
            yaml_file.unlink()
            print(f"DELETED: {yaml_file.name} (base version is larger)")
            continue

    # Fix internal id
    content = yaml_file.read_text(encoding='utf-8', errors='replace')
    content = content.replace("_corrected", "")
    yaml_file.write_text(content, encoding='utf-8')
    yaml_file.rename(new_path)
    print(f"RENAMED: {yaml_file.name} -> {new_name}")
    fixed += 1

print(f"\nCleaned {fixed} _corrected files.")
