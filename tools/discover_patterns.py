#!/usr/bin/env python3.12
"""
discover_patterns.py — Pattern Discovery Tool for LeanDeep Markers

Uses gensim NLP to discover new marker candidates from conversation text.

Modes:
  collocations  Find multi-word expressions (bigrams/trigrams) in text
  gaps          Find frequent phrases NOT covered by existing markers
  expand        Suggest semantically similar terms for marker keywords

Usage:
  python3.12 tools/discover_patterns.py collocations <text_files...>
  python3.12 tools/discover_patterns.py gaps <text_files...>
  python3.12 tools/discover_patterns.py expand <marker_id>

Options:
  --lang de|en       Language filter (default: all)
  --min-count N      Minimum phrase frequency (default: 3)
  --top N            Show top N results (default: 30)
  --threshold F      Gensim scoring threshold (default: 8.0)
  --yaml             Output as marker YAML candidates
  --registry PATH    Path to marker_registry.json
  --model NAME       Gensim model for expand mode (default: auto)

Input: text files with one message/sentence per line, or stdin.

Examples:
  # Find collocations in German chat logs
  python3.12 tools/discover_patterns.py collocations data/chats/*.txt --lang de

  # Find gaps — frequent phrases no marker catches
  python3.12 tools/discover_patterns.py gaps data/chats/*.txt

  # Expand a marker with semantically similar terms
  python3.12 tools/discover_patterns.py expand ATO_LOVE_DEVOTION
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = REPO / "build" / "markers_normalized" / "marker_registry.json"

# German stop/connector words for gensim Phrases (kept in alternation group)
GERMAN_CONNECTORS = frozenset(
    "und oder aber der die das den dem des ein eine einen einem einer "
    "in von zu für mit auf an bei nach über unter vor zwischen durch "
    "ich du er sie es wir ihr sich mich dich uns euch ihm ihr "
    "ist sind war waren hat haben wird werden kann können "
    "nicht kein keine keinen keinem keiner auch noch schon ja nein "
    "so wie was wer wo wenn dann doch nur mal sehr".split()
)

ENGLISH_CONNECTORS = frozenset(
    "the a an of to in for with on at by from is are was were "
    "be been being have has had do does did will would shall should "
    "can could may might must not no and or but if then so "
    "i you he she it we they me him her us them my your his its our "
    "this that these those very just also still only".split()
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def tokenize(text: str, lang: str | None = None) -> list[str]:
    """Simple word tokenizer preserving umlauts and unicode."""
    # Keep letters (incl. umlauts), digits, hyphens inside words
    tokens = re.findall(r"[\w'-]+", text.lower(), re.UNICODE)
    # Filter very short tokens and pure numbers
    return [t for t in tokens if len(t) >= 2 and not t.isdigit()]


def read_input_lines(files: list[str]) -> list[str]:
    """Read lines from files or stdin."""
    lines = []
    if not files or files == ["-"]:
        lines = sys.stdin.read().splitlines()
    else:
        for fp in files:
            p = Path(fp)
            if not p.exists():
                print(f"WARN: {fp} not found, skipping", file=sys.stderr)
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            lines.extend(text.splitlines())
    return [l.strip() for l in lines if l.strip()]


def load_registry(path: Path) -> dict:
    """Load marker registry JSON."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("markers", data)


def compile_marker_patterns(registry: dict) -> list[tuple[str, re.Pattern]]:
    """Compile all regex patterns from the registry."""
    compiled = []
    for mid, mdata in registry.items():
        for p in mdata.get("patterns", []):
            ptype = p.get("type", "regex") if isinstance(p, dict) else "regex"
            if ptype not in ("regex", "keyword"):
                continue
            raw = str(p.get("value", "")) if isinstance(p, dict) else str(p)
            if not raw or len(raw) < 3:
                continue
            try:
                compiled.append((mid, re.compile(raw, re.IGNORECASE)))
            except re.error:
                pass
    return compiled


def get_connector_words(lang: str | None):
    """Return connector words for language."""
    if lang == "de":
        return GERMAN_CONNECTORS
    elif lang == "en":
        return ENGLISH_CONNECTORS
    else:
        return GERMAN_CONNECTORS | ENGLISH_CONNECTORS


# ---------------------------------------------------------------------------
# Mode: collocations
# ---------------------------------------------------------------------------

