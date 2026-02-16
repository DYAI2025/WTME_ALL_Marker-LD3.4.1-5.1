#!/usr/bin/env python3
"""Remove ' 2' duplicate files from markers_rated where base version exists."""
import re
from pathlib import Path

QUALITY_DIR = Path("/Users/benjaminpoersch/Projects/Marker- entbiazed/WTME_ALL_Marker-LD3.4.1-5.1/build/markers_rated")

removed = 0
orphans_renamed = 0

for yaml_file in sorted(QUALITY_DIR.rglob("*.yaml")):
    name = yaml_file.name
    # Match " 2.yaml", " 2 2.yaml", " 3.yaml" patterns
    m = re.match(r'^(.+?) \d+(\.yaml)$', name)
    if not m:
        continue

    base_name = m.group(1) + m.group(2)
    base_path = yaml_file.parent / base_name

    if base_path.exists():
        # Base exists -> delete the " 2" copy
        yaml_file.unlink()
        removed += 1
        print(f"DELETED (dup):  {yaml_file.relative_to(QUALITY_DIR)}")
    else:
        # No base -> rename " 2" to clean name
        yaml_file.rename(base_path)
        orphans_renamed += 1
        print(f"RENAMED (orphan): {name} -> {base_name}")

print(f"\nDone. Deleted {removed} duplicates, renamed {orphans_renamed} orphans.")
