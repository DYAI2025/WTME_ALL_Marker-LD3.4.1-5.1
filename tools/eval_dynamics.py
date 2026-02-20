#!/usr/bin/env python3
"""Evaluate emotion dynamics (VAD, UED, state indices) on the gold corpus.

Processes each chunk through MarkerEngine.analyze_conversation() and reports:
  1. Average VAD per speaker (Person_A vs Person_B vs Person_C)
  2. UED metrics aggregated across conversations
  3. State index trends (early vs late chunks)
  4. Emotional hotspot chunks (highest arousal / lowest valence)
  5. DE vs EN comparison of VAD distributions

Usage:
    python3 tools/eval_dynamics.py --corpus eval/gold_corpus.jsonl --threshold 0.3 --top 10
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

# Allow importing from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.engine import MarkerEngine


def _safe_div(numerator: float, denominator: int | float) -> float:
    """Division with zero guard."""
    return numerator / denominator if denominator else 0.0


def _std(xs: list[float]) -> float:
    """Population standard deviation."""
    if len(xs) < 2:
        return 0.0
    mean = sum(xs) / len(xs)
    variance = sum((x - mean) ** 2 for x in xs) / len(xs)
    return math.sqrt(variance)


def load_corpus(path: str) -> list[dict]:
    """Load JSONL gold corpus."""
    chunks = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate emotion dynamics on the gold corpus."
    )
    parser.add_argument(
        "--corpus", default="eval/gold_corpus.jsonl",
        help="Path to gold corpus JSONL (default: eval/gold_corpus.jsonl)",
    )
    parser.add_argument(
        "--threshold", type=float, default=0.3,
        help="Detection threshold for analyze_conversation (default: 0.3)",
    )
    parser.add_argument(
        "--top", type=int, default=10,
        help="Number of hotspot entries to display (default: 10)",
    )
    args = parser.parse_args()

    # ── Load engine ──
    print("Loading MarkerEngine...", file=sys.stderr)
    eng = MarkerEngine()
    eng.load()
    print(
        f"  {len(eng.markers)} markers loaded "
        f"(ATO={len(eng.ato_markers)}, SEM={len(eng.sem_markers)}, "
        f"CLU={len(eng.clu_markers)}, MEMA={len(eng.mema_markers)})",
        file=sys.stderr,
    )

    # ── Load corpus ──
    chunks = load_corpus(args.corpus)
    print(f"Loaded {len(chunks)} chunks from {args.corpus}", file=sys.stderr)

    # ── Accumulators ──
    speaker_vads: dict[str, list[dict]] = {}  # speaker -> [{v,a,d}, ...]
    ued_list: list[dict] = []
    state_list: list[dict] = []  # ordered by chunk index
    hotspots: list[dict] = []    # per-message VAD entries for hotspot ranking

    total_timing_ms = 0.0
    t0 = time.perf_counter()

    for i, chunk in enumerate(chunks):
        chunk_id = chunk.get("id", str(i))
        lang = chunk.get("lang", "?")
        messages = [
            {"text": m["text"], "speaker": m.get("speaker", "?")}
            for m in chunk["messages"]
        ]

        result = eng.analyze_conversation(messages, threshold=args.threshold)
        total_timing_ms += result.get("timing_ms", 0)

        # ── Per-speaker VAD ──
        message_vad = result.get("message_vad", [])
        for msg_idx, mv in enumerate(message_vad):
            if msg_idx < len(messages):
                speaker = messages[msg_idx]["speaker"]
                entry = {**mv, "lang": lang}
                speaker_vads.setdefault(speaker, []).append(entry)

        # ── UED ──
        ued = result.get("ued_metrics")
        if ued is not None:
            ued_list.append(ued)

        # ── State indices ──
        si = result.get("state_indices")
        if si is not None:
            state_list.append({
                "chunk_idx": i,
                "chunk_id": chunk_id,
                "lang": lang,
                **si,
            })

        # ── Hotspot candidates ──
        for msg_idx, mv in enumerate(message_vad):
            snippet = messages[msg_idx]["text"][:80] if msg_idx < len(messages) else ""
            hotspots.append({
                "chunk_id": chunk_id,
                "msg_idx": msg_idx,
                "valence": mv["valence"],
                "arousal": mv["arousal"],
                "dominance": mv["dominance"],
                "lang": lang,
                "snippet": snippet,
            })

        if (i + 1) % 200 == 0:
            elapsed = time.perf_counter() - t0
            rate = (i + 1) / elapsed
            eta = (len(chunks) - i - 1) / rate
            print(
                f"  ...processed {i + 1}/{len(chunks)} chunks "
                f"({rate:.0f} chunks/s, ETA {eta:.0f}s)",
                file=sys.stderr,
            )

    wall_time = time.perf_counter() - t0

    # =====================================================================
    # REPORT
    # =====================================================================
    sep = "=" * 72
    print(f"\n{sep}")
    print("DYNAMICS EVALUATION REPORT")
    print(f"{sep}")
    print(f"Corpus:    {args.corpus}")
    print(f"Chunks:    {len(chunks)}")
    print(f"Threshold: {args.threshold}")
    print(f"Wall time: {wall_time:.1f}s  (engine: {total_timing_ms:.0f}ms)")

    # ── 1. Per-speaker VAD averages ──
    print(f"\n--- Average VAD per Speaker ---")
    speaker_stats = {}
    for speaker in sorted(speaker_vads.keys()):
        vads = speaker_vads[speaker]
        n = len(vads)
        avg_v = _safe_div(sum(v["valence"] for v in vads), n)
        avg_a = _safe_div(sum(v["arousal"] for v in vads), n)
        avg_d = _safe_div(sum(v["dominance"] for v in vads), n)
        std_v = _std([v["valence"] for v in vads])
        std_a = _std([v["arousal"] for v in vads])
        print(
            f"  {speaker:12s}  N={n:>6d}  "
            f"V={avg_v:+.3f} (sd={std_v:.3f})  "
            f"A={avg_a:.3f} (sd={std_a:.3f})  "
            f"D={avg_d:.3f}"
        )
        speaker_stats[speaker] = {
            "count": n,
            "avg_valence": round(avg_v, 4),
            "avg_arousal": round(avg_a, 4),
            "avg_dominance": round(avg_d, 4),
            "std_valence": round(std_v, 4),
            "std_arousal": round(std_a, 4),
        }

    # ── 2. UED metrics aggregated ──
    ued_agg = {}
    if ued_list:
        n_ued = len(ued_list)
        mean_hb_v = _safe_div(sum(u["home_base"]["valence"] for u in ued_list), n_ued)
        mean_hb_a = _safe_div(sum(u["home_base"]["arousal"] for u in ued_list), n_ued)
        mean_hb_d = _safe_div(sum(u["home_base"]["dominance"] for u in ued_list), n_ued)
        mean_var_v = _safe_div(sum(u["variability"]["valence"] for u in ued_list), n_ued)
        mean_var_a = _safe_div(sum(u["variability"]["arousal"] for u in ued_list), n_ued)
        mean_inst_v = _safe_div(sum(u["instability"]["valence"] for u in ued_list), n_ued)
        mean_inst_a = _safe_div(sum(u["instability"]["arousal"] for u in ued_list), n_ued)
        mean_density = _safe_div(sum(u["density"] for u in ued_list), n_ued)
        mean_rise = _safe_div(sum(u["rise_rate"] for u in ued_list), n_ued)
        mean_recovery = _safe_div(sum(u["recovery_rate"] for u in ued_list), n_ued)

        print(f"\n--- UED Metrics (aggregated over {n_ued} chunks) ---")
        print(f"  Home Base:    V={mean_hb_v:+.3f}  A={mean_hb_a:.3f}  D={mean_hb_d:.3f}")
        print(f"  Variability:  V={mean_var_v:.3f}   A={mean_var_a:.3f}")
        print(f"  Instability:  V={mean_inst_v:.3f}   A={mean_inst_a:.3f}")
        print(f"  Density:      {mean_density:.3f}")
        print(f"  Rise Rate:    {mean_rise:.3f}")
        print(f"  Recovery:     {mean_recovery:.3f}")

        ued_agg = {
            "count": n_ued,
            "mean_home_base": {
                "valence": round(mean_hb_v, 4),
                "arousal": round(mean_hb_a, 4),
                "dominance": round(mean_hb_d, 4),
            },
            "mean_variability": {
                "valence": round(mean_var_v, 4),
                "arousal": round(mean_var_a, 4),
            },
            "mean_instability": {
                "valence": round(mean_inst_v, 4),
                "arousal": round(mean_inst_a, 4),
            },
            "mean_density": round(mean_density, 4),
            "mean_rise_rate": round(mean_rise, 4),
            "mean_recovery_rate": round(mean_recovery, 4),
        }
    else:
        print("\n--- UED Metrics: no chunks produced UED data ---")

    # ── 3. State index trends: early 25% vs late 25% ──
    state_trend = {}
    if state_list:
        n_s = len(state_list)
        q1 = max(n_s // 4, 1)
        early = state_list[:q1]
        late = state_list[-q1:]

        def avg_si(items: list[dict], key: str) -> float:
            vals = [s[key] for s in items if key in s]
            return _safe_div(sum(vals), len(vals))

        print(f"\n--- State Index Trends (early {len(early)} vs late {len(late)} chunks) ---")
        for key in ("trust", "conflict", "deesc"):
            e = avg_si(early, key)
            la = avg_si(late, key)
            delta = la - e
            arrow = "\u2191" if delta > 0.01 else "\u2193" if delta < -0.01 else "\u2192"
            print(
                f"  {key:10s}  early={e:+.3f}  late={la:+.3f}  "
                f"\u0394={delta:+.3f} {arrow}"
            )
            state_trend[key] = {
                "early": round(e, 4),
                "late": round(la, 4),
                "delta": round(delta, 4),
            }

        # Also report avg contributing_markers
        avg_contrib_early = avg_si(early, "contributing_markers")
        avg_contrib_late = avg_si(late, "contributing_markers")
        print(
            f"  {'markers':10s}  early={avg_contrib_early:.1f}  "
            f"late={avg_contrib_late:.1f}"
        )
    else:
        print("\n--- State Index Trends: no state data available ---")

    # ── 4. Hotspot chunks ──
    # Filter out zero-VAD entries (no detections = no real hotspot)
    nonzero_hotspots = [
        h for h in hotspots
        if abs(h["valence"]) > 0.001 or abs(h["arousal"]) > 0.001
    ]

    print(f"\n--- Top {args.top} Emotional Hotspots (lowest valence) ---")
    by_valence = sorted(nonzero_hotspots, key=lambda h: h["valence"])[:args.top]
    for h in by_valence:
        print(
            f"  [{h['chunk_id']}#{h['msg_idx']:02d}] "
            f"V={h['valence']:+.3f} A={h['arousal']:.3f} "
            f"({h['lang']}) \"{h['snippet']}\""
        )

    print(f"\n--- Top {args.top} Emotional Hotspots (highest arousal) ---")
    by_arousal = sorted(nonzero_hotspots, key=lambda h: -h["arousal"])[:args.top]
    for h in by_arousal:
        print(
            f"  [{h['chunk_id']}#{h['msg_idx']:02d}] "
            f"V={h['valence']:+.3f} A={h['arousal']:.3f} "
            f"({h['lang']}) \"{h['snippet']}\""
        )

    # ── 5. DE vs EN comparison ──
    lang_stats = {}
    for lang_code in ("de", "en"):
        lang_vads = [h for h in hotspots if h["lang"] == lang_code]
        if not lang_vads:
            continue
        n_l = len(lang_vads)
        nz = [v for v in lang_vads if abs(v["valence"]) > 0.001 or abs(v["arousal"]) > 0.001]
        avg_v = _safe_div(sum(v["valence"] for v in lang_vads), n_l)
        avg_a = _safe_div(sum(v["arousal"] for v in lang_vads), n_l)
        avg_d = _safe_div(sum(v["dominance"] for v in lang_vads), n_l)
        std_v = _std([v["valence"] for v in lang_vads])
        std_a = _std([v["arousal"] for v in lang_vads])
        density = _safe_div(len(nz), n_l)
        lang_stats[lang_code] = {
            "total_messages": n_l,
            "nonzero_messages": len(nz),
            "avg_valence": round(avg_v, 4),
            "avg_arousal": round(avg_a, 4),
            "avg_dominance": round(avg_d, 4),
            "std_valence": round(std_v, 4),
            "std_arousal": round(std_a, 4),
            "detection_density": round(density, 4),
        }

    if lang_stats:
        print(f"\n--- DE vs EN VAD Comparison ---")
        for label in ("de", "en"):
            if label not in lang_stats:
                continue
            ls = lang_stats[label]
            print(
                f"  {label.upper()}: N={ls['total_messages']:>6d} "
                f"(detected={ls['nonzero_messages']}, density={ls['detection_density']:.2%})  "
                f"V={ls['avg_valence']:+.3f} (sd={ls['std_valence']:.3f})  "
                f"A={ls['avg_arousal']:.3f} (sd={ls['std_arousal']:.3f})  "
                f"D={ls['avg_dominance']:.3f}"
            )

    print(f"\n{sep}")

    # ── Export stats ──
    export = {
        "corpus": args.corpus,
        "total_chunks": len(chunks),
        "threshold": args.threshold,
        "wall_time_s": round(wall_time, 1),
        "engine_time_ms": round(total_timing_ms, 0),
        "speaker_vad": speaker_stats,
        "ued_aggregated": ued_agg,
        "state_trends": state_trend,
        "lang_comparison": lang_stats,
        "hotspots_lowest_valence": [
            {
                "chunk_id": h["chunk_id"],
                "msg_idx": h["msg_idx"],
                "valence": h["valence"],
                "arousal": h["arousal"],
                "lang": h["lang"],
                "snippet": h["snippet"],
            }
            for h in by_valence
        ],
        "hotspots_highest_arousal": [
            {
                "chunk_id": h["chunk_id"],
                "msg_idx": h["msg_idx"],
                "valence": h["valence"],
                "arousal": h["arousal"],
                "lang": h["lang"],
                "snippet": h["snippet"],
            }
            for h in by_arousal
        ],
    }

    out_path = Path("eval/dynamics_stats.json")
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(export, f, indent=2, ensure_ascii=False)
    print(f"\nExported: {out_path}")


if __name__ == "__main__":
    main()
