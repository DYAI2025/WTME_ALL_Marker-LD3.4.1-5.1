#!/usr/bin/env python3
"""LeanDeep continuous integration checks.

Validates core structural rules that must hold before shipping marker packs.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Iterable, Sequence

# Ensure repository root is on sys.path for module imports
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.audit_markers import (
    CANONICAL_PREFIXES,
    MarkerRecord,
    resolve_roots,
    scan_markers,
)

REQUIRED_TELEMETRY_KEYS = {"counter_confirmed", "counter_retracted", "ewma_precision"}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run structural CI checks on markers")
    parser.add_argument(
        "roots",
        nargs="*",
        help="Directories/files to include (defaults to Markers_canonical.json if present)",
    )
    parser.add_argument(
        "--families",
        help="Optional comma-separated list of intuition families to focus on",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    roots = resolve_roots(args.roots)
    report = scan_markers(roots)

    errors: list[str] = []
    warnings: list[str] = []

    # propagate loader issues immediately
    if report["parse_errors"]:
        for entry in report["parse_errors"]:
            errors.append(f"YAML parse error: {entry['file']} — {entry['error']}")

    if report["missing_ids"]:
        for entry in report["missing_ids"]:
            errors.append(f"Marker missing id in {entry['file']} (index {entry['index']})")

    records: Iterable[MarkerRecord] = report["records"]
    focus_ids = _determine_focus_ids(records, args.families)
    id_registry = {rec.id for rec in records}

    for rec in records:
        if focus_ids is not None and rec.id not in focus_ids:
            continue

        prefix = rec.prefix

        # enforce canonical prefixes only for core layers; collect warnings otherwise
        if prefix not in CANONICAL_PREFIXES:
            warnings.append(f"Non-canonical prefix {prefix} for {rec.id} ({_rel(rec.file)})")

        if prefix in {"ATO", "SEM", "CLU"} and rec.examples_count < 5:
            errors.append(
                f"{rec.id}: requires ≥5 examples, found {rec.examples_count} ({_rel(rec.file)})"
            )

        if prefix == "SEM":
            ato_refs = {rid for rid in rec.composed_refs if rid.startswith("ATO_")}
            if len(ato_refs) < 2:
                errors.append(
                    f"{rec.id}: composed_of must reference ≥2 distinct ATOs (found {sorted(ato_refs)})"
                )
            missing_atos = [rid for rid in ato_refs if rid not in id_registry]
            if missing_atos:
                errors.append(f"{rec.id}: unknown ATO references {missing_atos}")

            sem_refs = {rid for rid in rec.composed_refs if rid.startswith("SEM_")}
            if sem_refs:
                warnings.append(f"{rec.id}: references SEM(s) {sorted(sem_refs)} — review allowlist")

        if prefix == "CLU":
            non_sem = [rid for rid in rec.composed_refs if not rid.startswith("SEM_")]
            if non_sem:
                errors.append(f"{rec.id}: CLU composed_of must only include SEM ids, found {non_sem}")

        if rec.id.startswith("CLU_INTUITION_"):
            _check_intuition_cluster(rec, errors)

    if errors:
        for err in errors:
            print(f"CI ERR: {err}")
        for warn in warnings:
            print(f"CI WARN: {warn}")
        return 1

    for warn in warnings:
        print(f"CI WARN: {warn}")
    print("CI checks passed ✔")
    return 0


def _check_intuition_cluster(rec: MarkerRecord, errors: list[str]) -> None:
    data = rec.data or {}
    metadata = data.get("metadata") or {}
    family = metadata.get("family")
    if not isinstance(family, str) or not family:
        errors.append(f"{rec.id}: metadata.family missing")

    telemetry = metadata.get("telemetry") or metadata.get("telemetry_keys") or {}
    if not REQUIRED_TELEMETRY_KEYS.issubset(telemetry.keys()):
        errors.append(f"{rec.id}: telemetry keys incomplete (need {sorted(REQUIRED_TELEMETRY_KEYS)})")

    intuition = metadata.get("intuition") or {}
    activation = intuition.get("activation") or {}
    confirm = intuition.get("confirm") or {}
    decay = intuition.get("decay") or {}

    if not {"min_distinct_sems", "window"}.issubset(activation.keys()):
        errors.append(f"{rec.id}: intuition.activation requires min_distinct_sems + window")
    cooldown = activation.get("cooldown_messages")
    if family == "INCONSISTENCY" and (not isinstance(cooldown, int) or cooldown < 4):
        errors.append(f"{rec.id}: INCONSISTENCY cooldown_messages must be ≥4 (found {cooldown!r})")

    if "window" not in confirm:
        errors.append(f"{rec.id}: intuition.confirm.window missing")
    if not confirm.get("require_any"):
        errors.append(f"{rec.id}: intuition.confirm.require_any missing or empty")

    if "window" not in decay:
        errors.append(f"{rec.id}: intuition.decay.window missing")

    if "multiplier_on_confirm" not in intuition:
        errors.append(f"{rec.id}: intuition.multiplier_on_confirm missing")


def _determine_focus_ids(records: Iterable[MarkerRecord], families_arg: str | None) -> set[str] | None:
    if not families_arg:
        return None
    families = {fam.strip().upper() for fam in families_arg.split(",") if fam.strip()}
    if not families:
        return None

    by_id = {rec.id: rec for rec in records}
    selected: set[str] = set()

    for rec in records:
        if rec.id.startswith("CLU_"):
            metadata = rec.data.get("metadata") if isinstance(rec.data, dict) else None
            family = metadata.get("family") if isinstance(metadata, dict) else None
            if isinstance(family, str) and family.upper() in families:
                selected.add(rec.id)
                _collect_sem_and_ato(rec, by_id, selected)

    return selected


def _collect_sem_and_ato(clu: MarkerRecord, by_id: Dict[str, MarkerRecord], selected: set[str]) -> None:
    sem_ids = [rid for rid in clu.composed_refs if rid.startswith("SEM_")]
    metadata = clu.data.get("metadata") if isinstance(clu.data, dict) else {}
    intuition = metadata.get("intuition") if isinstance(metadata, dict) else {}
    confirm = intuition.get("confirm") if isinstance(intuition, dict) else {}
    confirm_targets = confirm.get("require_any") if isinstance(confirm, dict) else []
    for target in confirm_targets or []:
        if isinstance(target, str) and target.startswith("SEM_"):
            sem_ids.append(target)

    for sem_id in sem_ids:
        selected.add(sem_id)
        sem_rec = by_id.get(sem_id)
        if not sem_rec:
            continue
        ato_ids = [rid for rid in sem_rec.composed_refs if rid.startswith("ATO_")]
        selected.update(ato_ids)


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
