#!/usr/bin/env python3
"""Generate and normalize missing ATO/SEM markers for iteration 3."""
from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_DIR = REPO_ROOT / "Markers_canonical.json"
CANONICAL_ARCHIVE = REPO_ROOT / "Markers_canonical 2.json.zip"

GENERATOR_DISABLED_MESSAGE = (
    "Iteration 3 generator is disabled. Please curate markers manually; "
    "see Iteration03_missing_marker.md for guidance."
)

# Target ATOs gathered from audit (missing or legacy format) and additional helpers used by new SEMs.
TARGET_ATOS = [
    "ATO_ACCUSATION_PHRASE",
    "ATO_ANGER_EXPRESSION",
    "ATO_APOLOGY",
    "ATO_APPEAL_TO_AUTHORITY_EXPERT",
    "ATO_APPEAL_TO_AUTHORITY_STUDY",
    "ATO_AUTHORITY_REF",
    "ATO_BARBED_COMMENT",
    "ATO_BEDENKEN",
    "ATO_BLAME_ATTRIBUTION",
    "ATO_BLAME_SHIFT",
    "ATO_BOUNDARY_CROSS",
    "ATO_COMPARISON_OBJECT",
    "ATO_CRITICISM_ATTACK_MARKER",
    "ATO_CONTRADICTION_CUE",
    "ATO_CULTURAL_ELEMENT",
    "ATO_DEESCALATION_PHRASE",
    "ATO_DEFENSIVENESS",
    "ATO_DELETE_TRACES",
    "ATO_DOUBLE_BIND_EXPRESSIONS",
    "ATO_DREHEN_IM_KREIS",
    "ATO_EMOTIONAL_WITHDRAWAL",
    "ATO_EMPATHY_MARKERS",
    "ATO_ESCALATION_LEXICON",
    "ATO_EXTERNALIZATION",
    "ATO_FAKE_IDENTITY_STORY",
    "ATO_FIRSTTIME_CLAUSE",
    "ATO_FLIRTING_PHRASE",
    "ATO_FUTURE_IDEA",
    "ATO_GREETING",
    "ATO_GUILT_FRAMING",
    "ATO_GUILT_TRIPPING_MARKER",
    "ATO_INDIFFERENT",
    "ATO_KEINE_LOESUNG",
    "ATO_LL_PHYSICAL_TOUCH",
    "ATO_LL_QUALITY_TIME",
    "ATO_MEMORY_TRIGGER",
    "ATO_METAPHOR_CUE",
    "ATO_MICRO_DISMISSAL",
    "ATO_MUSS_SCHAUEN",
    "ATO_NO_MOTIVATION",
    "ATO_OUTSIDE_PERSPECTIVE",
    "ATO_REPAIR_REQUEST",
    "ATO_RESIGNATION_FINAL",
    "ATO_SELF_ATTRIBUTION_NEGATIVE",
    "ATO_SELF_REF",
    "ATO_SILENCE",
    "ATO_SOCIAL_CHECKIN",
    "ATO_SVT_BEZIEHUNG_DU_BOTSCHAFT",
    "ATO_SWEAR_WORD",
    "ATO_THREAT_ESCALATION",
    "ATO_TWIST",
    "ATO_UNKNOWN",
    "ATO_UNSICHER",
    "ATO_VICTIM_POSITIONING",
    "ATO_VOLL_STRESS",
    "ATO_WE_PLAN",
    "ATO_ZWEIFEL",
    "ATO_ROLE_CHILD",
    "ATO_SUPPORT_PHRASE",
    "ATO_SOFTENING",
]

# SEM targets grouped as existing (requires normalization) and net-new (to be generated) items.
SEM_NORMALIZE = [
    "SEM_BLAME_SHIFTING",
    "SEM_CHILD_RESISTANCE",
    "SEM_COMMITMENT_REQUEST",
    "SEM_CONDITIONALITY_FRAME",
    "SEM_FRAGMENTED_SELF_NARRATIVE",
    "SEM_IDEALIZATION_DEVALUATION",
    "SEM_I_STATEMENT",
    "SEM_LIE_CONCEALMENT",
    "SEM_PARENTAL_AUTHORITY",
    "SEM_REALITY_DISTORTION_FIELD",
    "SEM_REPETITIVE_COMPLAINT",
    "SEM_RESPECT_RELIABILITY_FRAME",
    "SEM_RIVALRY_MENTION",
    "SEM_SELF_RELIANCE_EARLY",
    "SEM_SHARED_GOAL_FRAMING",
    "SEM_SIBLING_RIVALRY",
    "SEM_SOFT_COMMITMENT_MARKER",
    "SEM_SVT_APPEAL_DIRECT",
    "SEM_UNRESOLVED_ISSUE",
    "SEM_VALIDATION_OF_FEELING",
]

