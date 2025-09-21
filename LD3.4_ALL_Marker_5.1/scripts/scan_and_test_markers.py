#!/usr/bin/env python3
import os
import re
import json
import glob
import yaml
from typing import Any, Dict, List, Tuple

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(REPO_ROOT)
MARKERS_ROOT = os.path.join(REPO_ROOT, 'ALL_Marker_5.1')
FAM_FILE = os.path.join(REPO_ROOT, 'markers', 'families.json')
OUT_DOC = os.path.join(REPO_ROOT, 'Test_docu.md')


def load_yaml_files(root: str) -> List[Tuple[str, Dict[str, Any]]]:
    paths = glob.glob(os.path.join(root, '**', '*.y*ml'), recursive=True)
    items = []
    for p in sorted(paths):
        try:
            with open(p, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            if isinstance(data, dict):
                items.append((p, data))
        except Exception as e:
            items.append((p, {'__error__': f'YAML-Fehler: {e}'}))
    return items


def compile_regex(pattern: str) -> Tuple[bool, str]:
    try:
        re.compile(pattern)
        return True, ''
    except re.error as e:
        return False, str(e)


def sentence_matches(pattern: str, sent: str) -> bool:
    try:
        return re.search(pattern, sent) is not None
    except re.error:
        return False


def proximity_negated(sent: str, guard_regex: str, signals: List[str], window_tokens: int = 3) -> bool:
    try:
        g = re.compile(guard_regex, re.I)
    except re.error:
        return False
    s_low = sent.lower()
    if not g.search(s_low):
        return False
    # Approximation: Fenster = window_tokens*10 Zeichen
    approx = window_tokens * 10
    idxN = g.search(s_low).start()
    for sig in signals or []:
        try:
            rg = re.compile(rf"\b{sig}\b", re.I)
        except re.error:
            continue
        m = rg.search(s_low)
        if not m:
            continue
        if abs(idxN - m.start()) <= approx:
            return True
    return False


def main() -> int:
    items = load_yaml_files(MARKERS_ROOT)
    with open(FAM_FILE, 'r', encoding='utf-8') as f:
        families = json.load(f)

    # Indexe
    by_id: Dict[str, Dict[str, Any]] = {}
    errors: List[str] = []
    for p, d in items:
        mid = d.get('id') if isinstance(d, dict) else None
        if isinstance(mid, str):
            by_id[mid] = d

    # Scans
    ato_results = []
    sem_results = []
    clu_results = []

    for p, d in items:
        if '__error__' in d:
            errors.append(f"{p}: {d['__error__']}")
            continue
        mid = d.get('id')
        mtype = d.get('type')
        schema_ok = (d.get('schema') == 'LeanDeep' and d.get('version') == '3.4')
        if not schema_ok:
            errors.append(f"{p}::{mid}: Schema/Version ungleich LeanDeep 3.4")

        if mtype == 'ATO':
            pat = ((d.get('pattern') or {}).get('regex'))
            if not isinstance(pat, str):
                errors.append(f"{p}::{mid}: pattern.regex fehlt")
                continue
            ok, msg = compile_regex(pat)
            if not ok:
                errors.append(f"{p}::{mid}: Regex-Fehler: {msg}")
            ex = d.get('examples') or []
            neg_ex = d.get('negatives') or []
            hits = sum(1 for s in ex if sentence_matches(pat, s))
            neg_guard = d.get('negation_guard') or {}
            neg_blocked = 0
            if isinstance(neg_guard, dict) and 'regex' in neg_guard:
                for s in neg_ex:
                    if proximity_negated(s, neg_guard['regex'], (d.get('frame') or {}).get('signal') or [], neg_guard.get('window', 3)):
                        neg_blocked += 1
            ato_results.append({
                'id': mid,
                'path': p,
                'examples_total': len(ex),
                'examples_matched': hits,
                'negatives_total': len(neg_ex),
                'negatives_blocked_by_guard': neg_blocked,
            })

        elif mtype == 'SEM':
            comp = d.get('composed_of') or []
            # Referenzen prüfen
            missing = [x for x in comp if x not in by_id]
            if missing:
                errors.append(f"{p}::{mid}: composed_of referenziert unbekannt: {missing}")
            # Beispiele bewerten: zähle ATO‑Treffer der referenzierten ATOs
            examples = d.get('examples') or []
            ato_pat = {}
            for aid in comp:
                a = by_id.get(aid) or {}
                rg = ((a.get('pattern') or {}).get('regex'))
                if isinstance(rg, str):
                    ato_pat[aid] = re.compile(rg, re.I)
            sem_ok = []
            for s in examples:
                cnt = 0
                for aid, rg in ato_pat.items():
                    if rg.search(s):
                        cnt += 1
                sem_ok.append({'text': s, 'ato_hits': cnt})
            sem_results.append({'id': mid, 'path': p, 'examples': sem_ok, 'need': max(1, min(2, len(comp)))})

        elif mtype == 'CLU':
            comp = d.get('composed_of') or []
            missing = [x for x in comp if x not in by_id and not x.startswith('HINT_')]
            if missing:
                errors.append(f"{p}::{mid}: composed_of referenziert unbekannt: {missing}")
            clu_results.append({'id': mid, 'path': p, 'composed_of': comp})

    # Familien‑Hint‑Machbarkeit
    fam_findings = []
    for fname, fam in families.items():
        fam_atos = fam.get('atos', [])
        fam_sems = fam.get('sems', [])
        any1_sems = []
        for sid in fam_sems:
            s = by_id.get(sid) or {}
            rule = (s.get('activation') or {}).get('rule', '')
            if isinstance(rule, str) and rule.strip().upper().startswith('ANY'):
                any1_sems.append(sid)
        # prüfe, ob 3 unterschiedliche ATOs ohne Trigger einer ANY‑1‑SEM möglich sind
        # Näherung: Wenn jede ATO einem ANY‑1‑SEM exklusiv zugeordnet ist, ist Hint unrealistisch
        atos_avoiding_any = []
        for aid in fam_atos:
            triggers_any = False
            for sid in any1_sems:
                s = by_id.get(sid) or {}
                if aid in (s.get('composed_of') or []):
                    triggers_any = True
                    break
            if not triggers_any:
                atos_avoiding_any.append(aid)
        hint_possible = len(set(atos_avoiding_any)) >= 3
        fam_findings.append({
            'family': fname,
            'hint_id': fam.get('hint_id'),
            'any1_sems': any1_sems,
            'atos_without_any1': atos_avoiding_any,
            'fallback_hint_feasible_with_3_atos': hint_possible,
        })

    # Komplexe Testfälle (generiert)
    complex_tests: List[Dict[str, Any]] = []
    # 1) Für jede SEM mit >=2 composed_of: kombiniere Beispiel‑Schnipsel
    for sid, s in by_id.items():
        if s.get('type') != 'SEM':
            continue
        comp = s.get('composed_of') or []
        if len(comp) >= 2:
            parts = []
            for aid in comp[:3]:
                a = by_id.get(aid) or {}
                ex = (a.get('examples') or [None])[0]
                if isinstance(ex, str):
                    parts.append(ex.rstrip('.'))
            if parts:
                txt = ' '.join(parts) + '.'
                complex_tests.append({'expected': sid, 'text': txt, 'note': 'SEM Komposition (>=2) kombiniert'})
    # 2) Familien‑Hint‑Kandidat (wenn möglich): 3 ATOs aus einer Familie ohne ANY‑1‑SEM
    for f in fam_findings:
        if not f['fallback_hint_feasible_with_3_atos']:
            continue
        aids = f['atos_without_any1'][:3]
        parts = []
        for aid in aids:
            a = by_id.get(aid) or {}
            ex = (a.get('examples') or [None])[0]
            if isinstance(ex, str):
                parts.append(ex.rstrip('.'))
        if parts:
            txt = ' '.join(parts) + '.'
            complex_tests.append({'expected': f['hint_id'], 'text': txt, 'note': 'Familien‑Hint (>=3 ATO) ohne ANY‑1‑SEM'})

    # Dokument schreiben
    lines: List[str] = []
    lines.append('## Marker Scan & Test – Inconsistency & Plausibility')
    lines.append('')
    lines.append('### Zusammenfassung')
    lines.append(f"- Gesamtdateien: {len(items)}")
    lines.append(f"- ATO geprüft: {sum(1 for _,d in items if d.get('type')=='ATO')}")
    lines.append(f"- SEM geprüft: {sum(1 for _,d in items if d.get('type')=='SEM')}")
    lines.append(f"- CLU geprüft: {sum(1 for _,d in items if d.get('type')=='CLU')}")
    lines.append('')

    if errors:
        lines.append('### Fehler / Inkonsistenzen')
        for e in errors:
            lines.append(f"- {e}")
        lines.append('')

    lines.append('### ATO Ergebnis (Regex‑Abdeckung & Negation)')
    for r in ato_results:
        lines.append(f"- {r['id']}: Beispiele {r['examples_matched']}/{r['examples_total']}, Negationen blockiert {r['negatives_blocked_by_guard']}/{r['negatives_total']}")
    lines.append('')

    lines.append('### SEM Ergebnis (approx. ATO‑Treffer pro Beispiel)')
    for r in sem_results:
        ok_count = sum(1 for e in r['examples'] if e['ato_hits'] >= r['need'])
        lines.append(f"- {r['id']}: {ok_count}/{len(r['examples'])} Beispiele erfüllen Komposition (benötigt {r['need']})")
        bad = [e for e in r['examples'] if e['ato_hits'] < r['need']]
        for b in bad[:3]:
            lines.append(f"  - Schwach: hits={b['ato_hits']} :: {b['text']}")
    lines.append('')

    lines.append('### Familien‑Hint‑Machbarkeit')
    for f in fam_findings:
        feas = 'JA' if f['fallback_hint_feasible_with_3_atos'] else 'NEIN'
        lines.append(f"- {f['family']} → Hint {f['hint_id']}: machbar mit 3 ATOs ohne ANY‑1‑SEM: {feas}")
        if f['any1_sems']:
            lines.append(f"  - ANY‑1‑SEMs: {', '.join(f['any1_sems'])}")
        if f['atos_without_any1']:
            lines.append(f"  - ATOs ohne ANY‑1‑Bindung: {', '.join(f['atos_without_any1'])}")
    lines.append('')

    lines.append('### Komplexe Testfälle (generiert)')
    for t in complex_tests:
        lines.append(f"- Erwartet: {t['expected']} :: {t['note']}")
        lines.append(f"  Text: {t['text']}")
    lines.append('')

    with open(OUT_DOC, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"OK: Test_docu.md geschrieben – {OUT_DOC}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())


