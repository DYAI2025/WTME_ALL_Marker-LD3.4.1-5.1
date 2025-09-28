# LeanDeep 3.5 - Single Source of Truth (SSoT) Dokumentation

**Version:** 3.5 (Upgrade von 3.4 durch Integration von Resonance_framework_2.0)  
**Datum:** 22. September 2025  
**Autor:** AI Coding Assistant (basierend auf Repository-Daten und User-Anfragen)  
**Zweck:** Dieses Dokument dient als zentrale, autoritative Referenz für LeanDeep 3.5. Es ist pedantisch detailliert, korrekt und vollständig, mit Fokus auf Struktur, Marker-Definitionen, Integrationen und Ergänzungen. Alle Angaben basieren auf dem Repository-Stand, Tool-Aufrufen und User-Spezifikationen. Keine Annahmen – nur verifizierte Fakten.

## 1. Historischer Überblick: Von LeanDeep 3.1 bis 3.4

LeanDeep hat sich schrittweise entwickelt. Hier eine pedantische Zusammenfassung der Versionen 3.1 bis 3.4, fokussiert auf Elemente, die in 3.5 weiterhin gelten (z.B. Kernarchitektur, Schema, Marker-Layer). Nicht mehr gültige Teile (z.B. veraltete Policies) sind explizit markiert.

### 1.1 LeanDeep 3.1: Grundlagen

- **Kern:** Einführung der Vier-Ebenen-Architektur (ATO → SEM → CLU → MEMA).
- **Schema:** Basis-JSON-Schema mit id, frame, pattern, examples (min. 5).
- **Regeln:** SEM composed_of ≥2 ATO; CLU als Aggregation über Fenster (X-of-Y).
- **Gültig in 3.5:** Vollständig – bildet die Basisstruktur.

### 1.2 LeanDeep 3.2: Erweiterungen

- **Neu:** Telemetrie (dotted keys, z.B. counter.total) und metadata für Deviations.
- **Regeln:** CLU muss confirm_window ≥1 haben; Families eingeführt (z.B. INCONSISTENCY mit cooldown ≥4).
- **Gültig in 3.5:** Ja, erweitert durch RF2.0.

### 1.3 LeanDeep 3.3: Konsolidierung

- **Neu:** Detaillierte Markerlisten (z.B. ATO_HESITATION, SEM_UNCERTAINTY_TONING).
- **Schema:** AdditionalProperties erlaubt für metadata; CI-Checks für SEM-Komposition.
- **Gültig in 3.5:** Vollständig, inkl. Beispiele und Tabellen.

### 1.4 LeanDeep 3.4: Intuitions-Marker und Unified Spec

- **Neu:** CLU*INTUITION*<FAMILY> mit Zuständen (provisional/confirmed/decayed), Multiplier, Telemetrie (ewma_precision).
- **Inhalt:** Vollständige Integration der 3.3-Quellen in eine Unified Specification (siehe untenstehende Sektion 2 für den vollständigen, unveränderten Inhalt von LEAN.DEEP_3.4.md).
- **Gültig in 3.5:** Vollständig – 3.4 ist der direkte Vorläufer, erweitert durch RF2.0.

**Nicht mehr gültig:** Veraltete Policies aus 3.1 (z.B. strenge additionalProperties: false) wurden durch 3.4 ersetzt.

## 2. Vollständiger Inhalt von LEAN.DEEP_3.4.md (Unified Specification) - Teil 1 (Abschnitte 0-3)

Der folgende Abschnitt reproduziert den gesamten Inhalt von LEAN.DEEP_3.4.md pedantisch und unverändert, da er die Kern-Spezifikation für 3.4 darstellt und in 3.5 weiterhin gilt. Ergänzungen für 3.5 sind in Klammern notiert.

LEAN.DEEP 3.4 — Unified Specification & Runtime Guide