def cmd_collocations(args):
    """Find multi-word expressions using gensim Phrases."""
    from gensim.models.phrases import Phrases

    lines = read_input_lines(args.files)
    if not lines:
        print("ERROR: No input text. Provide files or pipe via stdin.", file=sys.stderr)
        sys.exit(1)

    print(f"Input: {len(lines)} lines", file=sys.stderr)

    # Tokenize into sentences
    sentences = [tokenize(line, args.lang) for line in lines]
    sentences = [s for s in sentences if len(s) >= 2]

    connectors = get_connector_words(args.lang)

    # --- Bigrams ---
    print("Training bigram model...", file=sys.stderr)
    bigram_model = Phrases(
        sentences,
        min_count=args.min_count,
        threshold=args.threshold,
        connector_words=connectors,
    )

    # --- Trigrams ---
    print("Training trigram model...", file=sys.stderr)
    bigram_sentences = [bigram_model[s] for s in sentences]
    trigram_model = Phrases(
        bigram_sentences,
        min_count=max(2, args.min_count - 1),
        threshold=args.threshold,
        connector_words=connectors,
    )

    # Collect scored phrases
    scored_phrases = {}

    # Bigrams
    for phrase, score in bigram_model.export_phrases().items():
        phrase_str = phrase.replace("_", " ")
        if len(phrase_str) >= 5:
            scored_phrases[phrase_str] = score

    # Trigrams
    for phrase, score in trigram_model.export_phrases().items():
        phrase_str = phrase.replace("_", " ")
        if len(phrase_str) >= 7:
            scored_phrases[phrase_str] = max(scored_phrases.get(phrase_str, 0), score)

    # Also count raw frequency of discovered phrases in the corpus
    full_text = " ".join(" ".join(s) for s in sentences)
    freq_counted = {}
    for phrase in scored_phrases:
        count = full_text.count(phrase)
        if count > 0:
            freq_counted[phrase] = (scored_phrases[phrase], count)

    # Sort by combined score (gensim_score * frequency)
    ranked = sorted(
        freq_counted.items(),
        key=lambda x: x[1][0] * x[1][1],
        reverse=True,
    )[: args.top]

    # Output
    print(f"\n{'='*60}")
    print(f"  COLLOCATIONS — Top {len(ranked)} multi-word expressions")
    print(f"  (min_count={args.min_count}, threshold={args.threshold})")
    print(f"{'='*60}\n")
    print(f"  {'Phrase':<40s} {'Score':>8s} {'Freq':>6s}")
    print(f"  {'─'*40} {'─'*8} {'─'*6}")

    for phrase, (score, freq) in ranked:
        print(f"  {phrase:<40s} {score:>8.1f} {freq:>6d}")

    if args.yaml and ranked:
        _output_yaml_candidates(ranked, "collocations")


# ---------------------------------------------------------------------------
# Mode: gaps
# ---------------------------------------------------------------------------

def cmd_gaps(args):
    """Find frequent phrases in text not covered by any existing marker."""
    lines = read_input_lines(args.files)
    if not lines:
        print("ERROR: No input text.", file=sys.stderr)
        sys.exit(1)

    print(f"Input: {len(lines)} lines", file=sys.stderr)

    # Load and compile existing markers
    registry = load_registry(args.registry)
    compiled_patterns = compile_marker_patterns(registry)
    print(f"Loaded {len(compiled_patterns)} compiled patterns from {len(registry)} markers", file=sys.stderr)

    # Build n-gram frequency counts (1-gram to 4-gram)
    connectors = get_connector_words(args.lang)
    ngram_counts: Counter = Counter()

    for line in lines:
        tokens = tokenize(line, args.lang)
        # Filter connectors for n-gram building
        content_tokens = [t for t in tokens if t not in connectors and len(t) >= 3]

        for n in range(1, 5):
            for i in range(len(content_tokens) - n + 1):
                gram = " ".join(content_tokens[i : i + n])
                if len(gram) >= 4:
                    ngram_counts[gram] += 1

    # Filter by min_count
    frequent = {
        gram: count
        for gram, count in ngram_counts.items()
        if count >= args.min_count
    }
    print(f"Frequent n-grams (>={args.min_count}): {len(frequent)}", file=sys.stderr)

    # Check which frequent n-grams are NOT matched by any existing pattern
    gaps = {}
    for gram, count in frequent.items():
        matched_by = None
        for mid, pat in compiled_patterns:
            if pat.search(gram):
                matched_by = mid
                break
        if matched_by is None:
            gaps[gram] = count

    # Sort by frequency
    ranked = sorted(gaps.items(), key=lambda x: (-x[1], -len(x[0])))[: args.top]

    # Output
    print(f"\n{'='*60}")
    print(f"  GAPS — Top {len(ranked)} uncovered frequent phrases")
    print(f"  (not matched by any of {len(compiled_patterns)} marker patterns)")
    print(f"{'='*60}\n")
    print(f"  {'Phrase':<40s} {'Freq':>6s} {'Words':>6s}")
    print(f"  {'─'*40} {'─'*6} {'─'*6}")

    for gram, count in ranked:
        n_words = len(gram.split())
        print(f"  {gram:<40s} {count:>6d} {n_words:>6d}")

    if args.yaml and ranked:
        _output_yaml_candidates([(g, (0, c)) for g, c in ranked], "gaps")


