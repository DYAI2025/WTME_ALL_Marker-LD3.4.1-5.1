# Changelog
Alle relevanten Änderungen an diesem Repository werden in diesem Dokument festgehalten.

## 2025-09-21
- Initiale Toolchain-Struktur aufgebaut (`markers/`, `tools/`, `models/`, `extension/`, `negatives/`, `dist/`).
- NPM-Projekt mit `tsx`-gestützten Skripten für Auto-Linking, Registry-Build, Evaluation und Crawling eingerichtet.
- LeanDeep-3.4-Marker inklusive negativer Beispiele ergänzt und `dist/marker_registry.json` erzeugt.
- Xenova-Modell `all-MiniLM-L6-v2` lokal gebündelt (config, Tokenizer, Vokabular, ONNX-Gewichte).
- Chrome-Extension (Manifest v3) implementiert: Hintergrundservice, Worker-Engine, Content Script, Popup & Styles.
- Dokumentation erweitert: deutschsprachiges README mit Installations- & Nutzungsschritten, Active-Learning-Workflow.
- Bootstrap-Workflow (`npm run setup`) sowie Review-GUI (`npm run review:gui`) hinzugefügt – inkl. Express-Server, HTML-Frontend und automatischer Übernahme akzeptierter Beispiele.
