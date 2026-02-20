# Semiotic Dynamics + VAD Integration Plan

> **For Claude:** Use `~/.config/superpowers/skills/skills/collaboration/executing-plans/SKILL.md` to implement this plan task-by-task.

**Goal:** Add emotion trajectory tracking (VAD) and semiotic state indices (trust/conflict/deesc) to the LeanDeep engine, powered by per-marker annotations — no LLM required.

**Architecture:** Each ATO/SEM marker gets `vad_estimate` and `effect_on_state` fields in YAML. The engine aggregates these per message to produce VAD trajectories and relationship indices. A new `/v1/analyze/dynamics` endpoint exposes UED metrics (home base, variability, rise/recovery rate) over conversations. The emotion-dynamics dashboard is adapted for the playground.

**Tech Stack:** Python 3, FastAPI, ruamel.yaml, existing marker registry JSON, Chart.js (dashboard)

---

### Task 1: VAD Enrichment Tool

**Files:**
- Create: `tools/enrich_vad.py`
- Reference: `build/markers_normalized/marker_registry.json`
- Reference: `api/engine.py` (MarkerDef dataclass)

**Step 1: Write the failing test**

```python
# tests/test_enrich_vad.py
def test_vad_values_in_range():
    """VAD values must be valence [-1,1], arousal [0,1], dominance [0,1]."""
    import json
    from pathlib import Path
    registry = json.loads(Path("build/markers_normalized/marker_registry.json").read_text())
    markers = registry["markers"]
    for mid, m in markers.items():
        vad = m.get("vad_estimate")
        if vad is None:
            continue
        assert -1.0 <= vad["valence"] <= 1.0, f"{mid} valence out of range"
        assert 0.0 <= vad["arousal"] <= 1.0, f"{mid} arousal out of range"
        assert 0.0 <= vad["dominance"] <= 1.0, f"{mid} dominance out of range"
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_enrich_vad.py -v`
Expected: PASS (vacuously, no markers have VAD yet — test should pass but validate nothing)

**Step 3: Write the enrichment tool**

`tools/enrich_vad.py` must:
1. Load the marker registry
2. For each ATO and SEM marker, derive VAD estimates from its `frame`, `tags`, `description`, and `family` fields using a rules-based mapping:
   - `family` → base VAD (e.g., CONFLICT family → valence=-0.4, arousal=0.7, dominance=0.5)
   - `tags` containing emotion keywords → adjust (e.g., "anger" → arousal+0.2, "sadness" → arousal-0.2)
   - Known marker prefixes → override (e.g., ATO_JOY → valence=0.6, ATO_SUFFERING → valence=-0.7)
3. Also add `effect_on_state` with `{trust, conflict, deesc}` deltas [-1,1]:
   - Derived from family + frame.pragmatics + tags
4. Write enriched fields back to source YAMLs in `build/markers_rated/`
5. Flags: `--dry-run` (default), `--apply`, `--stats`

VAD mapping table (core rules):

| Signal Category | Valence | Arousal | Dominance |
|----------------|---------|---------|-----------|
| Positive emotion (joy, gratitude, humor) | +0.5 | 0.4 | 0.5 |
| Negative emotion (anger, fear, disgust) | -0.5 | 0.7 | 0.3 |
| Sadness/grief/loss | -0.6 | 0.3 | 0.2 |
| Control/power/assertion | -0.2 | 0.6 | 0.8 |
| Vulnerability/helplessness | -0.4 | 0.5 | 0.1 |
| Neutral/structural (modal verbs, questions) | 0.0 | 0.2 | 0.5 |
| De-escalation/repair | +0.2 | 0.2 | 0.5 |
| Conflict markers (blame, accusation) | -0.5 | 0.8 | 0.6 |
| Intimacy/attachment | +0.4 | 0.4 | 0.4 |

Effect-on-state mapping:

| Signal Category | Trust | Conflict | Deesc |
|----------------|-------|----------|-------|
| Positive emotion | +0.1 | -0.1 | +0.1 |
| Negative emotion | -0.1 | +0.2 | -0.1 |
| Control/power | -0.2 | +0.3 | -0.2 |
| De-escalation | +0.2 | -0.2 | +0.3 |
| Conflict markers | -0.3 | +0.4 | -0.2 |
| Intimacy/attachment | +0.3 | -0.1 | +0.1 |

