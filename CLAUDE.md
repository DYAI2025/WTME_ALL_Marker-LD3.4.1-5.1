# CLAUDE.md - WTME Marker Toolchain (LeanDeep 3.4/3.5)

## Project Overview

LeanDeep marker system for detecting psychological/conversational patterns in text. Four-layer architecture: **ATO** (atomic signals) -> **SEM** (semantic blends) -> **CLU** (cluster intuitions) -> **MEMA** (meta markers). Includes TypeScript toolchain, Chrome extension, and embedding-based evaluation.

## Architecture

- **Root YAML files**: Legacy/flat marker definitions (`ATO_*.yaml`, `SEM_*.yaml`, `CLU_*.yaml`, `MEMA_*.yaml`)
- **LD3.4_ALL_Marker_5.1/**: Aggregated v5.1 release with Python validator and CI workflows
- **MAIN_LeanDeep3.5_ALL_Marker_6.0/**: Next-gen v6.0 release (integrates Resonance Framework 2.0)
- **tools/**: TypeScript automation scripts (linking, validation, compilation, eval, crawling)
- **extension/**: Chrome Manifest v3 extension for live marker detection
- **models/**: Local Xenova `all-MiniLM-L6-v2` ONNX model for embeddings
- **dist/**: Generated artifacts (`marker_registry.json`, `devset.jsonl`, crawl exports)

## Build & Development Commands

```bash
npm install                  # Install dependencies
npm run setup                # Full bootstrap (check node, install, build, pack extension)
npm run validate             # Run marker schema/lint validation (tsx tools/validate_markers.ts)
npm run link:markers         # Auto-fill composed_of links between markers
npm run compile:markers      # Build dist/marker_registry.json
npm run eval                 # Evaluate precision/recall/F1 against dist/devset.jsonl
npm run crawl -- <urls>      # Active-learning crawler
npm run merge:auto           # Merge top auto-generated examples into markers
npm run review:gui           # Start review GUI on port 5173
npm run build:ext            # Build Chrome extension
npm run watch                # File watcher: auto link+compile on marker changes
```

Python validator (LD3.4):
```bash
pip install pyyaml
python3 LD3.4_ALL_Marker_5.1/validate_markers.py
```

## Marker YAML Conventions

- Two-space indentation, lowercase keys (uppercase for IDs only)
- IDs prefixed by layer: `ATO_HESITATION_VOICE`, `SEM_BLAME_SHIFT`, `CLU_INTUITION_CONFLICT`, `MEMA_RAPPORT_DYNAMICS`
- `namespace` must match host pack
- SEM markers require `composed_of` with >= 2 ATO references
- CLU markers need `confirm_window >= 1`; INCONSISTENCY family requires `cooldown_messages >= 4`
- CLU_INTUITION_* need >= 5 localized examples
- Inline short lists: `tags: [atomic, apology, text]`
- Negatives go in marker `negatives:` field; global hard-negatives in `negatives/hard_negatives.jsonl`

## Evaluation Targets

- ATO/SEM Precision >= 0.85
- ATO/SEM Recall >= 0.70
- Uncertain cases (score 0.53-0.60) flagged for review

## Key Files

| File | Purpose |
|------|---------|
| `core_bundle_manifest.json` | Bundle version & artifact hashes (v3.1.4) |
| `LeanDeep_3.5.md` | SSoT specification document |
| `AGENTS.md` | Agent guidelines for this repo |
| `bootstrap.sh` | Setup automation script |
| `review_gui.html` | Review interface HTML |
| `NEG_EXAMPLES.yaml` | Curated negative examples collection |
| `tsconfig.json` | TypeScript config for toolchain |

## Workflow

1. Edit/add markers in root YAML or pack directories
2. `npm run validate` before committing
3. `npm run link:markers` to auto-fill cross-references
4. `npm run compile:markers` to rebuild registry
5. `npm run eval` to check precision/recall
6. `npm run build:ext` to update Chrome extension

## Commit Style

Imperative titles referencing affected pack: `add CLU_INTUITION_SUPPORT examples`, `[LD3.4_ARCHE] refresh atomic apologies`. Include validator output in PRs.
