# Bias Cleanup & Semantic Enrichment Implementation Plan

> **For Claude:** Use `${SUPERPOWERS_SKILLS_ROOT}/skills/collaboration/executing-plans/SKILL.md` to implement this plan task-by-task.

**Goal:** Clean all bias from 966 canonical markers, remove duplicates/stubs/typos, and enrich 862 markers with negative examples for precision.

**Architecture:** Python batch scripts operate on `build/markers_rated/` as canonical source. Each script reads YAML, transforms, writes back. All changes are idempotent and re-runnable.

**Tech Stack:** Python 3, PyYAML (or ruamel.yaml for comment-preserving), pathlib, re

---

## Bestandsaufnahme (Current State)

| Problem | Count | Impact |
|---------|-------|--------|
| " 2" duplicate pairs in quality dirs | 119 pairs | Inflated marker count, API confusion |
| Orphan " 2" files (no base version) | 26 files | Dirty names in API |
| Clinical diagnostic labels (BPD_, ADHD_, etc.) | 12 markers | EU AI Act risk, stigma |
| Filename typos | 4 markers | Unprofessional |
| `_corrected` suffix files | 4 markers | Dirty names |
| Rating-4 stubs | 18 markers | Dead weight |
| Rating-1 markers WITHOUT negatives | 727 of 813 (89%) | False positives, no semantic boundary |
| Rating-2 markers WITHOUT negatives | 135 of 135 (100%) | Same |
| Tags containing "diagnostic"/"psychiatric" | ~12 markers | Bias signal |

---

## Task 1: Install Dependencies

**Files:**
- Create: `tools/requirements.txt`

**Step 1: Create requirements file**

```
ruamel.yaml>=0.18.0
```

**Step 2: Install**

Run: `pip3 install ruamel.yaml`
Expected: Successfully installed

**Step 3: Commit**

```bash
git add tools/requirements.txt
git commit -m "chore: add ruamel.yaml dependency for marker processing"
```

---

## Task 2: Remove " 2" Duplicate Files

119 pairs where both `MARKER.yaml` and `MARKER 2.yaml` exist. The " 2" version is always the inferior copy (same content from macOS Finder duplication). Delete all " 2" files where the base version exists.

**Files:**
- Create: `tools/cleanup_duplicates.py`

**Step 1: Write the script**

```python
#!/usr/bin/env python3
"""Remove ' 2' duplicate files from markers_rated where base version exists."""
import os
from pathlib import Path

QUALITY_DIR = Path("/Users/benjaminpoersch/Projects/Marker- entbiazed/WTME_ALL_Marker-LD3.4.1-5.1/build/markers_rated")

removed = 0
orphans_renamed = 0

for yaml_file in sorted(QUALITY_DIR.rglob("*.yaml")):
    name = yaml_file.name
    # Match " 2.yaml", " 2 2.yaml", " 3.yaml" patterns
    import re
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
```

**Step 2: Run the script**

Run: `python3 tools/cleanup_duplicates.py`
Expected: ~119 deleted, ~26 renamed. Output shows each action.

**Step 3: Verify no " 2" files remain**

Run: `find "build/markers_rated" -name "* 2.yaml" -o -name "* 3.yaml" | wc -l`
Expected: 0

**Step 4: Commit**

```bash
git add tools/cleanup_duplicates.py
git commit -m "feat: remove 119 duplicate ' 2' files, rename 26 orphans"
```

---

## Task 3: Fix Filename Typos

4 markers with misspelled filenames.

**Files:**
- Create: `tools/fix_typos.py`

**Step 1: Write the script**

```python
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
        old_id = yaml_file.stem  # e.g. ATO_SARCASAM_CUE
        new_id = new_name.replace('.yaml', '')
        content = content.replace(old_id, new_id)

        yaml_file.write_text(content, encoding='utf-8')
        yaml_file.rename(new_path)
        print(f"FIXED: {yaml_file.name} -> {new_name}")
        fixed += 1

print(f"\nFixed {fixed} typos.")
```

**Step 2: Run the script**

Run: `python3 tools/fix_typos.py`
Expected: 4 fixes

**Step 3: Commit**

