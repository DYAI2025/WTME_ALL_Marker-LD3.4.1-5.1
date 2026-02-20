#!/usr/bin/env python3
"""
Prosody Calibration Tool — Back-engineer structural emotion profiles from labeled data.

Downloads emotion-labeled text datasets from HuggingFace, extracts prosody features
(sentence structure, punctuation rhythm, pronoun focus, etc.), and computes per-emotion
statistical profiles with empirical thresholds.

Output: api/prosody_profiles.json — used by the engine as universal emotion constants
for the VAD lock-and-key gate.

Usage:
    python3 tools/calibrate_prosody.py [--samples N] [--output PATH]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np


# ─── Prosody Feature Extraction ─────────────────────────────────────────────

# Sentence splitter: split on .!? followed by space or end
_SENT_SPLIT = re.compile(r'(?<=[.!?])\s+|(?<=[.!?])$')

# Pronouns (DE + EN)
_ICH_PATS = re.compile(r'\b(ich|mir|mich|meiner?|I|me|my|mine|myself)\b', re.I)
_DU_PATS = re.compile(r'\b(du|dir|dich|deiner?|you|your|yours|yourself)\b', re.I)
_WIR_PATS = re.compile(r'\b(wir|uns|unser[em]?|we|us|our|ours|ourselves)\b', re.I)

# Negation (DE + EN)
_NEGATION = re.compile(
    r'\b(nicht|kein|keine|keinem|keinen|keiner|nie|niemals|nirgends|'
    r'not|never|no|nothing|nowhere|nobody|neither|nor|don\'t|doesn\'t|'
    r'didn\'t|won\'t|wouldn\'t|can\'t|couldn\'t|shouldn\'t|isn\'t|aren\'t|wasn\'t|weren\'t)\b', re.I
)

# Past tense indicators (simple heuristic)
_PAST_DE = re.compile(r'\b(war|hatte|wurde|gewesen|gehabt|geworden|habe .+?[gt]e?t)\b', re.I)
_PAST_EN = re.compile(r'\b(was|were|had|did|been|\w+ed)\b', re.I)

# Conditional/subjunctive
_CONDITIONAL = re.compile(
    r'\b(würde|könnte|sollte|hätte|wäre|müsste|dürfte|'
    r'would|could|should|might|may)\b', re.I
)

# Imperative indicators (DE: sentence-initial verb-like, EN: sentence-initial base verb)
_IMPERATIVE_DE = re.compile(r'^(hör|geh|mach|sag|lass|komm|gib|nimm|schau|zeig|halt|stop)', re.I)
_IMPERATIVE_EN = re.compile(r'^(stop|go|come|give|take|look|show|tell|listen|shut|leave|get|do|be|let|make|try|keep|help|run|sit|stand|wait|put)', re.I)

# Hedging words
_HEDGING = re.compile(
    r'\b(vielleicht|eventuell|möglicherweise|irgendwie|sozusagen|'
    r'maybe|perhaps|possibly|somehow|kind of|sort of|I guess|I think|probably)\b', re.I
)

# Intensifiers
_INTENSIFIERS = re.compile(
    r'\b(sehr|total|absolut|extrem|unglaublich|wahnsinnig|komplett|völlig|'
    r'very|really|extremely|absolutely|totally|completely|incredibly|so)\b', re.I
)

# Words (rough tokenizer)
_WORDS = re.compile(r'\b\w+\b')

# CAPS words (all uppercase, min 2 chars, exclude I)
_CAPS_WORD = re.compile(r'\b[A-ZÄÖÜ]{2,}\b')


def split_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    # Handle multiple punctuation (!!!, ???, ...)
    normalized = re.sub(r'([!?.]){2,}', r'\1', text)
    sentences = _SENT_SPLIT.split(normalized)
    return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 1]


def extract_prosody(text: str) -> dict[str, float]:
    """Extract prosody features from a single text."""
    if not text or len(text.strip()) < 5:
        return {}

    sentences = split_sentences(text)
    if not sentences:
        sentences = [text]

    n_sents = len(sentences)
    words = _WORDS.findall(text)
    n_words = max(len(words), 1)

    # Word lengths per sentence
    words_per_sent = [len(_WORDS.findall(s)) for s in sentences]
    avg_sent_len = np.mean(words_per_sent) if words_per_sent else 0

    # Punctuation ratios
    excl_count = text.count('!')
    question_count = text.count('?')
    ellipsis_count = text.count('...')

    # Pronoun counts
    ich_count = len(_ICH_PATS.findall(text))
    du_count = len(_DU_PATS.findall(text))
    wir_count = len(_WIR_PATS.findall(text))

    # Negation density
    neg_count = len(_NEGATION.findall(text))

    # Tense indicators
    past_count = len(_PAST_DE.findall(text)) + len(_PAST_EN.findall(text))
    cond_count = len(_CONDITIONAL.findall(text))

    # Imperative: check if any sentence starts with imperative verb
    imp_count = sum(
        1 for s in sentences
        if _IMPERATIVE_DE.match(s.strip()) or _IMPERATIVE_EN.match(s.strip())
    )

    # Hedging
    hedge_count = len(_HEDGING.findall(text))

    # Intensifiers
    intens_count = len(_INTENSIFIERS.findall(text))

    # Repetition: content words that appear more than once
    word_lower = [w.lower() for w in words if len(w) > 3]
    word_freq = defaultdict(int)
    for w in word_lower:
        word_freq[w] += 1
    repeated = sum(1 for v in word_freq.values() if v > 1)
    unique = max(len(word_freq), 1)

    # Fragments (very short sentences, < 4 words)
    fragments = sum(1 for wps in words_per_sent if wps < 4)

    # CAPS words
    caps_count = len(_CAPS_WORD.findall(text))

    return {
        "avg_sentence_length": round(float(avg_sent_len), 2),
        "sentence_count": n_sents,
        "excl_per_sent": round(excl_count / n_sents, 3),
        "question_per_sent": round(question_count / n_sents, 3),
        "ellipsis_per_1k": round(ellipsis_count / max(len(text), 1) * 1000, 2),
        "ich_ratio": round(ich_count / n_words, 4),
        "du_ratio": round(du_count / n_words, 4),
        "wir_ratio": round(wir_count / n_words, 4),
        "du_ich_balance": round(du_count / max(ich_count, 1), 3),
        "negation_per_1k": round(neg_count / max(len(text), 1) * 1000, 2),
        "past_tense_ratio": round(past_count / n_words, 4),
        "conditional_ratio": round(cond_count / n_words, 4),
        "imperative_ratio": round(imp_count / n_sents, 3),
        "hedging_per_1k": round(hedge_count / max(len(text), 1) * 1000, 2),
        "intensifier_per_1k": round(intens_count / max(len(text), 1) * 1000, 2),
        "repetition_score": round(repeated / unique, 3),
        "fragment_ratio": round(fragments / n_sents, 3),
        "caps_per_1k": round(caps_count / max(len(text), 1) * 1000, 2),
        "word_count": n_words,
    }


# ─── Dataset Loading ─────────────────────────────────────────────────────────

# Map dataset labels to Ekman basic emotions
EKMAN_MAP = {
    # dair-ai/emotion labels
    "anger": "ANGER", "fear": "FEAR", "joy": "JOY",
    "love": "LOVE", "sadness": "SADNESS", "surprise": "SURPRISE",
    # go_emotions labels
    "admiration": "JOY", "amusement": "JOY", "approval": "JOY",
    "caring": "LOVE", "desire": "LOVE", "gratitude": "JOY",
    "excitement": "SURPRISE", "curiosity": "SURPRISE",
    "optimism": "JOY", "pride": "JOY", "relief": "JOY",
    "annoyance": "ANGER", "disapproval": "ANGER",
    "disappointment": "SADNESS", "grief": "SADNESS", "remorse": "SADNESS",
    "confusion": "FEAR", "embarrassment": "FEAR", "nervousness": "FEAR",
    "disgust": "DISGUST",
    "realization": None, "neutral": None,  # skip
    # BRIGHTER labels
    "Anger": "ANGER", "Fear": "FEAR", "Joy": "JOY",
    "Sadness": "SADNESS", "Surprise": "SURPRISE", "Disgust": "DISGUST",
    "Contempt": "CONTEMPT",
}

# Integer label mapping for dair-ai/emotion
EMOTION_INT_MAP = {0: "SADNESS", 1: "JOY", 2: "LOVE", 3: "ANGER", 4: "FEAR", 5: "SURPRISE"}


def load_dair_emotion(max_samples: int = 20000) -> list[tuple[str, str]]:
    """Load dair-ai/emotion dataset."""
    print("  Loading dair-ai/emotion...")
    from datasets import load_dataset
    ds = load_dataset("dair-ai/emotion", split="train")
    samples = []
    for row in ds:
        text = row.get("text", "")
        label_int = row.get("label")
        if label_int is not None and label_int in EMOTION_INT_MAP:
            emotion = EMOTION_INT_MAP[label_int]
            samples.append((text, emotion))
        if len(samples) >= max_samples:
            break
    print(f"    → {len(samples)} samples")
    return samples


def load_go_emotions(max_samples: int = 30000) -> list[tuple[str, str]]:
    """Load go_emotions simplified dataset."""
    print("  Loading google-research-datasets/go_emotions...")
    from datasets import load_dataset
    ds = load_dataset("google-research-datasets/go_emotions", "simplified", split="train")

    # go_emotions has multi-label: labels is a list of ints
    # Label names from the dataset
    label_names = ds.features["labels"].feature.names if hasattr(ds.features["labels"], "feature") else None

    samples = []
    for row in ds:
        text = row.get("text", "")
        labels = row.get("labels", [])
        if not labels or not text:
            continue

        # Try to get label name
        for label_id in labels:
            if label_names:
                label_str = label_names[label_id] if label_id < len(label_names) else None
            else:
                label_str = str(label_id)

            emotion = EKMAN_MAP.get(label_str)
            if emotion:
                samples.append((text, emotion))
                break  # One label per text

        if len(samples) >= max_samples:
            break
    print(f"    → {len(samples)} samples")
    return samples


def load_brighter(max_samples: int = 20000) -> list[tuple[str, str]]:
    """Load BRIGHTER dataset (DE + EN)."""
    print("  Loading brighter-dataset/BRIGHTER-emotion-categories...")
    from datasets import load_dataset

    samples = []
    for lang in ["eng", "deu"]:
        try:
            ds = load_dataset("brighter-dataset/BRIGHTER-emotion-categories", lang, split="train")
            for row in ds:
                text = row.get("text", "")
                if not text:
                    continue
                # BRIGHTER has emotion columns as binary (0/1), lowercase
                for col in ["anger", "fear", "joy", "sadness", "surprise", "disgust", "contempt",
                            "Anger", "Fear", "Joy", "Sadness", "Surprise", "Disgust", "Contempt"]:
                    if row.get(col, 0) == 1:
                        emotion = EKMAN_MAP.get(col) or EKMAN_MAP.get(col.capitalize())
                        if emotion:
                            samples.append((text, emotion))
                            break
                if len(samples) >= max_samples:
                    break
        except Exception as e:
            print(f"    Warning: Could not load BRIGHTER/{lang}: {e}")

    print(f"    → {len(samples)} samples")
    return samples


# ─── Statistical Analysis ────────────────────────────────────────────────────

def compute_profiles(
    all_samples: list[tuple[str, str]],
) -> dict:
    """Compute per-emotion prosody profiles from labeled samples."""
    # Extract features
    emotion_features: dict[str, list[dict]] = defaultdict(list)
    skipped = 0

    print(f"\nExtracting prosody features from {len(all_samples)} samples...")
    for i, (text, emotion) in enumerate(all_samples):
        if i % 5000 == 0 and i > 0:
            print(f"  {i}/{len(all_samples)}...")
        features = extract_prosody(text)
        if features:
            emotion_features[emotion].append(features)
        else:
            skipped += 1

    print(f"  Extracted: {sum(len(v) for v in emotion_features.values())} samples, skipped: {skipped}")
    print(f"  Emotions: {sorted(emotion_features.keys())}")

    # Compute statistics per emotion per feature
    feature_names = [
        "avg_sentence_length", "excl_per_sent", "question_per_sent",
        "ellipsis_per_1k", "ich_ratio", "du_ratio", "wir_ratio",
        "du_ich_balance", "negation_per_1k", "past_tense_ratio",
        "conditional_ratio", "imperative_ratio", "hedging_per_1k",
        "intensifier_per_1k", "repetition_score", "fragment_ratio",
        "caps_per_1k",
    ]

    profiles = {}
    for emotion, features_list in sorted(emotion_features.items()):
        n = len(features_list)
        profile = {"n_samples": n}

        for feat in feature_names:
            values = [f[feat] for f in features_list if feat in f]
            if not values:
                continue
            arr = np.array(values)
            profile[feat] = {
                "mean": round(float(np.mean(arr)), 4),
                "std": round(float(np.std(arr)), 4),
                "p25": round(float(np.percentile(arr, 25)), 4),
                "p50": round(float(np.percentile(arr, 50)), 4),
                "p75": round(float(np.percentile(arr, 75)), 4),
                "p90": round(float(np.percentile(arr, 90)), 4),
            }

        profiles[emotion] = profile

    return profiles


def compute_discriminants(profiles: dict) -> dict:
    """Compute discriminative power of each feature across emotions.

    For each feature, computes how well it separates each emotion from the rest
    using Cohen's d effect size.
    """
    feature_names = [k for k in list(profiles.values())[0] if k != "n_samples" and isinstance(list(profiles.values())[0].get(k), dict)]

    discriminants = {}
    for feat in feature_names:
        # Collect all means and stds
        emotion_stats = {}
        for emotion, profile in profiles.items():
            if feat in profile:
                emotion_stats[emotion] = (profile[feat]["mean"], profile[feat]["std"])

        if len(emotion_stats) < 2:
            continue

        # Global mean/std across all emotions
        all_means = [s[0] for s in emotion_stats.values()]
        global_mean = np.mean(all_means)
        global_std = max(np.std(all_means), 0.001)

        # Per-emotion deviation from global (effect size)
        feat_disc = {}
        for emotion, (mean, std) in emotion_stats.items():
            effect = round((mean - global_mean) / global_std, 3)
            feat_disc[emotion] = effect

        discriminants[feat] = feat_disc

    return discriminants


def derive_thresholds(profiles: dict, discriminants: dict) -> dict:
    """Derive gate thresholds for each emotion based on profiles.

    For each emotion, identifies the top discriminating features and
    sets thresholds at the 25th percentile (minimum) for positive discriminants
    or 75th percentile (maximum) for negative discriminants.
    """
    thresholds = {}

    for emotion in profiles:
        # Find features where this emotion deviates most from global
        feature_scores = []
        for feat, disc in discriminants.items():
            if emotion in disc:
                feature_scores.append((feat, disc[emotion]))

        # Sort by absolute effect size
        feature_scores.sort(key=lambda x: abs(x[1]), reverse=True)

        # Take top 5 most discriminating features
        emotion_thresholds = {}
        for feat, effect in feature_scores[:6]:
            stats = profiles[emotion].get(feat, {})
            if not stats:
                continue

            if effect > 0.3:
                # This emotion has HIGH values → threshold at p25 (minimum to qualify)
                emotion_thresholds[feat] = {
                    "direction": "high",
                    "threshold": stats["p25"],
                    "typical": stats["p50"],
                    "effect_size": effect,
                }
            elif effect < -0.3:
                # This emotion has LOW values → threshold at p75 (maximum to qualify)
                emotion_thresholds[feat] = {
                    "direction": "low",
                    "threshold": stats["p75"],
                    "typical": stats["p50"],
                    "effect_size": effect,
                }

        thresholds[emotion] = emotion_thresholds

    return thresholds


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Calibrate prosody profiles from emotion datasets")
    parser.add_argument("--samples", type=int, default=20000, help="Max samples per dataset")
    parser.add_argument("--output", type=str, default="api/prosody_profiles.json")
    parser.add_argument("--datasets", type=str, default="dair,brighter",
                        help="Comma-separated: dair,go_emotions,brighter")
    args = parser.parse_args()

    print("=" * 60)
    print("Prosody Calibration Tool")
    print("=" * 60)

    # Load datasets
    all_samples: list[tuple[str, str]] = []
    ds_names = [d.strip() for d in args.datasets.split(",")]

    print(f"\nLoading datasets: {ds_names}")
    if "dair" in ds_names:
        all_samples.extend(load_dair_emotion(args.samples))
    if "go_emotions" in ds_names:
        all_samples.extend(load_go_emotions(args.samples))
    if "brighter" in ds_names:
        all_samples.extend(load_brighter(args.samples))

    if not all_samples:
        print("ERROR: No samples loaded!")
        sys.exit(1)

    # Count per emotion
    emotion_counts = defaultdict(int)
    for _, emotion in all_samples:
        emotion_counts[emotion] += 1
    print(f"\nTotal: {len(all_samples)} samples")
    for emotion, count in sorted(emotion_counts.items(), key=lambda x: -x[1]):
        print(f"  {emotion:12s}: {count:6d}")

    # Compute profiles
    profiles = compute_profiles(all_samples)

    # Compute discriminants
    print("\nComputing discriminative power per feature...")
    discriminants = compute_discriminants(profiles)

    # Print top discriminants per emotion
    for emotion in sorted(profiles.keys()):
        print(f"\n  {emotion}:")
        feature_scores = []
        for feat, disc in discriminants.items():
            if emotion in disc:
                feature_scores.append((feat, disc[emotion]))
        feature_scores.sort(key=lambda x: abs(x[1]), reverse=True)
        for feat, effect in feature_scores[:5]:
            direction = "↑" if effect > 0 else "↓"
            print(f"    {direction} {feat:25s}  effect={effect:+.2f}  "
                  f"mean={profiles[emotion][feat]['mean']:.4f}")

    # Derive thresholds
    print("\nDeriving gate thresholds...")
    thresholds = derive_thresholds(profiles, discriminants)

    # Build output
    output = {
        "meta": {
            "total_samples": len(all_samples),
            "datasets": ds_names,
            "emotions": sorted(profiles.keys()),
            "n_features": len(discriminants),
        },
        "profiles": profiles,
        "discriminants": discriminants,
        "thresholds": thresholds,
    }

    # Write output
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nOutput written to: {out_path}")
    print(f"  Profiles: {len(profiles)} emotions")
    print(f"  Features: {len(discriminants)}")
    print(f"  Thresholds: {sum(len(v) for v in thresholds.values())} rules")

    # Summary table
    print("\n" + "=" * 60)
    print("EMOTION GATE KEYS (top discriminating features)")
    print("=" * 60)
    for emotion in sorted(thresholds.keys()):
        rules = thresholds[emotion]
        if not rules:
            continue
        print(f"\n  🔑 {emotion}:")
        for feat, rule in sorted(rules.items(), key=lambda x: abs(x[1]["effect_size"]), reverse=True):
            d = rule["direction"]
            t = rule["threshold"]
            typ = rule["typical"]
            eff = rule["effect_size"]
            symbol = "≥" if d == "high" else "≤"
            print(f"    {feat:25s} {symbol} {t:.4f}  (typical: {typ:.4f}, effect: {eff:+.2f})")


if __name__ == "__main__":
    main()
