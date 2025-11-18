#!/usr/bin/env python3
"""Validate presence and separation of negative examples per marker."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.audit_markers import MarkerRecord, resolve_roots, scan_markers


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ensure markers supply positive/negative examples")
    parser.add_argument(
        "roots",
        nargs="*",
        help="Directories/files to include (defaults to Markers_canonical.json)",
    )
    parser.add_argument("--min-positive", type=int, default=10, help="Required minimum positive examples")
    parser.add_argument("--min-negative", type=int, default=10, help="Required minimum negative examples")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    roots = resolve_roots(args.roots)
    report = scan_markers(roots)
    records: Iterable[MarkerRecord] = report["records"]

    errors: list[str] = []

    for rec in records:
        metadata = rec.data.get("metadata") if isinstance(rec.data, dict) else None
        if not isinstance(metadata, dict):
            continue
        neg_examples = metadata.get("neg_examples")
        if not isinstance(neg_examples, list):
            continue

        positives = rec.data.get("examples", [])
        if not isinstance(positives, list):
            positives = []

        if len(positives) < args.min_positive:
            errors.append(
                f"{rec.id}: only {len(positives)} positive examples (<{args.min_positive})"
            )
        if len(neg_examples) < args.min_negative:
            errors.append(
                f"{rec.id}: only {len(neg_examples)} neg_examples (<{args.min_negative})"
            )

        clashes = _overlap(positives, neg_examples)
        if clashes:
            errors.append(f"{rec.id}: positive/negative overlap detected {sorted(clashes)}")

        dup_neg = _duplicates(neg_examples)
        if dup_neg:
            errors.append(f"{rec.id}: duplicate neg_examples {sorted(dup_neg)}")

    if errors:
        for err in errors:
            print(f"NEG ERR: {err}")
        return 1
    print("Negative example check passed ✔")
    return 0


def _normalize(entry: str) -> str:
    return " ".join(entry.strip().lower().split())


def _overlap(pos: list[str], neg: list[str]) -> set[str]:
    pos_norm = {_normalize(p): p for p in pos if isinstance(p, str)}
    clashes: set[str] = set()
    for item in neg:
        if not isinstance(item, str):
            continue
        norm = _normalize(item)
        if norm in pos_norm:
            clashes.add(pos_norm[norm])
    return clashes


def _duplicates(items: list[str]) -> set[str]:
    seen: dict[str, str] = {}
    dups: set[str] = set()
    for entry in items:
        if not isinstance(entry, str):
            continue
        norm = _normalize(entry)
        if norm in seen:
            dups.add(seen[norm])
            dups.add(entry)
        else:
            seen[norm] = entry
    return dups


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