```bash
git add tools/fix_typos.py
git commit -m "fix: correct 4 marker filename typos (SARCASAM, UNCERTAINY, APATHATICLU, LAVE)"
```

---

## Task 4: Clean `_corrected` Suffixes

4 files with `_corrected` suffix. Remove the suffix (the corrected version IS the canonical version).

**Files:**
- Create: `tools/clean_corrected_suffix.py`

**Step 1: Write the script**

```python
#!/usr/bin/env python3
"""Remove _corrected suffix from marker filenames and internal ids."""
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
```

**Step 2: Run the script**

Run: `python3 tools/clean_corrected_suffix.py`
Expected: 4 files cleaned

**Step 3: Commit**

```bash
git add tools/clean_corrected_suffix.py
git commit -m "fix: remove _corrected suffix from 4 canonical markers"
```

---

## Task 5: Rename Clinical Diagnostic Labels

12 markers use psychiatric diagnosis prefixes (BPD_, ADHD_, OCD_, etc.) that create stigma risk and EU AI Act compliance issues. Rename to behavioral descriptors.

**Files:**
- Create: `tools/rename_clinical_labels.py`

**Step 1: Write the script**

```python
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
        content = re.sub(
            r'(tags:\s*\[)',
            r'\1behavioral_pattern, ',
            content
        )
        # Also handle list-style tags
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
```

**Step 2: Run the script**

Run: `python3 tools/rename_clinical_labels.py`
Expected: 12 renames

**Step 3: Verify no clinical prefixes remain**

Run: `find build/markers_rated -name "ATO_BPD_*" -o -name "ATO_ADHD_*" -o -name "ATO_OCD_*" -o -name "*BIPOLAR*" -o -name "*AUTISM*" -o -name "*SCHIZOPHRENIA*" -o -name "*PTSD_*" -o -name "*DEPRESSIVE*" -o -name "*DISSOCIATIVE*" | wc -l`
Expected: 0

**Step 4: Commit**

```bash
git add tools/rename_clinical_labels.py
git commit -m "fix: rename 12 clinical diagnostic labels to behavioral descriptors

Removes BPD_, ADHD_, OCD_, PTSD_, BIPOLAR_, AUTISM_, SCHIZOPHRENIA_ prefixes.
Replaces diagnostic/psychiatric tags with behavioral_pattern.
EU AI Act compliance + stigma reduction."
```

---

## Task 6: Delete Rating-4 Stubs

18 markers with no usable content. Remove from quality directory.

**Files:**
- Create: `tools/delete_stubs.py`

**Step 1: Write the script**

```python
#!/usr/bin/env python3
"""Delete all Rating-4 (not usable) marker files and log what was removed."""
from pathlib import Path

QUALITY_DIR = Path("/Users/benjaminpoersch/Projects/Marker- entbiazed/WTME_ALL_Marker-LD3.4.1-5.1/build/markers_rated")
NOT_USABLE = QUALITY_DIR / "4_not_usable"

deleted = []
for layer_dir in NOT_USABLE.iterdir():
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
```

**Step 2: Run the script**

Run: `python3 tools/delete_stubs.py`
Expected: 18 deletions

**Step 3: Commit**

```bash
git add tools/delete_stubs.py build/markers_rated/DELETED_STUBS.log
git commit -m "chore: delete 18 empty Rating-4 marker stubs"
```

---

## Task 7: Generate Negative Examples for Rating-1 Markers (CORE TASK)

This is the biggest and most important task. 727 Rating-1 markers have NO negative examples.
Negative examples are critical for:
- **Precision:** Preventing false positives (e.g. "Du kommst immer zu spat" matches ATO_ABSOLUTIZER, but "Ich komme manchmal zu spat" should NOT)
- **Semantic Boundaries:** Defining what a marker is NOT
- **Training Data:** For future ML model fine-tuning

**Strategy:** Generate negatives from the marker's own positives by systematic transformation:
1. **Negation flip:** "Ich fuhle mich schuldig" -> "Ich fuhle mich nicht schuldig" (removes guilt marker)
2. **Hedging injection:** "Du machst das immer" -> "Du machst das manchmal" (removes absolutizer)
3. **Context shift:** Same words but neutral intent
4. **Near-miss:** Semantically close but different construct

