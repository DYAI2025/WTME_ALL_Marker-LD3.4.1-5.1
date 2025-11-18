# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the **LeanDeep Marker Collection** (version 5.1), a comprehensive linguistic marker system for detecting and analyzing conversational patterns, emotional states, relationship dynamics, and psychological indicators in text-based communication. The system uses YAML-based marker definitions organized in a hierarchical architecture.

**Core Purpose**: Define pattern-based markers that detect linguistic, emotional, and behavioral signals in conversations across multiple languages (primarily German and English).

## Architecture

### Hierarchical Marker System

The marker system follows a four-tier hierarchy from atomic patterns to meta-patterns:

1. **ATO (Atomic)** - Base-level lexical/pattern markers (329 markers)
   - Single regex patterns or word lists
   - Example: `ATO_ABSOLUTIZER` detects absolutist language ("immer", "nie", "ständig")
   - Activation: Usually "ANY 1" pattern match

2. **SEM (Semantic)** - Meaning bundles composed of 2+ ATOs (260 markers)
   - Combine atomic markers to detect semantic concepts
   - Example: `SEM_LIGHT_HUMOR_CRITIQUE` = ATO_CRITIQUE_ELEMENT + ATO_HUMOR_SIGNAL
   - Activation: Typically "ANY 2 IN 3 messages"

3. **CLU (Cluster)** - Emergent patterns from repeated SEMs (91 markers)
   - Detect recurring patterns over message windows
   - Example: `CLU_DEPRESSIVE_TRIAD` combines multiple depression-related SEMs
   - Activation: "AT_LEAST 2 DISTINCT SEMs IN X messages"
   - Window-based scoring with decay

4. **MEMA (Meta)** - High-level trend analysis (45 markers)
   - Aggregate CLUs and SEMs for systemic patterns
   - Example: `MEMA_DEPRESSIVE_LANGUAGE_PROFILE` integrates 5 ATOs + 1 CLU
   - Used for diagnostic/clinical assessment patterns

### Directory Structure

```
ALL_Marker_5.1/                    # Main marker collection (current working directory)
├── ATO_atomic/                    # 329 atomic markers
├── SEM_semantic/                  # 260 semantic markers (.yaml and .yml)
├── CLU_cluster/                   # 91 cluster markers
├── MEMA_meta/                     # 45 meta markers
├── Marker_LeanDeep3.4/            # 729 compiled markers (all categories)
├── EXPLAINABILITY_TEMPLATE.yaml   # Template for marker explanations

../LD3.4_THERA/                    # Therapeutic/psychiatric markers
├── ATO/                           # Depression, BPD, ADHD, autism, bipolar markers
├── CLU/                           # Attachment styles, intuition clusters
├── MEMA/                          # Clinical meta-patterns
├── SEM/                           # Therapeutic semantic markers

../LD3.4_ARCHE/                    # Archetypal patterns
../LD3.4_BIAS/                     # Cognitive bias markers
../LD3.4_LOVE_LANGUAGES_CONTEXT_GATED/  # Relationship communication patterns
../LD3.4_PRESENCE_BINDING/         # Presence and connection markers
../LD3.4_SCIENT/                   # Scientific communication markers
../LD3.4_SELF_CONSIST/             # Self-consistency markers
../LD3.4.1_DRIFT/                  # Drift detection markers

../LeanDeep_Addition 0.0.1/
├── schemas/
│   ├── LD_3.4.1_marker.schema.json    # JSON schema for marker validation
│   └── explainability.schema.json     # Explainability output schema
└── core_bundle_manifest.json
```

## Marker File Schema (LeanDeep 3.4)

### Required Fields

All markers must follow the LeanDeep 3.4 schema:

```yaml
schema: "LeanDeep"            # Schema identifier
version: "3.4"                # Schema version
namespace: "ld34_text_social_grammar"  # Namespace (for ATOs typically)
id: MARKER_ID                 # Unique identifier (ATO_*, SEM_*, CLU_*, MEMA_*)
lang: de|en                   # Language code
category: ATOMIC|SEMANTIC|CLUSTER|META
description: "Brief description"

frame:                        # Semantic frame (required)
  signal: ["key", "phrases"]  # Observable signals
  concept: "Core concept"     # Abstract concept being detected
  pragmatics: "Function"      # Pragmatic function in conversation
  narrative: "Story role"     # Narrative framing
```

