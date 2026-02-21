"""
LeanDeep 5.0 Marker Detection Engine.

Implements the four-layer hierarchy (ATO → SEM → CLU → MEMA) with:
- ATO: Regex pattern matching against input text
- SEM: Compositional activation (1 ATO + context OR ≥2 ATOs)
      + DRA guards: negation, reported speech, intensity modifiers
- CLU: Windowed aggregation over SEMs with family multipliers
- MEMA: Meta-level diagnosis via composed_of / detect_class

DRA Mode (Emotions-ATO-Regex-Lexikon):
  ATO_EMO_LEX_* = Evidence (broad, recall-strong)
  ATO_NEGATION_TOKEN = Context filter (SEM/CLU can downweight/block)
  ATO_REPORTED_SPEECH_VERB / ATO_QUOTE_MARK / ATO_HEARSAY_CUE = Attribution guard
  ATO_EMO_INTENSIFIER_HIGH/LOW = Modifiers (boost/dampen, never trigger alone)
"""

from __future__ import annotations

import json
import math
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from .config import settings


def _parse_activation_rule(rule_str: str) -> tuple[str, int]:
    """Parse activation rule string into (mode, min_hits).

    Returns:
        mode: 'ALL' | 'AT_LEAST' | 'ANY'
        min_hits: minimum number of composed_of refs that must be active

    Examples:
        'BOTH IN 1 message'      → ('ALL', -1)  # -1 means ALL required
        'ANY 2 IN 3 messages'    → ('ANY', 2)
        'AT_LEAST 2 IN 3 messages' → ('AT_LEAST', 2)
        'ANY 1'                  → ('ANY', 1)
        'WEIGHTED_AND'           → ('ALL', -1)
        'SEQUENCE IN 4 messages' → ('ALL', -1)
    """
    rule = rule_str.strip().upper().replace("_", " ")

    # ALL / BOTH / WEIGHTED_AND / SEQUENCE → require all refs
    if any(k in rule for k in ("ALL", "BOTH", "WEIGHTED AND", "SEQUENCE")):
        return ("ALL", -1)

    # AT LEAST X ... → extract X
    m = re.search(r"AT\s*LEAST\s+(\d+)", rule)
    if m:
        return ("AT_LEAST", int(m.group(1)))

    # ANY X ... → extract X
    m = re.search(r"ANY\s+(\d+)", rule)
    if m:
        return ("ANY", int(m.group(1)))

    # ANY (without number) → 1
    if "ANY" in rule:
        return ("ANY", 1)

    # WEIGHTED_OR → at least 1
    if "WEIGHTED" in rule:
        return ("ANY", 1)

    # Fallback: require 1
    return ("ANY", 1)


@dataclass
class CompiledPattern:
    """Pre-compiled regex pattern for fast matching."""
    raw: str
    compiled: re.Pattern | None
    flags_str: list[str] = field(default_factory=list)


@dataclass
class MarkerDef:
    """In-memory marker definition with compiled patterns."""
    id: str
    layer: str
    lang: str
    description: str
    frame: dict
    patterns: list[CompiledPattern]
    examples: dict
    tags: list[str]
    rating: int
    composed_of: list | dict | None = None
    activation: dict | None = None
    scoring: dict | None = None
    window: dict | None = None
    family: str | None = None
    multiplier: float = 1.0
    detect_class: str | None = None
    compositionality: str | None = None  # deterministic | contextual | emergent
    vad_estimate: dict | None = None        # {valence, arousal, dominance}
    effect_on_state: dict | None = None     # {trust, conflict, deesc}


@dataclass
class Match:
    """A pattern match result."""
    marker_id: str
    pattern: str
    start: int
    end: int
    matched_text: str
    confidence: float = 1.0


@dataclass
class Detection:
    """A detected marker with all match evidence."""
    marker_id: str
    layer: str
    confidence: float
    description: str
    matches: list[Match]
    family: str | None = None
    multiplier: float | None = None
    message_indices: list[int] = field(default_factory=list)
    vad: dict | None = None                 # copied from MarkerDef.vad_estimate