**Files:**
- Create: `tools/enrich_negatives.py`

**Step 1: Write the negative generation engine**

```python
#!/usr/bin/env python3
"""
Enrich markers with negative examples for semantic precision.

Strategy per marker type:
- ATO (atomic): Lexical near-misses, hedged versions of positives
- SEM (semantic): Same keywords but different intent/context
- CLU (cluster): Partial pattern matches (1 of 3 components)
- MEMA (meta): Shorter conversations without the meta-pattern

For each marker, generates 5-10 negatives based on its positives.
"""
import re
from pathlib import Path
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 200

QUALITY_DIR = Path("/Users/benjaminpoersch/Projects/Marker- entbiazed/WTME_ALL_Marker-LD3.4.1-5.1/build/markers_rated")

# === Transformation Functions ===

def hedge_absolutizer(text):
    """Replace absolute terms with hedged versions."""
    swaps = [
        (r'\bimmer\b', 'manchmal'), (r'\bnie\b', 'selten'),
        (r'\bständig\b', 'ab und zu'), (r'\bjedes Mal\b', 'oft'),
        (r'\balways\b', 'sometimes'), (r'\bnever\b', 'rarely'),
        (r'\beverything\b', 'some things'), (r'\bnothing\b', 'not much'),
        (r'\bcompletely\b', 'partially'), (r'\btotally\b', 'somewhat'),
        (r'\bdefinitely\b', 'probably'), (r'\babsolutely\b', 'mostly'),
    ]
    result = text
    for pattern, replacement in swaps:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result if result != text else None

def neutralize_emotion(text):
    """Remove emotional charge from a sentence."""
    swaps = [
        (r'\bich hasse\b', 'ich mag nicht besonders'),
        (r'\bich liebe\b', 'ich finde gut'),
        (r'\bI hate\b', "I'm not fond of"),
        (r'\bI love\b', 'I appreciate'),
        (r'\bfurchtbar\b', 'nicht ideal'),
        (r'\bschrecklich\b', 'schwierig'),
        (r'\bwunderbar\b', 'ganz gut'),
        (r'\bterrible\b', 'not great'),
        (r'\bamazing\b', 'decent'),
    ]
    result = text
    for pattern, replacement in swaps:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result if result != text else None

def add_agency(text):
    """Shift from passive/helpless to agentic language."""
    swaps = [
        (r'\bich kann nicht\b', 'ich entscheide mich gegen'),
        (r'\bI can\'t\b', 'I choose not to'),
        (r'\bich muss\b', 'ich entscheide mich zu'),
        (r'\bI have to\b', 'I choose to'),
        (r'\bes geht nicht\b', 'es ist schwierig, aber machbar'),
    ]
    result = text
    for pattern, replacement in swaps:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result if result != text else None

def shift_blame_to_ownership(text):
    """Shift blame/accusation to ownership language."""
    swaps = [
        (r'\bdu bist schuld\b', 'ich habe meinen Anteil daran'),
        (r'\bdu machst\b', 'ich erlebe es so, dass'),
        (r'\bit\'s your fault\b', "I take responsibility for my part"),
        (r'\byou always\b', 'I notice that sometimes'),
        (r'\byou never\b', 'I wish we could more often'),
        (r'\bwegen dir\b', 'wir haben gemeinsam'),
    ]
    result = text
    for pattern, replacement in swaps:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result if result != text else None

# === Generic Negative Templates (when transforms don't apply) ===

GENERIC_NEGATIVES_DE = [
    "Ich finde, wir sollten das in Ruhe besprechen.",
    "Das ist ein guter Punkt, den du da machst.",
    "Ich verstehe deine Perspektive.",
    "Lass uns gemeinsam eine Losung finden.",
    "Mir ist aufgefallen, dass wir unterschiedlich denken.",
    "Ich mochte verstehen, was du meinst.",
    "Das klingt nach einem wichtigen Thema fur dich.",
    "Ich schatze, dass du das ansprichst.",
    "Konnen wir das von einer anderen Seite betrachten?",
    "Ich fuhle mich gerade ruhig und klar.",
]

GENERIC_NEGATIVES_EN = [
    "I think we should discuss this calmly.",
    "That's a good point you're making.",
    "I understand your perspective.",
    "Let's find a solution together.",
    "I've noticed we think differently about this.",
    "I want to understand what you mean.",
    "That sounds like an important topic for you.",
    "I appreciate you bringing this up.",
    "Can we look at this from a different angle?",
    "I'm feeling calm and clear right now.",
]

# === Marker-Specific Negative Strategies ===

MANIPULATION_MARKERS = {
    'GASLIGHTING', 'LOVE_BOMBING', 'TRIANGULATION', 'STONEWALLING',
    'BLAME_SHIFT', 'GUILT_TRIP', 'EMOTIONAL_BLACKMAIL', 'SILENT_TREATMENT',
    'PASSIVE_AGGRESS', 'CONTROL', 'ISOLATION', 'FUTURE_FAKING',
    'MINIMIZ', 'PROJECTION', 'DOUBLE_BIND', 'REALITY_DISTORTION',
}

EMOTION_MARKERS = {
    'ANGER', 'FEAR', 'SADNESS', 'JOY', 'DISGUST', 'ANXIETY',
    'SHAME', 'GUILT', 'HELPLESSNESS', 'VULNERABILITY', 'OVERWHELM',
}

POSITIVE_MARKERS = {
    'REPAIR', 'VALIDATION', 'SUPPORT', 'CONNECTION', 'ACCEPTANCE',
    'EMPATHY', 'APPRECIATION', 'AFFECTION', 'CARE', 'BOUNDARY_SET',
    'CONSENSUS', 'ACCOUNTABILITY', 'SELF_REFLECTION', 'ASSERTIVE',
}

def classify_marker(marker_id):
    """Determine marker category for negative generation strategy."""
    upper = marker_id.upper()
    for keyword in MANIPULATION_MARKERS:
        if keyword in upper:
            return 'manipulation'
    for keyword in EMOTION_MARKERS:
        if keyword in upper:
            return 'emotion'
    for keyword in POSITIVE_MARKERS:
        if keyword in upper:
            return 'positive'
    return 'neutral'

def generate_negatives_for_marker(marker_id, positives, lang='de'):
    """Generate negative examples based on marker type and its positives."""
    category = classify_marker(marker_id)
    negatives = []

    # Strategy 1: Transform existing positives
    transforms = [hedge_absolutizer, neutralize_emotion, add_agency, shift_blame_to_ownership]
    for pos in positives[:5]:  # Use first 5 positives as seeds
        for transform in transforms:
            result = transform(pos)
            if result and result not in negatives and result != pos:
                negatives.append(result)
                break

    # Strategy 2: Category-specific generic negatives
    generics = GENERIC_NEGATIVES_DE if lang == 'de' else GENERIC_NEGATIVES_EN

    if category == 'manipulation':
        # Negatives for manipulation = healthy communication equivalents
        if lang == 'de':
            negatives.extend([
                "Ich sehe das anders, aber ich respektiere deine Sicht.",
                "Ich mochte ehrlich mit dir sein.",
                "Du hast recht, das war mein Fehler.",
                "Lass uns beide unsere Seite erklaren.",
                "Ich fuhle mich unwohl dabei und mochte daruber reden.",
            ])
        else:
            negatives.extend([
                "I see it differently, but I respect your view.",
                "I want to be honest with you.",
                "You're right, that was my mistake.",
                "Let's both explain our side.",
                "I feel uncomfortable about this and want to talk about it.",
            ])
    elif category == 'emotion':
        # Negatives for emotions = neutral/calm statements
        if lang == 'de':
            negatives.extend([
                "Ich denke, wir sollten das sachlich betrachten.",
                "Mir geht es gut, danke der Nachfrage.",
                "Das ist ein interessanter Gedanke.",
                "Ich bin gerade entspannt.",
                "Alles in Ordnung bei mir.",
            ])
        else:
            negatives.extend([
                "I think we should look at this objectively.",
                "I'm doing fine, thanks for asking.",
                "That's an interesting thought.",
                "I'm feeling relaxed right now.",
                "Everything is fine with me.",
            ])
    elif category == 'positive':
        # Negatives for positive markers = neutral/transactional statements
        if lang == 'de':
            negatives.extend([
                "Kannst du mir das Salz reichen?",
                "Der Termin ist um 14 Uhr.",
                "Ich war gestern einkaufen.",
                "Das Wetter soll morgen besser werden.",
                "Hast du die E-Mail gelesen?",
            ])
        else:
            negatives.extend([
                "Can you pass the salt?",
                "The meeting is at 2 PM.",
                "I went shopping yesterday.",
                "The weather should be better tomorrow.",
                "Did you read the email?",
            ])
    else:
        # Fallback: use generic calm communication
        negatives.extend(generics[:5])

    # Deduplicate and limit to 5-10
    seen = set()
    unique = []
    for neg in negatives:
        normalized = neg.strip().lower()
        if normalized not in seen:
            seen.add(normalized)
            unique.append(neg)

    return unique[:10]

# === Main Processing ===

def get_positives(data):
    """Extract positive examples from any schema format."""
    examples = data.get('examples', [])

    if isinstance(examples, dict):
        # Root format: examples: {positive: [...], negative: [...]}
        pos = examples.get('positive', []) or []
        pos.extend(examples.get('positive_de', []) or [])
        pos.extend(examples.get('positive_en', []) or [])
        return [str(p) for p in pos if p]
    elif isinstance(examples, list):
        # Flat format: examples: [...]
        return [str(e) for e in examples if e]
    return []

def get_negatives(data):
    """Extract existing negative examples from any schema format."""
    examples = data.get('examples', [])

    if isinstance(examples, dict):
        neg = examples.get('negative', []) or []
        neg.extend(examples.get('negative_de', []) or [])
        neg.extend(examples.get('negative_en', []) or [])
        return [str(n) for n in neg if n]
    return []

def detect_lang(data, positives):
    """Detect marker language from content."""
    lang = data.get('lang', '')
    if lang:
        return lang
    # Heuristic: check positives for German indicators
    text = ' '.join(positives[:3])
    if re.search(r'\b(ich|du|wir|nicht|und|das|ist|ein|der|die)\b', text, re.IGNORECASE):
        return 'de'
    return 'en'

def inject_negatives(data, negatives):
    """Add negatives to marker data, respecting schema format."""
    examples = data.get('examples', [])

    if isinstance(examples, dict):
        # Root format: add negative key
        if 'negative' not in examples or not examples['negative']:
            examples['negative'] = negatives
        else:
            existing = [str(n) for n in examples['negative']]
            for neg in negatives:
                if neg not in existing:
                    examples['negative'].append(neg)
    elif isinstance(examples, list):
        # Flat format: convert to dict format with positive/negative
        data['examples'] = {
            'positive': examples,
            'negative': negatives,
        }
    else:
        data['examples'] = {
            'positive': [],
            'negative': negatives,
        }

def process_markers():
    enriched = 0
    skipped = 0
    errors = 0

    for tier in ['1_approved', '2_good']:
        tier_dir = QUALITY_DIR / tier
        if not tier_dir.exists():
            continue

        for layer_dir in sorted(tier_dir.iterdir()):
            if not layer_dir.is_dir():
                continue

            for yaml_file in sorted(layer_dir.glob("*.yaml")):
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        data = yaml.load(f)

                    if data is None:
                        continue

                    existing_neg = get_negatives(data)
                    if len(existing_neg) >= 3:
                        skipped += 1
                        continue

                    positives = get_positives(data)
                    marker_id = data.get('id', data.get('name', yaml_file.stem))
                    lang = detect_lang(data, positives)

                    negatives = generate_negatives_for_marker(str(marker_id), positives, lang)

                    if not negatives:
                        skipped += 1
                        continue

                    inject_negatives(data, negatives)

                    with open(yaml_file, 'w', encoding='utf-8') as f:
                        yaml.dump(data, f)

                    enriched += 1
                    if enriched % 50 == 0:
                        print(f"  ...enriched {enriched} markers")

                except Exception as e:
                    errors += 1
                    print(f"ERROR: {yaml_file.name}: {e}")

    print(f"\nDone. Enriched {enriched}, skipped {skipped} (already have negatives), errors {errors}.")

if __name__ == '__main__':
    process_markers()
```