# ---------------------------------------------------------------------------
# Mode: expand
# ---------------------------------------------------------------------------

def cmd_expand(args):
    """Suggest semantically similar terms for a marker's keywords."""
    import gensim.downloader as api

    # Load registry and find marker
    registry = load_registry(args.registry)
    marker_id = args.marker_id

    if marker_id not in registry:
        print(f"ERROR: Marker '{marker_id}' not found in registry.", file=sys.stderr)
        # Fuzzy suggest
        candidates = [m for m in registry if marker_id.upper() in m.upper()]
        if candidates:
            print(f"Did you mean: {', '.join(candidates[:5])}", file=sys.stderr)
        sys.exit(1)

    mdata = registry[marker_id]

    # Extract keywords from patterns
    keywords = set()
    for p in mdata.get("patterns", []):
        raw = p.get("value", "") if isinstance(p, dict) else str(p)
        # Extract words from regex alternation groups
        # Strip regex syntax: \b, (?i), parentheses, etc.
        cleaned = re.sub(r"\\b|\\s\+|\(\?i\)|[\(\)\[\]\\]", " ", raw)
        words = re.findall(r"[\w'äöüÄÖÜß-]+", cleaned, re.UNICODE)
        for w in words:
            if len(w) >= 3 and not w.isdigit():
                keywords.add(w.lower())

    if not keywords:
        print(f"ERROR: No extractable keywords from marker '{marker_id}'.", file=sys.stderr)
        sys.exit(1)

    print(f"Marker: {marker_id}", file=sys.stderr)
    print(f"Keywords: {', '.join(sorted(keywords))}", file=sys.stderr)
    print(f"Language: {mdata.get('lang', '?')}", file=sys.stderr)

    # Select model based on language
    lang = mdata.get("lang", "de")
    model_name = args.model

    if not model_name:
        if lang == "de":
            # German: use fasttext-wiki (if available) or word2vec-google-news
            model_name = "fasttext-wiki-news-subwords-300"
            print(f"Note: Using English FastText model. For German, provide a custom model with --model.", file=sys.stderr)
        else:
            model_name = "fasttext-wiki-news-subwords-300"

    print(f"Loading model '{model_name}'... (first time downloads ~1GB)", file=sys.stderr)
    try:
        model = api.load(model_name)
    except Exception as e:
        print(f"ERROR: Could not load model: {e}", file=sys.stderr)
        print("Available models: " + ", ".join(api.info()["models"].keys()), file=sys.stderr)
        sys.exit(1)

    # Find similar words for each keyword
    print(f"\n{'='*60}")
    print(f"  EXPAND — Semantic neighbors for {marker_id}")
    print(f"  Model: {model_name}")
    print(f"{'='*60}\n")

    all_suggestions = Counter()

    for kw in sorted(keywords):
        try:
            similar = model.most_similar(kw, topn=15)
            print(f"  {kw}:")
            for word, score in similar:
                if score >= 0.4 and len(word) >= 3:
                    print(f"    {word:<30s} {score:.3f}")
                    all_suggestions[word] += score
        except KeyError:
            print(f"  {kw}: (not in vocabulary)")

    # Aggregate top suggestions
    if all_suggestions:
        print(f"\n  {'─'*50}")
        print(f"  Top expansion candidates (aggregated):")
        print(f"  {'─'*50}")
        for word, score in all_suggestions.most_common(args.top):
            # Skip if already a keyword
            if word.lower() not in keywords:
                print(f"    {word:<30s} {score:.3f}")


# ---------------------------------------------------------------------------
# Mode: from-examples (bonus: mine patterns from existing marker examples)
# ---------------------------------------------------------------------------