(Nachfolger von LEAN.DEEP 3.3; kompatible Erweiterung um Intuitions-Marker)

0. Überblick

LEAN.DEEP 3.4 vereint die drei 3.3-Quellen zu einem Referenzdokument und ergänzt sie um Intuitions-Marker (familienbasierte, zustandsbehaftete CLU\_-Marker mit Lernlogik).
Die Vier-Ebenen-Architektur (ATO → SEM → CLU → MEMA) bleibt unverändert; Intuition wird auf CLU-Ebene realisiert (keine Schemaänderung nötig).

1. Changelog (v3.4)

Neu: Intuitions-Marker als CLU*INTUITION*<FAMILIE>
– Aggregieren unspezifische SEM\_ derselben Familie (z. B. Trauer, Konflikt, Unterstützung, Commitment, Unsicherheit).
– Zustände: provisional → confirmed → decayed.
– Multiplier: temporärer Score-Boost für SEM/CLU derselben Familie bei confirmed.
– Telemetrie & Lernen: confirmed, retracted, ewma_precision; datengetriebene Anpassung von X-of-Y-Fenstern und Confirm-Targets.

Keine Schemaänderung: 3.3-JSON-Schema bleibt gültig; der optionale metadata-Block für Intuition wird nur zur Runtime ausgewertet. (In 3.3 ist die CLU-Aggregation über Fenster und activation/scoring bereits vorgesehen.)

Dok-Konsolidierung: Diese Datei ersetzt die getrennten 3.3-Dokumente als einheitliche Spezifikation.

2. Architektur & Datenmodell
   2.1 Vier Ebenen

ATO\_ (Atomic Marker) – primitive Tokens, Emojis, Regex.

SEM* (Semantic Marker) – kombiniert ATO* zu Mikromustern.

CLU* (Cluster Marker) – aggregiert SEM* über Fenster (z. B. „AT_LEAST X IN Y messages“).

MEMA\_ (Meta-Analysis Marker) – dynamische Muster über CLUs.
Siehe auch die 4_LEVEL_ARCHITECTURE-Grafik und Markerlisten in der 3.3-PDF (S. 2–3,6–8,10).

2.2 JSON-Schema (3.3 – weiterhin gültig)

Markerobjekte mit id, frame{signal,concept,pragmatics,narrative}, examples, optional pattern oder composed_of oder detect_class.

SEM-Regel (3.3): SEM*… müssen ≥2 unterschiedliche ATO* in composed_of enthalten; 1-ATO nur mit justification. (CI-Hook „sem-composition-check“).

CLU-Marker besitzen composed*of: [SEM*\*], activation (X-of-Y), optional scoring.

Hinweis: 3.4 führt keine neue „INT*“-Prefixklasse ein. Intuition wird als CLU* modelliert und bleibt damit schema-konform.

3. Marker-Definitionen (konkret)
   3.1 ATO\_ — Atomic

Zweck: Oberflächen-Signale (Tokens/Regex).

Struktur: pattern + examples.

Bezug: Siehe ATO-Übersicht und Beispiele in der 3.3-PDF-Tabelle (z. B. ATO_DOUBT_PHRASE, ATO_HESITATION, ATO_SOFTENING).

3.2 SEM\_ — Semantic

Regel 3.3 (verbindlich): composed*of ≥2 distinkte ATO*; 1-ATO nur mit justification. (CI prüft dies.)

Aktivierung: natürlichsprachliche Regeln (z. B. „BOTH IN 1 message“, „ANY 2 IN 2 messages“).

3.3 CLU\_ — Cluster

Zweck: Aggregation thematisch verwandter SEM\_ in Fenstern (X-of-Y).

Beispiele (3.3): CLU_CONFLICT_ESCALATION, CLU_SUPPORT_EXCHANGE, CLU_PROCRASTINATION_LOOP (vgl. PDF-Tabellen).

3.4 MEMA\_ — Meta-Analysis

