#!/bin/bash
# Deduplicate & Audit Script
# Finds all marker YAMLs, groups by basename, compares size/age,
# decides which version to keep vs. discard vs. needs-review

REPO_ROOT="/Users/benjaminpoersch/Projects/Marker- entbiazed/WTME_ALL_Marker-LD3.4.1-5.1"
OUTPUT="$REPO_ROOT/build/dedup_report.jsonl"
SUMMARY="$REPO_ROOT/build/dedup_summary.txt"

mkdir -p "$REPO_ROOT/build"
> "$OUTPUT"
> "$SUMMARY"

echo "=== Marker Deduplication Report ===" >> "$SUMMARY"
echo "Generated: $(date)" >> "$SUMMARY"
echo "" >> "$SUMMARY"

# Find ALL yaml/yml files, exclude .git and __MACOSX
find "$REPO_ROOT" \( -name "*.yaml" -o -name "*.yml" \) \
  -not -path "*/.git/*" \
  -not -path "*__MACOSX*" \
  -print0 | while IFS= read -r -d '' file; do
  BASENAME=$(basename "$file")
  SIZE=$(wc -c < "$file" | tr -d ' ')
  MTIME=$(stat -f "%m" "$file" 2>/dev/null || stat -c "%Y" "$file" 2>/dev/null)
  MTIME_HUMAN=$(stat -f "%Sm" -t "%Y-%m-%d" "$file" 2>/dev/null || date -r "$file" "+%Y-%m-%d" 2>/dev/null)
  # Normalize basename: remove " 2", " 3", " Kopie", " Kopie 2" etc.
  NORM=$(echo "$BASENAME" | sed 's/ [0-9]*\.\(ya\?ml\)$/.\1/' | sed 's/ Kopie[^.]*//g')
  REL_PATH="${file#$REPO_ROOT/}"
  echo "${NORM}|${REL_PATH}|${SIZE}|${MTIME}|${MTIME_HUMAN}" >> "$OUTPUT"
done

echo "Raw entries: $(wc -l < "$OUTPUT")"

# Now process: group by normalized name, find duplicates
sort -t'|' -k1,1 -k3,3rn "$OUTPUT" > "$OUTPUT.sorted"

# Generate the decision report
python3 << 'PYEOF'
import os, sys
from collections import defaultdict

repo = "/Users/benjaminpoersch/Projects/Marker- entbiazed/WTME_ALL_Marker-LD3.4.1-5.1"
sorted_file = f"{repo}/build/dedup_report.jsonl.sorted"
decision_file = f"{repo}/build/dedup_decisions.tsv"
stats_file = f"{repo}/build/dedup_stats.txt"

# Parse entries
entries = defaultdict(list)
with open(sorted_file) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        parts = line.split("|")
        if len(parts) != 5:
            continue
        norm, rel_path, size, mtime, mtime_human = parts
        # Only marker files
        if not any(norm.startswith(p) for p in ["ATO_","SEM_","CLU_","MEMA_"]):
            continue
        entries[norm].append({
            "path": rel_path,
            "size": int(size),
            "mtime": int(mtime),
            "mtime_human": mtime_human
        })

# Decision logic
decisions = []  # (norm_name, path, size, date, decision, reason)

unique_count = 0
dup_groups = 0
keep_count = 0
discard_count = 0
needs_review_count = 0

# Priority paths (checked ones first)
priority_dirs = [
    "LD3.4_ALL_Marker_5.1/ALL_Marker_5.1/",
    "LD3.4_ALL_Marker_5.1/spiral_persona/",
]
# Root level is highest priority
def path_priority(p):
    if "/" not in p or p.count("/") == 0:
        return 0  # root
    for i, pd in enumerate(priority_dirs):
        if p.startswith(pd):
            return i + 1
    if "SSoTh" in p:
        return 10
    if "BACKUP" in p:
        return 20
    if "Kopie" in p:
        return 15
    return 5

