# Marker-Toolchain & Chrome-Extension

## Überblick
Dieses Repository bündelt alle Werkzeuge, um LeanDeep-3.4-Marker lokal zu pflegen, automatisch zu verknüpfen, zu evaluieren und per Chrome-Erweiterung live zu testen. Kernbestandteile sind:
- `markers/`: Quellen der Marker-YAMLs inklusive positiver und negativer Beispiele
- `dist/`: erzeugte Artefakte (z. B. `marker_registry.json`, `devset.jsonl`, Crawling-Exports)
- `tools/`: TypeScript-Skripte zum Verknüpfen, Validieren, Kompilieren, Evaluieren und Crawlen
- `extension/`: Manifest-v3-Erweiterung mit Worker-Engine, Hintergrundprozess, Content Script und Popup

## Voraussetzungen
- Node.js ≥ 18 (getestet mit v22)
- npm ≥ 9
- Optional: Python 3 & `curl` zum manuellen Download weiterer Modelle
- Internetzugang für `npm install`, Modell-Downloads, optionales Crawling

## Installation & Grundsetup
1. Repository klonen oder in das Arbeitsverzeichnis wechseln.
2. Abhängigkeiten installieren:
   ```bash
   npm install
   ```
3. Xenova-Embedding-Modell laden (einmalig):
   ```bash
   mkdir -p models/all-MiniLM-L6-v2/onnx
   curl -L https://huggingface.co/Xenova/all-MiniLM-L6-v2/resolve/main/config.json -o models/all-MiniLM-L6-v2/config.json
   curl -L https://huggingface.co/Xenova/all-MiniLM-L6-v2/resolve/main/tokenizer.json -o models/all-MiniLM-L6-v2/tokenizer.json
   curl -L https://huggingface.co/Xenova/all-MiniLM-L6-v2/resolve/main/tokenizer_config.json -o models/all-MiniLM-L6-v2/tokenizer_config.json
   curl -L https://huggingface.co/Xenova/all-MiniLM-L6-v2/resolve/main/special_tokens_map.json -o models/all-MiniLM-L6-v2/special_tokens_map.json
   curl -L https://huggingface.co/Xenova/all-MiniLM-L6-v2/resolve/main/vocab.txt -o models/all-MiniLM-L6-v2/vocab.txt
   curl -L https://huggingface.co/Xenova/all-MiniLM-L6-v2/resolve/main/onnx/model.onnx -o models/all-MiniLM-L6-v2/onnx/model.onnx
   ```
   > Hinweis: Die Download-URLs entsprechen dem Hugging-Face-Release. Alternativ kannst du `node --input-type=module -e "process.env.TRANSFORMERS_CACHE='models/all-MiniLM-L6-v2'; const { pipeline } = await import('@xenova/transformers'); await (await pipeline('feature-extraction','Xenova/all-MiniLM-L6-v2'))('warmup');"` ausführen.

## Marker bearbeiten & validieren
1. Marker ergänzen oder anlegen (`markers/*.yaml`). Lokale Negativbeispiele gehören in den jeweiligen Marker (`negatives:`).
2. Optional: globale Hard-Negatives in `negatives/hard_negatives.jsonl` pflegen.
3. Konsistenz prüfen:
   ```bash
   npx tsx tools/validate_markers.ts
   ```
   - Warnungen für zu wenige Beispiele werden ausgegeben, Fehler brechen ab.

## Auto-Verknüpfung & Registry-Build
1. Verknüpfen (`composed_of` automatisch auffüllen und säubern):
   ```bash
   npm run link:markers
   ```
   Bericht landet in `build/link_report.json`.
2. Registry erzeugen:
   ```bash
   npm run compile:markers
   ```
   Ergebnis: `dist/marker_registry.json` (Nutzung in Tests & Extension).

## Evaluation (Precision/Recall/F1)
1. Gold-Set prüfen oder erweitern (`dist/devset.jsonl`).
2. Evaluation starten:
   ```bash
   npm run eval
   ```
   Ausgabe: pro Klasse `P`, `R`, `F1`. Ziele: ATO/SEM Precision ≥ 0.85, Recall ≥ 0.70.

## Optional: Crawling & Active Learning
- Konfiguration (`crawler/config.yaml`) Whitelistet Domains, Rate Limits und Unsicherheits-Band.
- Crawlen & Labeln:
  ```bash
  npm run crawl -- https://example.org/artikel-1 https://forum.beispiel.de/thread
  ```
  Ergebnisse → `dist/crawl_labeled.jsonl`.
- Vorschlags-Merge (Top-Beispiele in `.autogen.yml`):
  ```bash
  npx tsx tools/merge_autogen.ts
  ```

## Chrome-Extension bauen & nutzen
1. Registry aktualisieren (`npm run compile:markers`).
2. Extension bauen:
   ```bash
   npm run build:ext
   ```
   Dabei werden `extension/dist/background.js`, `content-script.js`, `engine.worker.js`, `marker_registry.json` sowie `models/` bereitgestellt.
3. In Chrome laden:
   - `chrome://extensions` öffnen → „Entpackte Erweiterung laden“ → Ordner `extension/` wählen.
4. Verwendung:
   - Seiten werden automatisch analysiert, erkannte SEM/CLU-Marker im Content hervorgehoben.
   - Unsichere Fälle (Score 0.53–0.60) landen per `chrome.storage.local` in einer Review-Liste.
   - Popup „Unsichere Fälle exportieren“ → JSON-Download.

## Dateiüberblick (Auszug)
- `markers/` – Marker-Definitionen mit lokalen Negativbeispielen
- `negatives/hard_negatives.jsonl` – globaler Verwechslungs-Pool
- `dist/devset.jsonl` – Gold-Labels für Evaluation
- `tools/*.ts` – Automatisierungen (Linking, Registry, Eval, Crawl, Merge, Validate)
- `extension/src/` – TypeScript-Quellen für Background, Worker, Content Script, Popup, Styles
- `models/all-MiniLM-L6-v2/` – lokales Transformer-Modell für Embeddings (Xenova-Port)

## Tipps & Fehlersuche
- **ts-node/tsx Fehler**: Falls Pipes blockiert sind, Skripte mit Admin-Rechten (`sudo npm run …`) ausführen oder temporäre Ordner bereinigen.
- **Modell fehlt**: Sicherstellen, dass `models/all-MiniLM-L6-v2/onnx/model.onnx` vorhanden ist; ansonsten Download wiederholen.
- **CI/Validation**: `tools/validate_markers.ts` vor jedem Commit laufen lassen, um Feld-Typos zu verhindern.
- **Extension aktualisieren**: Nach Marker-Updates erneut `npm run compile:markers && npm run build:ext` ausführen und den Ordner in Chrome neu laden.
