# Repository Guidelines

## Project Structure & Module Organization
- Domain packs live in the `LD3.4_*` folders (e.g., `LD3.4_ARCHE`, `LD3.4_BIAS`, `LD3.4_SELF_CONSIST`). Each pack groups LeanDeep 3.4 YAML markers by layer prefix: `ATO_` for atomic signals, `SEM_` for semantic blends, `CLU_` for cluster-level intuitions, and `MEMA_` for meta markers.
- `LD3.4_ALL_Marker_5.1` contains the aggregated release plus the canonical validator (`validate_markers.py`) and CI configuration under `.github/workflows/`.
- `_LeanDeep3.4_ALL_Marker_5.1` and archive ZIPs are frozen snapshots; never edit them. Use the active `LD3.4_*` packs for new work.
- Repository notes such as `LEAN.DEEP_3.4.md` provide background; touch them only when cross-cutting guidance changes.

## Build, Test, and Development Commands
- `python LD3.4_ALL_Marker_5.1/validate_markers.py` — runs the schema and lint suite for CLU markers; fails fast on missing fields, low example counts, or bad telemetry keys.
- `pip install pyyaml` — one-time setup required by the validator.
- `yq -o=json FILE.yaml | jq <expr>` — mirrors CI spot checks (see `.github/workflows/validate_markers.yml` for exact filters).
- `git ls-files '*.yml'` — list tracked marker files before staging changes.

## Coding Style & Naming Conventions
- YAML uses two-space indentation, lower-case keys except for IDs, and inline lists for short collections (e.g., `tags: [atomic, apology, text]`).
- Keep IDs uppercase with their layer prefix (`ATO_APOLOGY`, `SEM_SUPPORT_VALIDATION`, `CLU_INTUITION_TRUST`), and align `namespace` with the host pack.
- Provide diverse `examples`; `CLU_INTUITION_*` entries must ship at least five locally relevant utterances to satisfy CI.
- Use `metadata` for runtime notes and add `justification` when deviating from LeanDeep 3.4 defaults.

## Testing Guidelines
- Run the validator before every commit; it matches CI behavior.
- When editing CLU markers, manually confirm: no container-level `examples`, telemetry keys end with dotted counters, and `activation.cooldown_messages >= 4` whenever `metadata.family` is `INCONSISTENCY`.
- Document edge scenarios in pack-specific notebooks or `testlauf.md` so reviewers can replay reasoning.

## Commit & Pull Request Guidelines
- Use concise, imperative commit titles (e.g., `add CLU_INTUITION_SUPPORT examples`); expand on schema choices in the body when needed.
- Group related marker edits together to keep diffs reviewable and link Jira/GitHub issue IDs where applicable.
- Pull requests should name the affected pack (`[LD3.4_ARCHE]`, `[LD3.4_ALL]`), include validator output, and show before/after snippets when patterns change.
- Flag any required follow-up tasks or dependency updates directly in the PR description to unblock reviewers.
