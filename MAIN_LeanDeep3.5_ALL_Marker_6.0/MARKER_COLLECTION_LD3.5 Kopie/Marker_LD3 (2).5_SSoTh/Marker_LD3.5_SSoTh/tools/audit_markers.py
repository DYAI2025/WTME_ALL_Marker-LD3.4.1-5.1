#!/usr/bin/env python3
"""LeanDeep marker corpus audit utility.

Produces counts and compliance reports for the marker packs.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set

import yaml

ID_PATTERN = re.compile(r"^[A-Z0-9]+(?:_[A-Z0-9]+)*$")
CANONICAL_PREFIXES = {"ATO", "SEM", "CLU", "MEMA"}

default_roots: Sequence[str] = ("Markers_canonical.json",)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit LeanDeep marker packs for structural issues",
    )
    parser.add_argument(
        "roots",
        nargs="*",
        help="Directories or files to audit (defaults to known packs if present)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit audit findings as JSON",
    )
    return parser.parse_args(argv)


@dataclass
class MarkerRecord:
    id: str
    prefix: str
    file: Path
    data: Dict[str, object]
    composed_raw: object
    composed_refs: Set[str]
    examples_count: int
    neg_examples_count: int
    file_marker_count: int
    index_in_file: int


def resolve_roots(candidates: Sequence[str]) -> List[Path]:
    if candidates:
        roots = [Path(c).resolve() for c in candidates]
    else:
        roots = [Path(c).resolve() for c in default_roots if Path(c).exists()]
        if not roots:
            roots = [Path.cwd()]
    resolved: List[Path] = []
    for root in roots:
        if root.is_file() and root.suffix in {".yml", ".yaml"}:
            resolved.append(root)
        elif root.is_dir():
            resolved.append(root)
    return resolved


def collect_id_refs(node: object) -> Set[str]:
    found: Set[str] = set()
    if node is None:
        return found
    if isinstance(node, str):
        value = node.strip()
        if ID_PATTERN.match(value):
            found.add(value)
        return found
    if isinstance(node, Sequence) and not isinstance(node, (str, bytes)):
        for item in node:
            found.update(collect_id_refs(item))
        return found
    if isinstance(node, dict):
        for value in node.values():
            found.update(collect_id_refs(value))
    return found


def extract_markers(data: object) -> List[dict]:
    if not isinstance(data, dict):
        return []
    collection_keys = [
        "markers",
        "clus",
        "sems",
        "atos",
        "memas",
    ]
    for key in collection_keys:
        if key in data and isinstance(data[key], list):
            return [m for m in data[key] if isinstance(m, dict)]
    if "id" in data:
        return [data]
    return []


def read_yaml(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def scan_markers(roots: Iterable[Path]):
    records: List[MarkerRecord] = []
    parse_errors: List[Dict[str, str]] = []
    missing_ids: List[Dict[str, str]] = []
    duplicate_ids: Dict[str, List[MarkerRecord]] = defaultdict(list)

    prefix_counts: Counter[str] = Counter()
    files_scanned = 0
    repo_root = Path.cwd().resolve()

    for root in roots:
        paths: List[Path]
        if root.is_file():
            paths = [root]
        else:
            paths = sorted(root.rglob("*.yml")) + sorted(root.rglob("*.yaml"))
        for path in paths:
            files_scanned += 1
            try:
                data = read_yaml(path)
            except Exception as exc:  # pragma: no cover - defensive
                parse_errors.append({
                    "file": str(_rel_path(path, repo_root)),
                    "error": str(exc),
                })
                continue
            markers = extract_markers(data)
            if not markers:
                continue
            file_marker_count = len(markers)
            for index, marker in enumerate(markers):
                marker_id = marker.get("id")
                if not isinstance(marker_id, str) or not marker_id:
                    missing_ids.append({
                        "file": str(_rel_path(path, repo_root)),
                        "index": index,
                    })
                    continue
                prefix = marker_id.split("_", 1)[0]
                examples = marker.get("examples") if isinstance(marker, dict) else None
                examples_count = len(examples) if isinstance(examples, list) else 0
                neg_examples_count = 0
                metadata = marker.get("metadata") if isinstance(marker, dict) else None
                if isinstance(metadata, dict):
                    neg_block = metadata.get("neg_examples")
                    if isinstance(neg_block, list):
                        neg_examples_count = len(neg_block)
                composed_raw = marker.get("composed_of")
                composed_refs = collect_id_refs(composed_raw)
                record = MarkerRecord(
                    id=marker_id,
                    prefix=prefix,
                    file=path.resolve(),
                    data=marker,
                    composed_raw=composed_raw,
                    composed_refs=composed_refs,
                    examples_count=examples_count,
                    neg_examples_count=neg_examples_count,
                    file_marker_count=file_marker_count,
                    index_in_file=index,
                )
                records.append(record)
                prefix_counts[prefix] += 1
                duplicate_ids[marker_id].append(record)

    return {
        "records": records,
        "parse_errors": parse_errors,
        "missing_ids": missing_ids,
        "duplicate_ids": duplicate_ids,
        "prefix_counts": prefix_counts,
        "files_scanned": files_scanned,
    }


def _rel_path(path: Path, base: Path) -> Path:
    try:
        return path.resolve().relative_to(base)
    except ValueError:
        return path


def render_text(report: dict) -> str:
    records: List[MarkerRecord] = report["records"]
    prefix_counts: Counter[str] = report["prefix_counts"]
    duplicate_ids: Dict[str, List[MarkerRecord]] = report["duplicate_ids"]

    existing_ids = {rec.id for rec in records}
    repo_root = Path.cwd().resolve()

    sem_without_composed = [
        rec for rec in records
        if rec.prefix == "SEM" and (rec.composed_raw is None or not rec.composed_refs)
    ]
    sem_lt_two_ato = [
        rec for rec in records
        if rec.prefix == "SEM" and len({rid for rid in rec.composed_refs if rid.startswith("ATO_")}) < 2
    ]
    sem_unknown_ato_refs: Dict[str, Set[str]] = {}
    sem_sem_refs: List[MarkerRecord] = []
    for rec in records:
        if rec.prefix != "SEM":
            continue
        missing = {
            rid for rid in rec.composed_refs
            if rid.startswith("ATO_") and rid not in existing_ids
        }
        if missing:
            sem_unknown_ato_refs[rec.id] = missing
        if any(rid.startswith("SEM_") for rid in rec.composed_refs):
            sem_sem_refs.append(rec)

    clu_without_composed = [
        rec for rec in records
        if rec.prefix == "CLU" and (rec.composed_raw is None or not rec.composed_refs)
    ]
    clu_ref_ato = [
        rec for rec in records
        if rec.prefix == "CLU" and any(rid.startswith("ATO_") for rid in rec.composed_refs)
    ]
    clu_unknown_sem_refs: Dict[str, Set[str]] = {}
    for rec in records:
        if rec.prefix != "CLU":
            continue
        missing = {
            rid for rid in rec.composed_refs
            if rid.startswith("SEM_") and rid not in existing_ids
        }
        if missing:
            clu_unknown_sem_refs[rec.id] = missing

    filename_mismatch = []
    for rec in records:
        if rec.file_marker_count != 1:
            continue
        stem = rec.file.stem
        if stem != rec.id:
            filename_mismatch.append(rec)

    non_canonical_prefix = [
        rec for rec in records if rec.prefix not in CANONICAL_PREFIXES
    ]

    duplicates = {
        marker_id: [str(_rel_path(r.file, repo_root)) for r in recs]
        for marker_id, recs in duplicate_ids.items() if len(recs) > 1
    }

    lines: List[str] = []
    lines.append("=== LeanDeep Marker Audit ===")
    lines.append(f"Files scanned: {report['files_scanned']}")
    lines.append(f"Markers parsed: {len(records)} (unique IDs: {len(existing_ids)})")
    if prefix_counts:
        parts = ", ".join(f"{prefix} {count}" for prefix, count in sorted(prefix_counts.items()))
        lines.append(f"Counts by prefix: {parts}")
    if report["parse_errors"]:
        lines.append("")
        lines.append(f"Parse errors ({len(report['parse_errors'])}):")
        for entry in report["parse_errors"]:
            lines.append(f"  - {entry['file']}: {entry['error']}")
    if report["missing_ids"]:
        lines.append("")
        lines.append(f"Markers without id field ({len(report['missing_ids'])}):")
        for entry in report["missing_ids"]:
            lines.append(f"  - {entry['file']} [index {entry['index']}]")

    def list_section(title: str, items: Iterable[MarkerRecord], formatter=None):
        items = list(items)
        if not items:
            return
        lines.append("")
        lines.append(f"{title} ({len(items)}):")
        for rec in items:
            rel = _rel_path(rec.file, repo_root)
            if formatter:
                detail = formatter(rec)
            else:
                detail = ""
            suffix = f" -> {detail}" if detail else ""
            lines.append(f"  - {rec.id} ({rel}){suffix}")

    list_section("SEM without composed_of", sem_without_composed)
    list_section(
        "SEM with <2 distinct ATO references",
        sem_lt_two_ato,
        formatter=lambda rec: ", ".join(sorted(rid for rid in rec.composed_refs if rid.startswith("ATO_"))) or "—",
    )
    if sem_unknown_ato_refs:
        lines.append("")
        lines.append(f"SEM referencing unknown ATO IDs ({len(sem_unknown_ato_refs)}):")
        for sem_id, missing in sorted(sem_unknown_ato_refs.items()):
            lines.append(f"  - {sem_id}: {', '.join(sorted(missing))}")
    list_section(
        "SEM referencing SEM (should be avoided)",
        sem_sem_refs,
        formatter=lambda rec: ", ".join(sorted(rid for rid in rec.composed_refs if rid.startswith("SEM_")))
    )
    list_section("CLU without composed_of", clu_without_composed)
    list_section(
        "CLU referencing ATO directly",
        clu_ref_ato,
        formatter=lambda rec: ", ".join(sorted(rid for rid in rec.composed_refs if rid.startswith("ATO_")))
    )
    if clu_unknown_sem_refs:
        lines.append("")
        lines.append(f"CLU referencing unknown SEM IDs ({len(clu_unknown_sem_refs)}):")
        for clu_id, missing in sorted(clu_unknown_sem_refs.items()):
            lines.append(f"  - {clu_id}: {', '.join(sorted(missing))}")
    list_section(
        "Filename <> id mismatches",
        filename_mismatch,
        formatter=lambda rec: f"file '{rec.file.stem}'",
    )
    list_section(
        "IDs with non-canonical prefixes",
        non_canonical_prefix,
        formatter=lambda rec: rec.prefix,
    )
    if duplicates:
        lines.append("")
        lines.append(f"Duplicate marker IDs ({len(duplicates)}):")
        for marker_id, paths in sorted(duplicates.items()):
            joined = ", ".join(paths)
            lines.append(f"  - {marker_id}: {joined}")
    return "\n".join(lines)


def render_json(report: dict) -> str:
    repo_root = Path.cwd().resolve()
    records_payload = []
    for rec in report["records"]:
        records_payload.append({
            "id": rec.id,
            "prefix": rec.prefix,
            "file": str(_rel_path(rec.file, repo_root)),
            "composed_refs": sorted(rec.composed_refs),
            "examples_count": rec.examples_count,
            "neg_examples_count": rec.neg_examples_count,
            "file_marker_count": rec.file_marker_count,
            "index_in_file": rec.index_in_file,
        })
    payload = {
        "files_scanned": report["files_scanned"],
        "records": records_payload,
        "parse_errors": report["parse_errors"],
        "missing_ids": report["missing_ids"],
        "prefix_counts": dict(report["prefix_counts"]),
        "duplicates": {
            marker_id: [str(_rel_path(rec.file, repo_root)) for rec in recs]
            for marker_id, recs in report["duplicate_ids"].items()
            if len(recs) > 1
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    roots = resolve_roots(args.roots)
    report = scan_markers(roots)
    if args.json:
        print(render_json(report))
    else:
        print(render_text(report))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