SEM_CREATE = [
    "SEM_AI_BOT_SCAM",
    "SEM_APATHY_EXPRESSION",
    "SEM_AVOIDANT_CHILDHOOD_REFERENCE",
    "SEM_BOUNDARY_SHIFT",
    "SEM_COMPARATIVE_CLAIM",
    "SEM_COMPETITIVE_DRIVE",
    "SEM_ECOLOGICAL_METAPHOR",
    "SEM_ENERGY_DEFICIT",
    "SEM_FRIENDLY_FLIRTING",
    "SEM_GENERIC_PATTERN",
    "SEM_GUILT_TRIPPING",
    "SEM_HOLISTIC_SCOPE",
    "SEM_KPI_FOCUS",
    "SEM_LATENT_EXPECTATION",
    "SEM_LONG_HORIZON",
    "SEM_MIRRORED_STYLE",
    "SEM_PUN_RIDDLE_QA",
    "SEM_SECURE_CHILDHOOD_REFERENCE",
    "SEM_SOFTENING_MOVE",
    "SEM_TRADEOFF_LANGUAGE",
]

SEM_COMPONENTS: Dict[str, List[str]] = {
    # normalized
    "SEM_BLAME_SHIFTING": ["ATO_BLAME_SHIFT", "ATO_EXTERNALIZATION"],
    "SEM_CHILD_RESISTANCE": ["ATO_ROLE_CHILD", "ATO_DEFENSIVENESS"],
    "SEM_COMMITMENT_REQUEST": ["ATO_REPAIR_REQUEST", "ATO_WE_PLAN"],
    "SEM_CONDITIONALITY_FRAME": ["ATO_BOUNDARY_CROSS", "ATO_TWIST"],
    "SEM_FRAGMENTED_SELF_NARRATIVE": ["ATO_SELF_REF", "ATO_CONTRADICTION_CUE"],
    "SEM_IDEALIZATION_DEVALUATION": ["ATO_COMPARISON_OBJECT", "ATO_CRITICISM_ATTACK_MARKER"],
    "SEM_I_STATEMENT": ["ATO_SELF_REF", "ATO_SOFTENING"],
    "SEM_LIE_CONCEALMENT": ["ATO_DELETE_TRACES", "ATO_FAKE_IDENTITY_STORY"],
    "SEM_PARENTAL_AUTHORITY": ["ATO_AUTHORITY_REF", "ATO_BOUNDARY_CROSS"],
    "SEM_REALITY_DISTORTION_FIELD": ["ATO_GUILT_FRAMING", "ATO_EXTERNALIZATION"],
    "SEM_REPETITIVE_COMPLAINT": ["ATO_DREHEN_IM_KREIS", "ATO_NO_MOTIVATION"],
    "SEM_RESPECT_RELIABILITY_FRAME": ["ATO_WE_PLAN", "ATO_BEDENKEN"],
    "SEM_RIVALRY_MENTION": ["ATO_COMPARISON_OBJECT", "ATO_BOUNDARY_CROSS"],
    "SEM_SELF_RELIANCE_EARLY": ["ATO_SELF_REF", "ATO_WE_PLAN"],
    "SEM_SHARED_GOAL_FRAMING": ["ATO_WE_PLAN", "ATO_FUTURE_IDEA"],
    "SEM_SIBLING_RIVALRY": ["ATO_ROLE_CHILD", "ATO_COMPARISON_OBJECT"],
    "SEM_SOFT_COMMITMENT_MARKER": ["ATO_SOFTENING", "ATO_WE_PLAN"],
    "SEM_SVT_APPEAL_DIRECT": ["ATO_SVT_BEZIEHUNG_DU_BOTSCHAFT", "ATO_GUILT_FRAMING"],
    "SEM_UNRESOLVED_ISSUE": ["ATO_DREHEN_IM_KREIS", "ATO_KEINE_LOESUNG"],
    "SEM_VALIDATION_OF_FEELING": ["ATO_EMPATHY_MARKERS", "ATO_SUPPORT_PHRASE"],
    # new
    "SEM_AI_BOT_SCAM": ["ATO_FAKE_IDENTITY_STORY", "ATO_DELETE_TRACES"],
    "SEM_APATHY_EXPRESSION": ["ATO_INDIFFERENT", "ATO_NO_MOTIVATION"],
    "SEM_AVOIDANT_CHILDHOOD_REFERENCE": ["ATO_ROLE_CHILD", "ATO_EMOTIONAL_WITHDRAWAL"],
    "SEM_BOUNDARY_SHIFT": ["ATO_BOUNDARY_CROSS", "ATO_TWIST"],
    "SEM_COMPARATIVE_CLAIM": ["ATO_COMPARISON_OBJECT", "ATO_ZWEIFEL"],
    "SEM_COMPETITIVE_DRIVE": ["ATO_COMPARISON_OBJECT", "ATO_ESCALATION_LEXICON"],
    "SEM_ECOLOGICAL_METAPHOR": ["ATO_METAPHOR_CUE", "ATO_OUTSIDE_PERSPECTIVE"],
    "SEM_ENERGY_DEFICIT": ["ATO_VOLL_STRESS", "ATO_NO_MOTIVATION"],
    "SEM_FRIENDLY_FLIRTING": ["ATO_FLIRTING_PHRASE", "ATO_SOFTENING"],
    "SEM_GENERIC_PATTERN": ["ATO_UNKNOWN", "ATO_OUTSIDE_PERSPECTIVE"],
    "SEM_GUILT_TRIPPING": ["ATO_GUILT_TRIPPING_MARKER", "ATO_GUILT_FRAMING"],
    "SEM_HOLISTIC_SCOPE": ["ATO_OUTSIDE_PERSPECTIVE", "ATO_MEMORY_TRIGGER"],
    "SEM_KPI_FOCUS": ["ATO_MEMORY_TRIGGER", "ATO_WE_PLAN"],
    "SEM_LATENT_EXPECTATION": ["ATO_MEMORY_TRIGGER", "ATO_ZWEIFEL"],
    "SEM_LONG_HORIZON": ["ATO_FUTURE_IDEA", "ATO_WE_PLAN"],
    "SEM_MIRRORED_STYLE": ["ATO_METAPHOR_CUE", "ATO_EMPATHY_MARKERS"],
    "SEM_PUN_RIDDLE_QA": ["ATO_TWIST", "ATO_METAPHOR_CUE"],
    "SEM_SECURE_CHILDHOOD_REFERENCE": ["ATO_ROLE_CHILD", "ATO_MEMORY_TRIGGER"],
    "SEM_SOFTENING_MOVE": ["ATO_SOFTENING", "ATO_DEESCALATION_PHRASE"],
    "SEM_TRADEOFF_LANGUAGE": ["ATO_ZWEIFEL", "ATO_FUTURE_IDEA"],
}