def cmd_from_examples(args):
    """Mine patterns from the positive examples already in markers."""
    from gensim.models.phrases import Phrases

    registry = load_registry(args.registry)

    # Collect all positive examples
    lines = []
    for mid, mdata in registry.items():
        lang = mdata.get("lang", "de")
        if args.lang and lang != args.lang:
            continue
        examples = mdata.get("examples", {})
        positives = examples.get("positive", []) if isinstance(examples, dict) else []
        for ex in positives:
            if isinstance(ex, str) and len(ex) >= 5:
                lines.append(ex)

    print(f"Mined {len(lines)} positive examples from {len(registry)} markers", file=sys.stderr)

    if not lines:
        print("ERROR: No examples found.", file=sys.stderr)
        sys.exit(1)

    # Same pipeline as collocations
    sentences = [tokenize(line, args.lang) for line in lines]
    sentences = [s for s in sentences if len(s) >= 2]
    connectors = get_connector_words(args.lang)

    bigram_model = Phrases(
        sentences,
        min_count=max(2, args.min_count),
        threshold=args.threshold,
        connector_words=connectors,
    )

    scored = {}
    for phrase, score in bigram_model.export_phrases().items():
        phrase_str = phrase.replace("_", " ")
        if len(phrase_str) >= 5:
            scored[phrase_str] = score

    # Check which are already covered by patterns
    compiled_patterns = compile_marker_patterns(registry)
    uncovered = {}
    for phrase, score in scored.items():
        matched = False
        for mid, pat in compiled_patterns:
            if pat.search(phrase):
                matched = True
                break
        if not matched:
            uncovered[phrase] = score

    ranked = sorted(uncovered.items(), key=lambda x: -x[1])[: args.top]

    print(f"\n{'='*60}")
    print(f"  FROM-EXAMPLES — Collocations from positive examples")
    print(f"  not yet covered by any marker pattern")
    print(f"{'='*60}\n")
    print(f"  {'Phrase':<40s} {'Score':>8s}")
    print(f"  {'─'*40} {'─'*8}")

    for phrase, score in ranked:
        print(f"  {phrase:<40s} {score:>8.1f}")


# ---------------------------------------------------------------------------
# YAML output
# ---------------------------------------------------------------------------

def _output_yaml_candidates(ranked, source: str):
    """Output candidate patterns as marker YAML."""
    print(f"\n{'='*60}")
    print(f"  YAML CANDIDATES (from {source})")
    print(f"{'='*60}\n")

    # Group into a single suggested ATO marker
    phrases = []
    for item in ranked[:10]:
        phrase = item[0] if isinstance(item, tuple) else item
        phrases.append(phrase)

    # Build alternation regex
    escaped = [re.escape(p) for p in phrases]
    pattern = "(?i)\\\\b(" + "|".join(escaped) + ")\\\\b"

    print("# Suggested ATO marker candidate")
    print(f"# Source: {source} discovery")
    print(f"# Phrases: {len(phrases)}")
    print()
    print("name: ATO_DISCOVERED_PATTERN")
    print('label: "Discovered Pattern"')
    print("class: atomic")
    print("version: 1.0")
    print("languages: [de, en]")
    print(f'meaning: "Auto-discovered pattern from {source} analysis"')
    print("patterns:")
    print(f'  - type: regex')
    print(f'    value: "{pattern}"')
    print("examples:")
    print("  positive:")
    for p in phrases[:5]:
        print(f'  - "{p}"')
    print("  negative: []")
    print("tags: [atomic, auto-discovered]")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Pattern Discovery Tool for LeanDeep Markers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    # Shared args
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("files", nargs="*", default=[], help="Input text files (or stdin)")
    shared.add_argument("--lang", choices=["de", "en"], default=None, help="Language filter")
    shared.add_argument("--min-count", type=int, default=3, help="Minimum frequency (default: 3)")
    shared.add_argument("--top", type=int, default=30, help="Top N results (default: 30)")
    shared.add_argument("--threshold", type=float, default=8.0, help="Gensim scoring threshold")
    shared.add_argument("--yaml", action="store_true", help="Output YAML candidates")
    shared.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY,
        help=f"Path to registry JSON (default: {DEFAULT_REGISTRY})",
    )

    # collocations
    sub_coll = subparsers.add_parser("collocations", parents=[shared], help="Find multi-word expressions")
    sub_coll.set_defaults(func=cmd_collocations)

    # gaps
    sub_gaps = subparsers.add_parser("gaps", parents=[shared], help="Find uncovered frequent phrases")
    sub_gaps.set_defaults(func=cmd_gaps)

    # from-examples
    sub_ex = subparsers.add_parser("from-examples", parents=[shared], help="Mine collocations from marker examples")
    sub_ex.set_defaults(func=cmd_from_examples)

    # expand
    sub_exp = subparsers.add_parser("expand", help="Suggest similar terms for a marker")
    sub_exp.add_argument("marker_id", help="Marker ID to expand")
    sub_exp.add_argument("--model", default=None, help="Gensim model name (default: auto)")
    sub_exp.add_argument("--top", type=int, default=20, help="Top N results")
    sub_exp.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY,
        help="Path to registry JSON",
    )
    sub_exp.set_defaults(func=cmd_expand)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