class MarkerEngine:
    """Core detection engine that loads markers and runs analysis."""

    def __init__(self):
        self.markers: dict[str, MarkerDef] = {}
        self.ato_markers: list[MarkerDef] = []
        self.sem_markers: list[MarkerDef] = []
        self.clu_markers: list[MarkerDef] = []
        self.mema_markers: list[MarkerDef] = []
        self.engine_config: dict = {}
        self._loaded = False

    def load(self, registry_path: str | None = None):
        """Load and compile all markers from the registry."""
        path = Path(registry_path or settings.registry_path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.engine_config = data.get("ld5_engine", {})

        for marker_id, mdata in data.get("markers", {}).items():
            mdef = self._parse_marker(marker_id, mdata)
            self.markers[marker_id] = mdef

            if mdef.layer == "ATO":
                self.ato_markers.append(mdef)
            elif mdef.layer == "SEM":
                self.sem_markers.append(mdef)
            elif mdef.layer == "CLU":
                self.clu_markers.append(mdef)
            elif mdef.layer == "MEMA":
                self.mema_markers.append(mdef)

        # Build fuzzy reference index for CLU/MEMA composition matching.
        # Maps keyword fragments to marker IDs so "SEM_ANGER_ESCALATION"
        # resolves to "SEM_ANGER" or any SEM containing those keywords.
        self._ref_index: dict[str, set[str]] = {}
        for mid in self.markers:
            # Index each meaningful segment: SEM_ANGER_ESCALATION → {"ANGER", "ESCALATION"}
            parts = mid.split("_")[1:]  # Drop layer prefix
            for part in parts:
                self._ref_index.setdefault(part.upper(), set()).add(mid)

        self._loaded = True

    def _resolve_ref(self, ref: str, active_ids: set[str]) -> bool:
        """Check if a composed_of reference is satisfied by active markers.

        Tries exact match first, then keyword-based fuzzy matching.
        """
        if ref in active_ids:
            return True

        # Fuzzy: extract keywords from ref and check if any active marker
        # contains all those keywords
        parts = ref.split("_")[1:]  # Drop layer prefix
        if not parts:
            return False

        for active_id in active_ids:
            active_upper = active_id.upper()
            if all(p.upper() in active_upper for p in parts):
                return True

        return False

    # -----------------------------------------------------------------------
    # DRA Guard IDs and emotion marker prefixes
    # -----------------------------------------------------------------------
    _NEGATION_ID = "ATO_NEGATION_TOKEN"
    _REPORTED_SPEECH_IDS = {"ATO_REPORTED_SPEECH_VERB", "ATO_QUOTE_MARK", "ATO_HEARSAY_CUE"}
    _INTENSITY_HIGH_ID = "ATO_EMO_INTENSIFIER_HIGH"
    _INTENSITY_LOW_ID = "ATO_EMO_INTENSIFIER_LOW"
    _PUNCT_INTENSITY_ID = "ATO_EMO_PUNCT_INTENSITY"
    _EMO_LEX_PREFIX = "ATO_EMO_LEX_"

    def _is_emotion_ato(self, marker_id: str) -> bool:
        """Check if an ATO is an emotion lexicon marker."""
        return marker_id.startswith(self._EMO_LEX_PREFIX)

    def _apply_dra_guards(
        self, text: str, ato_detections: list[Detection]
    ) -> dict[str, float]:
        """
        Compute DRA guard modifiers for SEM emotion confidence.

        Returns a dict of modifier signals:
          'negation': -0.3 if negation token present near emotion
          'reported_speech': -0.2 if reported speech cue without self-report
          'intensity_high': +0.15 if high intensifier present
          'intensity_low': -0.1 if low intensifier present
          'punct_intensity': +0.1 if punctuation intensity present
        """
        active_ids = {d.marker_id for d in ato_detections}
        modifiers: dict[str, float] = {}

        # Negation guard: if ATO_NEGATION_TOKEN active → downweight emotion SEMs
        if self._NEGATION_ID in active_ids:
            modifiers["negation"] = -0.3

        # Reported speech guard: if speech verbs / quotes active without "ich" self-report
        if active_ids & self._REPORTED_SPEECH_IDS:
            # Check if first-person self-report is present (ich fühle, ich bin, mir)
            has_self_report = bool(re.search(
                r"(?i)\b(ich\s+(bin|fühle|fuehle|habe|hab|war|werde|merke|spüre|spuere))\b", text
            ))
            if not has_self_report:
                modifiers["reported_speech"] = -0.2

        # Intensity modifiers
        if self._INTENSITY_HIGH_ID in active_ids:
            modifiers["intensity_high"] = 0.15
        if self._INTENSITY_LOW_ID in active_ids:
            modifiers["intensity_low"] = -0.1
        if self._PUNCT_INTENSITY_ID in active_ids:
            modifiers["punct_intensity"] = 0.1

        return modifiers

    # -----------------------------------------------------------------------
    # VAD Congruence Gate (Quantum Collapse)
    # -----------------------------------------------------------------------

    def _vad_congruence(self, ato_vad: dict | None, msg_vad: dict | None) -> float:
        """Compute congruence between an ATO's VAD and the message's VAD.

        Returns 0.0 (completely incongruent) to 1.0 (perfectly aligned).
        Uses weighted euclidean distance with valence weighted 1.5x,
        dominance weighted 0.5x.
        """
        if not ato_vad or not msg_vad:
            return 0.5  # No VAD -> neutral, don't gate

        # Weighted distance: valence matters most, then arousal, then dominance
        dv = (ato_vad["valence"] - msg_vad["valence"]) * 1.5  # valence weighted
        da = ato_vad["arousal"] - msg_vad["arousal"]
        dd = (ato_vad["dominance"] - msg_vad["dominance"]) * 0.5  # dominance least important

        distance = math.sqrt(dv**2 + da**2 + dd**2)
        # Max possible distance: sqrt((3)^2 + (1)^2 + (0.5)^2) ~ 3.2
        max_dist = 3.2
        congruence = max(0.0, 1.0 - distance / max_dist)
        return round(congruence, 3)

    def _compute_raw_vad(self, detections: list[Detection]) -> dict:
        """Compute aggregate VAD from a list of detections."""
        vads = [d.vad for d in detections if d.vad]
        if not vads:
            return {"valence": 0.0, "arousal": 0.0, "dominance": 0.0}
        return {
            "valence": sum(v["valence"] for v in vads) / len(vads),
            "arousal": sum(v["arousal"] for v in vads) / len(vads),
            "dominance": sum(v["dominance"] for v in vads) / len(vads),
        }

    def _apply_vad_gate(
        self,
        ato_detections: list[Detection],
        msg_vad: dict,
        shadow_buffer: list[Detection] | None = None,
    ) -> tuple[list[Detection], list[Detection], list[Detection]]:
        """Apply VAD congruence gate to ATO detections.

        Returns:
            (gated_atos, suppressed_atos, surfaced_from_shadow)

        Gate thresholds:
            congruence >= 0.55 -> pass with full confidence (resonant)
            0.35 <= congruence < 0.55 -> pass with confidence *= 0.6 (weak resonance)
            congruence < 0.35 -> suppressed (noise), goes to shadow buffer

        ATOs without VAD always pass (structural markers like NEGATION).
        If message VAD is near-zero (neutral message), gate is relaxed.
        """
        # If message is emotionally neutral, don't gate aggressively
        msg_intensity = abs(msg_vad["valence"]) + msg_vad["arousal"]
        if msg_intensity < 0.15:
            # Neutral message: everything passes
            return ato_detections, [], []

        gated: list[Detection] = []
        suppressed: list[Detection] = []

        for det in ato_detections:
            if det.vad is None:
                # No VAD -> structural marker, always passes
                gated.append(det)
                continue

            congruence = self._vad_congruence(det.vad, msg_vad)

            if congruence >= 0.55:
                # Resonant: full pass
                gated.append(det)
            elif congruence >= 0.35:
                # Weak resonance: reduced confidence
                det.confidence = round(det.confidence * 0.6, 3)
                gated.append(det)
            else:
                # Noise: suppress
                suppressed.append(det)

        # Check shadow buffer: surface any that are now congruent
        surfaced: list[Detection] = []
        if shadow_buffer:
            for shadow_det in shadow_buffer:
                if shadow_det.vad is None:
                    continue
                congruence = self._vad_congruence(shadow_det.vad, msg_vad)
                if congruence >= 0.45:
                    # Surfaced from shadow with reduced confidence
                    shadow_det.confidence = round(shadow_det.confidence * 0.4, 3)
                    surfaced.append(shadow_det)

        return gated, suppressed, surfaced

    def _parse_marker(self, marker_id: str, data: dict) -> MarkerDef:
        """Parse a marker from registry data, compiling regex patterns."""
        patterns = []
        for p in data.get("patterns", []):
            ptype = p.get("type", "regex") if isinstance(p, dict) else "regex"
            if ptype not in ("regex", "keyword"):
                continue  # Skip emoji, audio, etc.
            raw = str(p.get("value", "")) if isinstance(p, dict) else str(p)
            flags = p.get("flags", []) if isinstance(p, dict) else []
            compiled = self._compile_pattern(raw, flags)
            patterns.append(CompiledPattern(raw=raw, compiled=compiled, flags_str=flags))

        return MarkerDef(
            id=marker_id,
            layer=data.get("layer", "UNKNOWN"),
            lang=data.get("lang", "de"),
            description=data.get("description", ""),
            frame=data.get("frame", {}),
            patterns=patterns,
            examples=data.get("examples", {}),
            tags=data.get("tags", []),
            rating=data.get("rating", 2),
            composed_of=data.get("composed_of"),
            activation=data.get("activation"),
            scoring=data.get("scoring"),
            window=data.get("window"),
            family=data.get("ld5_family"),
            multiplier=data.get("ld5_multiplier", 1.0),
            detect_class=data.get("detect_class"),
            compositionality=data.get("compositionality"),
            vad_estimate=data.get("vad_estimate"),
            effect_on_state=data.get("effect_on_state"),
        )

    def _compile_pattern(self, raw: str, flags: list[str]) -> re.Pattern | None:
        """Compile a regex pattern, returning None if invalid."""
        if not raw or not isinstance(raw, str):
            return None
        try:
            re_flags = re.IGNORECASE  # Default: case-insensitive
            if "MULTILINE" in flags:
                re_flags |= re.MULTILINE
            if "DOTALL" in flags:
                re_flags |= re.DOTALL
            return re.compile(raw, re_flags)
        except (re.error, TypeError):
            return None

    # -----------------------------------------------------------------------
    # Text Preprocessing
    # -----------------------------------------------------------------------

    _URL_RE = re.compile(
        r'https?://[^\s<>\"\')]+|www\.[^\s<>\"\')]+', re.IGNORECASE
    )

    @classmethod
    def _strip_urls(cls, text: str) -> str:
        """Replace URLs with whitespace to prevent false pattern matches."""
        return cls._URL_RE.sub(lambda m: ' ' * len(m.group()), text)

    # -----------------------------------------------------------------------
    # ATO Detection (Level 1): Pure regex matching
    # -----------------------------------------------------------------------

    def detect_ato(
        self, text: str, threshold: float = 0.5, *, include_context_only: bool = True
    ) -> list[Detection]:
        """Detect atomic markers via regex pattern matching.

        Args:
            include_context_only: If False, markers tagged 'context_only' are
                suppressed from the returned list (but should still be passed
                to SEM via a separate call with include_context_only=True).
        """
        # Strip URLs before matching to avoid FPs on link characters
        text = self._strip_urls(text)
        detections = []

        for mdef in self.ato_markers:
            matches = []
            for pat in mdef.patterns:
                if pat.compiled is None:
                    continue
                for m in pat.compiled.finditer(text):
                    matched = m.group()
                    # Skip noise: matches shorter than 3 chars or pure whitespace
                    if len(matched.strip()) < 3:
                        continue
                    matches.append(Match(
                        marker_id=mdef.id,
                        pattern=pat.raw,
                        start=m.start(),
                        end=m.end(),
                        matched_text=matched,
                    ))

            if matches:
                # Confidence: any match = baseline 0.6, more matches boost it.
                # distinct_patterns_matched / total_patterns adds 0-0.4 range.
                distinct_matched = len({m.pattern for m in matches})
                total_pats = max(len([p for p in mdef.patterns if p.compiled]), 1)
                pattern_coverage = distinct_matched / total_pats
                confidence = min(1.0, 0.6 + pattern_coverage * 0.4)

                if confidence >= threshold:
                    # Skip context_only markers from standalone output —
                    # they are noise on their own but valuable as SEM inputs
                    if not include_context_only and "context_only" in mdef.tags:
                        continue
                    det = Detection(
                        marker_id=mdef.id,
                        layer="ATO",
                        confidence=round(confidence, 3),
                        description=mdef.description,
                        matches=matches,
                    )
                    det.vad = mdef.vad_estimate
                    detections.append(det)

        return detections

    # -----------------------------------------------------------------------
    # SEM Activation (Level 2): Compositional + contextual reference
    # -----------------------------------------------------------------------

    def detect_sem(
        self, text: str, ato_detections: list[Detection], threshold: float = 0.5
    ) -> list[Detection]:
        """
        Detect semantic markers via composition rules + DRA guards.

        LD 5.0 paradigm: SEM = ATO + context.
        A SEM activates when:
          Path A: Composed ATOs are present (≥1 with context, or ≥2 without)
          Path B: Single ATO references active system context
          Path C: Accumulation of same ATO type
          Path D: Spontaneous emergence via detect_class (omission)

        DRA Guards applied to emotion SEMs:
          - Negation token nearby → confidence -0.3
          - Reported speech without self-report → confidence -0.2
          - High intensifier → confidence +0.15
          - Low intensifier → confidence -0.1
        """
        # Strip URLs before SEM's own pattern matching
        text = self._strip_urls(text)
        active_atos = {d.marker_id for d in ato_detections}

        # Pre-compute DRA guard modifiers for this text
        dra_modifiers = self._apply_dra_guards(text, ato_detections)

        # Check if any emotion ATOs fired (for guard application)
        has_emotion_atos = any(self._is_emotion_ato(a) for a in active_atos)

        detections = []

        for mdef in self.sem_markers:
            confidence = 0.0
            contributing_matches = []
            rule_blocked = False  # True when activation rule explicitly rejects

            # Check composition: both string refs and dict-format refs
            composed = mdef.composed_of
            if isinstance(composed, list) and composed:
                hits = []
                for c in composed:
                    if isinstance(c, str):
                        if c in active_atos:
                            hits.append(c)
                    elif isinstance(c, dict):
                        for mid in c.get("marker_ids", []):
                            if str(mid) in active_atos:
                                hits.append(str(mid))
                hit_ratio = len(hits) / max(len(composed), 1)

                # LD 5.0: generic activation rule parser
                activation = mdef.activation or {}
                if isinstance(activation, str):
                    rule_raw = activation
                elif isinstance(activation, dict) and "rule" in activation:
                    rule_raw = activation["rule"]
                else:
                    # No activation rule → require ALL composed_of refs (safe default)
                    rule_raw = "ALL"
                mode, min_hits = _parse_activation_rule(str(rule_raw))

                # ALL mode: every composed_of ref must be active
                if mode == "ALL":
                    min_hits = len(composed)

                if len(hits) >= min_hits:
                    # Scale confidence: 1 hit = 0.6 base, full coverage = 1.0
                    if min_hits >= 2 or mode == "ALL":
                        confidence = 0.7 + (hit_ratio * 0.3)
                    else:
                        confidence = 0.6 + (hit_ratio * 0.4)

                    # Compositionality modulation:
                    # deterministic = ATOs carry their own vector (full confidence)
                    # contextual    = ATOs need relational context (discounted)
                    # emergent      = meaning only through full constellation (strong discount)
                    comp = mdef.compositionality
                    if comp == "contextual":
                        confidence *= 0.70
                    elif comp == "emergent":
                        confidence *= 0.50
                    # deterministic / None = no discount
                else:
                    confidence = 0.0
                    rule_blocked = True

                # Collect matches from contributing ATOs
                for ato_det in ato_detections:
                    if ato_det.marker_id in hits:
                        contributing_matches.extend(ato_det.matches)

            # Also check SEM's own patterns (direct regex — independent of composition)
            own_pattern_matches: list[Match] = []
            for pat in mdef.patterns:
                if pat.compiled is None:
                    continue
                for m in pat.compiled.finditer(text):
                    matched = m.group()
                    if len(matched.strip()) < 3:
                        continue
                    own_pattern_matches.append(Match(
                        marker_id=mdef.id,
                        pattern=pat.raw,
                        start=m.start(),
                        end=m.end(),
                        matched_text=matched,
                    ))
            contributing_matches.extend(own_pattern_matches)

            # Direct pattern match can activate SEM even if composition rule_blocked
            if own_pattern_matches and confidence == 0.0:
                base = (mdef.scoring or {}).get("base", 1.0)
                confidence = min(1.0, 0.5 + len(own_pattern_matches) * 0.1 * base)
            elif contributing_matches and confidence == 0.0 and not rule_blocked:
                base = (mdef.scoring or {}).get("base", 1.0)
                confidence = min(1.0, 0.5 + len(contributing_matches) * 0.1 * base)

            # ─── DRA Guard Application ───
            # Apply guards to SEMs that involve emotion ATOs
            if confidence > 0 and has_emotion_atos:
                is_emotion_sem = any(
                    tag in mdef.tags
                    for tag in ("emotion", "shame", "anger", "sadness", "fear",
                                "joy", "disgust", "love", "envy", "pride", "hope",
                                "loneliness", "grief", "intuition")
                )
                # Also treat SEMs composed of emotion ATOs as emotion SEMs
                if not is_emotion_sem and isinstance(composed, list):
                    is_emotion_sem = any(
                        isinstance(c, str) and self._is_emotion_ato(c)
                        for c in composed
                    )

                if is_emotion_sem and dra_modifiers:
                    mod_sum = sum(dra_modifiers.values())
                    confidence = max(0.0, min(1.0, confidence + mod_sum))

            if confidence >= threshold and contributing_matches:
                det = Detection(
                    marker_id=mdef.id,
                    layer="SEM",
                    confidence=round(confidence, 3),
                    description=mdef.description,
                    matches=contributing_matches,
                )
                det.vad = mdef.vad_estimate
                detections.append(det)

        return detections

    # -----------------------------------------------------------------------
    # CLU Aggregation (Level 3): Windowed pattern over SEMs
    # -----------------------------------------------------------------------

    def detect_clu(
        self,
        sem_detections_per_message: list[list[Detection]],
        threshold: float = 0.5,
    ) -> list[Detection]:
        """
        Detect cluster markers over a conversation window.

        CLU requires multiple SEMs across messages. Uses family multipliers
        and the hypothesis lifecycle (provisional → confirmed → decayed).
        """
        # Flatten all active SEMs with their message indices
        all_sems: dict[str, list[int]] = {}
        for msg_idx, dets in enumerate(sem_detections_per_message):
            for d in dets:
                all_sems.setdefault(d.marker_id, []).append(msg_idx)

        active_sem_ids = set(all_sems.keys())
        detections = []

        for mdef in self.clu_markers:
            hits = []
            msg_indices = set()

            composed = mdef.composed_of
            if isinstance(composed, list) and composed:
                for c in composed:
                    if not isinstance(c, str):
                        continue
                    if self._resolve_ref(c, active_sem_ids):
                        hits.append(c)
                        # Find which active SEM matched this ref
                        for sid in active_sem_ids:
                            if c == sid or all(p.upper() in sid.upper() for p in c.split("_")[1:]):
                                msg_indices.update(all_sems.get(sid, []))
            elif isinstance(composed, dict):
                require = composed.get("require", composed.get("sem_pool", []))
                if isinstance(require, list):
                    for c in require:
                        if not isinstance(c, str):
                            continue
                        if self._resolve_ref(c, active_sem_ids):
                            hits.append(c)
                            for sid in active_sem_ids:
                                if c == sid or all(p.upper() in sid.upper() for p in c.split("_")[1:]):
                                    msg_indices.update(all_sems.get(sid, []))

            if not hits:
                continue

            # Check window constraint
            window_size = (mdef.window or {}).get("messages", 10)
            total_messages = len(sem_detections_per_message)
            window_start = max(0, total_messages - window_size)
            hits_in_window = [
                h for h in hits
                if any(idx >= window_start for idx in all_sems.get(h, []))
            ]

            if not hits_in_window:
                # Also check: did any of the resolved SEM matches appear in window?
                resolved_in_window = [
                    h for h in hits
                    if any(
                        any(idx >= window_start for idx in all_sems.get(sid, []))
                        for sid in active_sem_ids
                        if h == sid or all(p.upper() in sid.upper() for p in h.split("_")[1:])
                    )
                ]
                if not resolved_in_window:
                    continue
                hits_in_window = resolved_in_window

            distinct_hits = len(set(hits_in_window))

            # Calculate confidence: 1 hit = low, 2+ = higher
            composed_total = len(composed) if isinstance(composed, list) else len(
                composed.get("require", composed.get("sem_pool", []))
            )
            hit_ratio = distinct_hits / max(composed_total, 1)

            if distinct_hits >= 2:
                base_conf = 0.5 + (hit_ratio * 0.5)
            elif distinct_hits == 1:
                base_conf = 0.35 + (hit_ratio * 0.25)  # Lower confidence for single hit
            else:
                continue

            # Apply multiplier from LD5 family
            multiplier = mdef.multiplier
            confidence = min(1.0, base_conf * min(multiplier, 1.5))  # Cap effective boost

            if confidence >= threshold:
                detections.append(Detection(
                    marker_id=mdef.id,
                    layer="CLU",
                    confidence=round(confidence, 3),
                    description=mdef.description,
                    matches=[],
                    family=mdef.family,
                    multiplier=multiplier,
                    message_indices=sorted(msg_indices),
                ))

        return detections

    # -----------------------------------------------------------------------
    # MEMA Diagnosis (Level 4): Meta-level organism diagnosis
    # -----------------------------------------------------------------------

    def detect_mema(
        self,
        clu_detections: list[Detection],
        sem_detections: list[Detection],
        ato_detections: list[Detection] | None = None,
        threshold: float = 0.5,
    ) -> list[Detection]:
        """
        Detect meta markers from active CLUs/SEMs/ATOs.

        MEMA uses two paths:
          Option A (composed_of): Rule-based aggregation — fuzzy resolution
                   against all active CLUs + SEMs
          Option B (detect_class): Algorithmic inference from active marker
                   patterns (trend, absence, composite, cycle, etc.)
        """
        active_clus = {d.marker_id for d in clu_detections}
        active_sems = {d.marker_id for d in sem_detections}
        active_atos = {d.marker_id for d in (ato_detections or [])}
        all_active = active_clus | active_sems | active_atos

        # Collect CLU families for detect_class inference
        clu_families = set()
        for d in clu_detections:
            if d.family:
                clu_families.add(d.family.upper())

        detections = []

        for mdef in self.mema_markers:
            confidence = 0.0

            # Option A: composed_of check (with fuzzy resolution)
            composed = mdef.composed_of
            if isinstance(composed, list) and composed:
                hits = []
                for c in composed:
                    if isinstance(c, str):
                        if self._resolve_ref(c, all_active):
                            hits.append(c)
                    elif isinstance(c, dict):
                        # Dict format: {'marker_ids': ['CLU_X'], 'weight': 0.5}
                        for mid in c.get("marker_ids", []):
                            if self._resolve_ref(str(mid), all_active):
                                hits.append(str(mid))
                if hits:
                    hit_ratio = len(hits) / max(len(composed), 1)
                    confidence = 0.5 + (hit_ratio * 0.5)

            # Option B: detect_class inference
            if confidence < threshold and mdef.detect_class:
                dc = mdef.detect_class

                # Extract MEMA keywords for matching (exclude structural noise)
                _STRUCTURAL_KW = {"MARKER", "TEXT", "AUDIO", "PROSODY", "PATTERN",
                                  "ALERT", "TREND", "PROFILE", "META", "CLUSTER"}
                mema_keywords = set(
                    kw.upper() for kw in mdef.id.replace("MEMA_", "").split("_")
                    if len(kw) > 3 and kw.upper() not in _STRUCTURAL_KW
                )

                if not mema_keywords:
                    # Skip detect_class if no meaningful keywords
                    continue

                if dc == "absence_meta":
                    # Fire when conflict/negative signals active but expected
                    # positive/repair signals are absent
                    negative_families = {"CONFLICT", "GRIEF", "UNCERTAINTY"}
                    if clu_families & negative_families:
                        positive_families = {"SUPPORT", "COMMITMENT"}
                        if not (clu_families & positive_families):
                            confidence = max(confidence, 0.6)
                        else:
                            confidence = max(confidence, 0.5)

                elif dc == "trend_analysis":
                    # Check if active CLUs or SEMs match MEMA keywords
                    related = [
                        c for c in (active_clus | active_sems)
                        if any(kw in c.upper() for kw in mema_keywords)
                    ]
                    if related:
                        confidence = max(confidence, 0.5 + min(0.3, len(related) * 0.1))

                elif dc == "cycle_detection":
                    # Cycle needs escalation + recurring pattern
                    related = [
                        c for c in all_active
                        if any(kw in c.upper() for kw in mema_keywords)
                    ]
                    if len(related) >= 2:
                        confidence = max(confidence, 0.55)
                    elif related:
                        confidence = max(confidence, 0.45)

                elif dc == "pattern_detection":
                    # Pattern detection from active markers matching keywords
                    related = [
                        c for c in all_active
                        if any(kw in c.upper() for kw in mema_keywords)
                    ]
                    if related:
                        confidence = max(confidence, 0.5 + min(0.2, len(related) * 0.1))

                elif dc in ("composite_meta", "profile_composite", "archetype_composite"):
                    # Composite: keyword overlap with any active CLU/SEM
                    # CLU matches count more than SEM matches
                    related_clus = [
                        c for c in active_clus
                        if any(kw in c.upper() for kw in mema_keywords)
                    ]
                    related_sems = [
                        s for s in active_sems
                        if any(kw in s.upper() for kw in mema_keywords)
                    ]
                    # Weighted: CLU match = 1.0, SEM match = 0.5
                    weighted = len(related_clus) * 1.0 + len(related_sems) * 0.5
                    if weighted >= 1.5:
                        confidence = max(confidence, 0.5 + min(0.3, weighted * 0.1))
                    elif weighted >= 0.5:
                        confidence = max(confidence, 0.5)

                elif dc in ("E", "coherence_calculator", "echo_detector",
                            "evolution_pressure_analyzer", "node_crystallizer"):
                    # Specialized classes: use keyword matching as fallback
                    related = [
                        c for c in all_active
                        if any(kw in c.upper() for kw in mema_keywords)
                    ]
                    if related:
                        confidence = max(confidence, 0.5)

            if confidence >= threshold:
                detections.append(Detection(
                    marker_id=mdef.id,
                    layer="MEMA",
                    confidence=round(confidence, 3),
                    description=mdef.description,
                    matches=[],
                    family=mdef.family,
                    multiplier=mdef.multiplier,
                ))

        return detections

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def analyze_text(
        self,
        text: str,
        layers: list[str] | None = None,
        threshold: float = 0.5,
    ) -> dict:
        """
        Analyze a single text against the marker hierarchy.

        Returns dict with 'detections' list and 'timing_ms'.
        """
        if not self._loaded:
            self.load()

        start = time.perf_counter()
        layers = layers or ["ATO", "SEM", "CLU", "MEMA"]
        all_detections: list[Detection] = []

        # Level 1: ATO — detect all (including context_only for SEM input)
        ato_dets = []
        if "ATO" in layers or "SEM" in layers or "CLU" in layers or "MEMA" in layers:
            ato_dets = self.detect_ato(text, threshold)
            if "ATO" in layers:
                # Filter context_only markers from user-facing output
                ato_for_output = [
                    d for d in ato_dets
                    if "context_only" not in (self.markers.get(d.marker_id) or MarkerDef(
                        id="", layer="", lang="", description="", frame={},
                        patterns=[], examples={}, tags=[], rating=0
                    )).tags
                ]
                all_detections.extend(ato_for_output)

        # Level 2: SEM
        sem_dets = []
        if "SEM" in layers or "CLU" in layers or "MEMA" in layers:
            sem_dets = self.detect_sem(text, ato_dets, threshold)
            if "SEM" in layers:
                all_detections.extend(sem_dets)

        elapsed = (time.perf_counter() - start) * 1000
        return {"detections": all_detections, "timing_ms": round(elapsed, 2)}

    def analyze_conversation(
        self,
        messages: list[dict],
        layers: list[str] | None = None,
        threshold: float = 0.5,
        warm_start: dict[str, dict[str, float]] | None = None,
    ) -> dict:
        """
        Analyze a conversation (multiple messages) with temporal tracking.

        Returns detections across all layers including CLU/MEMA with
        message-level attribution and temporal patterns.
        """
        if not self._loaded:
            self.load()

        start = time.perf_counter()
        layers = layers or ["ATO", "SEM", "CLU", "MEMA"]

        all_ato_dets: list[list[Detection]] = []
        all_sem_dets: list[list[Detection]] = []
        flat_ato: list[Detection] = []
        flat_sem: list[Detection] = []
        all_detections: list[Detection] = []

        # Per-message ATO + SEM detection with VAD congruence gate
        shadow_buffer: list[Detection] = []

        for msg_idx, msg in enumerate(messages):
            text = msg.get("text", "")

            # Phase 1: Detect all ATOs (superposition)
            raw_atos = self.detect_ato(text, threshold)
            for d in raw_atos:
                d.message_indices = [msg_idx]

            # Phase 2: Compute raw message VAD (emotional field)
            raw_vad = self._compute_raw_vad(raw_atos)

            # Phase 3: Apply VAD congruence gate (quantum collapse)
            gated_atos, suppressed, surfaced = self._apply_vad_gate(
                raw_atos, raw_vad, shadow_buffer
            )

            # Update message indices for surfaced shadow ATOs
            for d in surfaced:
                d.message_indices = [msg_idx]

            # Phase 4: Update shadow buffer for next message
            shadow_buffer = suppressed

            # Use gated ATOs + surfaced for this message
            effective_atos = gated_atos + surfaced
            all_ato_dets.append(effective_atos)
            flat_ato.extend(effective_atos)

            # SEM detection uses gated+surfaced ATOs (meaningful ones only)
            sem_dets = self.detect_sem(text, effective_atos, threshold)
            for d in sem_dets:
                d.message_indices = [msg_idx]
            all_sem_dets.append(sem_dets)
            flat_sem.extend(sem_dets)

        if "ATO" in layers:
            # Filter context_only markers from user-facing output
            ato_for_output = [
                d for d in flat_ato
                if "context_only" not in (self.markers.get(d.marker_id) or MarkerDef(
                    id="", layer="", lang="", description="", frame={},
                    patterns=[], examples={}, tags=[], rating=0
                )).tags
            ]
            all_detections.extend(ato_for_output)
        if "SEM" in layers:
            all_detections.extend(flat_sem)

        # Level 3: CLU (over conversation window)
        clu_dets = []
        if "CLU" in layers or "MEMA" in layers:
            clu_dets = self.detect_clu(all_sem_dets, threshold)
            if "CLU" in layers:
                all_detections.extend(clu_dets)

        # Level 4: MEMA (now receives ATOs too for richer inference)
        if "MEMA" in layers:
            mema_dets = self.detect_mema(clu_dets, flat_sem, flat_ato, threshold)
            all_detections.extend(mema_dets)

        # ── Prosody-based emotion detection per message ──
        from .prosody import get_scorer
        scorer = get_scorer()
        message_emotions = scorer.score_conversation(messages)

        # ── VAD aggregation per message ──
        from .dynamics import compute_ued_metrics, compute_state_indices

        message_vad = []
        for msg_idx, msg in enumerate(messages):
            msg_dets = [d for d in flat_ato + flat_sem if msg_idx in d.message_indices]
            vads = [d.vad for d in msg_dets if d.vad]
            if vads:
                avg_v = sum(v["valence"] for v in vads) / len(vads)
                avg_a = sum(v["arousal"] for v in vads) / len(vads)
                avg_d = sum(v["dominance"] for v in vads) / len(vads)
                message_vad.append({
                    "valence": round(avg_v, 3),
                    "arousal": round(avg_a, 3),
                    "dominance": round(avg_d, 3),
                })
            else:
                message_vad.append({"valence": 0.0, "arousal": 0.0, "dominance": 0.0})

        # UED metrics (need at least 3 messages)
        ued_metrics = compute_ued_metrics(message_vad) if len(message_vad) >= 3 else None

        # State indices from effect_on_state
        state_indices = compute_state_indices(flat_ato + flat_sem, self.markers)

        # ── Per-speaker baseline (Polygraph principle) ──
        speaker_baselines = self._compute_speaker_baselines(messages, message_vad, warm_start=warm_start)

        # Temporal patterns
        temporal = self._extract_temporal_patterns(flat_ato + flat_sem, len(messages))

        elapsed = (time.perf_counter() - start) * 1000
        return {
            "detections": all_detections,
            "temporal_patterns": temporal,
            "message_vad": message_vad,
            "message_emotions": message_emotions,
            "ued_metrics": ued_metrics,
            "state_indices": state_indices,
            "speaker_baselines": speaker_baselines,
            "timing_ms": round(elapsed, 2),
        }

    @staticmethod
    def _compute_speaker_baselines(
        messages: list[dict],
        message_vad: list[dict],
        warm_start: dict[str, dict[str, float]] | None = None,
    ) -> dict:
        """
        Per-speaker baseline computation (Polygraph principle).

        For each speaker, tracks a running EWMA baseline of their VAD values.
        Detects significant deviations (shifts) from baseline — the signal
        isn't the absolute value but the DELTA from their own norm.

        If warm_start is provided (from persona profile), pre-seeds speaker
        EWMA baselines so the first message already computes a meaningful delta.

        Returns per-speaker stats + per-message deltas.
        """
        alpha = 0.3  # EWMA smoothing — lower = more stable baseline
        speaker_history: dict[str, list[float]] = {}
        speaker_ewma: dict[str, dict[str, float]] = {}  # running baseline
        per_message_delta: list[dict | None] = []

        # Pre-seed from warm_start (persona profile EWMA)
        if warm_start:
            for role, seed in warm_start.items():
                speaker_ewma[role] = {
                    "valence": seed.get("valence", 0),
                    "arousal": seed.get("arousal", 0),
                    "dominance": seed.get("dominance", 0),
                }
                speaker_history[role] = []

        for idx, msg in enumerate(messages):
            role = msg.get("role", "?")
            vad = message_vad[idx] if idx < len(message_vad) else None

            if not vad or (vad["valence"] == 0 and vad["arousal"] == 0 and vad["dominance"] == 0):
                per_message_delta.append(None)
                continue

            v, a, d = vad["valence"], vad["arousal"], vad["dominance"]

            if role not in speaker_ewma:
                # First message from this speaker: initialize baseline
                speaker_ewma[role] = {"valence": v, "arousal": a, "dominance": d}
                speaker_history[role] = [v]
                per_message_delta.append({
                    "speaker": role,
                    "delta_v": 0.0, "delta_a": 0.0,
                    "baseline_v": v, "baseline_a": a,
                    "shift": None,
                })
                continue

            bl = speaker_ewma[role]
            dv = round(v - bl["valence"], 3)
            da = round(a - bl["arousal"], 3)

            # Classify shift
            shift = None
            if dv > 0.18 and bl["valence"] < 0.0:
                shift = "repair"  # positive shift from negative baseline
            elif dv < -0.25 and bl["valence"] > -0.1:
                shift = "escalation"  # negative shift from neutral/positive baseline
            elif abs(dv) > 0.3:
                shift = "volatility"  # large swing either direction

            per_message_delta.append({
                "speaker": role,
                "delta_v": dv, "delta_a": da,
                "baseline_v": round(bl["valence"], 3),
                "baseline_a": round(bl["arousal"], 3),
                "shift": shift,
            })

            # Update EWMA baseline
            bl["valence"] = round(bl["valence"] * (1 - alpha) + v * alpha, 3)
            bl["arousal"] = round(bl["arousal"] * (1 - alpha) + a * alpha, 3)
            bl["dominance"] = round(bl["dominance"] * (1 - alpha) + d * alpha, 3)
            speaker_history.setdefault(role, []).append(v)

        # Summary per speaker
        speakers = {}
        for role, hist in speaker_history.items():
            speakers[role] = {
                "message_count": len(hist),
                "baseline_final": speaker_ewma.get(role, {}),
                "valence_mean": round(sum(hist) / len(hist), 3) if hist else 0,
                "valence_range": round(max(hist) - min(hist), 3) if hist else 0,
            }

        return {
            "speakers": speakers,
            "per_message_delta": per_message_delta,
        }

    def _extract_temporal_patterns(
        self, detections: list[Detection], total_messages: int
    ) -> list[dict]:
        """Extract temporal patterns from message-attributed detections."""
        marker_timeline: dict[str, list[int]] = {}
        for d in detections:
            for idx in d.message_indices:
                marker_timeline.setdefault(d.marker_id, []).append(idx)

        patterns = []
        for marker_id, indices in marker_timeline.items():
            if len(indices) < 2:
                continue

            indices = sorted(set(indices))
            first = indices[0]
            last = indices[-1]
            freq = len(indices)

            # Simple trend detection
            midpoint = total_messages // 2
            early = sum(1 for i in indices if i < midpoint)
            late = sum(1 for i in indices if i >= midpoint)

            if late > early * 1.5:
                trend = "increasing"
            elif early > late * 1.5:
                trend = "decreasing"
            else:
                trend = "stable"

            patterns.append({
                "pattern_type": "recurring",
                "marker_id": marker_id,
                "first_seen": first,
                "last_seen": last,
                "frequency": freq,
                "trend": trend,
            })

        return sorted(patterns, key=lambda p: -p["frequency"])

    def get_marker(self, marker_id: str) -> MarkerDef | None:
        """Get a single marker definition."""
        if not self._loaded:
            self.load()
        return self.markers.get(marker_id)

    def search_markers(
        self,
        layer: str | None = None,
        family: str | None = None,
        tag: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[MarkerDef], int]:
        """Search/filter markers with pagination."""
        if not self._loaded:
            self.load()

        results = list(self.markers.values())

        if layer:
            results = [m for m in results if m.layer == layer]
        if family:
            results = [m for m in results if m.family and m.family.upper() == family.upper()]
        if tag:
            results = [m for m in results if tag.lower() in [t.lower() for t in m.tags]]
        if search:
            q = search.lower()
            results = [
                m for m in results
                if q in m.id.lower() or q in m.description.lower()
            ]

        total = len(results)
        results = results[offset:offset + limit]
        return results, total


# Singleton engine instance
engine = MarkerEngine()