for norm, files in sorted(entries.items()):
    if len(files) == 1:
        unique_count += 1
        decisions.append((norm, files[0]["path"], files[0]["size"], files[0]["mtime_human"], "KEEP_UNIQUE", "only instance"))
        keep_count += 1
        continue

    dup_groups += 1
    # Sort by: priority dir first, then size desc, then mtime desc
    files.sort(key=lambda x: (path_priority(x["path"]), -x["size"], -x["mtime"]))

    best = files[0]
    best_decided = False

    for i, f in enumerate(files):
        if i == 0:
            # Check if another file has significantly more content
            larger_exists = any(other["size"] > f["size"] * 1.5 for other in files[1:])
            newer_larger = any(other["size"] > f["size"] * 1.2 and other["mtime"] > f["mtime"] for other in files[1:])

            if newer_larger:
                decisions.append((norm, f["path"], f["size"], f["mtime_human"], "REVIEW_MAYBE_OUTDATED", "another copy is newer AND larger"))
                needs_review_count += 1
            elif larger_exists:
                decisions.append((norm, f["path"], f["size"], f["mtime_human"], "REVIEW_SMALLER", "priority path but another copy has 50%+ more content"))
                needs_review_count += 1
            else:
                decisions.append((norm, f["path"], f["size"], f["mtime_human"], "KEEP_BEST", f"best of {len(files)} copies"))
                keep_count += 1
            continue

        # For duplicates: compare to best
        size_ratio = f["size"] / best["size"] if best["size"] > 0 else 0
        is_newer = f["mtime"] > best["mtime"]
        is_larger = f["size"] > best["size"]
        significantly_larger = f["size"] > best["size"] * 1.5
        significantly_smaller = f["size"] < best["size"] * 0.5

        if significantly_smaller:
            decisions.append((norm, f["path"], f["size"], f["mtime_human"], "DISCARD_SMALLER", f"only {size_ratio:.0%} of best ({best['size']}B)"))
            discard_count += 1
        elif significantly_larger and is_newer:
            decisions.append((norm, f["path"], f["size"], f["mtime_human"], "REVIEW_BETTER_CANDIDATE", f"newer AND {f['size']-best['size']}B larger than current best"))
            needs_review_count += 1
        elif significantly_larger and not is_newer:
            decisions.append((norm, f["path"], f["size"], f["mtime_human"], "REVIEW_OLDER_BUT_LARGER", f"older but {f['size']-best['size']}B larger - new version may be error"))
            needs_review_count += 1
        elif is_newer and is_larger:
            decisions.append((norm, f["path"], f["size"], f["mtime_human"], "REVIEW_NEWER_LARGER", f"newer and {f['size']-best['size']}B larger"))
            needs_review_count += 1
        elif abs(f["size"] - best["size"]) < 10:
            decisions.append((norm, f["path"], f["size"], f["mtime_human"], "DISCARD_IDENTICAL", f"same size as best (diff {abs(f['size']-best['size'])}B)"))
            discard_count += 1
        else:
            decisions.append((norm, f["path"], f["size"], f["mtime_human"], "DISCARD_REDUNDANT", f"{size_ratio:.0%} of best, not newer"))
            discard_count += 1

# Write decisions
with open(decision_file, "w") as f:
    f.write("MARKER\tPATH\tSIZE_B\tDATE\tDECISION\tREASON\n")
    for d in decisions:
        f.write("\t".join(str(x) for x in d) + "\n")

# Write stats
with open(stats_file, "w") as f:
    f.write(f"=== Deduplication Stats ===\n")
    f.write(f"Total unique marker names: {len(entries)}\n")
    f.write(f"  Singletons (no duplicates): {unique_count}\n")
    f.write(f"  Groups with duplicates: {dup_groups}\n")
    f.write(f"\nDecisions:\n")
    f.write(f"  KEEP (best or unique): {keep_count}\n")
    f.write(f"  DISCARD (smaller/identical/redundant): {discard_count}\n")
    f.write(f"  NEEDS REVIEW (newer/larger alternative exists): {needs_review_count}\n")
    f.write(f"\nTotal files processed: {sum(len(v) for v in entries.values())}\n")

    # Breakdown of review reasons
    review_reasons = defaultdict(int)
    for d in decisions:
        if "REVIEW" in d[4]:
            review_reasons[d[4]] += 1
    f.write(f"\nReview breakdown:\n")
    for reason, count in sorted(review_reasons.items(), key=lambda x: -x[1]):
        f.write(f"  {reason}: {count}\n")

    # Files to definitely keep
    f.write(f"\n=== KEEP list (canonical markers) ===\n")
    keeps = [(d[0], d[1], d[2]) for d in decisions if d[4].startswith("KEEP")]
    for norm, path, size in sorted(keeps):
        f.write(f"  {norm} -> {path} ({size}B)\n")

print(f"Done. {len(entries)} unique markers, {keep_count} keep, {discard_count} discard, {needs_review_count} review")
print(f"Files: {decision_file}")
print(f"Stats: {stats_file}")
PYEOF