# Helper dataclasses ---------------------------------------------------------

@dataclass
class LegacyMarker:
    positive: List[str]
    negative: List[str]
    composed: List[str]


LEGACY_CACHE: Dict[str, LegacyMarker] = {}


def load_legacy_marker(marker_id: str) -> LegacyMarker:
    if marker_id in LEGACY_CACHE:
        return LEGACY_CACHE[marker_id]
    path = f"Markers_canonical.json/{marker_id}.yaml"
    positive: List[str] = []
    negative: List[str] = []
    composed: List[str] = []
    if CANONICAL_ARCHIVE.exists():
        with zipfile.ZipFile(CANONICAL_ARCHIVE) as zf:
            try:
                with zf.open(path) as handle:
                    raw = yaml.safe_load(handle)
            except KeyError:
                raw = None
    else:
        raw = None
    if raw:
        positive = extract_examples(raw, positive=True)
        negative = extract_examples(raw, positive=False)
        composed = extract_composed_refs(raw)
    LEGACY_CACHE[marker_id] = LegacyMarker(positive=positive, negative=negative, composed=composed)
    return LEGACY_CACHE[marker_id]


def extract_examples(node: dict, *, positive: bool) -> List[str]:
    if not isinstance(node, dict):
        return []
    examples = node.get("examples")
    target: List[str] = []
    if isinstance(examples, list):
        # already a list of strings
        target.extend([str(x) for x in examples if isinstance(x, str)])
    elif isinstance(examples, dict):
        keys = ["positive", "positive_de"] if positive else ["negative", "negative_de"]
        for key in keys:
            val = examples.get(key)
            if isinstance(val, list):
                target.extend([str(x) for x in val if isinstance(x, str)])
    else:
        key = "positive" if positive else "negative"
        sub = node.get(key)
        if isinstance(sub, list):
            target.extend([str(x) for x in sub if isinstance(x, str)])
    return target