**Step 4: Run enrichment tool in dry-run**

Run: `python3 tools/enrich_vad.py --stats`
Expected: Table showing how many markers got VAD values per layer, distribution of valence/arousal/dominance

**Step 5: Apply and rebuild**

Run: `python3 tools/enrich_vad.py --apply && python3 tools/normalize_schema.py`
Expected: Registry now contains `vad_estimate` and `effect_on_state` on enriched markers

**Step 6: Run VAD validation test**

Run: `python3 -m pytest tests/test_enrich_vad.py -v`
Expected: PASS with actual markers validated

**Step 7: Commit**

```bash
git add tools/enrich_vad.py tests/test_enrich_vad.py
git commit -m "feat: add VAD + effect_on_state enrichment tool"
```

---

### Task 2: Engine — VAD Aggregation per Message

**Files:**
- Modify: `api/engine.py` (MarkerDef, Detection, analyze_text, analyze_conversation)
- Modify: `api/models.py` (response models)
- Modify: `tools/normalize_schema.py` (preserve new fields)

**Step 1: Write the failing test**

```python
# tests/test_engine_vad.py
def test_analyze_returns_vad():
    """analyze_text should return per-detection VAD when markers have vad_estimate."""
    from api.engine import MarkerEngine
    eng = MarkerEngine()
    eng.load()
    result = eng.analyze_text("Ich bin so wütend auf dich!", threshold=0.3)
    # At least one detection should have vad
    vad_dets = [d for d in result["detections"] if d.vad is not None]
    assert len(vad_dets) > 0

def test_conversation_returns_message_vad():
    """analyze_conversation should return aggregated VAD per message."""
    from api.engine import MarkerEngine
    eng = MarkerEngine()
    eng.load()
    messages = [
        {"text": "Ich bin so wütend!", "speaker": "A"},
        {"text": "Das tut mir leid.", "speaker": "B"},
    ]
    result = eng.analyze_conversation(messages, threshold=0.3)
    assert "message_vad" in result
    assert len(result["message_vad"]) == 2
    assert "valence" in result["message_vad"][0]
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_engine_vad.py -v`
Expected: FAIL — `Detection` has no `vad` attribute, `message_vad` not in result

**Step 3: Modify MarkerDef and Detection**

In `api/engine.py`:

```python
# MarkerDef — add fields:
vad_estimate: dict | None = None        # {valence, arousal, dominance}
effect_on_state: dict | None = None     # {trust, conflict, deesc}

# Detection — add field:
vad: dict | None = None                 # copied from MarkerDef if present

# In _parse_marker() — add:
vad_estimate=data.get("vad_estimate"),
effect_on_state=data.get("effect_on_state"),
```

**Step 4: Add VAD to Detection in detect_ato/detect_sem**

After creating a Detection, copy the marker's VAD:
```python
det.vad = mdef.vad_estimate
```

**Step 5: Add message_vad aggregation to analyze_conversation**

After per-message detection, aggregate VAD for each message:
```python
message_vad = []
for msg_idx, msg in enumerate(messages):
    msg_dets = [d for d in all_detections if msg_idx in d.message_indices]
    vads = [d.vad for d in msg_dets if d.vad]
    if vads:
        avg_v = sum(v["valence"] for v in vads) / len(vads)
        avg_a = sum(v["arousal"] for v in vads) / len(vads)
        avg_d = sum(v["dominance"] for v in vads) / len(vads)
        message_vad.append({"valence": round(avg_v, 3), "arousal": round(avg_a, 3), "dominance": round(avg_d, 3)})
    else:
        message_vad.append({"valence": 0.0, "arousal": 0.0, "dominance": 0.0})
```

Add `"message_vad": message_vad` to the return dict.

**Step 6: Preserve new fields in normalizer**

In `tools/normalize_schema.py`, add `"vad_estimate"` and `"effect_on_state"` to the preserved fields list.

**Step 7: Run tests**

Run: `python3 -m pytest tests/test_engine_vad.py -v`
Expected: PASS

**Step 8: Commit**

