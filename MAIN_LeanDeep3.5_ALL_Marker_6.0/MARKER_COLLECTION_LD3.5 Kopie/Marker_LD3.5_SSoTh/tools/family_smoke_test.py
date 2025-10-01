#!/usr/bin/env python3
"""Simulate intuition family state transitions on synthetic traces."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set

import yaml

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.audit_markers import MarkerRecord, resolve_roots, scan_markers

SMOKE_DIR = Path("tests/intuition_smoke")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run intuition family smoke simulations")
    parser.add_argument(
        "roots",
        nargs="*",
        help="Marker directories (defaults to Markers_canonical.json)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed state transitions",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    roots = resolve_roots(args.roots)
    report = scan_markers(roots)
    by_id: Dict[str, MarkerRecord] = {rec.id: rec for rec in report["records"]}

    if not SMOKE_DIR.exists():
        print(f"Smoke directory {SMOKE_DIR} missing")
        return 1

    errors: List[str] = []
    for yaml_file in sorted(SMOKE_DIR.glob("*.yaml")):
        with yaml_file.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle)
        if not isinstance(payload, dict):
            errors.append(f"{yaml_file}: invalid structure")
            continue
        try:
            _run_suite(payload, by_id, args.verbose)
        except AssertionError as exc:
            errors.append(f"{yaml_file}: {exc}")

    if errors:
        for err in errors:
            print(f"SMOKE ERR: {err}")
        return 1

    print("Family smoke tests passed ✔")
    return 0


def _run_suite(spec: dict, by_id: Dict[str, MarkerRecord], verbose: bool) -> None:
    family = spec.get("family")
    cluster_id = spec.get("cluster")
    if not isinstance(family, str) or not isinstance(cluster_id, str):
        raise AssertionError("family/cluster missing")
    cluster = by_id.get(cluster_id)
    if not cluster:
        raise AssertionError(f"cluster {cluster_id} not found")

    metadata = cluster.data.get("metadata") if isinstance(cluster.data, dict) else {}
    intuition = metadata.get("intuition") if isinstance(metadata, dict) else {}
    activation_meta = intuition.get("activation") if isinstance(intuition, dict) else {}
    confirm_meta = intuition.get("confirm") if isinstance(intuition, dict) else {}
    decay_meta = intuition.get("decay") if isinstance(intuition, dict) else {}

    cfg = SimulationConfig(
        family=family,
        cluster_id=cluster_id,
        sem_ids=[rid for rid in cluster.composed_refs if rid.startswith("SEM_")],
        min_distinct=int(activation_meta.get("min_distinct_sems", 2)),
        activation_window=int(activation_meta.get("window", 5)),
        cooldown=int(activation_meta.get("cooldown_messages", 0)),
        confirm_window=int(confirm_meta.get("window", 5)),
        confirm_targets=set(confirm_meta.get("require_any", [])),
        decay_window=int(decay_meta.get("window", 8)),
    )

    sequences = spec.get("sequences")
    if not isinstance(sequences, list):
        raise AssertionError("sequences missing")

    for sequence in sequences:
        name = sequence.get("name", "sequence")
        events = sequence.get("events")
        if not isinstance(events, list):
            raise AssertionError(f"{name}: events missing")
        trace = [_ensure_sem_set(event, name) for event in events]
        result = simulate(cfg, trace, verbose=verbose)
        if result.confirmed == 0:
            raise AssertionError(f"{name}: no confirmation observed")
        if result.retracted == 0:
            raise AssertionError(f"{name}: no decay/retraction observed")


def _ensure_sem_set(event: dict, name: str) -> Set[str]:
    if not isinstance(event, dict):
        raise AssertionError(f"{name}: event malformed")
    sems = event.get("sems", [])
    if isinstance(sems, list):
        return {str(s) for s in sems}
    raise AssertionError(f"{name}: sems must be a list")


class SimulationConfig:
    def __init__(
        self,
        family: str,
        cluster_id: str,
        sem_ids: List[str],
        min_distinct: int,
        activation_window: int,
        cooldown: int,
        confirm_window: int,
        confirm_targets: Set[str],
        decay_window: int,
    ) -> None:
        self.family = family
        self.cluster_id = cluster_id
        self.sem_ids = sem_ids
        self.min_distinct = max(1, min_distinct)
        self.activation_window = max(1, activation_window)
        self.cooldown = max(0, cooldown)
        self.confirm_window = max(1, confirm_window)
        self.confirm_targets = confirm_targets
        self.decay_window = max(1, decay_window)


class SimulationResult:
    def __init__(self) -> None:
        self.confirmed = 0
        self.retracted = 0


def simulate(cfg: SimulationConfig, trace: List[Set[str]], verbose: bool = False) -> SimulationResult:
    state = "idle"
    cooldown = 0
    confirm_timer = 0
    decay_timer = 0
    window: List[Set[str]] = []
    result = SimulationResult()
    cluster_sem_set = set(cfg.sem_ids)

    for idx, sems in enumerate(trace):
        if verbose:
            print(json.dumps({"step": idx + 1, "state": state, "sems": sorted(sems)}))

        relevant = sems & cluster_sem_set
        window.append(relevant)
        if len(window) > cfg.activation_window:
            window.pop(0)

        if state == "idle":
            if cooldown > 0:
                cooldown -= 1
            if cooldown == 0:
                distinct = set().union(*window) if window else set()
                if len(distinct) >= cfg.min_distinct:
                    state = "provisional"
                    confirm_timer = cfg.confirm_window
                    decay_timer = 0
                    if verbose:
                        print(f"  → provisional (distinct={sorted(distinct)})")
        elif state == "provisional":
            confirm_timer -= 1
            if sems & cfg.confirm_targets:
                state = "confirmed"
                result.confirmed += 1
                decay_timer = cfg.decay_window
                if verbose:
                    print("  → confirmed")
            elif confirm_timer == 0:
                state = "idle"
                cooldown = cfg.cooldown
                window.clear()
                if verbose:
                    print("  → provisional expired, back to idle")
        elif state == "confirmed":
            if sems & (cluster_sem_set | cfg.confirm_targets):
                decay_timer = cfg.decay_window
            else:
                decay_timer -= 1
                if verbose:
                    print(f"  decay countdown: {decay_timer}")
                if decay_timer <= 0:
                    result.retracted += 1
                    state = "idle"
                    cooldown = cfg.cooldown
                    window.clear()
                    if verbose:
                        print("  → decayed")

    return result


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
