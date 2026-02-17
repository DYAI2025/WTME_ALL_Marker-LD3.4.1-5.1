"""
LeanDeep Marker API — FastAPI Application.

Exposes the LeanDeep 5.0 marker detection engine as a REST API.

Endpoints:
  POST /v1/analyze              — Single text analysis
  POST /v1/analyze/conversation — Multi-message conversation analysis
  GET  /v1/markers              — List/filter markers
  GET  /v1/markers/{id}         — Get marker details
  GET  /v1/engine/config        — LD5 engine configuration
  GET  /v1/health               — Health check
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .auth import load_api_keys, verify_api_key
from .config import settings
from .engine import engine
from .models import (
    AnalyzeMeta,
    AnalyzeRequest,
    AnalyzeResponse,
    ConversationMarker,
    ConversationRequest,
    ConversationResponse,
    DetectedMarker,
    EngineConfig,
    HealthResponse,
    Layer,
    MarkerDetail,
    MarkerListResponse,
    PatternMatch,
    TemporalPattern,
)

_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load engine and auth on startup."""
    engine.load()
    load_api_keys()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description=(
        "Semantic marker detection for human communication analysis. "
        "Detects manipulation patterns, attachment styles, conflict dynamics, "
        "and 800+ behavioral markers across 4 hierarchical layers."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# POST /v1/analyze — Single text analysis
# ---------------------------------------------------------------------------

@app.post("/v1/analyze", response_model=AnalyzeResponse)
async def analyze_text(
    req: AnalyzeRequest,
    api_key: str = Depends(verify_api_key),
):
    """
    Analyze a single text against the LeanDeep marker hierarchy.

    Returns detected markers with confidence scores and pattern matches.
    For single-text analysis, only ATO and SEM layers are meaningful.
    CLU/MEMA require conversation context (use /v1/analyze/conversation).
    """
    layers = [l.value for l in req.layers]
    result = engine.analyze_text(req.text, layers=layers, threshold=req.threshold)

    markers = [
        DetectedMarker(
            id=d.marker_id,
            layer=Layer(d.layer),
            confidence=d.confidence,
            description=d.description,
            matches=[
                PatternMatch(
                    pattern=m.pattern,
                    span=(m.start, m.end),
                    matched_text=m.matched_text,
                )
                for m in d.matches
            ],
        )
        for d in result["detections"]
    ]

    return AnalyzeResponse(
        markers=sorted(markers, key=lambda m: -m.confidence),
        meta=AnalyzeMeta(
            processing_ms=result["timing_ms"],
            text_length=len(req.text),
            markers_detected=len(markers),
            layers_scanned=layers,
        ),
    )


# ---------------------------------------------------------------------------
# POST /v1/analyze/conversation — Conversation analysis
# ---------------------------------------------------------------------------

@app.post("/v1/analyze/conversation", response_model=ConversationResponse)
async def analyze_conversation(
    req: ConversationRequest,
    api_key: str = Depends(verify_api_key),
):
    """
    Analyze a multi-message conversation with temporal tracking.

    Supports all 4 layers including CLU (cluster patterns over messages)
    and MEMA (meta-level organism diagnosis). Returns temporal patterns
    showing how markers evolve across the conversation.
    """
    messages = [{"role": m.role, "text": m.text} for m in req.messages]
    layers = [l.value for l in req.layers]
    result = engine.analyze_conversation(messages, layers=layers, threshold=req.threshold)

    markers = [
        ConversationMarker(
            id=d.marker_id,
            layer=Layer(d.layer),
            confidence=d.confidence,
            description=d.description,
            message_indices=d.message_indices,
            family=d.family,
            multiplier=d.multiplier,
        )
        for d in result["detections"]
    ]

    temporal = [
        TemporalPattern(**tp)
        for tp in result.get("temporal_patterns", [])
    ]

    return ConversationResponse(
        markers=sorted(markers, key=lambda m: (-m.confidence, m.id)),
        temporal_patterns=temporal,
        meta=AnalyzeMeta(
            processing_ms=result["timing_ms"],
            text_length=sum(len(m.text) for m in req.messages),
            markers_detected=len(markers),
            layers_scanned=layers,
        ),
    )


# ---------------------------------------------------------------------------
# GET /v1/markers — List/filter markers
# ---------------------------------------------------------------------------

@app.get("/v1/markers", response_model=MarkerListResponse)
async def list_markers(
    layer: Layer | None = None,
    family: str | None = None,
    tag: str | None = None,
    search: str | None = Query(None, description="Full-text search in ID/description"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    api_key: str = Depends(verify_api_key),
):
    """List and filter markers from the registry."""
    results, total = engine.search_markers(
        layer=layer.value if layer else None,
        family=family,
        tag=tag,
        search=search,
        limit=limit,
        offset=offset,
    )

    markers = [
        MarkerDetail(
            id=m.id,
            layer=Layer(m.layer),
            lang=m.lang,
            description=m.description,
            frame=m.frame,
            patterns=[{"type": "regex", "value": p.raw} for p in m.patterns],
            examples=m.examples,
            tags=m.tags,
            rating=m.rating,
            family=m.family,
            multiplier=m.multiplier if m.multiplier != 1.0 else None,
            composed_of=m.composed_of,
            scoring=m.scoring,
            activation=m.activation,
            window=m.window,
        )
        for m in results
    ]

    return MarkerListResponse(total=total, offset=offset, limit=limit, markers=markers)


# ---------------------------------------------------------------------------
# GET /v1/markers/{marker_id} — Get single marker
# ---------------------------------------------------------------------------

@app.get("/v1/markers/{marker_id}", response_model=MarkerDetail)
async def get_marker(
    marker_id: str,
    api_key: str = Depends(verify_api_key),
):
    """Get full details for a specific marker by ID."""
    m = engine.get_marker(marker_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Marker '{marker_id}' not found")

    return MarkerDetail(
        id=m.id,
        layer=Layer(m.layer),
        lang=m.lang,
        description=m.description,
        frame=m.frame,
        patterns=[{"type": "regex", "value": p.raw} for p in m.patterns],
        examples=m.examples,
        tags=m.tags,
        rating=m.rating,
        family=m.family,
        multiplier=m.multiplier if m.multiplier != 1.0 else None,
        composed_of=m.composed_of,
        scoring=m.scoring,
        activation=m.activation,
        window=m.window,
    )


# ---------------------------------------------------------------------------
# GET /v1/engine/config — LD5 Engine configuration
# ---------------------------------------------------------------------------

@app.get("/v1/engine/config", response_model=EngineConfig)
async def get_engine_config(
    api_key: str = Depends(verify_api_key),
):
    """Get the LD5 engine configuration (families, EWMA, ARS, bias protection)."""
    cfg = engine.engine_config
    return EngineConfig(
        version=settings.version,
        total_markers=len(engine.markers),
        layers={
            "ATO": len(engine.ato_markers),
            "SEM": len(engine.sem_markers),
            "CLU": len(engine.clu_markers),
            "MEMA": len(engine.mema_markers),
        },
        families=cfg.get("families", {}),
        ewma=cfg.get("ewma", {}),
        ars=cfg.get("ars", {}),
        bias_protection=cfg.get("bias_protection", {}),
    )


# ---------------------------------------------------------------------------
# GET /v1/health — Health check
# ---------------------------------------------------------------------------

@app.get("/v1/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        markers_loaded=len(engine.markers),
        uptime_seconds=round(time.time() - _start_time, 1),
    )
