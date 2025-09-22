import pytest
import yaml
from markers_loader import Registry, validate_spec, SpecError, RULE_PATTERNS

@pytest.fixture(scope="module")
def spec():
    from markers_loader import load_all_markers
    return load_all_markers("spiral_persona")

def test_sem_has_two_atos(spec):
    reg = Registry.build(spec)
    errs = []
    for sid in reg.semantic_ids:
        comp = reg.by_id[sid].get("composed_of", [])
        ato_count = sum(1 for x in comp if x.startswith("ATO_"))
        if ato_count < 2:
            errs.append((sid, ato_count))
    assert not errs, f"SEM ≥2 ATO verletzt: {errs}"

def test_ids_exist(spec):
    reg = Registry.build(spec)
    missing = []
    for mid, m in reg.by_id.items():
        comp = m.get("composed_of", [])
        for x in comp:
            if x not in reg.by_id:
                missing.append((mid, x))
    assert not missing, f"unbekannte composed_of IDs: {missing}"

def test_rules_known(spec):
    reg = Registry.build(spec)
    bad = []
    for mid in reg.by_id:
        m = reg.by_id[mid]
        rule = (m.get("activation") or {}).get("rule")
        if rule:
            if not any(pat.match(rule) for pat in RULE_PATTERNS.values()):
                bad.append((mid, rule))
        else:
            # Meta mit detect_class zulassen
            if mid.startswith("SEM_") or mid.startswith("CLU_"):
                bad.append((mid, None))
    assert not bad, f"unbekannte oder fehlende Regeln: {bad}"

def test_intuition_clusters_have_telemetry(spec):
    reg = Registry.build(spec)
    problems = []
    for cid in reg.cluster_ids:
        m = reg.by_id[cid]
        frame = m.get("frame", {})
        signals = {s.lower() for s in frame.get("signal", [])} if isinstance(frame.get("signal"), list) else set()
        if "intuition" in signals or cid.startswith("CLU_INTUITION_"):
            md = m.get("metadata", {}) or {}
            tele = md.get("telemetry_keys") or {}
            learn = md.get("learning") or {}
            alpha = learn.get("ewma_alpha")
            if alpha is None or not (0 < float(alpha) <= 1):
                problems.append((cid, "ewma_alpha"))
            needed = {"counter_confirmed", "counter_retracted", "ewma_precision"}
            if not needed.issubset(set(tele.keys())):
                problems.append((cid, "telemetry_keys"))
            intu = md.get("intuition") or {}
            for k in ["confirm_window", "decay_window", "confirm_rule"]:
                if k not in intu:
                    problems.append((cid, f"intuition.{k}"))
    assert not problems, f"Intuitions-Metadaten unvollständig: {problems}"

def test_validate_spec_end_to_end(spec):
    reg = Registry.build(spec)
    validate_spec(reg)  # sollte ohne Exception laufen
