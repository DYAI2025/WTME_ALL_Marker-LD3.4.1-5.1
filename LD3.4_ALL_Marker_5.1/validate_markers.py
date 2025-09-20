#!/usr/bin/env python3
import sys
import os
import glob
import yaml
from typing import Any, Dict, List, Tuple

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
MARKERS_ROOT = os.path.join(REPO_ROOT, 'ALL_Marker_5.1')
CLU_DIR = os.path.join(MARKERS_ROOT, 'CLU_cluster')

# Count examples for a marker dict
# Supports either list or dict (e.g. {positive: [...], negative: [...]})

def count_examples(marker: Dict[str, Any]) -> int:
    ex = marker.get('examples')
    if ex is None:
        return 0
    if isinstance(ex, list):
        return len(ex)
    if isinstance(ex, dict):
        total = 0
        for v in ex.values():
            if isinstance(v, list):
                total += len(v)
        return total
    return 0


ALLOWED_TOP_LEVEL_KEYS = {
    'schema','version','id','name','type','frame','tags','pattern','examples',
    'composed_of','activation','scoring','metadata','requires','inhibitors',
    'justification','telemetry'
}


def validate_container(file_path: str, data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    markers = data.get('markers')
    if not isinstance(markers, list):
        errors.append(f"{file_path}: 'markers' muss eine Liste sein")
        return errors

    # Warn/err: container-level examples should not exist
    if 'examples' in data:
        errors.append(f"{file_path}: examples auf Container-Ebene gefunden (werden ignoriert) – bitte in jeden Marker verschieben")

    for m in markers:
        if not isinstance(m, dict):
            errors.append(f"{file_path}: Eintrag in 'markers' ist kein Mapping")
            continue
        mid = m.get('id')
        if not mid or not isinstance(mid, str):
            errors.append(f"{file_path}: Marker ohne gültige id in 'markers'")
            continue
        # Lint: keine unbekannten Top-Level-Felder (außerhalb metadata)
        unknown = [k for k in m.keys() if k not in ALLOWED_TOP_LEVEL_KEYS and k != 'markers']
        if unknown:
            errors.append(f"{file_path}::{mid}: unbekannte Felder: {', '.join(sorted(unknown))}")

        if mid.startswith('CLU_INTUITION_'):
            # Pflichtbeispiele ≥5
            n = count_examples(m)
            if n < 5:
                errors.append(f"{file_path}::{mid}: hat nur {n} Beispiele (min. 5)")
            # metadata Pflicht
            if 'metadata' not in m:
                errors.append(f"{file_path}::{mid}: metadata fehlt")
            # type/name Pflicht
            if m.get('type') != 'CLU':
                errors.append(f"{file_path}::{mid}: type muss 'CLU' sein")
            name = m.get('name')
            if not isinstance(name, str) or not name.startswith('CLU_INTUITION_'):
                errors.append(f"{file_path}::{mid}: name fehlt oder verletzt Schema ^CLU_INTUITION_…$")
            # telemetry Keys + Schema
            tel = m.get('telemetry', {}) if isinstance(m.get('telemetry'), dict) else {}
            for k in ['counter_confirmed','counter_retracted','ewma_precision']:
                if k not in tel:
                    errors.append(f"{file_path}::{mid}: telemetry.{k} fehlt")
                else:
                    val = tel[k]
                    if not isinstance(val, str) or '.' not in val:
                        errors.append(f"{file_path}::{mid}: telemetry {k} Namensschema verletzt: {val}")
            # activation.confirm_window Pflicht ≥1
            act = m.get('activation', {}) if isinstance(m.get('activation'), dict) else {}
            cw = act.get('confirm_window')
            if not isinstance(cw, int) or cw < 1:
                errors.append(f"{file_path}::{mid}: activation.confirm_window fehlt oder < 1")
            # INCONSISTENCY: cooldown_messages ≥4 wenn Familie erkannt
            fam = None
            meta = m.get('metadata', {}) if isinstance(m.get('metadata'), dict) else {}
            fam = meta.get('family')
            if fam == 'INCONSISTENCY':
                cd = act.get('cooldown_messages')
                if not isinstance(cd, int) or cd < 4:
                    errors.append(f"{file_path}::{mid}: activation.cooldown_messages < 4 für Familie INCONSISTENCY")
    return errors


def validate_flat_clu(file_path: str, data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    mid = data.get('id', '')
    # Lint: keine unbekannten Top-Level-Felder (außer metadata)
    unknown = [k for k in data.keys() if k not in ALLOWED_TOP_LEVEL_KEYS]
    if unknown:
        errors.append(f"{file_path}::{mid or '(ohne id)'}: unbekannte Felder: {', '.join(sorted(unknown))}")

    if isinstance(mid, str) and mid.startswith('CLU_INTUITION_'):
        # Pflichtbeispiele
        n = count_examples(data)
        if n < 5:
            errors.append(f"{file_path}::{mid}: hat nur {n} Beispiele (min. 5)")
        # metadata Pflicht
        if 'metadata' not in data:
            errors.append(f"{file_path}::{mid}: metadata fehlt")
        # type/name Pflicht
        if data.get('type') != 'CLU':
            errors.append(f"{file_path}::{mid}: type muss 'CLU' sein")
        name = data.get('name')
        if not isinstance(name, str) or not name.startswith('CLU_INTUITION_'):
            errors.append(f"{file_path}::{mid}: name fehlt oder verletzt Schema ^CLU_INTUITION_…$")
        # telemetry Schema
        tel = data.get('telemetry', {}) if isinstance(data.get('telemetry'), dict) else {}
        for k in ['counter_confirmed','counter_retracted','ewma_precision']:
            if k not in tel:
                errors.append(f"{file_path}::{mid}: telemetry.{k} fehlt")
            else:
                val = tel[k]
                if not isinstance(val, str) or '.' not in val:
                    errors.append(f"{file_path}::{mid}: telemetry {k} Namensschema verletzt: {val}")
        # activation.confirm_window Pflicht
        act = data.get('activation', {}) if isinstance(data.get('activation'), dict) else {}
        cw = act.get('confirm_window')
        if not isinstance(cw, int) or cw < 1:
            errors.append(f"{file_path}::{mid}: activation.confirm_window fehlt oder < 1")
        # INCONSISTENCY cooldown >=4
        fam = (data.get('metadata') or {}).get('family') if isinstance(data.get('metadata'), dict) else None
        if fam == 'INCONSISTENCY':
            cd = act.get('cooldown_messages')
            if not isinstance(cd, int) or cd < 4:
                errors.append(f"{file_path}::{mid}: activation.cooldown_messages < 4 für Familie INCONSISTENCY")
    return errors


def main() -> int:
    clu_files = sorted(glob.glob(os.path.join(CLU_DIR, '*.y*ml')))
    all_errors: List[str] = []

    for path in clu_files:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except Exception as e:
            all_errors.append(f"{path}: YAML-Fehler: {e}")
            continue
        if not isinstance(data, dict):
            all_errors.append(f"{path}: Inhalt ist kein Mapping")
            continue

        if 'markers' in data:
            all_errors.extend(validate_container(path, data))
        else:
            all_errors.extend(validate_flat_clu(path, data))

    if all_errors:
        print("VALIDATION FAILED:")
        for e in all_errors:
            print("- ", e)
        return 1
    print("VALIDATION OK: Alle CLU-Marker erfüllen die Mindestbeispiel-Anforderung oder sind keine CLUs.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