```bash
git add api/engine.py api/models.py tools/normalize_schema.py tests/test_engine_vad.py
git commit -m "feat: engine aggregates VAD per message from marker annotations"
```

---

### Task 3: UED Metrics Computation

**Files:**
- Modify: `api/engine.py` (analyze_conversation)
- Create: `api/dynamics.py` (UED metric computation)

**Step 1: Write the failing test**

```python
# tests/test_dynamics.py
def test_ued_metrics_from_vad_sequence():
    from api.dynamics import compute_ued_metrics
    vad_seq = [
        {"valence": -0.5, "arousal": 0.8, "dominance": 0.3},
        {"valence": -0.3, "arousal": 0.6, "dominance": 0.4},
        {"valence": 0.2, "arousal": 0.3, "dominance": 0.5},
        {"valence": -0.4, "arousal": 0.7, "dominance": 0.2},
        {"valence": 0.1, "arousal": 0.4, "dominance": 0.5},
    ]
    metrics = compute_ued_metrics(vad_seq)
    assert "home_base" in metrics
    assert "variability" in metrics
    assert "rise_rate" in metrics
    assert "recovery_rate" in metrics
    assert "density" in metrics
    assert metrics["home_base"]["valence"] == round(sum(v["valence"] for v in vad_seq) / 5, 3)
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_dynamics.py -v`
Expected: FAIL — module `api.dynamics` does not exist

**Step 3: Implement api/dynamics.py**

```python
def compute_ued_metrics(vad_sequence: list[dict]) -> dict:
    """Compute UED metrics from a sequence of VAD values."""
    # Home Base: mean valence/arousal
    # Variability: std of valence/arousal → low/medium/high
    # Instability: mean absolute successive difference
    # Rise Rate: avg positive arousal delta after negative valence
    # Recovery Rate: avg negative arousal delta after peak
    # Density: proportion of utterances with |valence| > 0.2 or arousal > 0.3
```

Full implementation with math.

**Step 4: Wire into analyze_conversation**

Add to the return dict:
```python
ued_metrics = compute_ued_metrics(message_vad) if len(message_vad) >= 3 else None
```

**Step 5: Run tests**

Run: `python3 -m pytest tests/test_dynamics.py tests/test_engine_vad.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add api/dynamics.py tests/test_dynamics.py api/engine.py
git commit -m "feat: add UED metrics (home base, variability, rise/recovery rate)"
```

---

### Task 4: Relationship State Indices (Trust/Conflict/Deesc)

**Files:**
- Modify: `api/engine.py` (analyze_conversation)
- Modify: `api/dynamics.py` (add state index computation)

**Step 1: Write the failing test**

```python
# tests/test_state_indices.py
def test_state_indices_from_conversation():
    from api.engine import MarkerEngine
    eng = MarkerEngine()
    eng.load()
    messages = [
        {"text": "Du bist immer so egoistisch!", "speaker": "A"},
        {"text": "Das stimmt nicht, ich tue mein Bestes.", "speaker": "B"},
        {"text": "Lass uns in Ruhe darüber reden.", "speaker": "A"},
    ]
    result = eng.analyze_conversation(messages, threshold=0.3)
    assert "state_indices" in result
    si = result["state_indices"]
    assert "trust" in si and "conflict" in si and "deesc" in si
    # Conflict should be > 0 after accusation
    assert si["conflict"] > 0
```

**Step 2: Implement state index aggregation**

In `api/dynamics.py`:
```python
def compute_state_indices(detections: list, markers: dict) -> dict:
    """Aggregate effect_on_state from all detections."""
    trust = 0.0
    conflict = 0.0
    deesc = 0.0
    count = 0
    for d in detections:
        mdef = markers.get(d.marker_id)
        if mdef and mdef.effect_on_state:
            eos = mdef.effect_on_state
            trust += eos.get("trust", 0)
            conflict += eos.get("conflict", 0)
            deesc += eos.get("deesc", 0)
            count += 1
    return {
        "trust": round(max(-1, min(1, trust)), 3),
        "conflict": round(max(-1, min(1, conflict)), 3),
        "deesc": round(max(-1, min(1, deesc)), 3),
        "contributing_markers": count,
    }
```

**Step 3: Wire into analyze_conversation return**

**Step 4: Run tests**

