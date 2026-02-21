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

import io
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

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
    DynamicsResponse,
    EmotionScore,
    EngineConfig,
    Episode,
    HealthResponse,
    Layer,
    MarkerDetail,
    MarkerListResponse,
    PatternMatch,
    PersonaCreateResponse,
    PersonaSessionSummary,
    PredictionReservoir,
    PredictionResponse,
    SpeakerBaselines,
    SpeakerDelta,
    SpeakerSummary,
    StateIndices,
    TemporalPattern,
    UEDMetrics,
    VADPoint,
)
from .personas import PersonaStore

_start_time = time.time()


persona_store = PersonaStore()


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

# Serve static assets (neutral_insights.json, etc.)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


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
            family=d.family,
            multiplier=d.multiplier,
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
# POST /v1/analyze/dynamics — Emotion dynamics analysis
# ---------------------------------------------------------------------------

@app.post("/v1/analyze/dynamics", response_model=DynamicsResponse)
async def analyze_dynamics(
    req: ConversationRequest,
    api_key: str = Depends(verify_api_key),
):
    """
    Analyze a conversation with full emotion dynamics tracking.

    Returns VAD trajectories per message, UED metrics (home base, variability,
    rise/recovery rate), and relationship state indices (trust/conflict/deesc).

    If persona_token is provided (Pro tier), loads persona profile for warm-start
    and accumulates session data into the profile.
    """
    messages = [{"role": m.role, "text": m.text} for m in req.messages]
    layers = [l.value for l in req.layers]

    # Persona warm-start
    persona = None
    warm_start = None
    if req.persona_token:
        try:
            persona = persona_store.get(req.persona_token)
        except ValueError:
            raise HTTPException(status_code=404, detail="Invalid persona token")
        if persona is None:
            raise HTTPException(status_code=404, detail="Persona not found")
        warm_start = persona_store.extract_warm_start(persona)

    result = engine.analyze_conversation(
        messages, layers=layers, threshold=req.threshold, warm_start=warm_start
    )

    markers = [
        ConversationMarker(
            id=d.marker_id,
            layer=Layer(d.layer),
            confidence=d.confidence,
            description=d.description,
            message_indices=d.message_indices,
            family=d.family,
            multiplier=d.multiplier,
            matches=[
                PatternMatch(
                    pattern=m.pattern,
                    span=(m.start, m.end),
                    matched_text=m.matched_text,
                )
                for m in d.matches
            ],
            frame=getattr(engine.markers.get(d.marker_id), 'frame', None) or None,
        )
        for d in result["detections"]
    ]

    temporal = [
        TemporalPattern(**tp)
        for tp in result.get("temporal_patterns", [])
    ]

    message_vad = [
        VADPoint(**mv) for mv in result.get("message_vad", [])
    ]

    ued_raw = result.get("ued_metrics")
    ued_metrics = None
    if ued_raw:
        ued_metrics = UEDMetrics(
            home_base=VADPoint(**ued_raw["home_base"]),
            variability=ued_raw["variability"],
            instability=ued_raw["instability"],
            rise_rate=ued_raw["rise_rate"],
            recovery_rate=ued_raw["recovery_rate"],
            density=ued_raw["density"],
        )

    si_raw = result.get("state_indices", {"trust": 0, "conflict": 0, "deesc": 0, "contributing_markers": 0})
    state_indices = StateIndices(**si_raw)

    # Prosody-based emotion scores per message
    raw_emotions = result.get("message_emotions", [])
    message_emotions = [
        EmotionScore(
            scores=e.scores, dominant=e.dominant, dominant_score=e.dominant_score,
            prosody=getattr(e, 'prosody', None),
        )
        if e is not None else None
        for e in raw_emotions
    ]

    # Speaker baselines (Polygraph principle)
    sb_raw = result.get("speaker_baselines")
    speaker_baselines = None
    if sb_raw:
        speakers = {}
        for role, info in sb_raw.get("speakers", {}).items():
            bf = info.get("baseline_final", {})
            speakers[role] = SpeakerSummary(
                message_count=info["message_count"],
                baseline_final=VADPoint(
                    valence=bf.get("valence", 0),
                    arousal=bf.get("arousal", 0),
                    dominance=bf.get("dominance", 0),
                ),
                valence_mean=info["valence_mean"],
                valence_range=info["valence_range"],
            )
        deltas = []
        for d in sb_raw.get("per_message_delta", []):
            if d is None:
                deltas.append(None)
            else:
                deltas.append(SpeakerDelta(**d))
        speaker_baselines = SpeakerBaselines(speakers=speakers, per_message_delta=deltas)

    # Persona accumulation (Pro tier)
    persona_session_summary = None
    if persona:
        summary = persona_store.accumulate_session(persona, messages, result)
        persona_session_summary = PersonaSessionSummary(
            session_number=summary["session_number"],
            warm_start_applied=summary["warm_start_applied"],
            new_episodes=[Episode(**ep) for ep in summary["new_episodes"]],
            state_snapshot=summary["state_snapshot"],
            prediction_available=summary["prediction_available"],
        )

    return DynamicsResponse(
        markers=sorted(markers, key=lambda m: (-m.confidence, m.id)),
        message_vad=message_vad,
        message_emotions=message_emotions,
        ued_metrics=ued_metrics,
        state_indices=state_indices,
        speaker_baselines=speaker_baselines,
        temporal_patterns=temporal,
        persona_session=persona_session_summary,
        meta=AnalyzeMeta(
            processing_ms=result["timing_ms"],
            text_length=sum(len(m.text) for m in req.messages),
            markers_detected=len(markers),
            layers_scanned=layers,
        ),
    )