def extract_composed_refs(node: dict) -> List[str]:
    refs: List[str] = []
    if not isinstance(node, dict):
        return refs
    if "composed_of" in node and isinstance(node["composed_of"], list):
        refs.extend([str(x) for x in node["composed_of"] if isinstance(x, str)])
    combination = node.get("combination")
    if isinstance(combination, dict):
        components = combination.get("components", [])
        for comp in components:
            if isinstance(comp, dict):
                marker_id = comp.get("marker_id") or comp.get("id")
                if marker_id:
                    refs.append(str(marker_id))
    return refs

# Utility helpers ------------------------------------------------------------

ABBREVIATION_OVERRIDES = {
    "LL": "Love Language",
    "SVT": "Schulz von Thun",
}


def humanize(identifier: str) -> str:
    parts = identifier.split("_")[1:]  # drop prefix
    words = []
    for part in parts:
        if part in ABBREVIATION_OVERRIDES:
            words.extend(ABBREVIATION_OVERRIDES[part].split())
        else:
            words.append(part.lower().capitalize())
    if not words:
        return identifier.title()
    return " ".join(words)


def keywords(identifier: str) -> List[str]:
    words: List[str] = []
    for part in identifier.split("_")[1:]:
        if part in ABBREVIATION_OVERRIDES:
            words.extend([w.lower() for w in ABBREVIATION_OVERRIDES[part].split()])
        else:
            words.append(part.lower())
    return [w for w in words if w and len(w) > 2]


POS_TEMPLATES = [
    "Hier zeigt sich {concept_lower}: {sample}.",
    "Deutlicher Hinweis auf {concept_lower}: {sample}.",
    "Der Satz »{sample}« illustriert {concept_lower} klar.",
    "{sample} – das ist typisch {concept_lower}.",
    "In dieser Formulierung ({sample}) steckt deutlich {concept_lower}.",
    "Das Beispiel {sample} liefert ein sauberes Signal für {concept_lower}.",
    "Wer {sample} sagt, markiert {concept_lower} direkt.",
    "\"{sample_cap}\" setzt {concept_lower} sprachlich um.",
    "Kontext: {sample}. Damit ist {concept_lower} aktiviert.",
    "{concept_cap} in Aktion: {sample}.",
]

NEG_TEMPLATES = [
    "Hier fehlt {concept_lower} völlig; es ist nur eine neutrale Feststellung.",
    "Der Satz vermeidet {concept_lower} und bleibt sachlich.",
    "Keine Spur von {concept_lower}: {sample} beschreibt lediglich Fakten.",
    "Diese Formulierung ({sample}) enthält kein {concept_lower}.",
    "Statt {concept_lower} geht es hier um etwas anderes.",
    "Die Aussage {sample} signalisiert bewusst kein {concept_lower}.",
    "Neutraler Tonfall – {concept_lower} taucht nicht auf.",
    "{sample} lenkt vom Thema ab, {concept_lower} entsteht nicht.",
    "Selbst in der Erweiterung bleibt {sample} frei von {concept_lower}.",
    "Der Abschnitt verzichtet bewusst auf {concept_lower}.",
]

SEM_POS_TEMPLATES = [
    "{sem_concept} entsteht, wenn {ato1_desc} auf {ato2_desc} trifft – genau wie in diesem Dialog.",
    "Der Turn kombiniert {ato1_desc} und {ato2_desc}, wodurch {sem_concept} aktiviert wird.",
    "Sobald {ato1_desc} gemeinsam mit {ato2_desc} fällt, spricht man von {sem_concept}.",
    "Beispiel für {sem_concept}: {ato1_desc} plus {ato2_desc} im selben Fenster.",
    "{sem_concept} leuchtet auf, weil sowohl {ato1_desc} als auch {ato2_desc} vorkommt.",
    "In dieser Passage laufen {ato1_desc} und {ato2_desc} zusammen – klassisches {sem_concept}.",
    "Die Kombination aus {ato1_desc} und {ato2_desc} kippt direkt in {sem_concept}.",
    "{ato1_desc} verstärkt {ato2_desc}; so wirkt {sem_concept} im Gespräch.",
    "{sem_concept} wird deutlich, wenn {ato1_desc} und {ato2_desc} nacheinander auftreten.",
    "Sequenzlich {ato1_desc}, danach {ato2_desc}: das markiert {sem_concept}.",
]

