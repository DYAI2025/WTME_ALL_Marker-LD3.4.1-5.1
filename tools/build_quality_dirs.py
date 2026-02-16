#!/usr/bin/env python3
"""
Build quality-rated directory structure from canonical KEEP markers.

Auto-rates markers by structural analysis:
- Has examples (positive count)?
- Has negative examples?
- Has frame/description?
- Has composed_of?
- File size (proxy for completeness)?
- Is a stub (<100 bytes)?

Rating:
  1 = Approved: 5+ examples, has frame, >500B
  2 = Good: has some examples OR good structure, needs minor fixes
  3 = Needs work: sparse content, <5 examples, missing key fields
  4 = Not usable: stub (<100B), empty, or no detection value
"""

import os
import sys
import shutil
import re
from pathlib import Path

REPO = Path("/Users/benjaminpoersch/Projects/Marker- entbiazed/WTME_ALL_Marker-LD3.4.1-5.1")
DECISIONS = REPO / "build" / "dedup_decisions.tsv"
QUALITY_DIR = REPO / "build" / "markers_rated"

# Clean and recreate
if QUALITY_DIR.exists():
    shutil.rmtree(QUALITY_DIR)

for rating in ["1_approved", "2_good", "3_needs_work", "4_not_usable"]:
    for layer in ["ATO", "SEM", "CLU", "MEMA"]:
        (QUALITY_DIR / rating / layer).mkdir(parents=True, exist_ok=True)

def count_examples(content):
    """Count positive examples in YAML content. Handles multiple schema formats."""
    pos_count = 0
    in_pos_section = False
    indent_level = 0

    for line in content.split('\n'):
        stripped = line.strip()
        curr_indent = len(line) - len(line.lstrip())

        # Detect positive example sections (multiple schema formats)
        if re.match(r'^(examples|positives)\s*:\s*$', stripped):
            in_pos_section = True
            indent_level = curr_indent
            continue
        # SSoTh format: examples.positive_de, examples.positive_en, examples.positive
        if re.match(r'^\s*(positive_de|positive_en|positive|pos)\s*:\s*$', stripped):
            in_pos_section = True
            indent_level = curr_indent
            continue
        # Negatives section ends positive counting
        if re.match(r'^(negatives|negative_de|negative_en|negative|neg)\s*:', stripped):
            in_pos_section = False
            continue
        # New top-level key ends section
        if curr_indent <= indent_level and re.match(r'^[a-zA-Z]', stripped) and not stripped.startswith('-') and not stripped.startswith('#'):
            if in_pos_section and stripped not in ('positive_de:', 'positive_en:', 'positive:', 'pos:'):
                in_pos_section = False
                continue

        if in_pos_section and stripped.startswith('- '):
            item = stripped[2:].strip().strip('"').strip("'")
            if item and item not in ('[]', '""', "''", '~', 'null', ''):
                pos_count += 1

    return pos_count

def count_negatives(content):
    """Count negative examples. Handles multiple schema formats."""
    neg_count = 0
    in_neg_section = False
    indent_level = 0

    for line in content.split('\n'):
        stripped = line.strip()
        curr_indent = len(line) - len(line.lstrip())

        if re.match(r'^(negatives|negative_de|negative_en|negative|neg)\s*:', stripped):
            in_neg_section = True
            indent_level = curr_indent
            continue
        if re.match(r'^[a-zA-Z]', stripped) and curr_indent <= indent_level and not stripped.startswith('-'):
            if in_neg_section:
                in_neg_section = False

        if in_neg_section and stripped.startswith('- '):
            item = stripped[2:].strip().strip('"').strip("'")
            if item and item not in ('[]', '""', "''", '~', 'null', ''):
                neg_count += 1

    return neg_count

def has_field(content, field):
    """Check if a YAML field exists with content. Handles aliases."""
    # Map of field names to check (multiple schema formats)
    aliases = {
        'id': ['id', 'name'],
        'frame': ['frame', 'meaning', 'intent', 'label'],
        'description': ['description', 'meaning', 'intent'],
        'composed_of': ['composed_of', 'ingredients', 'requires'],
        'pattern': ['pattern', 'patterns', 'regex'],
    }
    fields_to_check = aliases.get(field, [field])

    for f in fields_to_check:
        pat = re.compile(rf'^{f}\s*:', re.MULTILINE)
        match = pat.search(content)
        if match:
            pos = match.end()
            rest = content[pos:pos+100].strip()
            if rest and rest not in ('', '[]', '{}', '~', 'null', '""', "''"):
                return True
    return False

def get_layer(filename):
    """Extract layer from filename."""
    for prefix in ["ATO_", "SEM_", "CLU_", "MEMA_"]:
        if filename.startswith(prefix):
            return prefix.rstrip("_")
    return "OTHER"

