Präambel (Preflight)

Ziel: Pipeline reparieren, damit alle weiteren Schritte deterministisch testbar sind.

Gegebener Befund (Bestand des Repos):
938 Marker‑Dateien erfolgreich parsebar, 7 YAML‑Parserfehler, Klassen‑Counts: ATO 442 · SEM 298 · CLU 135 · MEMA 55, 18 IDs mit unkonventionellen Präfixen (z. B. EMO*, ACT*), 5 Dateiname↔ID‑Präfix‑Mismatches.
Zusätzlich: 29 SEM ohne composed_of, 95 SEM mit < 2 distinkten ATOs, 41 SEM→ATO‑Referenzen auf 57 nicht definierte ATO‑IDs, 40 CLU ohne composed_of, 16 CLU referenzieren ATO direkt, 18 CLU→unbekannte SEM‑Referenzen (24 fehlende SEM‑IDs), 9 SEM referenzieren SEM.
(Diese Zahlen stammen aus einer frischen Analyse des Markers‑ZIP.)

Preflight‑Fix (Task P0):
a) Die 7 YAML‑Fehler beheben (Sonderzeichen wie ↔, Anführungszeichen in Listen strikt quoten).
b) Basis‑Audit & CI‑Helfer ins Repo legen:

tools/audit_markers.py – vollständiger Statusbericht (Counts, Lücken).

tools/ci_check.py – harte CI‑Regeln (SEM ≥ 2 ATO, CLU→nur SEM, Examples ≥ 5).

tools/neg_examples_check.py – prüft mindestens 10 positive und 10 negative Beispiele (Iteration 3).
Akzeptanz: python tools/audit_markers.py läuft fehlerfrei; python tools/ci_check.py schlägt jetzt erwartungsgemäß an (Lücken sichtbar), YAML‑Parserfehler = 0.

Hinweis zu Regeln: SEM brauchen ≥ 2 distinkte ATO in composed_of; CLU aggregieren SEM\* über X‑of‑Y‑Fenster; Intuition bleibt CLU‑Klasse; examples Pflichtfeld. Diese Norm ist in LD 3.3/3.4/3.5 verbindlich.

Iteration 1 — Familien‑Packs schließen (Intuition + SEM‑Abdeckung je Family)

Inkrement‑Ziel: Alle Intuition‑Familien sind lauffähig und konsistent: CONSISTENCY, INCONSISTENCY, EFFICACY, SHUTDOWN, SUPPORT (optional: CONFLICT). Jede Familie hat: (1) 1 × CLU*INTUITION*<FAMILY> mit Confirm/Decay‑Fenstern & Telemetrie, (2) definierte Family‑SEMs als Input, (3) SEM‑Konformität (≥ 2 ATO), (4) Beispiele ≥ 5.

Umfang (Scope)

Intuition‑CLU pro Familie prüfen/erstellen (ID‑Konvention CLU*INTUITION*<FAMILY>).

Felder: activation.rule (X‑of‑Y auf Family‑SEMs), metadata.intuition mit confirm_window, confirm_rule, decay_window, multiplier_on_confirm, Telemetrie‑Keys.

Family‑SEMs kuratieren: je Familie mindestens 3 SEM‑Quellen mit ≥ 2 distinkten ATOs.

Fenster & Confirm‑Targets je Familie objektivieren (konkrete Regeln).

Smoke‑Tests auf Mini‑Korpora (synthetische Sequenzen, 5–10 pro Familie).

Vorgehen (Tasks)

T1.1 Family‑Audit
Tool: tools/family*audit.py (neu) – prüft je Familie: existiert CLU_INTUITION*\*, referenzierte SEM existieren, haben ≥ 2 ATO, examples ≥ 5.

# tools/family_audit.py (Kurzfassung)

# prüft je Familie: intuition-CLU vorhanden, SEM-Input valide, Fenster gesetzt

T1.2 Intuition‑CLU finalisieren
Für nicht vorhandene: Vorlagen anlegen (je Familie 1 Datei). Beispiel‑Skeleton:

id: CLU_INTUITION_INCONSISTENCY
version: "3.5"
frame: {signal: ["intuition"], concept: "Vorahnung: Inconsistency", narrative: "hypothesis"}
composed_of:

- SEM_FACT_CONFLICT
- SEM_TEMPORAL_CONFLICT
- SEM_ROLE_STABILITY_BREAK
  activation: { rule: "AT_LEAST 2 DISTINCT SEMs IN 5 messages" }
  scoring: { base: 0.5, weight: 1.0 }
  metadata:
  family: INCONSISTENCY
  intuition:
  confirm_window: 5
  confirm_rule: "AT_LEAST 1 of [SEM_FACT_CONFLICT, SEM_TEMPORAL_CONFLICT] IN confirm_window"
  decay_window: 8
  multiplier_on_confirm: 2.0
  telemetry_keys:
  counter_confirmed: "INT_INCON.confirmed"
  counter_retracted: "INT_INCON.retracted"
  ewma_precision: "INT_INCON.ewma_precision"
  examples: ["<min. 5 kurze Sequenzen>"]

(Analog für CONSISTENCY, EFFICACY, SHUTDOWN, SUPPORT.)

T1.3 Family‑SEMs komplettieren
Die 29 SEM ohne composed_of und die 95 SEM mit < 2 ATO priorisiert schließen – zuerst jene, die Family‑CLU speisen (z. B. SEM_FACT_CONFLICT, SEM_TEMPORAL_CONFLICT, SEM_ROLE_STABILITY_BREAK, SEM_SUPPORT_VALIDATION, SEM_SHUTDOWN_PATTERN, …).
Prinzip: jeweils mindestens 2 passende ATO (distinct!) anfügen oder fehlende ATO (Iteration 3) temporär über vorhandene ATO ersetzen, falls semantisch vertretbar.

T1.4 Fenster‑Feintuning je Family
Startwerte:

INCONSISTENCY: AT_LEAST 2 DISTINCT SEMs IN 5; Confirm‑Target: SEM_FACT_CONFLICT|SEM_TEMPORAL_CONFLICT; Decay = 8.

CONSISTENCY: AT_LEAST 3 SEMs IN 8; Confirm‑Target: stabile SEMs; Decay = 10.

EFFICACY: AT_LEAST 2 IN 6; Confirm: SEM_SELF_EFFICACY_STRONG.

SHUTDOWN: AT_LEAST 2 IN 4; Confirm: SEM_STONEWALLING|SEM_WITHDRAWAL.

SUPPORT: AT_LEAST 2 IN 5; Confirm: SEM_VALIDATION|SEM_EMPATHY.
Begründung: kompatibel zur 3.4‑Intuitionslogik (Provisional→Confirmed→Decayed, Multiplier).

T1.5 Mini‑Korpora & Smoke‑Tests
Für jede Familie 5–10 Kurzdialoge (synthetisch) beilegen und verifizieren, dass Provisional/Confirm/Decay wie erwartet feuert (Telemetrie‑Zähler steigen).

Definition of Done (DoD) – Iteration 1

python tools/audit*markers.py → keine Parserfehler; alle CLU_INTUITION*_ vorhanden (5 Familien), haben metadata.intuition._ und ≥ 5 Beispiele.

Alle Family‑SEMs, die in Intuition‑CLUs referenziert werden, haben ≥ 2 distinct ATO und ≥ 5 Beispiele.

Smoke‑Tests: Für jede Familie mindestens eine Confirm‑Sequenz (Telemet
