## Überblick

Dieses Repository enthält LeanDeep 3.4 Marker (YAML) sowie eine minimal lauffähige Extension‑Engine, die Marker lädt, wertet und Familien‑Hinweise (Hints) generiert.

- **Markerquellen**: `ALL_Marker_5.1/ATO_atomic`, `ALL_Marker_5.1/SEM_semantic`, `ALL_Marker_5.1/CLU_cluster`, `ALL_Marker_5.1/MEMA_meta`
- **Validator**: `validate_markers.py` (prüft aktuell CLU‑Marker)
- **Engine/Build**: `extension/src/*`, `tsup.config.ts`, `package.json`
- **Familien‑Konfiguration**: `markers/families.json`

## Schema (LeanDeep 3.4)

Top‑Level Felder, die je nach Marker‑Typ vorkommen können:

- **schema, version** (Pflicht): Kennzeichnen LeanDeep 3.4
- **id, type**: Eindeutige ID und Typ (`ATO|SEM|CLU`)
- **frame**: Enthält u. a. `concept`, `narrative`, `signal`
- **pattern** (optional): Regex/Pattern, v. a. in ATOs
- **examples**: Positive Beispiele (für CLU_INTUITION_* gelten Mindestmengen)
- **composed_of**: Zusammensetzung (SEM aus ATOs, CLU aus SEMs/Hints)
- **activation, scoring, metadata, telemetry**: Aktivierungsfenster, Gewichte, Zusatzinfos
- **negation_guard** (optional in ATO): Negationsschutz (siehe unten)

Beispiel ATO mit Negationsschutz:

```yaml
schema: "LeanDeep"
version: "3.4"
id: ATO_JOY_EXPRESSION
type: ATO
frame:
  concept: "Freude/Glück ausdrücken"
  narrative: "positive_affect"
  signal: ["Freude","erfreut","glücklich","Spaß","lacht","lächelt"]
pattern:
  regex: '(?i)\b(freude|erfreut\w*|gl(ü|ue)cklich|spa(ß|ss)\b|lach\w*|l(ä|ae)chel\w*)\b'
negation_guard:
  regex: '(?i)\b(nicht|kein|ohne)\b'
  window: 3
```

## Familien (Topics/Hinting)

Familien gruppieren **ATOs** und **SEMs** und definieren eine **Hint‑ID**. Wenn sich genügend ATOs einer Familie häufen, aber keine SEM derselben Familie feuert, erzeugt die Engine einen Familien‑Hint als schwache Evidenz.

Definition: `markers/families.json`

```json
{
  "positive_affect": {
    "atos": [
      "ATO_JOY_EXPRESSION",
      "ATO_POSITIVE_PREFERENCE",
      "ATO_SATISFACTION_STATE",
      "ATO_NONVERBAL_JOY_VERB",
      "ATO_POSITIVE_OUTLOOK_CUE"
    ],
    "sems": [
      "SEM_ACTIVE_ENJOYMENT",
      "SEM_STATE_OF_HAPPINESS",
      "SEM_EXPRESSED_SATISFACTION",
      "SEM_POSITIVE_OUTLOOK",
      "SEM_REPORTED_NONVERBAL_JOY",
      "SEM_POSITIVE_EMOTION_REGULATION"
    ],
    "hint_id": "HINT_POSITIVE_AFFECT"
  }
}
```

## Negationsschutz (ATO)

- **Ziel**: False‑Positives reduzieren, wenn Negation sehr nahe am Signal auftritt.
- **Felder**:
  - `negation_guard.regex`: Muster für Negationswörter
  - `negation_guard.window`: maximale Distanz in Tokens (heuristisch ~10 Zeichen je Token)

Die Engine verwirft ATO‑Treffer, wenn `negation_guard.regex` im Satz vorkommt und innerhalb des Fensters zur Signal‑Stelle liegt.

## Engine‑Logik (extension/src)

- **Embedding**: `@xenova/transformers` („all‑MiniLM‑L6‑v2“), Mean‑Pooling, normalisiert
- **Scoring**:
  - ATO: ab Score ≥ 0.60 (mit Negationsprüfung), „uncertain“ zwischen 0.53–0.60
  - SEM/CLU: ab Score ≥ 0.60
