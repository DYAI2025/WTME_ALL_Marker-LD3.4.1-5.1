"""
LeanDeep Persona Profile System (Pro Tier).

Persistent YAML-based persona profiles with:
- EWMA warm-start across sessions
- Episode detection (escalation, repair, withdrawal, rupture, stabilization)
- Welford online mean/variance for VAD history
- Shift prediction reservoir with conditional distributions
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ruamel.yaml import YAML

from .config import settings

yaml = YAML()
yaml.default_flow_style = False
yaml.allow_unicode = True

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_MAX_EPISODES = 50


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _blank_persona(token: str, now: str) -> dict:
    return {
        "schema": "LeanDeep-Persona",
        "version": "1.0",
        "token": token,
        "created_at": now,
        "updated_at": now,
        "stats": {
            "session_count": 0,
            "total_messages": 0,
            "first_session": now,
            "last_session": now,
        },
        "speaker_ewma": {},
        "vad_history": {},
        "marker_frequencies": {},
        "family_distribution": {},
        "state_trajectory": {"trust": [], "conflict": [], "deesc": []},
        "episodes": [],
        "predictions": {
            "shift_counts": {"repair": 0, "escalation": 0, "volatility": 0, "none": 0},
            "shift_prior": {"repair": 0.0, "escalation": 0.0, "volatility": 0.0, "none": 1.0},
            "shift_given_valence_quartile": {},
            "top_transition_pairs": [],
        },
    }


class PersonaStore:
    """CRUD for persona YAML files with UUID path-traversal guard."""

    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir or settings.personas_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _validate_token(self, token: str) -> bool:
        return bool(_UUID_RE.match(token))

    def _path(self, token: str) -> Path:
        if not self._validate_token(token):
            raise ValueError(f"Invalid persona token: {token}")
        return self.base_dir / f"{token}.yaml"

    def create(self) -> dict:
        token = str(uuid.uuid4())
        now = _now_iso()
        persona = _blank_persona(token, now)
        with open(self._path(token), "w", encoding="utf-8") as f:
            yaml.dump(persona, f)
        return persona

    def get(self, token: str) -> dict | None:
        path = self._path(token)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return yaml.load(f)

    def save(self, persona: dict) -> None:
        token = persona["token"]
        persona["updated_at"] = _now_iso()
        with open(self._path(token), "w", encoding="utf-8") as f:
            yaml.dump(persona, f)

    def delete(self, token: str) -> bool:
        path = self._path(token)
        if not path.exists():
            return False
        path.unlink()
        return True

    def extract_warm_start(self, persona: dict) -> dict[str, dict[str, float]] | None:
        """Extract warm-start EWMA seeds from persona for engine use.

        Returns {role: {valence, arousal, dominance}} or None.
        """
        ewma = persona.get("speaker_ewma", {})
        if not ewma:
            return None
        result = {}
        for role, state in ewma.items():
            result[role] = {
                "valence": float(state.get("valence", 0)),
                "arousal": float(state.get("arousal", 0)),
                "dominance": float(state.get("dominance", 0)),
            }
        return result if result else None

    def accumulate_session(
        self,
        persona: dict,
        messages: list[dict],
        result: dict,
    ) -> dict:
        """Accumulate a session's data into the persona profile.

        Args:
            persona: The persona dict (mutated in place)
            messages: Raw messages [{role, text}, ...]
            result: Engine analyze_conversation result dict

        Returns:
            Dict with session summary info for the API response.
        """
        now = _now_iso()
        stats = persona["stats"]
        stats["session_count"] += 1
        stats["total_messages"] += len(messages)
        stats["last_session"] = now
        session_num = stats["session_count"]

        # --- Speaker EWMA update ---
        sb = result.get("speaker_baselines", {})
        speakers_data = sb.get("speakers", {})
        for role, info in speakers_data.items():
            bf = info.get("baseline_final", {})
            existing = persona["speaker_ewma"].get(role, {})
            prev_count = int(existing.get("message_count", 0))
            prev_sessions = int(existing.get("sessions_seen", 0))
            new_count = int(info.get("message_count", 0))

            if isinstance(bf, dict) and bf:
                v = float(bf.get("valence", 0))
                a = float(bf.get("arousal", 0))
                d = float(bf.get("dominance", 0))
            else:
                v = float(getattr(bf, "valence", 0))
                a = float(getattr(bf, "arousal", 0))
                d = float(getattr(bf, "dominance", 0))

            if existing and prev_sessions > 0:
                # Blend: weight new session by 0.3, existing by 0.7
                alpha = 0.3
                v = round(float(existing.get("valence", 0)) * (1 - alpha) + v * alpha, 3)
                a = round(float(existing.get("arousal", 0)) * (1 - alpha) + a * alpha, 3)
                d = round(float(existing.get("dominance", 0)) * (1 - alpha) + d * alpha, 3)

            persona["speaker_ewma"][role] = {
                "valence": v,
                "arousal": a,
                "dominance": d,
                "message_count": prev_count + new_count,
                "sessions_seen": prev_sessions + 1,
            }

        # --- VAD history (Welford online mean/variance) ---
        message_vad = result.get("message_vad", [])
        for msg_idx, msg in enumerate(messages):
            role = msg.get("role", "?")
            vad = message_vad[msg_idx] if msg_idx < len(message_vad) else None
            if not vad:
                continue
            v = float(vad.get("valence", vad.valence if hasattr(vad, "valence") else 0))
            a = float(vad.get("arousal", vad.arousal if hasattr(vad, "arousal") else 0))
            d = float(vad.get("dominance", vad.dominance if hasattr(vad, "dominance") else 0))

            hist = persona["vad_history"].setdefault(role, {
                "valence_mean": 0, "valence_var": 0,
                "arousal_mean": 0, "arousal_var": 0,
                "dominance_mean": 0, "dominance_var": 0,
                "n": 0,
            })
            n = int(hist["n"]) + 1
            for dim, val in [("valence", v), ("arousal", a), ("dominance", d)]:
                old_mean = float(hist[f"{dim}_mean"])
                new_mean = old_mean + (val - old_mean) / n
                old_var = float(hist[f"{dim}_var"])
                new_var = old_var + (val - old_mean) * (val - new_mean)
                hist[f"{dim}_mean"] = round(new_mean, 4)
                hist[f"{dim}_var"] = round(new_var, 4)
            hist["n"] = n

        # --- Marker frequencies ---
        for det in result.get("detections", []):
            mid = det.marker_id if hasattr(det, "marker_id") else det.get("marker_id", det.get("id", ""))
            if mid:
                persona["marker_frequencies"][mid] = persona["marker_frequencies"].get(mid, 0) + 1

        # --- Family distribution (EWMA-blended) ---
        session_families: dict[str, int] = {}
        for det in result.get("detections", []):
            fam = det.family if hasattr(det, "family") else det.get("family")
            if fam:
                session_families[fam] = session_families.get(fam, 0) + 1
        total_fam = sum(session_families.values()) or 1
        session_dist = {f: c / total_fam for f, c in session_families.items()}
        alpha_fam = 0.3
        for fam, prop in session_dist.items():
            old = float(persona["family_distribution"].get(fam, prop))
            persona["family_distribution"][fam] = round(old * (1 - alpha_fam) + prop * alpha_fam, 3)

        # --- State trajectory ---
        si = result.get("state_indices", {})
        for key in ("trust", "conflict", "deesc"):
            persona["state_trajectory"].setdefault(key, []).append(
                round(float(si.get(key, 0)), 3)
            )

        # --- Episode detection ---
        per_message_delta = sb.get("per_message_delta", [])
        new_episodes = _detect_episodes(
            session_num, messages, message_vad, per_message_delta, si, result.get("detections", [])
        )
        episodes = persona.get("episodes", [])
        episodes = new_episodes + episodes  # newest first
        persona["episodes"] = episodes[:_MAX_EPISODES]

        # --- Prediction reservoir update ---
        _update_predictions(persona, per_message_delta, message_vad)

        # --- Save ---
        self.save(persona)

        # Build session summary
        predictions = persona.get("predictions", {})
        total_shifts = sum(predictions.get("shift_counts", {}).values())
        return {
            "session_number": session_num,
            "warm_start_applied": session_num > 1,
            "new_episodes": new_episodes,
            "state_snapshot": {
                "trust": round(float(si.get("trust", 0)), 3),
                "conflict": round(float(si.get("conflict", 0)), 3),
                "deesc": round(float(si.get("deesc", 0)), 3),
            },
            "prediction_available": total_shifts >= 5,
        }


def _detect_episodes(
    session_num: int,
    messages: list[dict],
    message_vad: list[dict],
    per_message_delta: list[dict | None],
    state_indices: dict,
    detections: list,
) -> list[dict]:
    """Heuristic detection of 5 episode types from session data."""
    episodes: list[dict] = []
    n = len(messages)
    if n < 3:
        return episodes

    # Collect VAD values
    vals = []
    aros = []
    for i, vad in enumerate(message_vad):
        if isinstance(vad, dict):
            vals.append(float(vad.get("valence", 0)))
            aros.append(float(vad.get("arousal", 0)))
        else:
            vals.append(float(getattr(vad, "valence", 0)))
            aros.append(float(getattr(vad, "arousal", 0)))

    # Collect shifts
    shifts = []
    for d in per_message_delta:
        if d is None:
            shifts.append(None)
        elif isinstance(d, dict):
            shifts.append(d.get("shift"))
        else:
            shifts.append(getattr(d, "shift", None))

    # Collect marker IDs
    marker_ids = set()
    for det in detections:
        mid = det.marker_id if hasattr(det, "marker_id") else det.get("marker_id", det.get("id", ""))
        if mid:
            marker_ids.add(mid)

    ep_counter = 0

    def _make_ep(ep_type: str, duration: int, markers: list[str], vad_d: dict, entry: dict, exit_: dict):
        nonlocal ep_counter
        ep_counter += 1
        return {
            "id": f"ep_{session_num:03d}_{ep_counter:02d}",
            "type": ep_type,
            "session": session_num,
            "duration_messages": duration,
            "markers_involved": markers[:10],
            "vad_delta": vad_d,
            "state_at_entry": entry,
            "state_at_exit": exit_,
        }

    state_entry = {
        "trust": round(float(state_indices.get("trust", 0)), 3),
        "conflict": round(float(state_indices.get("conflict", 0)), 3),
    }

    # 1. escalation_cluster: >=3 escalation shifts in <=8 messages
    esc_indices = [i for i, s in enumerate(shifts) if s == "escalation"]
    if len(esc_indices) >= 3:
        for start_idx in range(len(esc_indices) - 2):
            span = esc_indices[start_idx + 2] - esc_indices[start_idx]
            if span <= 8:
                duration = span + 1
                v_delta = vals[min(esc_indices[start_idx + 2], n - 1)] - vals[esc_indices[start_idx]]
                a_delta = aros[min(esc_indices[start_idx + 2], n - 1)] - aros[esc_indices[start_idx]]
                episodes.append(_make_ep(
                    "escalation_cluster", duration, sorted(marker_ids)[:5],
                    {"valence": round(v_delta, 3), "arousal": round(a_delta, 3)},
                    state_entry, state_entry,
                ))
                break

    # 2. repair_trend: net valence delta > +0.20 after negative start
    if vals and vals[0] < -0.1:
        net_delta = vals[-1] - vals[0]
        if net_delta > 0.20:
            episodes.append(_make_ep(
                "repair_trend", n, sorted(marker_ids)[:5],
                {"valence": round(net_delta, 3), "arousal": round(aros[-1] - aros[0], 3)},
                state_entry, state_entry,
            ))

    # 3. withdrawal_phase: >55% messages with low arousal + negative valence
    if n >= 4:
        withdrawal_count = sum(
            1 for i in range(n)
            if i < len(vals) and i < len(aros)
            and vals[i] < 0 and aros[i] < 0.35
        )
        if withdrawal_count / n > 0.55:
            episodes.append(_make_ep(
                "withdrawal_phase", n, sorted(marker_ids)[:5],
                {"valence": round(sum(vals) / n, 3), "arousal": round(sum(aros) / n, 3)},
                state_entry, state_entry,
            ))

    # 4. rupture: single spike dv < -0.35 AND arousal > 0.7
    for i in range(1, n):
        if i < len(vals) and i < len(aros):
            dv = vals[i] - vals[i - 1]
            if dv < -0.35 and aros[i] > 0.7:
                episodes.append(_make_ep(
                    "rupture", 1, sorted(marker_ids)[:5],
                    {"valence": round(dv, 3), "arousal": round(aros[i], 3)},
                    state_entry, state_entry,
                ))
                break

    # 5. stabilization: deesc increasing across session halves
    if n >= 6:
        mid = n // 2
        first_half_vals = vals[:mid]
        second_half_vals = vals[mid:]
        first_half_aros = aros[:mid]
        second_half_aros = aros[mid:]
        if first_half_vals and second_half_vals:
            first_var = sum(abs(v) for v in first_half_vals) / len(first_half_vals)
            second_var = sum(abs(v) for v in second_half_vals) / len(second_half_vals)
            first_aro = sum(first_half_aros) / len(first_half_aros)
            second_aro = sum(second_half_aros) / len(second_half_aros)
            if second_var < first_var * 0.8 and second_aro < first_aro:
                episodes.append(_make_ep(
                    "stabilization", n, sorted(marker_ids)[:5],
                    {"valence": round(sum(vals) / n, 3), "arousal": round(second_aro - first_aro, 3)},
                    state_entry, state_entry,
                ))

    return episodes


def _update_predictions(
    persona: dict,
    per_message_delta: list[dict | None],
    message_vad: list[dict],
) -> None:
    """Update the prediction reservoir with shift counts and conditional distributions."""
    predictions = persona.setdefault("predictions", {
        "shift_counts": {"repair": 0, "escalation": 0, "volatility": 0, "none": 0},
        "shift_prior": {"repair": 0.0, "escalation": 0.0, "volatility": 0.0, "none": 1.0},
        "shift_given_valence_quartile": {},
        "top_transition_pairs": [],
    })

    counts = predictions["shift_counts"]

    # Count shifts in this session
    for d in per_message_delta:
        if d is None:
            counts["none"] = counts.get("none", 0) + 1
            continue
        shift = d.get("shift") if isinstance(d, dict) else getattr(d, "shift", None)
        if shift and shift in counts:
            counts[shift] = counts.get(shift, 0) + 1
        else:
            counts["none"] = counts.get("none", 0) + 1

    # Update priors
    total = sum(counts.values()) or 1
    predictions["shift_prior"] = {
        k: round(v / total, 3) for k, v in counts.items()
    }

    # Conditional distributions by valence quartile
    # Classify each message's valence into quartile (0=most negative, 3=most positive)
    quartile_shifts: dict[str, dict[str, int]] = predictions.get("shift_given_valence_quartile", {})
    # Ensure we have dicts not ruamel CommentedMaps for safety
    for qk in list(quartile_shifts.keys()):
        quartile_shifts[qk] = dict(quartile_shifts[qk])

    for i, d in enumerate(per_message_delta):
        if d is None or i >= len(message_vad):
            continue
        vad = message_vad[i]
        v = float(vad.get("valence", 0) if isinstance(vad, dict) else getattr(vad, "valence", 0))
        # Quartile: 0=[-1,-0.5), 1=[-0.5,0), 2=[0,0.5), 3=[0.5,1]
        if v < -0.5:
            q = "0"
        elif v < 0:
            q = "1"
        elif v < 0.5:
            q = "2"
        else:
            q = "3"
        shift = (d.get("shift") if isinstance(d, dict) else getattr(d, "shift", None)) or "none"
        q_counts = quartile_shifts.setdefault(q, {"repair": 0, "escalation": 0, "volatility": 0, "none": 0})
        q_counts[shift] = q_counts.get(shift, 0) + 1

    # Normalize quartile distributions
    for q, qc in quartile_shifts.items():
        qt = sum(qc.values()) or 1
        quartile_shifts[q] = {k: round(v / qt, 3) for k, v in qc.items()}

    predictions["shift_given_valence_quartile"] = quartile_shifts

    # Top transition pairs: track consecutive marker pairs
    # (simplified — we track from marker_frequencies changes)
    # Keep existing pairs, no complex tracking needed for MVP