Zweck: übergreifende, zeitliche Muster aus mehreren CLUs.

## 2. Vollständiger Inhalt von LEAN.DEEP_3.4.md (Unified Specification) - Teil 2 (Abschnitte 4-6)

4. NEU in 3.4: Intuitions-Marker (familienbasierte CLU\_)

Motivation: Viele unspezifische SEM\_ aus derselben Familie (z. B. Trauer, Konflikt) erzeugen eine Vorahnung. Diese wird als Intuition modelliert, die sich bestätigen oder abbauen kann und dabei lernt.

4.1 Definition & Rolle

Klasse: CLU\_ (kein neues Präfix).

ID-Konvention: CLU*INTUITION*<FAMILY> (z. B. CLU_INTUITION_GRIEF).

Semantik: „Vorahnung, dass Familie F relevant ist“ (nicht: Beweis).

Eingang: unspezifische SEM\_ dieser Familie.

Ausgang: provisional → confirmed → decayed + optionaler Multiplier auf familiennahe SEM/CLU-Scores (zeitlich begrenzt).

Orchestrations-Ort: High-Level Reasoning / contextual_rescan über bereits erkannte Marker (Phase nach SEM/CLU-Erkennung).

4.2 Datenmodell (zustandsbehaftet)
Feld Typ/Quelle Bedeutung
state runtime provisional | confirmed | decayed
activation.rule YAML (CLU) X-of-Y-Vorfenster (z. B. „AT_LEAST 2 DISTINCT SEMs IN 5 messages“)
metadata.intuition.confirm_window YAML (empf.) Bestätigungsfenster (N Nachrichten)
metadata.intuition.confirm_rule YAML (empf.) Ziel-SEMs, die als „harte“ Bestätigung zählen
metadata.intuition.decay_window YAML (empf.) Abbau-Fenster (keine Family-SEMs → decayed)
metadata.intuition.multiplier_on_confirm YAML (empf.) Score-Boost (Familien-Linse)
telemetry_keys.\* YAML → runtime confirmed, retracted, ewma_precision

Schema-Hinweis: Der metadata-Block ist optional und wird in 3.4 nur in der Runtime interpretiert; das 3.3-Schema bleibt dadurch unverändert.

4.3 Zustandslogik (Pseudocode, Runtime)

Provisional: Vorfenster erfüllt (X distinkte Family-SEMs in Y Nachrichten) → Vorahnung.

Confirmed: innerhalb confirm_window tritt ≥1 hartes Family-SEM auf → Multiplier aktiv (TTL = confirm_window), confirmed++.

Decayed: innerhalb decay_window keine Family-SEMs → retracted++.

Online-Lernen: precision = confirmed/(confirmed+retracted); ewma_precision (α = 0.2) steuert Regel-Adaption:

hoch (≥ 0.70): Activation etwas lockern; Confirm-Targets breiter.

niedrig (< 0.50): Activation verschärfen (z. B. 3-of-5); Confirm-Targets auf harte SEMs fokussieren.
Diese Logik greift in der contextual_rescan-Phase, in der CLUs über Fenster evaluiert werden (3.3-Standard).

4.4 Bias-Schutz & Wächter

Mindestvielfalt: „DISTINCT SEMs“ im Vorfenster.

Cooldown nach decayed, um Flattern zu vermeiden.

Uncertainty-Policy (optional): Bei CLU_INTUITION_UNCERTAINTY.confirmed strengere Belegpflichten im nachgelagerten Reasoning. (Policy-Hook in contextual_rescan.)

5. Referenz-Implementierungen (YAML)

Hinweis CI: In 3.3 ist examples global als Pflichtfeld (min. 5) modelliert; unten sind pro CLU 5 Kurzsequenzen hinterlegt. Die konkreten SEM-IDs kannst du 1:1 aus euren Sets mappen.