# ---------------------------------------------------------------------------
# POST /v1/personas — Create blank persona (Pro tier)
# ---------------------------------------------------------------------------

@app.post("/v1/personas", response_model=PersonaCreateResponse)
async def create_persona(api_key: str = Depends(verify_api_key)):
    """Create a new blank persona profile. Returns a UUID token for future sessions."""

    persona = persona_store.create()
    return PersonaCreateResponse(token=persona["token"], created_at=persona["created_at"])


# ---------------------------------------------------------------------------
# GET /v1/personas/{token} — Get full persona profile
# ---------------------------------------------------------------------------

@app.get("/v1/personas/{token}")
async def get_persona(token: str, api_key: str = Depends(verify_api_key)):
    """Get the full persona profile by token."""

    try:
        persona = persona_store.get(token)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid persona token")
    if persona is None:
        raise HTTPException(status_code=404, detail="Persona not found")
    return persona


# ---------------------------------------------------------------------------
# DELETE /v1/personas/{token} — Delete persona
# ---------------------------------------------------------------------------

@app.delete("/v1/personas/{token}")
async def delete_persona(token: str, api_key: str = Depends(verify_api_key)):
    """Delete a persona profile permanently."""

    try:
        deleted = persona_store.delete(token)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid persona token")
    if not deleted:
        raise HTTPException(status_code=404, detail="Persona not found")
    return {"status": "deleted", "token": token}


# ---------------------------------------------------------------------------
# GET /v1/personas/{token}/predict — Shift prediction from reservoir
# ---------------------------------------------------------------------------

@app.get("/v1/personas/{token}/predict", response_model=PredictionResponse)
async def predict_persona(token: str, api_key: str = Depends(verify_api_key)):
    """Get shift predictions from the persona's accumulated data."""

    try:
        persona = persona_store.get(token)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid persona token")
    if persona is None:
        raise HTTPException(status_code=404, detail="Persona not found")

    session_count = persona.get("stats", {}).get("session_count", 0)
    predictions_data = persona.get("predictions", {})
    total_shifts = sum(predictions_data.get("shift_counts", {}).values())

    if total_shifts < 5:
        return PredictionResponse(
            token=token,
            session_count=session_count,
            predictions=None,
            confidence="insufficient_data",
        )

    if session_count >= 10:
        confidence = "high"
    elif session_count >= 5:
        confidence = "medium"
    else:
        confidence = "low"

    return PredictionResponse(
        token=token,
        session_count=session_count,
        predictions=PredictionReservoir(**predictions_data),
        confidence=confidence,
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


# ---------------------------------------------------------------------------
# GET /playground — Visual Playground UI
# ---------------------------------------------------------------------------

@app.get("/playground", response_class=HTMLResponse)
async def playground():
    """Serve the interactive marker playground."""
    html_path = Path(__file__).parent / "static" / "playground.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# GET /analysis — Analysis UI (intuitive emotion dynamics)
# ---------------------------------------------------------------------------

@app.get("/analysis", response_class=HTMLResponse)
async def analysis():
    """Serve the intuitive analysis UI for emotion dynamics and marker interpretation."""
    html_path = Path(__file__).parent / "static" / "analysis.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# POST /v1/upload — Document upload (extracts text from .docx/.txt/.md)
# ---------------------------------------------------------------------------

@app.post("/v1/upload")
async def upload_document(file: UploadFile = File(...)):
    """Extract text from uploaded document (.txt, .md, .docx)."""
    name = file.filename or ""
    content = await file.read()

    if name.endswith(".txt") or name.endswith(".md"):
        text = content.decode("utf-8", errors="replace")
    elif name.endswith(".docx"):
        try:
            from docx import Document
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="python-docx not installed. Run: pip install python-docx",
            )
        doc = Document(io.BytesIO(content))
        text = "\n".join(p.text for p in doc.paragraphs)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {name}. Use .txt, .md, or .docx",
        )

    return {"filename": name, "text": text, "length": len(text)}