Run: `python3 -m pytest tests/test_state_indices.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add api/dynamics.py api/engine.py tests/test_state_indices.py
git commit -m "feat: add trust/conflict/deesc state indices from marker annotations"
```

---

### Task 5: API Endpoint `/v1/analyze/dynamics`

**Files:**
- Modify: `api/main.py` (add endpoint)
- Modify: `api/models.py` (add response model)

**Step 1: Write the failing test**

```python
# tests/test_api_dynamics.py
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_dynamics_endpoint():
    resp = client.post("/v1/analyze/dynamics", json={
        "messages": [
            {"text": "Ich bin wütend!", "speaker": "A"},
            {"text": "Es tut mir leid.", "speaker": "B"},
            {"text": "Ich verstehe dich.", "speaker": "A"},
        ]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "message_vad" in data
    assert "ued_metrics" in data
    assert "state_indices" in data
    assert "detections" in data
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_api_dynamics.py -v`
Expected: FAIL — 404

**Step 3: Implement the endpoint**

In `api/main.py`:
```python
@app.post("/v1/analyze/dynamics")
async def analyze_dynamics(req: ConversationRequest):
    messages = [{"text": m.text, "speaker": m.speaker} for m in req.messages]
    result = engine.analyze_conversation(messages, threshold=req.threshold or 0.3)
    # result now contains message_vad, ued_metrics, state_indices
    return result
```

**Step 4: Run tests**

Run: `python3 -m pytest tests/test_api_dynamics.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add api/main.py api/models.py tests/test_api_dynamics.py
git commit -m "feat: add /v1/analyze/dynamics endpoint with VAD + UED + state indices"
```

---

### Task 6: Eval — Run Dynamics on Gold Corpus

**Files:**
- Create: `tools/eval_dynamics.py`
- Reference: `eval/gold_corpus.jsonl`

**Step 1: Write eval_dynamics.py**

Runs the dynamics analysis on all corpus chunks and reports:
- Avg VAD per speaker (Person_A vs Person_B)
- UED metrics aggregated across conversations
- State index trends over time (early chunks vs late chunks)
- Emotional "hotspot" chunks (highest arousal, lowest valence)

**Step 2: Run it**

Run: `python3 tools/eval_dynamics.py --top 20`
Expected: Report showing emotion trajectories and relationship state evolution over the 6-year conversation

**Step 3: Commit**

```bash
git add tools/eval_dynamics.py
git commit -m "feat: add dynamics evaluation against gold corpus"
```

---

### Task 7: Playground Dashboard Integration

**Files:**
- Modify: `api/main.py` (playground HTML)
- Reference: `skill_semiotic-dynamics/.../emotion-dynamics-dashboard.html`

**Step 1: Add Chart.js visualization to playground**

Extend the existing playground at `/playground` with:
- VAD trajectory chart (valence + arousal line chart per message)
- State indices gauge (trust/conflict/deesc)
- UED metric cards (home base, variability, rise/recovery rate)

Uses the same Chart.js approach from the semiotic-dynamics dashboard, adapted for the API response format.

**Step 2: Test in browser**

Open `http://localhost:8420/playground`, paste a conversation, verify charts render.

**Step 3: Commit**

```bash
git add api/main.py
git commit -m "feat: add VAD trajectory + state indices to playground dashboard"
```

---

## Summary

| Task | What it builds | Effort |
|------|---------------|--------|
| 1 | VAD enrichment tool → annotates ~420 ATOs with valence/arousal/dominance | Medium |
| 2 | Engine aggregates VAD per message from marker detections | Low |
| 3 | UED metrics (home base, variability, rise/recovery rate) | Low |
| 4 | Trust/conflict/deesc state indices from effect_on_state | Low |
| 5 | `/v1/analyze/dynamics` API endpoint | Low |
| 6 | Eval dynamics on gold corpus | Low |
| 7 | Playground dashboard with Chart.js charts | Medium |

Tasks 1-5 are the core. Tasks 6-7 are validation and visualization.

After completion: LeanDeep will produce emotion trajectories and relationship state tracking from pure regex detection — no LLM required. The same analysis depth that Grok/GPT achieved with the semiotic-dynamics skill, but deterministic, fast (~77ms/chunk), and reproducible.
