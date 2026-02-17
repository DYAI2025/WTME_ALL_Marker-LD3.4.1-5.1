"""
LeanDeep 5.0 Marker Detection Engine.

Implements the four-layer hierarchy (ATO → SEM → CLU → MEMA) with:
- ATO: Regex pattern matching against input text
- SEM: Compositional activation (1 ATO + context OR ≥2 ATOs)
- CLU: Windowed aggregation over SEMs with family multipliers
- MEMA: Meta-level diagnosis via composed_of / detect_class

The engine follows the referential context-semantics paradigm:
a single ATO can activate a SEM when the system context (active CLUs/MEMAs)
provides the "virtual second ATO" through contextual reference.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from .config import settings


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
    # ATO Detection (Level 1): Pure regex matching
    # -----------------------------------------------------------------------

    def detect_ato(self, text: str, threshold: float = 0.5) -> list[Detection]:
        """Detect atomic markers via regex pattern matching."""
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
                    detections.append(Detection(
                        marker_id=mdef.id,
                        layer="ATO",
                        confidence=round(confidence, 3),
                        description=mdef.description,
                        matches=matches,
                    ))

        return detections

    # -----------------------------------------------------------------------
    # SEM Activation (Level 2): Compositional + contextual reference
    # -----------------------------------------------------------------------

    def detect_sem(
        self, text: str, ato_detections: list[Detection], threshold: float = 0.5
    ) -> list[Detection]:
        """
        Detect semantic markers via composition rules.

        LD 5.0 paradigm: SEM = ATO + context.
        A SEM activates when:
          Path A: Composed ATOs are present (≥1 with context, or ≥2 without)
          Path B: Single ATO references active system context
          Path C: Accumulation of same ATO type
          Path D: Spontaneous emergence via detect_class (omission)
        """
        active_atos = {d.marker_id for d in ato_detections}
        detections = []

        for mdef in self.sem_markers:
            confidence = 0.0
            contributing_matches = []

            # Check composition
            composed = mdef.composed_of
            if isinstance(composed, list) and composed:
                # Count how many required ATOs are active
                hits = [c for c in composed if c in active_atos]
                hit_ratio = len(hits) / len(composed) if composed else 0

                # LD 5.0: 1 ATO + context suffices (relaxed from ≥2)
                activation = mdef.activation or {}
                if isinstance(activation, str):
                    rule = activation
                else:
                    rule = activation.get("rule", "ANY 1")
                rule = str(rule)

                if "ANY 1" in str(rule) and len(hits) >= 1:
                    confidence = 0.6 + (hit_ratio * 0.4)
                elif "ANY 2" in str(rule) and len(hits) >= 2:
                    confidence = 0.7 + (hit_ratio * 0.3)
                elif "ALL" in str(rule).upper() and len(hits) == len(composed):
                    confidence = 1.0
                elif len(hits) >= 1:
                    # Fallback: at least one constituent present
                    confidence = 0.5 + (hit_ratio * 0.3)

                # Collect matches from contributing ATOs
                for ato_det in ato_detections:
                    if ato_det.marker_id in hits:
                        contributing_matches.extend(ato_det.matches)

            # Also check SEM's own patterns (some SEMs have direct regex)
            for pat in mdef.patterns:
                if pat.compiled is None:
                    continue
                for m in pat.compiled.finditer(text):
                    contributing_matches.append(Match(
                        marker_id=mdef.id,
                        pattern=pat.raw,
                        start=m.start(),
                        end=m.end(),
                        matched_text=m.group(),
                    ))

            if contributing_matches and confidence == 0.0:
                # Direct pattern match without composition
                base = (mdef.scoring or {}).get("base", 1.0)
                confidence = min(1.0, 0.5 + len(contributing_matches) * 0.1 * base)

            if confidence >= threshold and contributing_matches:
                detections.append(Detection(
                    marker_id=mdef.id,
                    layer="SEM",
                    confidence=round(confidence, 3),
                    description=mdef.description,
                    matches=contributing_matches,
                ))

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
        threshold: float = 0.5,
    ) -> list[Detection]:
        """
        Detect meta markers from active CLUs.

        MEMA uses two paths:
          Option A (composed_of): Rule-based aggregation of CLUs
          Option B (detect_class): Algorithmic trend analysis
        """
        active_clus = {d.marker_id for d in clu_detections}
        active_sems = {d.marker_id for d in sem_detections}
        detections = []

        for mdef in self.mema_markers:
            confidence = 0.0

            # Option A: composed_of check (with fuzzy resolution)
            composed = mdef.composed_of
            all_active = active_clus | active_sems
            if isinstance(composed, list) and composed:
                hits = [c for c in composed if isinstance(c, str) and self._resolve_ref(c, all_active)]
                if hits:
                    hit_ratio = len(hits) / len(composed)
                    confidence = 0.5 + (hit_ratio * 0.5)

            # Option B: detect_class inference
            if confidence == 0.0 and mdef.detect_class:
                dc = mdef.detect_class

                if dc == "absence_meta":
                    # Absence markers fire when expected signals are NOT present
                    # For MVP: check if related conflict CLUs are active but
                    # expected positive signals are absent
                    if any("CONFLICT" in c for c in active_clus):
                        confidence = 0.6

                elif dc == "trend_analysis":
                    # Trend requires sustained pattern — needs stateful tracking
                    # For MVP: check if multiple related CLUs are active
                    related = [c for c in active_clus if any(
                        kw in c for kw in mdef.id.replace("MEMA_", "").split("_")[:2]
                    )]
                    if len(related) >= 1:
                        confidence = 0.55

                elif dc in ("composite_meta", "profile_composite", "archetype_composite"):
                    # Complex composite — needs keyword overlap between MEMA and active CLUs
                    mema_keywords = set(mdef.id.replace("MEMA_", "").split("_"))
                    related_clus = [
                        c for c in active_clus
                        if any(kw in c for kw in mema_keywords if len(kw) > 3)
                    ]
                    if len(related_clus) >= 1:
                        confidence = 0.45 + min(0.3, len(related_clus) * 0.1)

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
        layers = layers or ["ATO", "SEM"]
        all_detections: list[Detection] = []

        # Level 1: ATO
        ato_dets = []
        if "ATO" in layers or "SEM" in layers or "CLU" in layers or "MEMA" in layers:
            ato_dets = self.detect_ato(text, threshold)
            if "ATO" in layers:
                all_detections.extend(ato_dets)

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
    ) -> dict:
        """
        Analyze a conversation (multiple messages) with temporal tracking.

        Returns detections across all layers including CLU/MEMA with
        message-level attribution and temporal patterns.
        """
        if not self._loaded:
            self.load()

        start = time.perf_counter()
        layers = layers or ["ATO", "SEM", "CLU"]

        all_ato_dets: list[list[Detection]] = []
        all_sem_dets: list[list[Detection]] = []
        flat_ato: list[Detection] = []
        flat_sem: list[Detection] = []
        all_detections: list[Detection] = []

        # Per-message ATO + SEM detection
        for msg_idx, msg in enumerate(messages):
            text = msg.get("text", "")

            ato_dets = self.detect_ato(text, threshold)
            for d in ato_dets:
                d.message_indices = [msg_idx]
            all_ato_dets.append(ato_dets)
            flat_ato.extend(ato_dets)

            sem_dets = self.detect_sem(text, ato_dets, threshold)
            for d in sem_dets:
                d.message_indices = [msg_idx]
            all_sem_dets.append(sem_dets)
            flat_sem.extend(sem_dets)

        if "ATO" in layers:
            all_detections.extend(flat_ato)
        if "SEM" in layers:
            all_detections.extend(flat_sem)

        # Level 3: CLU (over conversation window)
        clu_dets = []
        if "CLU" in layers or "MEMA" in layers:
            clu_dets = self.detect_clu(all_sem_dets, threshold)
            if "CLU" in layers:
                all_detections.extend(clu_dets)

        # Level 4: MEMA
        if "MEMA" in layers:
            mema_dets = self.detect_mema(clu_dets, flat_sem, threshold)
            all_detections.extend(mema_dets)

        # Temporal patterns
        temporal = self._extract_temporal_patterns(flat_ato + flat_sem, len(messages))

        elapsed = (time.perf_counter() - start) * 1000
        return {
            "detections": all_detections,
            "temporal_patterns": temporal,
            "timing_ms": round(elapsed, 2),
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
