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


class DynamicsResponse(BaseModel):
    markers: list[ConversationMarker]
    message_vad: list[VADPoint]
    ued_metrics: UEDMetrics | None = None
    state_indices: StateIndices
    temporal_patterns: list[TemporalPattern] = []
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