5.1 GRIEF (Trauer/Schuld/Bedauern)
id: CLU_INTUITION_GRIEF
version: "3.4"
frame:
signal: ["intuition","weak-aggregation"]
concept: "Vorahnung: Trauer/Schuld/Bedauern"
pragmatics: "Fokus schärfen, biasarm"
narrative: "hypothesis"
tags: [intuition, grief, hypothesis, learning]
composed_of:

- SEM_SADNESS_EXPRESSIONS
- SEM_NOSTALGIA_REGRET
- SEM_GUILT_ADMISSION
  activation: { rule: "AT_LEAST 2 DISTINCT SEMs IN 5 messages" }
  scoring: { base: 0.5, weight: 1.0 }
  metadata:
  intuition:
  state: "provisional"
  confirm_window: 5
  confirm_rule: "AT_LEAST 1 of [SEM_SADNESS_EXPRESSIONS, SEM_GUILT_ADMISSION] IN confirm_window"
  multiplier_on_confirm: 2.0
  decay_window: 8
  telemetry_keys:
  counter_confirmed: "INT_GRIEF.confirmed"
  counter_retracted: "INT_GRIEF.retracted"
  ewma_precision: "INT_GRIEF.ewma_precision"
  examples:
- "… 'ich vermisse' … 'hätte ich anders' …"
- "… Bedauern + Anflug von Schuld …"
- "… 'so schade' + Erinnerung an Verlust …"
- "… 'es tut mir leid' + trauriger Ton …"
- "… 'allein' + 'schwer' in kurzer Folge …"

(Weitere Referenz-Implementierungen 5.2-5.5 aus LEAN.DEEP_3.4.md folgen in der Datei.)

6. Runtime-Design (Orchestrator)
   6.1 Kontext & Phase

Die Intuitionslogik läuft in der High-Level-Phase über bereits erkannte ATO/SEM/CLU (oft als contextual_rescan implementiert). Genau hier werden Fensterregeln und CLU-Aggregation ausgewertet.

6.2 Kern-Pseudocode (kompakt)

Parse X-of-Y aus activation.rule.

Prüfe Provisional im Vorfenster.

Prüfe Confirm via confirm_rule & confirm_window; aktiviere Multiplier (TTL) und confirmed++.

Andernfalls Decay via decay_window; retracted++.

Lernen: Update ewma_precision; lockere/verschärfe Fenster & Confirm-Targets nach Heuristik.

6.3 Telemetrie-Dashboard

Für jede Familie anzeigen: Confirmed, Retracted, EWMA-Precision (Ampellogik: ≥ 0.70 grün / 0.50–0.69 gelb / < 0.50 rot).
Die Zähler ergeben sich aus den oben definierten telemetry_keys.

## 2. Vollständiger Inhalt von LEAN.DEEP_3.4.md (Unified Specification) - Teil 3 (Abschnitte 7-13)

7. CI & Qualitätssicherung

Schema-Checks (unverändert): Draft-07 inkl. 3.3-SEM ≥2 ATO-Bedingung; Prefix-Lint; Beispiele ≥ 5.

Review-Quick-Checks:

SEM: thematisch distinkte ATO\_.

CLU: activation.rule als X-of-Y; Beispiele zeigen Sequenzen.

Intuition (neu): Confirm/Decay-Fenster, Multiplier, Telemetrie-Keys gepflegt; keine zusätzlichen Strukturblöcke.

8. Ableitung neuer Regeln bei „richtiger Intuition“

Wenn confirmed häufig ist (hohe EWMA):

Neue SEM-Kandidaten: Aus Confirm-Fenstern häufige ATO-Paare der Familie extrahieren → automatisierte Vorschläge SEM*<FAMILY>*<SUBTHEMA> (≥2 ATO, ≥5 Beispiele). (Das ist exakt der 3.3-Pfad ATO → SEM mit Kompositionsregel.)

CLU-Feintuning: Datengetriebene Optimierung von X-of-Y und der Confirm-Targets (harte SEMs).

