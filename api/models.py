"""Pydantic models for the LeanDeep Marker API."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# --- Enums ---

class Layer(str, Enum):
    ATO = "ATO"
    SEM = "SEM"
    CLU = "CLU"
    MEMA = "MEMA"


class Language(str, Enum):
    DE = "de"
    EN = "en"
    BILINGUAL = "bilingual"


# --- Request Models ---

class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50_000, description="Text to analyze")
    language: Language = Language.DE
    layers: list[Layer] = Field(default=[Layer.ATO, Layer.SEM], description="Layers to detect")
    threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence threshold")


class Message(BaseModel):
    role: str = Field(..., description="Speaker role (A/B, therapist/client, etc.)")
    text: str = Field(..., min_length=1, max_length=50_000)


class ConversationRequest(BaseModel):
    messages: list[Message] = Field(..., min_length=1, max_length=200)
    language: Language = Language.DE
    layers: list[Layer] = Field(
        default=[Layer.ATO, Layer.SEM, Layer.CLU, Layer.MEMA],
        description="Layers to detect",
    )
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    persona_token: str | None = Field(None, description="Persona token for persistent profiling (Pro tier)")


class MarkerQuery(BaseModel):
    layer: Layer | None = None
    family: str | None = None
    tag: str | None = None
    search: str | None = Field(None, description="Full-text search in ID/description")
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


# --- Response Models ---

class PatternMatch(BaseModel):
    pattern: str
    span: tuple[int, int]
    matched_text: str


class DetectedMarker(BaseModel):
    id: str
    layer: Layer
    confidence: float = Field(ge=0.0, le=1.0)
    description: str = ""
    matches: list[PatternMatch] = []
    family: str | None = None
    multiplier: float | None = None


class AnalyzeResponse(BaseModel):
    markers: list[DetectedMarker]
    meta: AnalyzeMeta


class AnalyzeMeta(BaseModel):
    processing_ms: float
    version: str = "5.1-LD5"
    text_length: int
    markers_detected: int
    layers_scanned: list[str]


class ConversationMarker(BaseModel):
    id: str
    layer: Layer
    confidence: float
    description: str = ""
    message_indices: list[int] = []
    family: str | None = None
    multiplier: float | None = None
    matches: list[PatternMatch] = []
    frame: dict[str, Any] | None = None


class TemporalPattern(BaseModel):
    pattern_type: str
    marker_id: str
    first_seen: int
    last_seen: int
    frequency: int
    trend: str = "stable"


class ConversationResponse(BaseModel):
    markers: list[ConversationMarker]
    temporal_patterns: list[TemporalPattern] = []
    meta: AnalyzeMeta


class VADPoint(BaseModel):
    valence: float
    arousal: float
    dominance: float


class UEDVariability(BaseModel):
    valence: float
    arousal: float


class UEDMetrics(BaseModel):
    home_base: VADPoint
    variability: UEDVariability
    instability: UEDVariability
    rise_rate: float
    recovery_rate: float
    density: float


class StateIndices(BaseModel):
    trust: float
    conflict: float
    deesc: float
    contributing_markers: int


class EmotionScore(BaseModel):
    scores: dict[str, float]   # {ANGER: 0.12, JOY: 0.45, ...}
    dominant: str              # "JOY"
    dominant_score: float      # 0.45
    prosody: dict[str, float] | None = None  # 17 structural features


class SpeakerDelta(BaseModel):
    speaker: str
    delta_v: float
    delta_a: float
    baseline_v: float
    baseline_a: float
    shift: str | None = None  # "repair" | "escalation" | "volatility"


class SpeakerSummary(BaseModel):
    message_count: int
    baseline_final: VADPoint
    valence_mean: float
    valence_range: float


class SpeakerBaselines(BaseModel):
    speakers: dict[str, SpeakerSummary]
    per_message_delta: list[SpeakerDelta | None]


class DynamicsResponse(BaseModel):
    markers: list[ConversationMarker]
    message_vad: list[VADPoint]
    message_emotions: list[EmotionScore | None] = []
    ued_metrics: UEDMetrics | None = None
    state_indices: StateIndices
    speaker_baselines: SpeakerBaselines | None = None
    temporal_patterns: list[TemporalPattern] = []
    persona_session: "PersonaSessionSummary | None" = None
    meta: AnalyzeMeta


class MarkerDetail(BaseModel):
    id: str
    layer: Layer
    lang: str
    description: str
    frame: dict[str, Any]
    patterns: list[dict[str, Any]]
    examples: dict[str, list[str]]
    tags: list[str]
    rating: int
    family: str | None = None
    multiplier: float | None = None
    composed_of: Any = None
    scoring: dict[str, Any] | None = None
    activation: dict[str, Any] | None = None
    window: dict[str, Any] | None = None


class MarkerListResponse(BaseModel):
    total: int
    offset: int
    limit: int
    markers: list[MarkerDetail]


class EngineConfig(BaseModel):
    version: str
    total_markers: int
    layers: dict[str, int]
    families: dict[str, Any]
    ewma: dict[str, Any]
    ars: dict[str, Any]
    bias_protection: dict[str, Any]


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "5.1-LD5"
    markers_loaded: int
    uptime_seconds: float


# --- Persona Models (Pro Tier) ---

class SpeakerEWMAState(BaseModel):
    valence: float
    arousal: float
    dominance: float
    message_count: int = 0
    sessions_seen: int = 0


class Episode(BaseModel):
    id: str
    type: str  # escalation_cluster | repair_trend | withdrawal_phase | rupture | stabilization
    session: int
    duration_messages: int
    markers_involved: list[str] = []
    vad_delta: dict[str, float] = {}
    state_at_entry: dict[str, float] = {}
    state_at_exit: dict[str, float] = {}


class PredictionReservoir(BaseModel):
    shift_counts: dict[str, int] = {}
    shift_prior: dict[str, float] = {}
    shift_given_valence_quartile: dict[str, dict[str, float]] = {}
    top_transition_pairs: list[list] = []


class PersonaStats(BaseModel):
    session_count: int
    total_messages: int
    first_session: str
    last_session: str


class PersonaCreateResponse(BaseModel):
    token: str
    created_at: str


class PredictionResponse(BaseModel):
    token: str
    session_count: int
    predictions: PredictionReservoir | None = None
    confidence: str = "insufficient_data"  # "low" | "medium" | "high" | "insufficient_data"


class PersonaSessionSummary(BaseModel):
    session_number: int
    warm_start_applied: bool
    new_episodes: list[Episode] = []
    state_snapshot: dict[str, float] = {}
    prediction_available: bool = False
