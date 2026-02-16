#!/usr/bin/env python3
"""Delete all Rating-4 (not usable) marker files and log what was removed."""
from pathlib import Path

QUALITY_DIR = Path("/Users/benjaminpoersch/Projects/Marker- entbiazed/WTME_ALL_Marker-LD3.4.1-5.1/build/markers_rated")
NOT_USABLE = QUALITY_DIR / "4_not_usable"

deleted = []
for layer_dir in sorted(NOT_USABLE.iterdir()):
    if not layer_dir.is_dir():
        continue
    for yaml_file in sorted(layer_dir.glob("*.yaml")):
        deleted.append(f"{layer_dir.name}/{yaml_file.name} ({yaml_file.stat().st_size}B)")
        yaml_file.unlink()

# Write deletion log
log_path = QUALITY_DIR / "DELETED_STUBS.log"
with open(log_path, 'w') as f:
    f.write(f"Deleted {len(deleted)} Rating-4 stubs:\n\n")
    for d in deleted:
        f.write(f"  {d}\n")

print(f"Deleted {len(deleted)} stubs. Log: {log_path}")
for d in deleted:
    print(f"  {d}")
