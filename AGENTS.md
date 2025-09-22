# Repository Guidelines

## Project Structure & Module Organization
LeanDeep 3.4 packs live in the `LD3.4_*` directories such as `LD3.4_ARCHE`, `LD3.4_BIAS`, and `LD3.4_SELF_CONSIST`; each pack stores YAML markers grouped by layer prefix (`ATO_` for atomic signals, `SEM_` for semantic blends, `CLU_` for cluster intuitions, `MEMA_` for meta markers). `LD3.4_ALL_Marker_5.1` keeps the aggregated release, the canonical validator at `LD3.4_ALL_Marker_5.1/validate_markers.py`, and CI rules under `.github/workflows/`. Treat `_LeanDeep3.4_ALL_Marker_5.1` and archive ZIPs as read-only snapshots and rely on `LEAN.DEEP_3.4.md` plus pack-level `testlauf.md` notes for historical context.

## Build, Test, and Development Commands
- `pip install pyyaml` — install the validator dependency once per workstation.
- `python3 LD3.4_ALL_Marker_5.1/validate_markers.py` — run the schema and lint suite before committing changes (the repo ships only with `python3`).
- `yq -o=json LD3.4_ARCHE/CLU_cluster/example.yaml | jq '.metadata'` — preview structured fields the same way CI inspects them.
- `git ls-files '*.yml'` — confirm which marker files are tracked prior to staging.

## Coding Style & Naming Conventions
YAML uses two-space indentation and lower-case keys except for uppercase IDs. Keep IDs prefixed by their layer (e.g., `SEM_SUPPORT_VALIDATION`) and ensure the `namespace` matches the host pack. Inline short lists (`tags: [atomic, apology, text]`), maintain diverse `examples`, and record deviations in `metadata` or `justification` rather than free-form notes.

## Testing Guidelines
Run the validator whenever you touch marker files and again before pushing. For `CLU_INTUITION_*` entries, supply at least five localized examples, keep telemetry counters dotted (e.g., `telemetry.counter.total`), and enforce `activation.cooldown_messages >= 4` when `metadata.family` is `INCONSISTENCY`. Avoid container-level `examples` blocks and capture edge scenarios in the relevant `testlauf.md` so reviewers can replay reasoning.

## Commit & Pull Request Guidelines
Write concise, imperative commit titles like `add CLU_INTUITION_SUPPORT examples`, grouping related marker edits by pack. PR titles should call out the affected pack (e.g., `[LD3.4_ARCHE] refresh atomic apologies`), include the latest validator output, and highlight meaningful before/after snippets when telemetry or activation logic changes. Link Jira/GitHub issues when applicable and flag any follow-up or dependency updates directly in the PR description.
