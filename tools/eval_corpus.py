#!/usr/bin/env python3
"""
eval_corpus.py — Run LeanDeep engine against the gold eval corpus.

Loads the anonymized corpus, runs the detection engine on each chunk,
and reports comprehensive statistics for precision analysis.

Since we don't have ground-truth annotations yet, this tool:
  1. Measures detection density per marker (hits per 1000 messages)
  2. Identifies inflationäre markers (fire too often)
  3. Shows confidence distributions per layer
  4. Samples random detections for manual review
  5. Compares DE vs EN detection patterns
  6. Exports a review file for human annotation

Usage:
  python3 tools/eval_corpus.py                    # Full eval, summary stats
  python3 tools/eval_corpus.py --top 20           # Show top 20 markers by frequency
  python3 tools/eval_corpus.py --layer SEM        # Filter by layer
  python3 tools/eval_corpus.py --sample 10        # Sample 10 random detections for review
  python3 tools/eval_corpus.py --export           # Export full results to eval/results.jsonl
  python3 tools/eval_corpus.py --threshold 0.3    # Custom threshold (default: 0.3)
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

# Add project root to path so we can import the engine
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from api.engine import MarkerEngine

EVAL_DIR = PROJECT_ROOT / "eval"
CORPUS_PATH = EVAL_DIR / "gold_corpus.jsonl"
EMAILS_PATH = EVAL_DIR / "gold_emails.jsonl"
RESULTS_PATH = EVAL_DIR / "results.jsonl"
REVIEW_PATH = EVAL_DIR / "review_sample.jsonl"


def load_corpus() -> list[dict]:
    """Load the gold corpus."""
    entries = []
    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            entries.append(json.loads(line))
    return entries


def run_eval(
    engine: MarkerEngine,
    corpus: list[dict],
    threshold: float = 0.3,
    layers: list[str] | None = None,
    max_chunks: int = 0,
) -> dict:
    """Run engine against corpus and collect all detections."""
    layers = layers or ["ATO", "SEM", "CLU", "MEMA"]
    results = []
    total_messages = 0
    total_chars = 0
    total_time_ms = 0.0

    chunks_to_process = corpus[:max_chunks] if max_chunks > 0 else corpus

    for i, entry in enumerate(chunks_to_process):
        messages = [{"text": m["text"], "speaker": m["speaker"]} for m in entry["messages"]]
        total_messages += len(messages)
        total_chars += sum(len(m["text"]) for m in messages)

        result = engine.analyze_conversation(messages, layers=layers, threshold=threshold)

        detections = []
        for d in result["detections"]:
            det = {
                "marker_id": d.marker_id,
                "layer": d.layer,
                "confidence": round(d.confidence, 3),
                "description": d.description,
                "family": d.family,
                "message_indices": d.message_indices,
                "matches": [
                    {"value": m.matched_text, "pattern": m.pattern}
                    for m in d.matches
                ] if hasattr(d, "matches") and d.matches else [],
            }
            detections.append(det)

        chunk_result = {
            "chunk_id": entry["id"],
            "lang": entry["lang"],
            "message_count": entry["message_count"],
            "detection_count": len(detections),
            "detections": detections,
            "timing_ms": result["timing_ms"],
        }
        results.append(chunk_result)
        total_time_ms += result["timing_ms"]

        if (i + 1) % 100 == 0:
            print(f"  ...processed {i+1}/{len(chunks_to_process)} chunks", file=sys.stderr)

    return {
        "results": results,
        "total_chunks": len(chunks_to_process),
        "total_messages": total_messages,
        "total_chars": total_chars,
        "total_time_ms": round(total_time_ms, 1),
        "threshold": threshold,
        "layers": layers,
    }


def compute_stats(eval_data: dict) -> dict:
    """Compute detection statistics."""
    results = eval_data["results"]
    total_messages = eval_data["total_messages"]
    total_chunks = eval_data["total_chunks"]

    # Per-marker stats
    marker_counts = Counter()
    marker_confidences = defaultdict(list)
    marker_layers = {}
    marker_families = {}
    marker_descriptions = {}
    marker_langs = defaultdict(lambda: {"de": 0, "en": 0})
    marker_samples = defaultdict(list)

    # Per-layer stats
    layer_counts = Counter()
    layer_confidences = defaultdict(list)

    # Per-chunk stats
    chunk_detection_counts = []

    for chunk in results:
        chunk_detection_counts.append(chunk["detection_count"])
        lang = chunk["lang"]

        for det in chunk["detections"]:
            mid = det["marker_id"]
            marker_counts[mid] += 1
            marker_confidences[mid].append(det["confidence"])
            marker_layers[mid] = det["layer"]
            marker_families[mid] = det.get("family")
            marker_descriptions[mid] = det["description"]
            marker_langs[mid][lang] += 1

            layer_counts[det["layer"]] += 1
            layer_confidences[det["layer"]].append(det["confidence"])

            # Keep sample matches (up to 3 per marker)
            if len(marker_samples[mid]) < 3 and det["matches"]:
                marker_samples[mid].append({
                    "chunk_id": chunk["chunk_id"],
                    "matches": det["matches"][:2],
                    "confidence": det["confidence"],
                })

    # Compute derived stats
    marker_stats = []
    for mid, count in marker_counts.most_common():
        confs = marker_confidences[mid]
        avg_conf = sum(confs) / len(confs)
        hits_per_1k = (count / total_messages) * 1000
        marker_stats.append({
            "marker_id": mid,
            "layer": marker_layers[mid],
            "family": marker_families.get(mid),
            "description": marker_descriptions.get(mid, ""),
            "count": count,
            "hits_per_1k_msgs": round(hits_per_1k, 2),
            "avg_confidence": round(avg_conf, 3),
            "min_confidence": round(min(confs), 3),
            "max_confidence": round(max(confs), 3),
            "chunks_hit": len(set(
                r["chunk_id"] for r in results
                if any(d["marker_id"] == mid for d in r["detections"])
            )),
            "chunk_coverage": round(len(set(
                r["chunk_id"] for r in results
                if any(d["marker_id"] == mid for d in r["detections"])
            )) / total_chunks * 100, 1),
            "de_count": marker_langs[mid]["de"],
            "en_count": marker_langs[mid]["en"],
            "samples": marker_samples.get(mid, []),
        })

    layer_stats = {}
    for layer in ["ATO", "SEM", "CLU", "MEMA"]:
        confs = layer_confidences.get(layer, [])
        layer_stats[layer] = {
            "total_detections": layer_counts.get(layer, 0),
            "unique_markers": len([m for m in marker_stats if m["layer"] == layer]),
            "avg_confidence": round(sum(confs) / len(confs), 3) if confs else 0,
            "hits_per_1k_msgs": round(
                (layer_counts.get(layer, 0) / total_messages) * 1000, 2
            ) if total_messages > 0 else 0,
        }

    return {
        "marker_stats": marker_stats,
        "layer_stats": layer_stats,
        "total_detections": sum(marker_counts.values()),
        "unique_markers_fired": len(marker_counts),
        "avg_detections_per_chunk": round(
            sum(chunk_detection_counts) / len(chunk_detection_counts), 1
        ) if chunk_detection_counts else 0,
        "median_detections_per_chunk": sorted(chunk_detection_counts)[
            len(chunk_detection_counts) // 2
        ] if chunk_detection_counts else 0,
    }


def print_report(eval_data: dict, stats: dict, top_n: int = 30, layer_filter: str | None = None):
    """Print human-readable evaluation report."""
    print(f"\n{'='*70}")
    print(f"  LEANDEEP EVAL CORPUS REPORT")
    print(f"{'='*70}\n")

    print(f"  Corpus:     {eval_data['total_chunks']} chunks, "
          f"{eval_data['total_messages']:,} messages, "
          f"{eval_data['total_chars']:,} chars")
    print(f"  Threshold:  {eval_data['threshold']}")
    print(f"  Layers:     {', '.join(eval_data['layers'])}")
    print(f"  Runtime:    {eval_data['total_time_ms']:,.0f}ms "
          f"({eval_data['total_time_ms']/eval_data['total_chunks']:.1f}ms/chunk)")

    print(f"\n  --- Layer Summary ---")
    print(f"  {'Layer':<8} {'Detections':>12} {'Unique':>8} {'Avg Conf':>10} {'Hits/1K':>10}")
    print(f"  {'─'*52}")
    for layer in ["ATO", "SEM", "CLU", "MEMA"]:
        ls = stats["layer_stats"].get(layer, {})
        print(f"  {layer:<8} {ls.get('total_detections', 0):>12,} "
              f"{ls.get('unique_markers', 0):>8} "
              f"{ls.get('avg_confidence', 0):>10.3f} "
              f"{ls.get('hits_per_1k_msgs', 0):>10.2f}")

    total = stats["total_detections"]
    unique = stats["unique_markers_fired"]
    print(f"  {'─'*52}")
    print(f"  {'TOTAL':<8} {total:>12,} {unique:>8}")
    print(f"\n  Avg detections/chunk: {stats['avg_detections_per_chunk']}")
    print(f"  Median detections/chunk: {stats['median_detections_per_chunk']}")

    # Top markers
    markers = stats["marker_stats"]
    if layer_filter:
        markers = [m for m in markers if m["layer"] == layer_filter.upper()]

    print(f"\n  --- Top {top_n} Markers by Frequency ---")
    print(f"  {'#':<4} {'Marker':<45} {'Layer':<5} {'Count':>7} {'H/1K':>7} "
          f"{'AvgC':>6} {'Cov%':>6}")
    print(f"  {'─'*84}")

    for i, m in enumerate(markers[:top_n], 1):
        flag = ""
        # Flag inflationäre markers
        if m["layer"] == "ATO" and m["hits_per_1k_msgs"] > 50:
            flag = " !!!"
        elif m["layer"] == "SEM" and m["hits_per_1k_msgs"] > 10:
            flag = " !!"
        elif m["layer"] == "CLU" and m["hits_per_1k_msgs"] > 5:
            flag = " !"

        print(f"  {i:<4} {m['marker_id']:<45} {m['layer']:<5} "
              f"{m['count']:>7,} {m['hits_per_1k_msgs']:>7.2f} "
              f"{m['avg_confidence']:>6.3f} {m['chunk_coverage']:>5.1f}%{flag}")

    # Inflationäre markers warning
    inflationary = [
        m for m in markers
        if (m["layer"] == "ATO" and m["hits_per_1k_msgs"] > 100)
        or (m["layer"] == "SEM" and m["hits_per_1k_msgs"] > 20)
        or (m["layer"] == "CLU" and m["hits_per_1k_msgs"] > 10)
    ]
    if inflationary:
        print(f"\n  --- INFLATIONÄRE MARKER ({len(inflationary)}) ---")
        print(f"  These fire too often and likely need precision fixes:")
        for m in inflationary:
            print(f"    {m['marker_id']:<45} {m['hits_per_1k_msgs']:>7.2f} hits/1K msgs")

    # Low-confidence markers
    low_conf = [m for m in markers if m["avg_confidence"] < 0.5 and m["count"] > 5]
    if low_conf:
        print(f"\n  --- LOW CONFIDENCE MARKERS ({len(low_conf)}) ---")
        for m in low_conf[:10]:
            print(f"    {m['marker_id']:<45} avg={m['avg_confidence']:.3f} "
                  f"(range {m['min_confidence']:.3f}-{m['max_confidence']:.3f})")

    # DE vs EN comparison
    de_results = [r for r in eval_data["results"] if r["lang"] == "de"]
    en_results = [r for r in eval_data["results"] if r["lang"] == "en"]
    if de_results and en_results:
        de_msgs = sum(r["message_count"] for r in de_results)
        en_msgs = sum(r["message_count"] for r in en_results)
        de_dets = sum(r["detection_count"] for r in de_results)
        en_dets = sum(r["detection_count"] for r in en_results)
        print(f"\n  --- DE vs EN ---")
        print(f"  DE: {de_dets:,} detections in {de_msgs:,} msgs "
              f"({de_dets/de_msgs*1000:.1f} hits/1K)")
        print(f"  EN: {en_dets:,} detections in {en_msgs:,} msgs "
              f"({en_dets/en_msgs*1000:.1f} hits/1K)")


def sample_detections(eval_data: dict, n: int = 10, layer_filter: str | None = None):
    """Sample random detections for manual review."""
    all_samples = []
    for chunk in eval_data["results"]:
        for det in chunk["detections"]:
            if layer_filter and det["layer"] != layer_filter.upper():
                continue
            # Get the message text for context
            all_samples.append({
                "chunk_id": chunk["chunk_id"],
                "lang": chunk["lang"],
                **det,
            })

    if not all_samples:
        print("  No detections to sample.", file=sys.stderr)
        return

    samples = random.sample(all_samples, min(n, len(all_samples)))

    print(f"\n  --- Random Detection Sample ({len(samples)}) ---\n")
    for i, s in enumerate(samples, 1):
        matches_str = ""
        if s.get("matches"):
            matches_str = " | ".join(m["value"] for m in s["matches"][:3])
        print(f"  [{i}] {s['marker_id']} ({s['layer']}, conf={s['confidence']:.3f})")
        print(f"      Chunk: {s['chunk_id']} ({s['lang']})")
        if matches_str:
            print(f"      Matched: \"{matches_str}\"")
        print()


def export_results(eval_data: dict, stats: dict):
    """Export full results to JSONL for further analysis."""
    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        for chunk in eval_data["results"]:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    print(f"\n  Exported: {RESULTS_PATH} ({len(eval_data['results'])} chunks)")

    # Also export stats summary
    stats_path = EVAL_DIR / "stats.json"
    # Remove samples from stats for cleaner export
    export_stats = {
        "summary": {
            "total_chunks": eval_data["total_chunks"],
            "total_messages": eval_data["total_messages"],
            "total_chars": eval_data["total_chars"],
            "threshold": eval_data["threshold"],
            "total_detections": stats["total_detections"],
            "unique_markers_fired": stats["unique_markers_fired"],
            "avg_detections_per_chunk": stats["avg_detections_per_chunk"],
        },
        "layer_stats": stats["layer_stats"],
        "marker_stats": [
            {k: v for k, v in m.items() if k != "samples"}
            for m in stats["marker_stats"]
        ],
    }
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(export_stats, f, indent=2, ensure_ascii=False)
    print(f"  Exported: {stats_path}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate LeanDeep engine against gold corpus")
    parser.add_argument("--top", type=int, default=30, help="Show top N markers (default: 30)")
    parser.add_argument("--layer", type=str, help="Filter by layer (ATO/SEM/CLU/MEMA)")
    parser.add_argument("--sample", type=int, default=0, help="Sample N random detections")
    parser.add_argument("--export", action="store_true", help="Export results to eval/results.jsonl")
    parser.add_argument("--threshold", type=float, default=0.3, help="Detection threshold (default: 0.3)")
    parser.add_argument("--max-chunks", type=int, default=0, help="Limit chunks to process (0=all)")
    args = parser.parse_args()

    if not CORPUS_PATH.exists():
        print(f"ERROR: Corpus not found at {CORPUS_PATH}", file=sys.stderr)
        print(f"Run: python3 tools/build_eval_corpus.py --build", file=sys.stderr)
        return

    # Load engine
    print("Loading engine...", file=sys.stderr)
    eng = MarkerEngine()
    eng.load()
    print(f"  Loaded {len(eng.markers)} markers", file=sys.stderr)

    # Load corpus
    corpus = load_corpus()
    print(f"  Loaded {len(corpus)} chunks", file=sys.stderr)

    # Run evaluation
    print(f"\nRunning evaluation (threshold={args.threshold})...", file=sys.stderr)
    layers = [args.layer.upper()] if args.layer else None
    eval_data = run_eval(eng, corpus, threshold=args.threshold, layers=layers,
                         max_chunks=args.max_chunks)

    # Compute stats
    stats = compute_stats(eval_data)

    # Print report
    print_report(eval_data, stats, top_n=args.top, layer_filter=args.layer)

    # Sample detections
    if args.sample > 0:
        sample_detections(eval_data, n=args.sample, layer_filter=args.layer)

    # Export
    if args.export:
        export_results(eval_data, stats)


if __name__ == "__main__":
    main()