SEM_NEG_TEMPLATES = [
    "Hier fehlt {sem_concept}: weder {ato1_desc} noch {ato2_desc} taucht gemeinsam auf.",
    "Ohne {ato1_desc} plus {ato2_desc} entsteht kein {sem_concept}.",
    "Die Passage lässt {sem_concept} aus, weil nur einzelne Signale auftreten.",
    "Es bleibt neutral – {sem_concept} braucht {ato1_desc} und {ato2_desc}.",
    "Kein {sem_concept} hier: {ato1_desc} fehlt komplett.",
    "Der Dialog enthält zwar etwas Kontext, aber kein echtes {sem_concept}.",
    "Sobald {ato2_desc} fehlt, bleibt {sem_concept} aus – so auch hier.",
    "Diese Aussage löst kein {sem_concept} aus, weil die nötigen ATOs fehlen.",
    "Statt {sem_concept} passiert nur Lapidares; kein {ato1_desc} erkennbar.",
    "Die Struktur bricht ab – {sem_concept} setzt beide ATOs voraus.",
]


def select_sample_words(legacy_positive: Sequence[str], fallback: Sequence[str]) -> List[str]:
    samples: List[str] = []
    for item in legacy_positive:
        if not isinstance(item, str):
            continue
        text = item.strip()
        if not text:
            continue
        tokens = text.lower().split()
        if len(tokens) >= 2:
            samples.append(" ".join(tokens[:2]))
        else:
            samples.append(text.lower())
    if samples:
        return samples
    return list(fallback)


def build_pattern(words: Sequence[str], legacy_positive: Sequence[str]) -> List[str]:
    cleaned = [w for w in words if w]
    phrases = []
    for sample in legacy_positive:
        if not isinstance(sample, str):
            continue
        text = sample.strip().lower()
        if not text:
            continue
        phrases.append(text)
    cleaned.extend(phrases[:4])
    if not cleaned:
        return ["(?i).*"]
    return [f"(?i){re.escape(w)}" for w in cleaned]


def ensure_examples(source: List[str], generator, count: int, *, exclude: Optional[Sequence[str]] = None) -> List[str]:
    seen = set()
    items: List[str] = []
    excluded = {s.strip() for s in exclude or [] if isinstance(s, str)}
    for s in source:
        if not isinstance(s, str):
            continue
        cleaned = s.strip()
        if not cleaned or cleaned in seen or cleaned in excluded:
            continue
        items.append(cleaned)
        seen.add(cleaned)
    idx = 0
    while len(items) < count:
        candidate = generator(idx).strip()
        if candidate and candidate not in seen and candidate not in excluded:
            items.append(candidate)
            seen.add(candidate)
        idx += 1
    return items[:count]


def positive_generator(concept: str, sample_words: List[str]):
    concept_lower = concept.lower()
    concept_cap = concept_lower.capitalize()
    samples = sample_words or [concept_lower]
    def make(idx: int) -> str:
        tmpl = POS_TEMPLATES[idx % len(POS_TEMPLATES)]
        sample = samples[idx % len(samples)]
        sample_cap = sample.capitalize()
        return tmpl.format(concept_lower=concept_lower, concept_cap=concept_cap, sample=sample, sample_cap=sample_cap)
    return make


def negative_generator(concept: str, sample_words: List[str]):
    concept_lower = concept.lower()
    samples = sample_words or ["die Aussage"]
    def make(idx: int) -> str:
        tmpl = NEG_TEMPLATES[idx % len(NEG_TEMPLATES)]
        sample = samples[idx % len(samples)]
        return tmpl.format(concept_lower=concept_lower, sample=sample)
    return make


def sem_positive_generator(concept: str, ato_desc: Sequence[str]):
    ato1_desc, ato2_desc = ato_desc
    def make(idx: int) -> str:
        tmpl = SEM_POS_TEMPLATES[idx % len(SEM_POS_TEMPLATES)]
        return tmpl.format(sem_concept=concept, ato1_desc=ato1_desc, ato2_desc=ato2_desc)
    return make


