# Repository Guidelines

## Project Structure & Module Organization
LeanDeep 3.4 domain packs live under `LD3.4_*` (e.g., `LD3.4_ARCHE`) grouped by layer prefixes: `ATO_atomic`, `SEM_semantic`, `CLU_cluster`, `MEMA_meta`. Use `LD3.4_ALL_Marker_5.1` for active aggregation, validation, and CI assets; `_LeanDeep3.4_ALL_Marker_5.1` and zip archives are frozen snapshots. Engine sources reside in `extension/src`, bundled artifacts in `extension/dist`, and marker family wiring in `markers/families.json`.

## Build, Test, and Development Commands
`npm run setup` installs extension dependencies; rerun if `package.json` changes. `npm run build:ext` regenerates `extension/dist/*` for local Chrome loads. Validate CLU markers with `python3 validate_markers.py`; install prerequisites once via `pip install pyyaml`. Spot-check schema fields with `yq -o=json ALL_Marker_5.1/CLU_cluster/*.yml | jq '<expr>'` to mirror CI filters.

## Coding Style & Naming Conventions
YAML markers use two-space indentation, lowercase keys, and uppercase IDs with layer prefixes (`ATO_`, `SEM_`, `CLU_`, `MEMA_`). Align each marker’s `namespace` with its source pack and keep inline lists concise (e.g., `tags: [atomic, apology, text]`). Provide diverse `examples`; `CLU_INTUITION_*` entries must ship at least five. Document deviations via `metadata` and `justification`. TypeScript in `extension/` follows the repo’s `tsconfig.json` and ships through `tsup`.

## Testing Guidelines
Always run `python3 validate_markers.py` before committing, especially after editing CLU files in `ALL_Marker_5.1/CLU_cluster`. For `metadata.family: INCONSISTENCY`, confirm `activation.cooldown_messages >= 4` and ensure telemetry keys end with dotted counters. Smoke-test the extension using `extension/dist/devset.jsonl` to confirm ATO→SEM→CLU propagation. Record nuanced edge cases in pack notebooks or `testlauf.md` for reviewer replay.

## Commit & Pull Request Guidelines
Write imperative commit titles (`add CLU_INTUITION_SUPPORT examples`) and group related marker edits together. Reference Jira/GitHub issues when relevant. PR titles should tag the pack (`[LD3.4_ARCHE]`) and share validator output plus before/after snippets if patterns change. Flag follow-up tasks or dependencies directly in the PR description to keep reviewers unblocked.

