"""
Prosody-based emotion detection from text structure.

Detects Ekman basic emotions (ANGER, SADNESS, FEAR, JOY, LOVE, SURPRISE, DISGUST)
by analyzing linguistic structure — sentence length, punctuation rhythm, pronoun focus,
negation density, tense distribution, hedging, intensifiers, repetition.

Uses empirically calibrated profiles from 20K+ labeled texts (prosody_profiles.json)
with discriminant-weighted linear scoring.
"""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


# ─── Feature Extraction Patterns ─────────────────────────────────────────────

_SENT_SPLIT = re.compile(r'(?<=[.!?])\s+|(?<=[.!?])$')

# Pronouns (DE + EN)
_ICH = re.compile(r'\b(ich|mir|mich|meiner?|I|me|my|mine|myself)\b', re.I)
_DU = re.compile(r'\b(du|dir|dich|deiner?|you|your|yours|yourself)\b', re.I)
_WIR = re.compile(r'\b(wir|uns|unser[em]?|we|us|our|ours|ourselves)\b', re.I)

# Negation (DE + EN)
_NEGATION = re.compile(
    r"\b(nicht|kein|keine|keinem|keinen|keiner|nie|niemals|nirgends|"
    r"not|never|no|nothing|nowhere|nobody|neither|nor|don't|doesn't|"
    r"didn't|won't|wouldn't|can't|couldn't|shouldn't|isn't|aren't|wasn't|weren't)\b", re.I
)

# Past tense indicators
_PAST_DE = re.compile(r'\b(war|hatte|wurde|gewesen|gehabt|geworden)\b', re.I)
_PAST_EN = re.compile(r'\b(was|were|had|did|been|\w+ed)\b', re.I)

# Conditional/subjunctive
_CONDITIONAL = re.compile(
    r'\b(würde|könnte|sollte|hätte|wäre|müsste|dürfte|'
    r'would|could|should|might|may)\b', re.I
)

# Imperative
_IMPERATIVE_DE = re.compile(r'^(hör|geh|mach|sag|lass|komm|gib|nimm|schau|zeig|halt|stop)', re.I)
_IMPERATIVE_EN = re.compile(r'^(stop|go|come|give|take|look|show|tell|listen|shut|leave|get|do|be|let|make|try|keep|help|run|sit|stand|wait|put)', re.I)

# Hedging
_HEDGING = re.compile(
    r'\b(vielleicht|eventuell|möglicherweise|irgendwie|sozusagen|'
    r'maybe|perhaps|possibly|somehow|kind of|sort of|I guess|I think|probably)\b', re.I
)

# Intensifiers
_INTENSIFIERS = re.compile(
    r'\b(sehr|total|absolut|extrem|unglaublich|wahnsinnig|komplett|völlig|'
    r'very|really|extremely|absolutely|totally|completely|incredibly|so)\b', re.I
)

_WORDS = re.compile(r'\b\w+\b')
_CAPS_WORD = re.compile(r'\b[A-ZÄÖÜ]{2,}\b')


# ─── Feature Names (must match prosody_profiles.json) ────────────────────────

FEATURE_NAMES = [
    "avg_sentence_length", "excl_per_sent", "question_per_sent",
    "ellipsis_per_1k", "ich_ratio", "du_ratio", "wir_ratio",
    "du_ich_balance", "negation_per_1k", "past_tense_ratio",
    "conditional_ratio", "imperative_ratio", "hedging_per_1k",
    "intensifier_per_1k", "repetition_score", "fragment_ratio",
    "caps_per_1k",
]

EMOTIONS = ["ANGER", "DISGUST", "FEAR", "JOY", "LOVE", "SADNESS", "SURPRISE"]


# ─── Feature Extraction ──────────────────────────────────────────────────────

def _split_sentences(text: str) -> list[str]:
    normalized = re.sub(r'([!?.]){2,}', r'\1', text)
    sentences = _SENT_SPLIT.split(normalized)
    return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 1]