### Category-Specific Fields

**ATOMIC markers:**
```yaml
pattern:                      # Regex patterns for detection
  - '(?i)\bpattern1\b'
  - '(?i)\bpattern2\b'
activation_logic: "ANY 1"     # Activation rule
examples:                     # Example sentences
  - "Example sentence 1"
  - "Example sentence 2"
tags: [atomic, keyword]
metadata:                     # Optional metadata
  repair_log:
    - { rule: "R09", note: "Frame added", date: "2025-08-29" }
```

**SEMANTIC markers:**
```yaml
composed_of:                  # Component markers
  - ATO_MARKER_1
  - ATO_MARKER_2
activation_logic: "ANY 2 IN 3 messages"
scoring: { base: 1.4, weight: 1.1 }
examples: [...]
```

**CLUSTER markers:**
```yaml
composed_of:
  - { marker_ids: [SEM_MARKER_1], weight: 0.6 }
  - { marker_ids: [SEM_MARKER_2], weight: 0.5 }
activation:
  rule: "AT_LEAST 2 DISTINCT SEMs IN 24 messages"
window:
  messages: 50
scoring:
  base: 2.0
  weight: 1.3
  decay: 0.01
  formula: "logistic"
```

**META markers:**
```yaml
components:                   # List of component marker IDs
  - ATO_MARKER_1
  - CLU_MARKER_2
pattern:
  - "Complex meta-pattern description"
examples:
  positive:                   # Examples that SHOULD match
    - "Example 1"
  negative:                   # Examples that should NOT match
    - "Example 2"
```

## Common Development Tasks

### Creating a New Marker

1. **Determine the appropriate category** (ATO, SEM, CLU, or MEMA)
2. **Choose the correct directory**:
   - General markers → `ALL_Marker_5.1/[category]_[type]/`
   - Therapeutic markers → `LD3.4_THERA/[category]/`
3. **Use the naming convention**: `[CATEGORY]_[DESCRIPTIVE_NAME].yaml`
4. **Follow the schema** as documented above
5. **Include at least 5 examples** (or positive/negative examples for meta markers)

### Validating Markers

Markers should conform to the JSON schema at:
`../LeanDeep_Addition 0.0.1/schemas/LD_3.4.1_marker.schema.json`

### Testing Examples

Use the `examples` field to validate marker behavior. For therapeutic/diagnostic markers in `LD3.4_THERA`, include both `positive` (should match) and `negative` (should not match) examples.

### Pattern Writing Guidelines

- Use case-insensitive regex: `(?i)` flag
- Use word boundaries: `\b` for whole-word matching
- Escape special characters properly
- Test patterns against both positive and negative examples
- For German markers, include common variations (e.g., "aber" vs "nur")

## Domain-Specific Notes

### Therapeutic Markers (LD3.4_THERA)

This collection includes clinically-informed markers for:
- **Depression**: Negative emotions, absolutist language, self-focus, past-focus, suicide risk
- **BPD**: Fear of abandonment, intense emotions
- **ADHD**: Disorganized thoughts
- **Autism**: Literal language patterns
- **Bipolar**: Manic speech patterns
- **Attachment Styles**: Anxious, avoidant, secure patterns

Recent additions (per git log):
- 5 ATO depression markers
- 1 CLU depressive triad marker
- 1 MEMA depressive language profile marker

Simulation testing shows 80-100% positive hit rates with 0-40% false positive rates.

### Frame Semantics

The `frame` structure is core to the LeanDeep system and must be complete:
- **signal**: Observable surface features (words, phrases)
- **concept**: Abstract meaning being detected
- **pragmatics**: What the speaker is DOING (function in interaction)
- **narrative**: Role in the conversational story

### Metadata and Repair Logs

Markers include repair logs documenting schema compliance fixes:
- R08: Examples added
- R09: Frame completed
- R10: ATO-default activation set

## File Formats

- Primary format: YAML (`.yaml`)
- Some semantic markers use `.yml` extension (both are valid)
- Schema validation: JSON Schema (`.json`)

## Multi-Language Support

- Markers support `lang: de` (German) and `lang: en` (English)
- Some markers include bilingual examples
- Pattern regex should account for language-specific orthography