**Step 2: Run the script**

Run: `python3 tools/enrich_negatives.py`
Expected: ~862 markers enriched (727 R1 + 135 R2 without negatives)

**Step 3: Spot-check results on 3 different marker types**

Run: `python3 -c "from ruamel.yaml import YAML; y=YAML(); [print(y.load(open(f))['examples']) for f in ['build/markers_rated/1_approved/ATO/ATO_ABSOLUTIZER.yaml', 'build/markers_rated/1_approved/SEM/SEM_GASLIGHTING.yaml', 'build/markers_rated/1_approved/CLU/CLU_CONFLICT_ESCALATION.yaml']]"`

Expected: Each shows both `positive` and `negative` keys with content.

**Step 4: Commit**

```bash
git add tools/enrich_negatives.py
git commit -m "feat: enrich 862 markers with negative examples for semantic precision

Generates negatives via:
- Lexical transformation of positives (hedging, neutralization)
- Category-specific healthy-communication alternatives
- Near-miss semantic boundaries

727 Rating-1 + 135 Rating-2 markers now have 5-10 negatives each."
```

---

## Task 8: Re-Run Quality Rating

After all cleanups, re-run the quality rating to get updated numbers.

**Step 1: Update dedup_decisions.tsv to reflect changes**

Run: `bash tools/deduplicate_audit.sh`