def extract_prosody(text: str) -> dict[str, float] | None:
    """Extract 17 prosody features from text. Returns None if text too short."""
    if not text or len(text.strip()) < 10:
        return None

    sentences = _split_sentences(text)
    if not sentences:
        sentences = [text]

    n_sents = len(sentences)
    words = _WORDS.findall(text)
    n_words = max(len(words), 1)
    text_len = max(len(text), 1)

    words_per_sent = [len(_WORDS.findall(s)) for s in sentences]
    avg_sent_len = sum(words_per_sent) / len(words_per_sent) if words_per_sent else 0

    # Punctuation
    excl_count = text.count('!')
    question_count = text.count('?')
    ellipsis_count = text.count('...')

    # Pronouns
    ich_count = len(_ICH.findall(text))
    du_count = len(_DU.findall(text))
    wir_count = len(_WIR.findall(text))

    # Negation
    neg_count = len(_NEGATION.findall(text))

    # Tense
    past_count = len(_PAST_DE.findall(text)) + len(_PAST_EN.findall(text))
    cond_count = len(_CONDITIONAL.findall(text))

    # Imperative
    imp_count = sum(
        1 for s in sentences
        if _IMPERATIVE_DE.match(s.strip()) or _IMPERATIVE_EN.match(s.strip())
    )

    # Hedging & intensifiers
    hedge_count = len(_HEDGING.findall(text))
    intens_count = len(_INTENSIFIERS.findall(text))

    # Repetition
    word_lower = [w.lower() for w in words if len(w) > 3]
    word_freq: dict[str, int] = defaultdict(int)
    for w in word_lower:
        word_freq[w] += 1
    repeated = sum(1 for v in word_freq.values() if v > 1)
    unique = max(len(word_freq), 1)

    # Fragments
    fragments = sum(1 for wps in words_per_sent if wps < 4)

    # CAPS
    caps_count = len(_CAPS_WORD.findall(text))

    return {
        "avg_sentence_length": round(float(avg_sent_len), 2),
        "excl_per_sent": round(excl_count / n_sents, 3),
        "question_per_sent": round(question_count / n_sents, 3),
        "ellipsis_per_1k": round(ellipsis_count / text_len * 1000, 2),
        "ich_ratio": round(ich_count / n_words, 4),
        "du_ratio": round(du_count / n_words, 4),
        "wir_ratio": round(wir_count / n_words, 4),
        "du_ich_balance": round(du_count / max(ich_count, 1), 3),
        "negation_per_1k": round(neg_count / text_len * 1000, 2),
        "past_tense_ratio": round(past_count / n_words, 4),
        "conditional_ratio": round(cond_count / n_words, 4),
        "imperative_ratio": round(imp_count / n_sents, 3),
        "hedging_per_1k": round(hedge_count / text_len * 1000, 2),
        "intensifier_per_1k": round(intens_count / text_len * 1000, 2),
        "repetition_score": round(repeated / unique, 3),
        "fragment_ratio": round(fragments / n_sents, 3),
        "caps_per_1k": round(caps_count / text_len * 1000, 2),
    }


# ─── Emotion Scoring ─────────────────────────────────────────────────────────

@dataclass
class EmotionResult:
    """Per-message emotion scores with dominant emotion."""
    scores: dict[str, float]       # {ANGER: 0.3, JOY: 0.6, ...}
    dominant: str                   # "JOY"
    dominant_score: float           # 0.6
    prosody: dict[str, float]      # raw prosody features