def rate_marker(filepath, content, size):
    """Auto-rate a marker 1-4 based on structural analysis."""
    if size < 50:
        return 4, "empty stub"

    pos = count_examples(content)
    neg = count_negatives(content)
    has_frame = has_field(content, 'frame')
    has_desc = has_field(content, 'description')
    has_composed = has_field(content, 'composed_of')
    has_pattern = has_field(content, 'pattern')
    has_id = has_field(content, 'id')

    # Rating 4: Not usable
    if size < 100 and pos == 0:
        return 4, f"stub ({size}B), no examples"
    if not has_id and pos == 0 and not has_frame:
        return 4, "no id, no examples, no frame"

    # Rating 1: Approved
    if pos >= 5 and has_frame and size > 500:
        extra = []
        if neg >= 5:
            extra.append(f"{neg} neg")
        if has_desc:
            extra.append("desc")
        if has_composed:
            extra.append("composed")
        detail = f"{pos} pos" + (", " + ", ".join(extra) if extra else "")
        return 1, detail

    if pos >= 10 and size > 400:
        return 1, f"{pos} examples, {size}B"

    # Rating 2: Good
    if pos >= 3 and (has_frame or has_desc):
        return 2, f"{pos} examples, has {'frame' if has_frame else 'desc'}"

    if has_frame and has_composed and size > 400:
        return 2, f"good structure ({size}B), needs examples"

    if pos >= 5:
        return 2, f"{pos} examples, missing frame/desc"

    if (has_frame or has_pattern) and size > 300:
        return 2, f"has {'frame+pattern' if has_frame and has_pattern else 'frame' if has_frame else 'pattern'}, needs examples"

    # Rating 3: Needs work
    if pos > 0 or has_frame or has_desc or size > 200:
        parts = []
        if pos > 0:
            parts.append(f"{pos} examples")
        if has_frame:
            parts.append("frame")
        if has_desc:
            parts.append("desc")
        parts.append(f"{size}B")
        return 3, ", ".join(parts)

    # Rating 4 fallback
    return 4, f"minimal content ({size}B)"

# Parse decisions
keeps = []
with open(DECISIONS) as f:
    header = f.readline()
    for line in f:
        parts = line.strip().split('\t')
        if len(parts) < 6:
            continue
        marker, path, size, date, decision, reason = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
        if decision.startswith("KEEP"):
            keeps.append((marker, path, int(size)))

# Also check REVIEW_BETTER_CANDIDATE - pick the best one per marker
review_best = {}
with open(DECISIONS) as f:
    header = f.readline()
    for line in f:
        parts = line.strip().split('\t')
        if len(parts) < 6:
            continue
        marker, path, size = parts[0], parts[1], int(parts[2])
        decision = parts[4]
        if "REVIEW_BETTER_CANDIDATE" in decision or "REVIEW_NEWER_LARGER" in decision:
            if marker not in review_best or size > review_best[marker][1]:
                review_best[marker] = (path, size)

# For markers where review found something better, swap
keep_dict = {k[0]: (k[1], k[2]) for k in keeps}
upgrades = 0
for marker, (rpath, rsize) in review_best.items():
    if marker in keep_dict:
        kpath, ksize = keep_dict[marker]
        if rsize > ksize * 1.3:  # 30% larger
            keep_dict[marker] = (rpath, rsize)
            upgrades += 1

print(f"Upgraded {upgrades} markers to better REVIEW versions")

# Process each KEEP marker
stats = {1: 0, 2: 0, 3: 0, 4: 0}
layer_stats = {}
rating_details = []

for marker, (rel_path, size) in sorted(keep_dict.items()):
    layer = get_layer(marker)
    if layer == "OTHER":
        continue

    full_path = REPO / rel_path
    if not full_path.exists():
        continue

    try:
        content = full_path.read_text(encoding='utf-8', errors='replace')
    except:
        content = ""

    rating, reason = rate_marker(rel_path, content, size)
    stats[rating] += 1

    key = f"{layer}_{rating}"
    layer_stats[key] = layer_stats.get(key, 0) + 1

    # Determine target dir
    rating_dir = {1: "1_approved", 2: "2_good", 3: "3_needs_work", 4: "4_not_usable"}[rating]
    target = QUALITY_DIR / rating_dir / layer / marker
    shutil.copy2(full_path, target)

    rating_details.append((marker, layer, rating, reason, size, rel_path))

# Write summary
summary_path = QUALITY_DIR / "RATING_SUMMARY.tsv"
with open(summary_path, 'w') as f:
    f.write("MARKER\tLAYER\tRATING\tREASON\tSIZE_B\tSOURCE_PATH\n")
    for d in sorted(rating_details, key=lambda x: (x[1], x[2], x[0])):
        f.write("\t".join(str(x) for x in d) + "\n")

# Print stats
print(f"\n=== Quality Rating Results ===")
print(f"Total rated: {sum(stats.values())}")
print(f"  Rating 1 (Approved):   {stats[1]}")
print(f"  Rating 2 (Good):       {stats[2]}")
print(f"  Rating 3 (Needs work): {stats[3]}")
print(f"  Rating 4 (Not usable): {stats[4]}")
print(f"\nPer layer:")
for layer in ["ATO", "SEM", "CLU", "MEMA"]:
    row = []
    for r in [1,2,3,4]:
        row.append(f"R{r}={layer_stats.get(f'{layer}_{r}', 0)}")
    total = sum(layer_stats.get(f'{layer}_{r}', 0) for r in [1,2,3,4])
    print(f"  {layer}: {', '.join(row)} (total={total})")

print(f"\nOutput: {QUALITY_DIR}")
print(f"Summary: {summary_path}")
