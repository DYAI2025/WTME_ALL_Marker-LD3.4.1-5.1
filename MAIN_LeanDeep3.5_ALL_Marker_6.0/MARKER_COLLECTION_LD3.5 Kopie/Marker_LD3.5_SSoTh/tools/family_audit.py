#!/usr/bin/env python3
"""Family pack audit for LeanDeep intuition layers."""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, Sequence

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.audit_markers import MarkerRecord, resolve_roots, scan_markers

DEFAULT_FAMILIES = ["INCONSISTENCY", "CONSISTENCY", "EFFICACY", "SHUTDOWN", "SUPPORT"]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit intuition families for completeness")
    parser.add_argument(
        "--families",
        default=",".join(DEFAULT_FAMILIES),
        help="Comma-separated list of families to verify",
    )
    parser.add_argument(
        "roots",
        nargs="*",
        help="Directories/files to include (defaults to Markers_canonical.json)",
    )
    parser.add_argument(
        "--min-sems",
        type=int,
        default=3,
        help="Minimum SEM sources each intuition CLU must aggregate",
    )
    parser.add_argument(
        "--min-examples",
        type=int,
        default=5,
        help="Minimum examples required for CLUs and SEMs",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    families = [fam.strip().upper() for fam in args.families.split(",") if fam.strip()]
    roots = resolve_roots(args.roots)
    report = scan_markers(roots)

    records: Iterable[MarkerRecord] = report["records"]
    by_id: Dict[str, MarkerRecord] = {rec.id: rec for rec in records}

    errors: list[str] = []

    family_to_clus: Dict[str, list[MarkerRecord]] = defaultdict(list)
    for rec in records:
        if not rec.id.startswith("CLU_INTUITION_"):
            continue
        metadata = rec.data.get("metadata") if isinstance(rec.data, dict) else None
        if not isinstance(metadata, dict):
            continue
        family = metadata.get("family")
        if isinstance(family, str):
            family_to_clus[family.upper()].append(rec)

    for family in families:
        clusters = family_to_clus.get(family, [])
        if not clusters:
            errors.append(f"Family {family}: no CLU with metadata.family={family}")
            continue
        for clu in clusters:
            _audit_cluster(clu, by_id, family, args.min_sems, args.min_examples, errors)

    if errors:
        for err in errors:
            print(f"FAMILY ERR: {err}")
        return 1
    print(f"Family audit passed for {', '.join(families)} ✔")
    return 0


def _audit_cluster(
    clu: MarkerRecord,
    by_id: Dict[str, MarkerRecord],
    family: str,
    min_sems: int,
    min_examples: int,
    errors: list[str],
) -> None:
    meta = clu.data.get("metadata") if isinstance(clu.data, dict) else {}
    intuition = meta.get("intuition") if isinstance(meta, dict) else {}
    activation = intuition.get("activation") if isinstance(intuition, dict) else {}

    if clu.examples_count < min_examples:
        errors.append(f"{clu.id}: needs ≥{min_examples} examples (found {clu.examples_count})")

    sem_ids = [rid for rid in clu.composed_refs if rid.startswith("SEM_")]
    if len(sem_ids) < min_sems:
        errors.append(
            f"{clu.id}: composed_of lists {len(sem_ids)} SEMs (<{min_sems})"
        )

    if not isinstance(activation, dict) or "min_distinct_sems" not in activation or "window" not in activation:
        errors.append(f"{clu.id}: intuition.activation must define min_distinct_sems + window")

    confirm = intuition.get("confirm") if isinstance(intuition, dict) else {}
    confirm_targets = []
    if isinstance(confirm, dict):
        confirm_targets = confirm.get("require_any") or []
    if not confirm_targets:
        errors.append(f"{clu.id}: intuition.confirm.require_any missing")

    decay = intuition.get("decay") if isinstance(intuition, dict) else {}
    if not isinstance(decay, dict) or "window" not in decay:
        errors.append(f"{clu.id}: intuition.decay.window missing")

    multiplier = intuition.get("multiplier_on_confirm") if isinstance(intuition, dict) else None
    if multiplier is None:
        errors.append(f"{clu.id}: intuition.multiplier_on_confirm missing")

    if family == "INCONSISTENCY":
        cooldown = activation.get("cooldown_messages") if isinstance(activation, dict) else None
        if not isinstance(cooldown, int) or cooldown < 4:
            errors.append(f"{clu.id}: cooldown_messages must be ≥4 for family INCONSISTENCY")

    for sem_id in sem_ids:
        sem_rec = by_id.get(sem_id)
        if not sem_rec:
            errors.append(f"{clu.id}: referenced SEM {sem_id} not found")
            continue
        _audit_sem(sem_rec, family, min_examples, errors)

    for target in confirm_targets:
        if not isinstance(target, str):
            continue
        if not target.startswith("SEM_"):
            errors.append(f"{clu.id}: confirm target {target} should be a SEM id")
            continue
        if target not in by_id:
            errors.append(f"{clu.id}: confirm target {target} not found in corpus")


def _audit_sem(sem_rec: MarkerRecord, family: str, min_examples: int, errors: list[str]) -> None:
    if sem_rec.prefix != "SEM":
        errors.append(f"{sem_rec.id}: expected SEM, found prefix {sem_rec.prefix}")
        return

    if sem_rec.examples_count < min_examples:
        errors.append(f"{sem_rec.id}: needs ≥{min_examples} examples (found {sem_rec.examples_count})")

    ato_refs = {rid for rid in sem_rec.composed_refs if rid.startswith("ATO_")}
    if len(ato_refs) < 2:
        errors.append(f"{sem_rec.id}: requires ≥2 distinct ATOs, found {sorted(ato_refs)}")

    metadata = sem_rec.data.get("metadata") if isinstance(sem_rec.data, dict) else None
    if isinstance(metadata, dict):
        sem_family = metadata.get("family")
        if sem_family and sem_family.upper() != family:
            errors.append(
                f"{sem_rec.id}: metadata.family={sem_family} does not match CLU family {family}"
            )
    else:
        # encourage adding metadata
        errors.append(f"{sem_rec.id}: metadata.family missing (expected {family})")


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