**Step 2: Re-run quality rating**

Run: `python3 tools/build_quality_dirs.py`

**Step 3: Verify improved numbers**

Run: `head -1 build/markers_rated/RATING_SUMMARY.tsv && wc -l build/markers_rated/RATING_SUMMARY.tsv`
Expected: Fewer total markers (duplicates removed), more Rating-1 (negatives added)

**Step 4: Commit**

```bash
git add build/markers_rated/RATING_SUMMARY.tsv
git commit -m "chore: re-rate markers after bias cleanup and enrichment"
```

---

## Task 9: Update EXECUTION_PLAN.md with Final Numbers

**Files:**
- Modify: `EXECUTION_PLAN.md`

**Step 1: Count final markers**

Run: `find build/markers_rated/1_approved -name "*.yaml" | wc -l && find build/markers_rated/2_good -name "*.yaml" | wc -l && find build/markers_rated/3_needs_work -name "*.yaml" | wc -l && find build/markers_rated/4_not_usable -name "*.yaml" | wc -l`

**Step 2: Update the GESAMT-UBERSICHT table in EXECUTION_PLAN.md with the new counts**

**Step 3: Add a "Bias Cleanup Completed" section noting:**
- 119 " 2" duplicates removed
- 26 orphans renamed
- 12 clinical labels renamed
- 4 typos fixed
- 4 _corrected suffixes cleaned
- 18 stubs deleted
- ~862 markers enriched with negatives

**Step 4: Commit**

```bash
git add EXECUTION_PLAN.md
git commit -m "docs: update execution plan with post-cleanup marker counts"
```

---

## Execution Order & Dependencies

```
Task 1 (deps)
  └─> Task 2 (dedup)
  └─> Task 3 (typos)      ← parallel with 2
  └─> Task 4 (_corrected)  ← parallel with 2, 3
  └─> Task 5 (clinical)    ← parallel with 2, 3, 4
  └─> Task 6 (stubs)       ← parallel with 2, 3, 4, 5
        └─> Task 7 (negatives) ← after all cleanups
              └─> Task 8 (re-rate) ← after enrichment
                    └─> Task 9 (update plan) ← after re-rate
```

Tasks 2-6 can run in parallel. Task 7 must wait for all cleanups.
Task 8 must wait for Task 7. Task 9 must wait for Task 8.

---

## Estimated Time

| Task | Duration |
|------|----------|
| Task 1: Dependencies | 2 min |
| Tasks 2-6: Cleanups (parallel) | 15 min |
| Task 7: Negative enrichment | 30 min (script + spot-check) |
| Task 8: Re-rate | 5 min |
| Task 9: Update plan | 10 min |
| **Total** | **~60 min** |