- **ATO→SEM**: SEM triggert, wenn mindestens 2 Einträge aus `composed_of` (oder alle, falls nur 1 definiert) in diesem Satz via ATOs getroffen wurden.
- **Fallback Familien‑Hint**: Wenn ≥3 ATOs einer Familie im Satz, aber keine SEM dieser Familie, wird `hint_id` emittiert.
- **CLU mit Hints**: CLUs akzeptieren Hints als schwache SEM. Es müssen ~60% der `composed_of` erreicht werden (mindestens 1).
- **Anti‑Inflation**:
  - Pro Satz zählt dieselbe ATO‑ID nur einmal (Cooldown)
  - Maximal 2 ATO‑Credits pro Lemma‑Stamm (`*_WORD|PHRASE|VERB` abgestrippt)

Einstiegspunkte:

- `extension/src/background.ts`: lädt `dist/registry.json` und `dist/families.json`, initiiert `engine.worker`
- `extension/src/engine.worker.ts`: Kernlogik; `scoreSentence()` liefert `{ ato, sem, clu, scores }`

## CLU‑Spezifika & Validierung

- Der Validator (`validate_markers.py`) prüft CLU‑Dateien in `ALL_Marker_5.1/CLU_cluster`:
  - `CLU_INTUITION_*`: mindestens 5 Beispiele, `metadata` Pflicht, `type: CLU`, `name` beginnt mit `CLU_INTUITION_…`, Telemetrieschlüssel vorhanden, `activation.confirm_window ≥ 1`
  - Familie `INCONSISTENCY`: `activation.cooldown_messages ≥ 4`

Hinweis: `CLU_INTUITION_WELLBEING` nutzt `HINT_POSITIVE_AFFECT` zusätzlich in `composed_of`.

## Build & Nutzung

Voraussetzungen: Node.js 18+, npm

```bash
npm run setup
npm run build:ext
```

Artefakte (automatisch erzeugt):

- `extension/dist/registry.json` (alle Marker zusammengeführt)
- `extension/dist/families.json` (aus `markers/` kopiert)
- `extension/dist/engine.worker.js`, `extension/dist/background.js`
- `extension/dist/devset.jsonl` (kleines Dev‑Set)

### Extension laden (Chrome, Manifest V3)

1. Chrome → Erweiterungen → Entwicklermodus aktivieren
2. „Entpackte Erweiterung laden“ → Ordner `extension/` auswählen
3. Hintergrunddienst (Service Worker) beobachten (Konsole), `ready`‑Event erscheint nach Init

## Tests (Devset)

Kleine Beispiele liegen in `extension/dist/devset.jsonl`:

```json
{"text":"Am glücklichsten bin ich, wenn ich mich geborgen fühle.","gold":["SEM_STATE_OF_HAPPINESS"]}
{"text":"Ich mag Rätsel und lerne gerne Neues.","gold":["SEM_ACTIVE_ENJOYMENT"]}
{"text":"Freude, Freude, Freude.","gold":["HINT_POSITIVE_AFFECT"]}
```

Die Datei dient als Smoke‑Test für ATO→SEM und Familien‑Hinting.

## Struktur

- `ALL_Marker_5.1/ATO_atomic/*`: atomare Marker (Regex/Signale)
- `ALL_Marker_5.1/SEM_semantic/*`: semantische Kompositionen aus ATOs
- `ALL_Marker_5.1/CLU_cluster/*`: Cluster/Intuitionen; akzeptieren auch Hints
- `ALL_Marker_5.1/MEMA_meta/*`: Meta‑Sequenzen
- `markers/families.json`: Familienkonfiguration (ATOs/SEMs→Hint)
- `extension/src/*`: Engine (Worker, Background), Registry‑Builder
- `extension/dist/*`: gebaute Artefakte
- `validate_markers.py`: CLU‑Validierung

## Erweiterung/Anpassung

- Neue ATOs/SEMs hinzufügen, Beispiele pflegen, ggf. `negation_guard` setzen
- Familien erweitern (`markers/families.json`) und neu bauen
- CLUs können Hints in `composed_of` mit berücksichtigen


