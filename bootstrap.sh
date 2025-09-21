#!/usr/bin/env bash
set -euo pipefail

need_node=18
have_node=$(node -v | sed 's/v\([0-9]\+\).*/\1/')
if [ "$have_node" -lt "$need_node" ]; then
  echo "Node >=$need_node nötig. Gefunden: $(node -v)"; exit 1
fi

echo ">> Installiere Dependencies"
npm i

echo ">> Ordner anlegen"
mkdir -p negatives build dist extension/dist extension/dist/models

echo ">> Seeds"
[ -f negatives/hard_negatives.jsonl ] || cat > negatives/hard_negatives.jsonl <<'JSON'
{"text":"Ich akzeptiere die AGB.","label":"NONE","note":"kein Emotionskontext"}
{"text":"Schwarzbild am Monitor.","label":"NONE","note":"technisch, kein Shutdown"}
JSON

[ -f dist/devset.jsonl ] || cat > dist/devset.jsonl <<'JSON'
{"text":"Ich traue mir zu, das zu schaffen.","gold":["SEM_POSITIVE_SELF_EFFICACY"]}
{"text":"Ich stecke den Kopf in den Sand.","gold":["SEM_RESIGNATION_TENDENCY"]}
{"text":"Es wurde schwarz vor Augen.","gold":["SEM_SHUTDOWN_EPISODE"]}
{"text":"Ich akzeptiere die AGB.","gold":["NONE"]}
JSON

[ -f dist/review_state.json ] || echo "[]" > dist/review_state.json

echo ">> Validierung"
npm run validate

echo ">> Auto-Linking"
npm run link:markers

echo ">> Registry bauen"
npm run compile:markers

echo ">> Evaluation"
npm run eval || true

echo ">> Extension bauen"
npm run build:ext

echo "Fertig. Review-GUI: npm run review:gui  → http://localhost:5173"