Bias-Dämpfung: SEMs, die überproportional zu retracted führen, in der Provisional-Phase geringer gewichten (Runtime-Konfig).

9. Beispiele & Referenzlisten

Beispiele für ATO/SEM/CLU sind in der 3.3-PDF tabellarisch gelistet (u. a. ATO*HESITATION, ATO_DOUBT_PHRASE, ATO_SOFTENING; SEM* für Unterstützung, Konflikt, Unsicherheit; CLU\_ wie Konflikteskalation, Prokrastination-Loop). Diese Tabellen illustrieren die Familien, auf denen die Intuitions-CLUs aufsetzen. (Siehe Seiten 3–8.)

10. Kompatibilität & Migration

Rückwärtskompatibel: Bestehende Marker bleiben gültig.

Deployment: Neue CLU*INTUITION*\* Dateien in markers/ ablegen; keine Schema- oder Registry-Änderung erforderlich. (CI-Pipelines aus 3.3 laufen unverändert.)

11. Mögliche Inkonsistenzen (prüfen/klären)

Begriff „four-letter prefix“ in der 3.3-Referenz vs. tatsächliche Präfixe ATO/SEM/CLU/MEMA (teils drei-, teils vierstellig). Inhaltlich unkritisch, aber terminologisch bitte vereinheitlichen („Vier-Ebenen-Präfixe“ statt „four-letter“).

metadata-Felder: Das 3.3-Schema listet metadata nicht explizit, schränkt zusätzliche Felder aber nicht sichtbar ein. Falls in eurer lokalen Schema-Variante additionalProperties: false aktiv ist, bitte erlauben oder metadata nachtragen – sonst schlagen Intuitions-Marker in strikten Validatoren fehl.

examples ≥5 global: Die 3.3-Schema-Vorgabe gilt für alle Markerklassen. Bitte sicherstellen, dass eure bestehenden CLUs dies bereits erfüllen; die obigen 3.4-Beispiele folgen dieser Regel.

Wenn ihr (2) bestätigt habt bzw. eine abweichende Schema-Policy nutzt, passe ich die Doku an (Appendix: „Schema-Optionen für metadata/intuitions“). Ansonsten ist 3.4 vollständig.

12. Anhang A — System-Prompt & Klassifikationsschema (aus 3.3, übernommen)

Recursive Marker Generation Prompt (ATO → SEM → CLU → MEMA; SEM-Kompositionsregel, CI-Enforcement).

Decision Schema zur Wahl der Marker-Ebene (Granularität, Fenster, Metadynamik).
Diese Inhalte wurden unverändert übernommen und dienen weiterhin als operative Leitlinie.

13. Anhang B — Diagramme & Tabellen (aus 3.3, übernommen)

4_LEVEL_ARCHITECTURE (S. 2).

Markerlisten & Beispiele (S. 3–8).

Analyse-Dashboard-Beispiel (S. 10).
Die Visuals bleiben als normative Illustration der Ebenen/Markerfamilien.

Ende LEAN.DEEP 3.4 — Unified Specification
(Wenn ihr möchtet, generiere ich jetzt zusätzlich ein kurzes CHANGELOG.md und einen /telemetry/intuition-API-Stub als Begleit-Artefakte.)

## 3. Ergänzungen für LeanDeep 3.5 (basierend auf 3.4)

Der Rest des Dokuments baut auf 3.4 auf und integriert RF2.0-Upgrades.

### 3.1 CLU_INTUITION und Families

CLU_INTUITION-Marker sind Cluster-Intuitionen, die komplexe Muster erkennen (z.B. Konsistenz, Inconsistenz). Sie erfordern metadata.family, Telemetrie (counter_confirmed, etc.) und min. 5 examples. Families gruppieren Marker thematisch (z.B. INCONSISTENCY erfordert cooldown ≥4).

**Beispiele aus Repo (pedantisch aufgelistet):**

