# SELF_CONSIST_MARKER

Dieses Verzeichnis enthält LeanDeep 3.4–konforme Marker, die Selbst‑Marker nach außen adaptieren (Konsistenzprüfung externer Sprecher).

- Namespace: `consistency_external`
- Datei: `CONSISTENCY_EXTERNAL.yaml`
- Ebenen: ATO → SEM → CLU → MEMA
- Intuition: CLU‑basierte Vorahnung mit `confirm/decay` und Telemetrie (EWMA)

Schnellstart

1) YAML laden (Schema `LeanDeep`, Version `3.4`).
2) Nachrichtenstruktur: `{ id, speaker, text, ts }`; `self` = Analysator, `other` = Ziel.
3) Nutze `CLU_CONSISTENCY_ALERT` für Hypothesen, `MEMA_INCONSISTENCY_TREND` für Trends.

Hinweise

- SEM kombinieren ≥2 ATOs (Regel 3.3); Ausnahmen nur mit `justification`.
- Intuitions‑Metadaten leben im `metadata`‑Block des CLU (Runtime).
- Beispiele ≥5 pro Marker für CI.
