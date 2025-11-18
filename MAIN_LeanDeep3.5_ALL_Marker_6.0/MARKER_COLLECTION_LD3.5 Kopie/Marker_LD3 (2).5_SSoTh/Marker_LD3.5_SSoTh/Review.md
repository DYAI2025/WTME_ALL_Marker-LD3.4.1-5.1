# Iteration 1 Review

## Changes
- Added toolchain for corpus validation (`tools/audit_markers.py`, `tools/ci_check.py`, `tools/neg_examples_check.py`) plus focussed family audit & smoke simulator.
- Standardised intuition clusters for INCONSISTENCY, CONSISTENCY, EFFICACY, SHUTDOWN, SUPPORT with structured metadata (activation/confirm/decay), telemetry keys, and ≥5 narrative examples each.
- Curated family SEMs feeding those clusters: ensured ≥2 distinct ATO inputs, added rich example suites, and tagged each SEM with its host family.
- Refined supporting ATOs (causal/temporal/contradiction/redefinition/self-reference/silent-treatment) to include explicit patterns and ≥10 examples for consistent detection.
- Introduced synthetic smoke scenarios in `tests/intuition_smoke/` plus simulator to prove confirm/decay flows for every family.

## Tests
- `python3 tools/family_smoke_test.py`
- `python3 tools/ci_check.py --families INCONSISTENCY,CONSISTENCY,EFFICACY,SHUTDOWN,SUPPORT`
- `python3 tools/family_audit.py --families INCONSISTENCY,CONSISTENCY,EFFICACY,SHUTDOWN,SUPPORT`