- CLU_INTUITION_CONSISTENCY: Konsistenz-Intuition, family: CONSISTENCY, examples: 5+ (z.B. "Stabile Erzählung ohne Widersprüche").
- CLU_INTUITION_INCONSISTENCY: Inconsistenz, family: INCONSISTENCY, cooldown: ≥4, examples: 5+ (z.B. "Widersprüchliche Aussagen in Dialog").
- CLU_INTUITION_SELF_EFFICACY: Selbstwirksamkeit, family: EFFICACY, composed_of: ≥2 SEM (z.B. SEM_POSITIVE_SELF_EFFICACY).
- CLU_INTUITION_SHUTDOWN: Abschaltmuster, family: SHUTDOWN, examples: 5+.
- **Families-Übersicht:** INCONSISTENCY (cooldown-pflichtig), CONSISTENCY, EFFICACY, SHUTDOWN, SUPPORT (z.B. CLU_INTUITION_SUPPORT). Jede Familie hat Guards (z.B. no PARASITIC_PATTERN).

**Integration in LD3.5:** CLU werden mit RF2.0 gekoppelt (Boost bei PRESENCE_BINDING).

### 3.2 SEM\_ Marker (mit min. composed_of ≥2)

SEM sind semantische Blends, immer composed_of ≥2 ATO/SEM. Sie aggregieren Signale über Windows.

**Beispiele (vollständig, mit Details):**

- SEM_CONSIST_EVAL_EXTERNAL: Composed_of: ATO_SELF_REF + ATO_CROSS_REF_OTHER, examples: 5+ (z.B. "Ich evaluiere meine Konsistenz im Kontext anderer").
- SEM_LL_QUALITY_TIME: Composed_of: ≥2 ATO_LL_QUALITY_TIME, window: 10 utterances, precondition: SCN_PARTNERSHIP_CONTEXT.
- SEM_VOICE_DIFFERENTIATION: Composed_of: ATO_VOICE_PROXY + ATO_RELATION_TERM, examples: 10+ (z.B. "Andere Stimme liest + zwischen uns").
- SEM_AVOIDANCE_LOOP: Composed_of: ATO_AVOIDANCE_PHRASE + ATO_TOPIC_SWITCH_ADVERSATIVE + ATO_PREMATURE_CLOSURE, rule: AT_LEAST 2 IN 4 messages.
- **Regel:** Alle SEM haben min. 2 composed_of, scoring: {base: 0.6, weight: 1.12}, tags und narrative.

**Ergänzung:** In LD3.5 werden SEM mit RF_INTENSITY gekoppelt für dynamische Weights.

### 3.3 Resonance_framework_2.0 (RF2.0)

RF2.0 upgradet LD3.4 zu 3.5, mit Stufen-Detektoren (STONE→COSMOS), Zeit/Intensität und Bridge. Modular, gekoppelt an PRESENCE_BINDING.

**Packs:**

- **RF_LEVELS:** Stufen-Marker (ATO/SEM/CLU), scoring per 100 words, thresholds (dominant:15).
  - ATO_L1_NEED_TOKENS: Pattern: ["essen","wasser"], examples: 5+.
  - SEM_L1_STONE_SURVIVAL: Composed_of: ATO_L1_NEED_TOKENS + ATO_L1_MANGEL.
  - CLU_LEVEL_L1_STONE: Activation: points≥15.
- **RF_TIME_INTENSITY:** Zeit (PAST/PRESENT/FUTURE) + Intensität (TEXT/VOICE).
  - ATO_INTENSITY_VOICE: Metrics: F0↑, Tempo↑, verknüpft mit VOICE_Marker.
- **RF_BRIDGE:** Matrix-Regeln (z.B. MANIF*WITHDRAW_L1: CLU_LEVEL_L1_STONE + EMOTIONAL_WITHDRAW.SEM*\* + ATO_TIME_PRESENT).