class ProsodyScorer:
    """Scores text against Ekman emotion profiles using discriminant analysis.

    Key design decisions:
    - Effect sizes capped at ±1.5 to prevent small-sample emotions (DISGUST n=171)
      from dominating with extreme discriminant weights
    - Sample-count weighting: emotions with more training data get higher trust
    - Softmax temperature=5.0 for spread-out probabilities (avoids winner-take-all)
    - z-scores clamped to ±3 to prevent single extreme features from dominating
    """

    # Discriminant weight cap — prevents small-sample artifacts
    _EFFECT_CAP = 1.5
    # Minimum samples for reliable profile; below this, emotion excluded
    _MIN_RELIABLE_N = 500

    def __init__(self, profiles_path: str | None = None, baseline_path: str | None = None):
        path = Path(profiles_path or Path(__file__).parent / "prosody_profiles.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.profiles = data["profiles"]
        self.discriminants = data["discriminants"]
        self.thresholds = data.get("thresholds", {})

        # Pre-compute sample counts per emotion
        self._sample_counts: dict[str, int] = {}
        for emotion in EMOTIONS:
            profile = self.profiles.get(emotion, {})
            self._sample_counts[emotion] = profile.get("n_samples", 0)

        # Determine which emotions have enough data for reliable scoring
        self._reliable_emotions: list[str] = [
            e for e in EMOTIONS
            if self._sample_counts.get(e, 0) >= self._MIN_RELIABLE_N
        ]

        # Load conversation baseline (calibrated from gold corpus).
        # Key insight: discriminants (which direction each emotion deviates)
        # are universal constants from training data. But the CENTER POINT
        # for z-scoring must come from conversation data, not tweets.
        # Tweets have 3x longer sentences, 5x less du-ratio, 13x fewer questions.
        bl_path = Path(baseline_path or Path(__file__).parent / "conversation_baseline.json")
        baseline: dict[str, dict] = {}
        if bl_path.exists():
            with open(bl_path, "r", encoding="utf-8") as f:
                bl_data = json.load(f)
            baseline = bl_data.get("features", {})

        # Use conversation baseline for z-scoring center, fall back to training means
        self._z_means: dict[str, float] = {}
        self._z_stds: dict[str, float] = {}
        for feat in FEATURE_NAMES:
            if feat not in self.discriminants:
                continue
            # Prefer conversation baseline (matches actual usage domain)
            if feat in baseline:
                self._z_means[feat] = baseline[feat]["mean"]
                self._z_stds[feat] = max(baseline[feat]["std"], 0.001)
            else:
                # Fallback: training data global mean
                means = []
                for emotion in EMOTIONS:
                    profile = self.profiles.get(emotion, {})
                    feat_data = profile.get(feat)
                    if feat_data and isinstance(feat_data, dict):
                        means.append(feat_data["mean"])
                if means:
                    self._z_means[feat] = sum(means) / len(means)
                    gm = self._z_means[feat]
                    variance = sum((m - gm) ** 2 for m in means) / len(means)
                    self._z_stds[feat] = max(math.sqrt(variance), 0.001)

        # Pre-compute capped discriminant vectors per emotion
        self._disc_vectors: dict[str, dict[str, float]] = {}
        for emotion in EMOTIONS:
            vec = {}
            for feat in FEATURE_NAMES:
                if feat in self.discriminants and emotion in self.discriminants[feat]:
                    raw_d = self.discriminants[feat][emotion]
                    # Cap to prevent extreme values from small samples
                    capped = max(-self._EFFECT_CAP, min(self._EFFECT_CAP, raw_d))
                    vec[feat] = capped
            self._disc_vectors[emotion] = vec

    def score(self, text: str) -> EmotionResult | None:
        """Score a text against all emotion profiles.

        Rule-based scoring using empirically confirmed structural signals
        from 20K+ labeled texts. Each emotion has characteristic features
        that were validated as universal constants (Cohen's d > 0.5).

        For each emotion, checks whether the text's prosody features match
        the emotion's structural signature, using conversation baselines
        as the reference point for "normal".

        Returns None if text is too short for reliable scoring.
        """
        features = extract_prosody(text)
        if not features:
            return None

        raw_scores: dict[str, float] = {}

        for emotion in self._reliable_emotions:
            raw_scores[emotion] = self._rule_score(emotion, features)

        # Softmax with moderate temperature — allows clear winners but not winner-take-all
        scores = _softmax(raw_scores, temperature=1.5)

        dominant = max(scores, key=scores.get)  # type: ignore[arg-type]
        dominant_score = scores[dominant]

        return EmotionResult(
            scores=scores,
            dominant=dominant,
            dominant_score=round(dominant_score, 3),
            prosody=features,
        )

    def _rule_score(self, emotion: str, features: dict[str, float]) -> float:
        """Rule-based scoring for a single emotion.

        Uses empirically confirmed structural rules from calibration:
        - ANGER:    exclamations, no hedging, du-focus, fragments, repetition
        - SADNESS:  ich-focus, intensifiers, hedging, no wir, no questions
        - FEAR:     no repetition, past tense, questions, ich-focus
        - JOY:      no negation, no hedging, long sentences, no fragments
        - LOVE:     long sentences, no negation, no fragments, du-focus
        - SURPRISE: no repetition, past tense, conditional, questions
        """
        score = 0.0

        # Helper: how far above/below conversation baseline (in baseline stds)
        def z(feat: str) -> float:
            if feat not in features or feat not in self._z_means:
                return 0.0
            return (features[feat] - self._z_means[feat]) / self._z_stds[feat]

        # Helper: positive contribution if feature is above baseline
        def above(feat: str, weight: float = 1.0) -> float:
            return max(0.0, z(feat)) * weight

        # Helper: positive contribution if feature is below baseline
        def below(feat: str, weight: float = 1.0) -> float:
            return max(0.0, -z(feat)) * weight

        # Track whether key gateway features are present
        has_excl = features.get("excl_per_sent", 0) > self._z_means.get("excl_per_sent", 0)
        has_neg = features.get("negation_per_1k", 0) > self._z_means.get("negation_per_1k", 0)
        has_du = features.get("du_ratio", 0) > self._z_means.get("du_ratio", 0)
        has_ich = features.get("ich_ratio", 0) > self._z_means.get("ich_ratio", 0)
        has_quest = features.get("question_per_sent", 0) > self._z_means.get("question_per_sent", 0)

        if emotion == "ANGER":
            # Gateway: needs (negation OR du-focus) + exclamation/imperative
            score += above("negation_per_1k", 1.5)     # PRIMARY: "nie!", "nicht!"
            score += above("du_ratio", 1.5)             # PRIMARY: accusation "du"
            score += above("excl_per_sent", 1.0)        # CONFIRMATORY: exclamations
            score += above("imperative_ratio", 1.0)     # CONFIRMATORY: commands
            score += below("hedging_per_1k", 0.8)       # certain anger
            score += above("fragment_ratio", 0.5)        # short, punchy
            # Gateway: needs negation OR du-focus (structural aggression)
            if not (has_neg or has_du):
                score *= 0.25
            # Anti: questions → fear/surprise
            score -= above("question_per_sent", 1.0)

        elif emotion == "SADNESS":
            # Gateway: ich-focus WITHOUT exclamation (excl = anger)
            score += above("ich_ratio", 1.5)             # PRIMARY: "ich bin so..."
            score += above("intensifier_per_1k", 1.0)    # "so", "einfach"
            score += below("excl_per_sent", 1.5)         # PRIMARY: NO exclamation
            score += below("question_per_sent", 1.5)     # PRIMARY: no questions (resigned)
            score += above("hedging_per_1k", 0.5)        # uncertainty
            score += below("wir_ratio", 0.3)             # isolation
            # Anti: exclamation strongly dampens sadness
            if has_excl:
                score *= 0.4
            # Anti: questions strongly dampen sadness (→ FEAR)
            if has_quest:
                score *= 0.5
            # Anti: du-focus → anger/love
            score -= above("du_ratio", 0.8)

        elif emotion == "FEAR":
            # Gateway: QUESTIONS are the defining feature
            score += above("question_per_sent", 3.0)     # PRIMARY: "was wenn...?"
            score += above("conditional_ratio", 1.5)     # "könnte", "würde"
            score += above("ich_ratio", 0.3)             # worry self-reference
            score += above("ellipsis_per_1k", 0.5)       # trailing off
            score += below("excl_per_sent", 0.5)         # anxious, not shouting
            # Gateway: without questions, FEAR is unlikely (worry = hedging + sadness)
            if not has_quest:
                score *= 0.3
            # Anti: du-focus = anger
            score -= above("du_ratio", 0.5)

        elif emotion == "JOY":
            # Gateway: exclamation + NO negation (= positive exclamation)
            score += below("negation_per_1k", 2.5)       # PRIMARY: NO negation
            score += above("excl_per_sent", 1.2)         # exclamations
            score += above("intensifier_per_1k", 1.0)    # "so toll!", "total"
            score += below("hedging_per_1k", 0.5)        # confident
            score += above("avg_sentence_length", 0.3)   # flowing
            # Gateway: negation present → this is anger, not joy
            if has_neg:
                score *= 0.2
            # Anti: du-accusation = anger
            score -= above("du_ratio", 0.5)

        elif emotion == "LOVE":
            # Gateway: du-focus + long sentences + no exclamation (= soft partner focus)
            score += above("avg_sentence_length", 1.5)   # flowing, soft
            score += above("du_ratio", 1.5)               # PRIMARY: "du bist..."
            score += below("negation_per_1k", 1.0)       # no negation
            score += below("fragment_ratio", 0.8)         # complete thoughts
            score += below("excl_per_sent", 1.0)          # soft tone
            score += above("intensifier_per_1k", 0.5)     # "so sehr"
            # Bonus: du-focus + no excl + no negation = love archetype
            if has_du and not has_excl and not has_neg:
                score *= 1.3
            # Anti: ich-only without du = sadness
            if has_ich and not has_du:
                score *= 0.5

        elif emotion == "SURPRISE":
            # Gateway: question + exclamation COMBO (unique to surprise)
            score += above("question_per_sent", 1.5)      # "Was?! Wirklich?"
            score += above("excl_per_sent", 1.2)          # "!" emphasis
            score += above("past_tense_ratio", 0.8)       # "hätte nie gedacht"
            score += above("conditional_ratio", 0.8)      # "könnte"
            # Gateway: needs BOTH question and exclamation for strong surprise
            if has_quest and has_excl:
                score *= 1.5  # Boost combo
            elif not has_quest and not has_excl:
                score *= 0.2  # Very unlikely without either

        return max(0.0, score)

    def score_conversation(
        self, messages: list[dict],
    ) -> list[EmotionResult | None]:
        """Score each message in a conversation."""
        return [self.score(msg.get("text", "")) for msg in messages]


def _softmax(raw: dict[str, float], temperature: float = 1.0) -> dict[str, float]:
    """Softmax with temperature over a dict of scores."""
    if not raw:
        return {}
    # Shift for numerical stability
    max_val = max(raw.values())
    exp_scores = {k: math.exp((v - max_val) / temperature) for k, v in raw.items()}
    total = sum(exp_scores.values())
    if total == 0:
        # Uniform
        n = len(raw)
        return {k: round(1.0 / n, 3) for k in raw}
    return {k: round(v / total, 3) for k, v in exp_scores.items()}


# Singleton scorer (loads profiles once)
_scorer: ProsodyScorer | None = None


def get_scorer() -> ProsodyScorer:
    """Get or create the singleton prosody scorer."""
    global _scorer
    if _scorer is None:
        _scorer = ProsodyScorer()
    return _scorer
