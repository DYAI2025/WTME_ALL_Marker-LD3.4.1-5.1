from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Any, Tuple, Iterable
import re
import yaml
import json
from pathlib import Path
from collections import defaultdict, deque

# -------- Dateien laden --------
def load_markers(path: str | Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
        except Exception:
            data = {}
    return data

def load_all_markers(root_dir: str) -> Dict[str, Any]:
    spec = {
        "atomic_markers": [],
        "semantic_markers": [],
        "cluster_markers": [],
        "meta_markers": [],
    }
    categories = {
        "ATO": "atomic_markers",
        "SEM": "semantic_markers",
        "CLU": "cluster_markers",
        "MEMA": "meta_markers",
    }
    root = Path(root_dir)
    for cat_dir, cat_key in categories.items():
        dir_path = root / cat_dir
        if dir_path.is_dir():
            for yaml_file in dir_path.glob("*.yaml"):
                marker = load_markers(yaml_file)
                if isinstance(marker, dict) and "id" in marker:
                    spec[cat_key].append(marker)
    meta_path = root / "metadata.yaml"
    if meta_path.is_file():
        spec["metadata"] = load_markers(meta_path)["metadata"]
    return spec

# -------- Index erstellen --------
@dataclass
class Registry:
    spec: Dict[str, Any]
    by_id: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    atomic_ids: Set[str] = field(default_factory=set)
    semantic_ids: Set[str] = field(default_factory=set)
    cluster_ids: Set[str] = field(default_factory=set)
    meta_ids: Set[str] = field(default_factory=set)

    @classmethod
    def build(cls, spec: Dict[str, Any]) -> "Registry":
        r = cls(spec=spec)
        for k, target in [
            ("atomic_markers", r.atomic_ids),
            ("semantic_markers", r.semantic_ids),
            ("cluster_markers", r.cluster_ids),
            ("meta_markers", r.meta_ids),
        ]:
            if k in spec and spec[k]:
                for m in spec[k]:
                    if not isinstance(m, dict) or "id" not in m:
                        continue
                    mid = m["id"]
                    r.by_id[mid] = m
                    target.add(mid)
        return r

# -------- Validierung --------
RULE_PATTERNS = {
    # deckt die im YAML verwendeten Regeln ab
    "BOTH_IN_N": re.compile(r"^\s*BOTH\s+IN\s+(\d+)\s+messages?\s*$", re.I),
    "AT_LEAST_X_IN_Y": re.compile(r"^\s*AT_LEAST\s+(\d+)\s+IN\s+(\d+)\s+messages?\s*$", re.I),
    "ANY_X_IN_Y": re.compile(r"^\s*ANY\s+(\d+)\s+IN\s+(\d+)\s+messages?\s*$", re.I),
    "AT_LEAST_X_DISTINCT_SEMs_IN_Y": re.compile(
        r"^\s*AT_LEAST\s+(\d+)\s+DISTINCT\s+SEMs\s+IN\s+(\d+)\s+messages?\s*$", re.I
    ),
}

class SpecError(Exception): ...

def validate_spec(reg: Registry) -> None:
    errors: List[str] = []

    # 1) Existenz und Duplikate
    if len(reg.by_id) == 0:
        errors.append("leere Konfiguration")

    # 2) SEM ≥2 ATO und IDs vorhanden
    for sid in reg.semantic_ids:
        s = reg.by_id[sid]
        comp = s.get("composed_of", [])
        if not isinstance(comp, list) or len(comp) == 0:
            errors.append(f"{sid}: composed_of fehlt oder leer")
            continue
        missing = [x for x in comp if x not in reg.by_id]
        if missing:
            errors.append(f"{sid}: unbekannte Marker in composed_of: {missing}")
        # SEM ≥2 ATO
        ato_count = sum(1 for x in comp if x.startswith("ATO_"))
        if ato_count < 2:
            errors.append(f"{sid}: SEM benötigt ≥2 ATO, gefunden {ato_count}")

    # 3) Aktivierungsregeln formell bekannt
    def _rule_ok(rule: str) -> bool:
        return any(pat.match(rule) for pat in RULE_PATTERNS.values())

    for group, ids in [
        ("semantic_markers", reg.semantic_ids),
        ("cluster_markers", reg.cluster_ids),
        ("meta_markers", reg.meta_ids),
    ]:
        for mid in ids:
            m = reg.by_id[mid]
            rule = (m.get("activation") or {}).get("rule")
            # Meta kann detect_class statt rule haben
            if rule is None:
                if "detect_class" in m:
                    continue
                # manche SEM nutzen nur composed_of, dann erzwingen wir rule
                errors.append(f"{mid}: activation.rule fehlt")
            else:
                if not _rule_ok(rule):
                    errors.append(f"{mid}: unbekanntes activation.rule '{rule}'")

    # 4) Intuitions-CLUs Telemetrie und Learning
    for cid in reg.cluster_ids:
        m = reg.by_id[cid]
        frame = m.get("frame", {})
        signals = set(map(str.lower, frame.get("signal", []))) if isinstance(frame.get("signal"), list) else set()
        if "intuition" in signals or cid.startswith("CLU_INTUITION_"):
            md = m.get("metadata", {}) or {}
            learning = (md.get("learning") or {})
            tele = (md.get("telemetry_keys") or {})
            alpha = learning.get("ewma_alpha")
            if alpha is None or not (0 < float(alpha) <= 1):
                errors.append(f"{cid}: learning.ewma_alpha fehlt oder ungültig")
            needed = {"counter_confirmed", "counter_retracted", "ewma_precision"}
            if not needed.issubset(tele.keys()):
                errors.append(f"{cid}: telemetry_keys unvollständig, benötigt {sorted(needed)}")
            # Zustandsmaschine Felder
            intu = (md.get("intuition") or {})
            for k in ["confirm_window", "decay_window", "confirm_rule"]:
                if k not in intu:
                    errors.append(f"{cid}: intuition.{k} fehlt")

    if errors:
        raise SpecError("\n".join(errors))

# -------- Aktivierungsregeln auswerten --------
def _window(messages: List[Set[str]], n: int) -> Iterable[List[Set[str]]]:
    if n <= 0:
        return []
    dq: deque = deque(maxlen=n)
    for msg in messages:
        dq.append(msg)
        if len(dq) == n:
            yield list(dq)

def evaluate_activation(rule: str, composed_of: List[str], messages: List[Set[str]]) -> bool:
    # messages: Liste von Sets mit Marker-IDs pro Nachricht
    if RULE_PATTERNS["BOTH_IN_N"].match(rule):
        n = int(RULE_PATTERNS["BOTH_IN_N"].match(rule).group(1))
        for win in _window(messages, n):
            present: Set[str] = set()
            for s in win:
                present |= (s & set(composed_of))
            if all(c in present for c in composed_of):
                return True
        return False

    if RULE_PATTERNS["AT_LEAST_X_IN_Y"].match(rule):
        x, y = map(int, RULE_PATTERNS["AT_LEAST_X_IN_Y"].match(rule).groups())
        for win in _window(messages, y):
            count = sum(1 for s in win for c in composed_of if c in s)
            if count >= x:
                return True
        return False

    if RULE_PATTERNS["ANY_X_IN_Y"].match(rule):
        x, y = map(int, RULE_PATTERNS["ANY_X_IN_Y"].match(rule).groups())
        for win in _window(messages, y):
            count = sum(1 for s in win for _ in s)  # irgendein Marker
            if count >= x:
                return True
        return False

    if RULE_PATTERNS["AT_LEAST_X_DISTINCT_SEMs_IN_Y"].match(rule):
        x, y = map(int, RULE_PATTERNS["AT_LEAST_X_DISTINCT_SEMs_IN_Y"].match(rule).groups())
        for win in _window(messages, y):
            seen = set()
            for s in win:
                seen |= {m for m in s if m.startswith("SEM_")}
            if len(seen & set(composed_of)) >= x:
                return True
        return False

    raise ValueError(f"unbekannte Regel: {rule}")

# -------- Intuitions-Zustand --------
@dataclass
class IntuitionState:
    state: str = "provisional"  # provisional | confirmed | decayed
    score: float = 0.0
    base: float = 0.5
    weight: float = 1.0
    multiplier_on_confirm: float = 1.5
    confirm_window: int = 5
    decay_window: int = 7
    confirm_rule: str = ""
    ewma_alpha: float = 0.1
    ewma_precision: float = 0.5

    def update_ewma(self, precision: float) -> None:
        a = self.ewma_alpha
        self.ewma_precision = a * precision + (1 - a) * self.ewma_precision

    def tick(self, activated: bool, window_msgs: List[Set[str]], confirm_ids: List[str]) -> None:
        # Score
        if activated:
            self.score += self.base * self.weight
        else:
            self.score *= 0.9

        # Bestätigung prüfen
        if self.state == "provisional":
            # confirm_rule gilt auf confirm_window
            ok = evaluate_activation(self.confirm_rule, confirm_ids, window_msgs[-self.confirm_window :]) if self.confirm_rule else False
            if ok:
                self.state = "confirmed"
                self.score *= self.multiplier_on_confirm
        # Verfall
        if not activated and self.state == "confirmed":
            # keine strenge Regel, einfacher Time-based Decay
            last = window_msgs[-self.decay_window :]
            any_support = any(any(mid in msg for mid in confirm_ids) for msg in last)
            if not any_support:
                self.state = "decayed"

# -------- Laufzeit-Hilfen --------
def compile_runtime(reg: Registry) -> Dict[str, Any]:
    """Erzeugt schnelle Lookups für composed_of und Regeln."""
    runtime = {"activation": {}, "composed_of": {}}
    for mid in reg.by_id:
        m = reg.by_id[mid]
        runtime["composed_of"][mid] = m.get("composed_of", [])
        rule = (m.get("activation") or {}).get("rule")
        if rule:
            runtime["activation"][mid] = rule
    return runtime

# -------- Beispielnutzung --------
def demo() -> None:
    spec = load_markers("markers/LEAN_DEEP_MARKERS.yaml")
    reg = Registry.build(spec)
    validate_spec(reg)
    rt = compile_runtime(reg)

    # synthetischer Chat: Sets je Nachricht mit getriggerten Marker-IDs
    msgs = [
        {"ATO_HESITATION", "ATO_DOUBT_PHRASE"},
        {"ATO_SADNESS_WORD", "ATO_SOFTENING"},
        {"ATO_ANGER_WORD", "ATO_BLAME_PHRASE"},
        {"SEM_ANGER_ESCALATION"},  # angenommen vom Upstream-Detektor gesetzt
        {"ATO_TRUST_PHRASE", "ATO_SUPPORT_PHRASE"},
    ]

    sem = "SEM_UNCERTAINTY_TONING"
    ok = evaluate_activation(rt["activation"][sem], rt["composed_of"][sem], msgs)
    print(f"{sem} aktiviert:", ok)

    # Intuition Beispiel
    clu = "CLU_INTUITION_CONFLICT"
    m = reg.by_id[clu]
    meta = m["metadata"]
    istate = IntuitionState(
        base=m["scoring"]["base"],
        weight=m["scoring"]["weight"],
        multiplier_on_confirm=meta["intuition"]["multiplier_on_confirm"],
        confirm_window=meta["intuition"]["confirm_window"],
        decay_window=meta["intuition"]["decay_window"],
        confirm_rule=meta["intuition"]["confirm_rule"],
        ewma_alpha=meta["learning"]["ewma_alpha"],
    )
    # Streaming-Update
    composed = rt["composed_of"][clu]
    rule = rt["activation"][clu]
    for i in range(len(msgs)):
        window = msgs[: i + 1]
        activated = evaluate_activation(rule, composed, window)
        istate.tick(activated, window, confirm_ids=["SEM_ANGER_ESCALATION"])
        istate.update_ewma(precision=1.0 if activated else 0.0)
    print("INT_CONFLICT:", istate.state, "score=", round(istate.score, 3), "ewma=", round(istate.ewma_precision, 3))

if __name__ == "__main__":
    demo()