def sem_negative_generator(concept: str, ato_desc: Sequence[str]):
    ato1_desc, ato2_desc = ato_desc
    def make(idx: int) -> str:
        tmpl = SEM_NEG_TEMPLATES[idx % len(SEM_NEG_TEMPLATES)]
        return tmpl.format(sem_concept=concept, ato1_desc=ato1_desc, ato2_desc=ato2_desc)
    return make


def describe_ato(ato_id: str) -> str:
    return humanize(ato_id).lower()


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False, allow_unicode=True)


def build_ato(id_: str) -> dict:
    legacy = load_legacy_marker(id_)
    concept = humanize(id_)
    words = keywords(id_) or [concept.lower()]
    sample_words = select_sample_words(legacy.positive, words)
    pos = ensure_examples(legacy.positive, positive_generator(concept, sample_words), 10)
    neg = ensure_examples(legacy.negative, negative_generator(concept, sample_words), 10, exclude=pos)
    pattern_values = build_pattern(sample_words, legacy.positive)
    metadata = {
        "neg_examples": neg,
        "tags": ["semantic", concept.lower().replace(" ", "-")],
        "maintainer": "ld35-auto",
    }
    family = deduce_family(id_)
    if family:
        metadata["family"] = family

    return {
        "schema": "LeanDeep",
        "version": "3.5",
        "id": id_,
        "lang": "de",
        "frame": {
            "signal": [concept.lower()],
            "concept": concept,
            "pragmatics": "surface cue",
            "narrative": "definition",
        },
        "pattern": {
            "any_of": pattern_values,
        },
        "activation": {"rule": "ANY 1"},
        "examples": pos,
        "metadata": {
            "neg_examples": neg,
            "tags": ["atomic", concept.lower().replace(" ", "-")],
            "maintainer": "ld35-auto",
        },
    }


def build_sem(id_: str, new: bool) -> dict:
    atos = SEM_COMPONENTS[id_]
    concept = humanize(id_)
    legacy = load_legacy_marker(id_)
    pos = ensure_examples(legacy.positive, sem_positive_generator(concept, [describe_ato(a) for a in atos[:2]]), 10)
    neg = ensure_examples(legacy.negative, sem_negative_generator(concept, [describe_ato(a) for a in atos[:2]]), 10, exclude=pos)
    metadata = {
        "neg_examples": neg,
        "tags": ["semantic", concept.lower().replace(" ", "-")],
        "maintainer": "ld35-auto",
    }
    family = deduce_family(id_)
    if family:
        metadata["family"] = family
    return {
        "schema": "LeanDeep",
        "version": "3.5",
        "id": id_,
        "lang": "de",
        "frame": {
            "signal": [concept.lower()],
            "concept": concept,
            "pragmatics": "semantic blend",
            "narrative": "working hypothesis",
        },
        "composed_of": atos,
        "activation": {"rule": "AT_LEAST 2 DISTINCT ATOs IN 3 messages"},
        "scoring": {"base": 0.6, "weight": 1.1},
        "examples": pos,
        "metadata": metadata,
    }


def deduce_family(sem_id: str) -> Optional[str]:
    if "GUILT" in sem_id:
        return "SUPPORT"
    if "SHUTDOWN" in sem_id or "APATHY" in sem_id:
        return "SHUTDOWN"
    if "BOUNDARY" in sem_id or "RIVALRY" in sem_id:
        return "CONFLICT"
    if "COMMIT" in sem_id or "GOAL" in sem_id or "TRADEOFF" in sem_id:
        return "EFFICACY"
    if "CHILD" in sem_id:
        return "FAMILY"
    if "ENERGY" in sem_id or "STRESS" in sem_id:
        return "SUPPORT"
    if "AI_BOT_SCAM" in sem_id:
        return "INCONSISTENCY"
    return None


def main() -> None:
    print(GENERATOR_DISABLED_MESSAGE)
    return

    # Legacy implementation retained below for reference; kept behind immediate return.
    for ato_id in TARGET_ATOS:
        data = build_ato(ato_id)
        write_yaml(CANONICAL_DIR / f"{ato_id}.yaml", data)

    for sem_id in SEM_NORMALIZE:
        data = build_sem(sem_id, new=False)
        write_yaml(CANONICAL_DIR / f"{sem_id}.yaml", data)

    for sem_id in SEM_CREATE:
        data = build_sem(sem_id, new=True)
        write_yaml(CANONICAL_DIR / f"{sem_id}.yaml", data)

    print("Generated/updated markers for iteration 3 content.")


if __name__ == "__main__":
    main()
