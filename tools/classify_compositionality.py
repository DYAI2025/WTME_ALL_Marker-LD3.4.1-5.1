#!/usr/bin/env python3
"""
classify_compositionality.py — Auto-classify SEM markers by compositionality.

Tests each ATO's "broadness" (how often it fires on neutral text),
then classifies SEMs based on their composed_of ATOs:

  deterministic  — composed of specific ATOs that carry meaning on their own
  contextual     — composed of mixed ATOs, needs relational context
  emergent       — composed of broad/common ATOs, meaning only through constellation

Analogy: Neuroplasticity. Deterministic = hard-wired pathways.
Contextual = context-dependent plasticity. Emergent = novel connections
that only form through the experience of meaning (the relational vector).

Usage:
  python3 tools/classify_compositionality.py              # Dry run (show classifications)
  python3 tools/classify_compositionality.py --apply      # Write compositionality to source YAMLs
  python3 tools/classify_compositionality.py --stats      # Show statistics only
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from ruamel.yaml import YAML
except ImportError:
    YAML = None

REPO = Path(__file__).resolve().parent.parent
REGISTRY = REPO / "build" / "markers_normalized" / "marker_registry.json"
RATED_DIR = REPO / "build" / "markers_rated"

# ---------------------------------------------------------------------------
# Neutral test corpus — everyday sentences with no psychological signal
# ---------------------------------------------------------------------------
NEUTRAL_SENTENCES = [
    "Heute ist Dienstag.",
    "Der Zug kommt um 14 Uhr.",
    "Ich gehe einkaufen.",
    "Das Wetter ist schön.",
    "Wir essen heute Abend Pizza.",
    "Der Hund braucht Futter.",
    "Kannst du mir helfen?",
    "Die Besprechung war lang.",
    "Morgen habe ich frei.",
    "Das Auto muss in die Werkstatt.",
    "Bitte schick mir die Datei.",
    "Der Film war gut.",
    "Ich bin müde.",
    "Hast du schon gegessen?",
    "Die Kinder spielen draußen.",
    "Wir fahren am Wochenende weg.",
    "Der Kaffee ist kalt geworden.",
    "Ich rufe dich später an.",
    "Das Paket ist angekommen.",
    "Vergiss nicht den Termin.",
    "Die Heizung ist aus.",
    "Bring bitte Brot mit.",
    "Ich bin gleich da.",
    "Das passt mir gut.",
    "Wir treffen uns um acht.",
    "Der Aufzug ist kaputt.",
    "Ich habe Kopfschmerzen.",
    "Das Spiel war spannend.",
    "Nächste Woche ist Feiertag.",
    "Die Straße ist gesperrt.",
    # English neutral
    "The report is due tomorrow.",
    "Can you check the budget numbers?",
    "I will send the email later.",
    "The meeting starts at three.",
    "Please review the document.",
    "We need to update the software.",
    "The office is closed on Monday.",
    "I left my keys at home.",
    "The project deadline is Friday.",
    "Thanks for the update.",
]

N_NEUTRAL = len(NEUTRAL_SENTENCES)


def load_registry() -> dict:
    with open(REGISTRY, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("markers", data)


def score_ato_broadness(registry: dict) -> dict[str, float]:
    """Score each ATO by how many neutral sentences it matches (0.0 = specific, 1.0 = broad)."""
    scores = {}

    for mid, m in registry.items():
        if m.get("layer") != "ATO":
            continue

        # Compile patterns
        compiled = []
        for p in m.get("patterns", []):
            if not isinstance(p, dict):
                continue
            raw = str(p.get("value", ""))
            if len(raw) < 2:
                continue
            try:
                compiled.append(re.compile(raw, re.IGNORECASE))
            except re.error:
                pass

        if not compiled:
            scores[mid] = 0.0
            continue

        # Test against neutral sentences
        hits = 0
        for sent in NEUTRAL_SENTENCES:
            for pat in compiled:
                if pat.search(sent):
                    hits += 1
                    break

        scores[mid] = hits / N_NEUTRAL

    return scores


def classify_sem(
    sem_data: dict,
    ato_broadness: dict[str, float],
) -> tuple[str, float, list[tuple[str, float]]]:
    """Classify a SEM marker's compositionality.

    Returns: (classification, avg_broadness, [(ato_id, broadness), ...])
    """
    composed = sem_data.get("composed_of") or []
    if isinstance(composed, dict):
        composed = list(composed.keys()) if hasattr(composed, "keys") else []
    if not isinstance(composed, list):
        composed = [composed]

    # Get broadness for each composed_of ATO
    ato_scores = []
    for ref in composed:
        if isinstance(ref, str):
            broadness = ato_broadness.get(ref, 0.0)
            ato_scores.append((ref, broadness))

    if not ato_scores:
        return "deterministic", 0.0, ato_scores

    avg_broadness = sum(s for _, s in ato_scores) / len(ato_scores)
    max_broadness = max(s for _, s in ato_scores)
    broad_count = sum(1 for _, s in ato_scores if s > 0.0)  # any neutral hits
    specific_count = sum(1 for _, s in ato_scores if s == 0.0)

    # Classification logic — based on neuroplasticity analogy:
    # deterministic = hard-wired pathways (all ATOs specific, self-sufficient)
    # contextual    = context-dependent plasticity (some broad ATOs, meaning modulated)
    # emergent      = novel connections (major broad ATOs, meaning only through constellation)
    #
    # Thresholds:
    #   Any ATO with >10% neutral hit rate → emergent (too broad to self-determine)
    #   Any ATO with >0% neutral hit rate  → contextual (needs some context)
    #   All ATOs at 0%                     → deterministic (meaning self-contained)
    if max_broadness >= 0.10:
        classification = "emergent"
    elif broad_count > 0:
        classification = "contextual"
    else:
        classification = "deterministic"

    return classification, avg_broadness, ato_scores


def apply_to_source(mid: str, classification: str) -> bool:
    """Write compositionality field to the source YAML in markers_rated."""
    if YAML is None:
        print("ERROR: ruamel.yaml not installed, cannot --apply", file=sys.stderr)
        return False

    yaml = YAML()
    yaml.preserve_quotes = True

    # Find source file
    for tier in ["1_approved", "2_good"]:
        # Direct file
        layer = mid.split("_")[0]
        path = RATED_DIR / tier / layer / f"{mid}.yaml"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.load(f)
            if isinstance(data, dict):
                data["compositionality"] = classification
                with open(path, "w", encoding="utf-8") as f:
                    yaml.dump(data, f)
                return True
            elif isinstance(data, list):
                # Composite file — shouldn't have SEM in ATO dir
                pass

        # Also search in SEM directory
        for sem_dir in (RATED_DIR / tier / "SEM").glob("*.yaml"):
            with open(sem_dir, "r", encoding="utf-8") as f:
                content = f.read()
            if f"id: {mid}" in content or f"name: {mid}" in content:
                with open(sem_dir, "r", encoding="utf-8") as f:
                    data = yaml.load(f)
                if isinstance(data, dict):
                    data["compositionality"] = classification
                    with open(sem_dir, "w", encoding="utf-8") as f:
                        yaml.dump(data, f)
                    return True

    return False


def main():
    parser = argparse.ArgumentParser(description="Auto-classify SEM compositionality")
    parser.add_argument("--apply", action="store_true", help="Write classifications to source YAMLs")
    parser.add_argument("--stats", action="store_true", help="Show statistics only")
    parser.add_argument("--verbose", action="store_true", help="Show ATO broadness details")
    args = parser.parse_args()

    registry = load_registry()

    # Step 1: Score ATO broadness
    print("Scoring ATO broadness against neutral text...", file=sys.stderr)
    ato_broadness = score_ato_broadness(registry)

    broad_atos = {k: v for k, v in ato_broadness.items() if v > 0.0}
    if args.verbose:
        print(f"\nBroad ATOs (fire on >{0}% neutral text):", file=sys.stderr)
        for mid, score in sorted(broad_atos.items(), key=lambda x: -x[1]):
            pct = score * 100
            print(f"  {mid:<45s} {pct:>5.1f}%", file=sys.stderr)

    # Step 2: Classify SEMs
    results = {}
    for mid, m in registry.items():
        if m.get("layer") != "SEM":
            continue
        classification, avg_broad, ato_scores = classify_sem(m, ato_broadness)
        results[mid] = (classification, avg_broad, ato_scores)

    # Step 3: Output
    counts = {"deterministic": 0, "contextual": 0, "emergent": 0}
    for cls, _, _ in results.values():
        counts[cls] += 1

    print(f"\n{'='*65}")
    print(f"  SEM COMPOSITIONALITY CLASSIFICATION")
    print(f"  {len(NEUTRAL_SENTENCES)} neutral sentences, {len(ato_broadness)} ATOs scored")
    print(f"{'='*65}\n")

    print(f"  deterministic  {counts['deterministic']:>4d}  ATOs carry their own meaning vector")
    print(f"  contextual     {counts['contextual']:>4d}  ATOs need relational context")
    print(f"  emergent       {counts['emergent']:>4d}  Meaning only through full constellation")
    print(f"  {'─'*55}")
    print(f"  total          {sum(counts.values()):>4d}\n")

    if args.stats:
        return

    # Detailed output
    for cls in ["emergent", "contextual", "deterministic"]:
        items = [(mid, data) for mid, data in results.items() if data[0] == cls]
        if not items:
            continue

        print(f"\n  ── {cls.upper()} ({len(items)}) ──")
        for mid, (_, avg_broad, ato_scores) in sorted(items, key=lambda x: -x[1][1]):
            broad_refs = [f"{a}({s*100:.0f}%)" for a, s in ato_scores if s > 0]
            specific_refs = [a for a, s in ato_scores if s == 0]
            print(f"    {mid}")
            if broad_refs:
                print(f"      broad: {', '.join(broad_refs[:5])}")
            if args.verbose and specific_refs:
                print(f"      specific: {', '.join(specific_refs[:5])}")

    # Step 4: Apply if requested
    if args.apply:
        print(f"\nApplying classifications to source YAMLs...", file=sys.stderr)
        applied = 0
        failed = 0
        for mid, (cls, _, _) in results.items():
            if apply_to_source(mid, cls):
                applied += 1
            else:
                failed += 1
        print(f"  Applied: {applied}, Failed: {failed}", file=sys.stderr)
        if applied > 0:
            print(f"\nRun 'python3 tools/normalize_schema.py' to rebuild registry.", file=sys.stderr)


if __name__ == "__main__":
    main()