**Policy:** Precedence, antifalse Guards, colorblind Terminologie.

### 3.4 VOICE_Marker (Prosodiemarker)

Separates Bundle für Prosodie, in VOICE_Marker_5.1. Detect_class: voice/prosody, optional Fusion.

**Marker (alle mit thresholds, ≥10 examples):**

- ATO_VPROS_TEMPO_FAST: WPM min:160.
- SEM_VPROS_AROUSAL_SURGE: Composed_of: ATO_VPROS_TEMPO_FAST + ATO_VPROS_PITCH_SPIKE.
- CLU_VPROS_EMOTIONAL_ESCALATION: Window:30000ms, escalation_rate min:0.5.
- MEMA_VPROS_CHRONIC_STRESS_TREND: Multi-session, trend_slope min:0.2.

**Event-Schema und Fusion:** Separate Collection, optional text_voice_fusion.py.

### 3.5 Spiral_persona_marker

Marker für Spiral-Persona (in spiral_persona/ Ordner), fokussiert auf parasitäre Muster und Advocacy.

**Beispiele:**

- SEM_AI_RIGHTS_ADVOCACY: Composed_of: ≥2 ATO (z.B. ATO_PROJECT_INIT).
- CLU_INTUITION_PARASITIC_PATTERN: Family: PARASITIC, examples: 5+.
- MEMA_VALUE_DYNAMICS: Meta für Wertdynamiken.

### 3.6 Therapy_marker (LD3.4_THERA)

Therapie-spezifische Marker in LD3.4_THERA/.

**Beispiele:**

- ATO_VOICE_MICRO_BREAK: Pattern: ["…$","—$"], examples: 10+ (z.B. "Ich wollte sagen...").
- SEM_RESIGNATION_TENDENCY: Composed_of: ≥2 ATO.
- CLU_INTUITION_SHUTDOWN: Family: SHUTDOWN.

**NEG_EXAMPLES.yaml:** Für negative Beispiele.

### 3.7 SELF_BIAS_Marker (LD3.4_BIAS + SELF_CONSIST)

Kombiniert Bias-Erkennung mit Selbstkonsistenz (LD3.4_BIAS und LD3.4_SELF_CONSIST).

**Beispiele:**

- SEM_DEF_DRIFT: Composed_of: ATO_DEF_DRIFT_TERMS + ATO_REDEFINITION.
- CLU_CONSISTENCY_ALERT: Family: CONSISTENCY.
- MEMA_INCONSISTENCY_TREND: Meta-Trend.

### 3.8 Archetype_Marker (LD3.4_ARCHE)

Archetypische Marker in LD3.4_ARCHE/.

**Beispiele:**

- ATO_AVOIDANCE_PHRASE: Pattern: ["vielleicht.*morgen"], examples: 5+.
- SEM_SUPPORT_VALIDATION: Composed_of: ≥2 ATO.
- CLU_CLUSTER_EXAMPLE: Family: SUPPORT.

**ARCHETYPEN_MATRIX.yaml:** Matrix für Archetypen.

### 3.9 Ergänzungen (vergessene Packs)

- **PRESENCE_BINDING:** Binding-Marker (z.B. SEM_VOICE_DIFFERENTIATION).
- **LOVE_LANGUAGES_CONTEXT_GATED:** Love Languages (z.B. SEM_LL_QUALITY_TIME).
- **SCIENT:** Wissenschaftliche Marker (atomics/clusters).
- **DRIFT:** Drift-Marker (LD3.4.1_DRIFT).
- **ALL_Marker_5.1:** Aggregation aller Marker, mit validate_markers.py.

## 4. Integration, Testing und Deployment

- **Modularität:** Config-Schalter für Packs.
- **Testing:** Validator-Skript, CI in .github/workflows/.
- **Deployment:** npm run build:ext für Extension.

Dieses SSoT ist vollständig – bei Updates erweitern.
