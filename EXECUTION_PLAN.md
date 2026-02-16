# EXECUTION PLAN: LeanDeep Marker API Monetarisierung

**Ziel:** Schnellstmoglicher Weg von aktuellem Zustand zu monetarisierbarer API
**Zeitrahmen:** 7 Wochen bis MVP-Launch (Bias-Cleanup abgeschlossen)
**Erstellt:** 2026-02-16
**Aktualisiert:** 2026-02-16 (Bias-Cleanup + Negative-Enrichment abgeschlossen)

---

## TEIL 1: VOLLSTANDIGES MARKER-AUDIT (966 kanonische Marker)

### Methodik

Das Repo enthalt **11.108 YAML-Dateien** uber alle Verzeichnisse (inkl. Kopien, Backups, SSoTh-Varianten).
Per Deduplizierungs-Skript (`tools/deduplicate_audit.sh`) wurden diese auf **966 kanonische Marker** reduziert:
- Normalisierung: "Kopie"-Suffixe, " 2"/" 3"-Duplikate entfernt
- Auswahl: Grosste + neueste Version pro Marker-Name behalten
- Ergebnis: `build/dedup_decisions.tsv` (alle Entscheidungen), `build/markers_rated/` (Qualitatsverzeichnis)

Automatische Qualitats-Bewertung (`tools/build_quality_dirs.py`) basierend auf:
- Anzahl positiver/negativer Beispiele
- Vorhandensein von Frame/Description/Pattern/composed_of
- Dateigrosse als Proxy fur Vollstandigkeit
- Unterstutzung beider Schema-Formate (Root-Schema + SSoTh-Schema)

### Legende
- **1 = Approved** -- Produktionsreif. 5+ Beispiele, Frame vorhanden, >500B. Kommerziell nutzbar
- **2 = Good** -- Solide Basis, braucht kleine Anpassungen (Beispiele, EN-Ubersetzung, Rename)
- **3 = Needs Work** -- Potenzial, aber signifikante Uberarbeitung notig
- **4 = Not Usable** -- Leerer Stub oder kein kommerzieller Anwendungsfall

---

### ATO_ ATOMIC MARKERS -- Manuelles Detail-Audit (49 Root-Level)

> **Hinweis:** Dieses manuelle Audit deckt nur die 49 Root-Level ATO-Marker ab.
> Insgesamt gibt es **491 kanonische ATO-Marker** (409 Approved, 76 Good, 6 Not Usable).
> Die vollstandige automatische Bewertung aller 491: `build/markers_rated/RATING_SUMMARY.tsv`

| # | Marker | Rating | Grund | Aktion |
|---|--------|--------|-------|--------|
| 1 | ATO_OPEN_QUESTION_THERAPIST | **1** | Bilingual DE/EN, activation/scoring, klares Konzept | -- |
| 2 | ATO_REFLECTIVE_STATEMENT_THERAPIST | **1** | Bilingual, vollstandige Struktur, Coaching-Plattform-ready | -- |
| 3 | ATO_VALIDATION_THERAPIST | **1** | Bilingual, vollstandig, Therapie-Plattform-ready | -- |
| 4 | ATO_SUBSTANCE_CRAVING | **1** | 20 Pos/20 Neg, starke Regex, Sucht-Recovery nutzbar | -- |
| 5 | ATO_SUBSTANCE_DENIAL | **1** | 20 Pos/20 Neg, starke Regex, Sucht-Recovery nutzbar | -- |
| 6 | ATO_ADHD_DISORGANIZED_THOUGHTS | **2** | 20 Pos/20 Neg, aber klinisches Label | Rename -> ATO_DISORGANIZED_THOUGHT_PATTERN |
| 7 | ATO_BPD_FEAR_OF_ABANDONMENT | **2** | 23 Pos/20 Neg, exzellent, nur Label-Problem | Rename -> ATO_ABANDONMENT_ANXIETY |
| 8 | ATO_BPD_INTENSE_EMOTIONS | **2** | 20 Pos/20 Neg, stark, Label-Problem | Rename -> ATO_INTENSE_EMOTION_SWING |
| 9 | ATO_OCD_REPETITIVE_LANGUAGE | **2** | 5 Pos/5 Neg, gutes Pattern | Rename -> ATO_REPETITIVE_CHECKING_LANGUAGE, +10 Beispiele |
| 10 | ATO_CLARIFICATION_REQUEST | **2** | Bilingual, activation/scoring | +5 Pos/Neg Beispiele |
| 11 | ATO_DISCLOSURE_STATEMENT | **2** | Bilingual, gute Struktur | +5 Pos/Neg Beispiele |
| 12 | ATO_DISMISSIVE_DOWNPLAY | **2** | Bilingual, activation/scoring | +5 Pos/Neg Beispiele |
| 13 | ATO_FULL_STRESS | **2** | Gutes DE-Pattern, klares Konzept | +5 Beispiele, Schema-Felder erganzen |
| 14 | ATO_HELPLESSNESS_DEPENDENCY | **2** | Gute Regex, activation/scoring | +5 bilinguale Beispiele, EN-Patterns |
| 15 | ATO_HESITATION_VOICE | **2** | Bilingual, activation/scoring | +5 Beispiele, Abgrenzung zu ANXIETY_HESITATION |
| 16 | ATO_IMPOSTER_FEELING | **2** | 5 DE-Regex, klares Konzept | +10 bilinguale Beispiele, EN-Patterns |
| 17 | ATO_LAUGHTER_EVENT | **2** | Audio-Detektor, gute Params | +Text-Fallbacks ([laughs], haha) |
| 18 | ATO_OFFENDED_SILENCE | **2** | Kreative Regex fur Minimalantworten | +5 Pos/Neg Beispiele |
| 19 | ATO_PAUSE_LONG | **2** | Audio-Detektor (min_ms: 600) | +Text-Fallback ([pause], ...) |
| 20 | ATO_PROJECTION_AWARENESS | **2** | 4 DE-Regex, psychodynamisch | +bilinguale Beispiele, EN-Patterns |
| 21 | ATO_PROTECTIVE_DISTANCING | **2** | 4 DE-Regex, klares Konzept | +bilinguale Beispiele, EN-Patterns |
| 22 | ATO_RISING_INTONATION | **2** | Praziser Audio-Detektor | +Text-Fallback (Fragezeichen, Uptalk) |
| 23 | ATO_SELF_OBSERVATION | **2** | 3 DE-Regex, metakognitiv | +bilinguale Beispiele, EN-Patterns |
| 24 | ATO_UNCLEAR_INTENTION | **2** | 10 Signale, 1 Compound-Regex | +10 Beispiele, EN-Patterns, Frame "Taeuschung" neutralisieren |
| 25 | ATO_VALIDATE_AND_BOUNDARY | **2** | Compound-Regex (Validation+Boundary) | +bilinguale Beispiele, EN-Patterns |
| 26 | ATO_VULNERABILITY | **2** | 4 DE-Regex, prosozial | +bilinguale Beispiele, EN-Patterns |
| 27 | ATO_WE_LANGUAGE | **2** | Bilingual, activation/scoring | +Beispiele (affiliatives "wir" vs. generisches) |
| 28 | ATO_YOUR_FAULT_PHRASE | **2** | Gute DE-Pattern, Logistic-Scoring | +5 bilinguale Beispiele, EN-Patterns |
| 29 | ATO_ANXIETY_HESITATION | **3** | Matched universale Fullworter (um, uh, like) | Rename -> ATO_HESITATION_FILLER, +15 Beispiele, Regex verscharfen |
| 30 | ATO_BLAME_SHIFT | **3** | Gute Regex, aber 0 Beispiele, v3.3 | +10 Pos/Neg, Schema auf v3.4 |
| 31 | ATO_DEPRESSIVE_NEGATIVE_TALK | **3** | Klinisches Label, nur 5/5 Beispiele | Rename -> ATO_NEGATIVE_SELF_TALK, +15 Beispiele |
| 32 | ATO_DISGUST | **3** | Nur DE, keine Beispiele, kein Schema | +10 bilinguale Beispiele, EN-Patterns, Schema |
| 33 | ATO_EMO_HIGH_VALENCE_MARKER | **3** | Kein Regex, referenziert nicht-existierende Klasse | Regex-Fallback, +10 Beispiele, v3.4 |
| 34 | ATO_EMO_LOW_VALENCE_MARKER | **3** | Kein Regex (valence <= -0.6), v3.2 | Regex-Fallback, +Beispiele, v3.4 |
| 35 | ATO_FEAR | **3** | Nur DE, keine Beispiele | +EN-Patterns, +10 bilinguale Beispiele, Schema |
| 36 | ATO_HEDGING_CUE | **3** | Bare Words ohne Regex-Anchors, Uber-Trigger-Gefahr | Word-Boundary Regex, EN-Patterns, +10 Beispiele |
| 37 | ATO_INDIRECT_DISLIKE | **3** | "interessant" zu generisch | Kontext-abhangige Patterns, +10 Beispiele |
| 38 | ATO_INVITING_RESONANCE | **3** | Nur 2 Regex trotz 5 Signalen | +3 fehlende Patterns, +10 Beispiele |
| 39 | ATO_SADNESS | **3** | Nur DE, Mix DE/EN in Pattern | Sprachtrennung, +10 Beispiele |
| 40 | ATO_SARCASM | **3** | Matched "really", "sure", "great" -- massives False-Positive-Risiko | Fundamentales Pattern-Rework notig |
| 41 | ATO_SARCASM_SUBTILE | **3** | "ja klar" ohne Kontext = Uber-Trigger | Kontext-Patterns, +10 Beispiele |
| 42 | ATO_SELF_RELIANCE_EARLY_MARKER | **3** | Pattern "habe ich" matched alles -- kaputt | Pattern komplett neu schreiben |
| 43 | ATO_SUBTLE_IRRITATION | **3** | Nur RP-Marker (*seufz*), zu eng | Verbale Irritation erganzen |
| 44 | ATO_C_SOFT_COMMITMENT_MARKER | **4** | 40-Byte Stub, leer | Loschen |
| 45 | ATO_DEFENSIVENESS_SHIFT_MARKER | **4** | 40-Byte Stub, leer | Loschen |
| 46 | ATO_EMOTIONAL_INVALIDATION | **4** | 40-Byte Stub, leer | Loschen (oder von Grund auf neu) |
| 47 | ATO_GUILT_TRIPPING_MARKER | **4** | 40-Byte Stub, leer | Loschen |
| 48 | ATO_S_BLAME_SHIFT_EXPRESSIONS_MARKER | **4** | 40-Byte Stub, Duplikat von BLAME_SHIFT | Loschen |
| 49 | ATO_LONG_RESPONSE_GAP | **4** | 104 Byte, nur ID + Family, kein Pattern | Loschen |

**ATO Summary: 5x Rating-1 | 24x Rating-2 | 14x Rating-3 | 6x Rating-4**

---

### SEM_ SEMANTIC MARKERS -- Manuelles Detail-Audit (318 aus Root+LD3.4)

> **Hinweis:** Insgesamt gibt es **252 kanonische SEM-Marker** nach Deduplizierung
> (225 Approved, 23 Good, 4 Not Usable). Die 318 hier schliessen Duplikate mit ein.

#### Rating 1 = Approved (72 Marker)

| Marker | Beispiele | Besonderheit |
|--------|-----------|-------------|
| SEM_ACCUSATION_MARKER | 19 | Frame, composed_of, tags -- vollstandig |
| SEM_ANALYTICAL_THINKING | 10 | Kognitiver Stil-Marker |
| SEM_AROUSAL_SPIKE_AT_BREAK | 8 | Audio-Pattern, gut definiert |
| SEM_BREAK_UP | 18 | Beziehungsende-Erkennung |
| SEM_CERTAINTY_CLAIMS | 10 | Uberzeugungsstarke, composed_of |
| SEM_CONFIRMATION_BIAS | 10 | Kognitiver Bias, composed_of |
| SEM_CONFLICT_AVOIDANCE | 15 | Vermeidungsmuster |
| SEM_CONFLICT_LVL1_3 | 16 | Granularer Konflikt-Level |
| SEM_CONFLICT_LVL4_6 | 17 | Mittlerer Konflikt-Level |
| SEM_CONFLICT_LVL6_9 | 16 | Hoher Konflikt-Level |
| SEM_CONFLICT_MACRO | 7 | Gottman-Eskalationskette, 4 composed_of |
| SEM_CONNECTION | 37 | Sehr gut populiert |
| SEM_CONSENSUS_BUILDING | 15 | Kollaboratives Muster |
| SEM_CONTRADICTION | 16 | Widerspruche erkennen |
| SEM_DEEPENING_BY_QUESTIONING | 30 | Exzellentes Trainingsvolumen |
| SEM_DEFENSIVENESS_SHIFT_MARKER | 41 | **Best-in-Class**, 7 Tags |
| SEM_DISSONANCE_TEXT | 8 | Kognitive Dissonanz |
| SEM_EMOTIONAL_ACCEPTANCE | 15 | Positives Muster |
| SEM_EMOTIONAL_AWARENESS | 15 | Emotionale Intelligenz |
| SEM_EMOTIONAL_OVERWHELM | 10 | Uberforderung, 3 composed_of |
| SEM_EXTERNALIZING_LOCUS_OF_CONTROL | 15 | Externe Kontrollattribution |
| SEM_FIRST_TIME_DEPTH_MARKER | 13 | Erst-Offenbarung |
| SEM_FIRSTTIME_CLAUSE_MARKER | 32 | Erstmalige Aussage, exzellent |
| SEM_FORMULATED_INTENTION_TO_CHANGE | 15 | Therapie/Coaching Pattern |
| SEM_GASLIGHTING_ATTEMPT | 10 | Manipulation, 3 composed_of |
| SEM_GASLIGHTING | 25 | Gaslighting-Erkennung |
| SEM_INTERACTIVE_STONEWALLING_MARKER | 14 | Gottman Stonewalling |
| SEM_JOINT_FUTURE_INITIATIVE | 10 | Gemeinsame Zukunftsplanung |
| SEM_LL_ACTS_OF_SERVICE | 10 | Love Language |
| SEM_LL_PHYSICAL_TOUCH | 10 | Love Language |
| SEM_LL_QUALITY_TIME | 10 | Love Language |
| SEM_LL_RECEIVING_GIFTS | 10 | Love Language |
| SEM_LL_WORDS_OF_AFFIRMATION | 10 | Love Language |
| SEM_LOVE_BOMBING | 20 | Manipulation, composed_of |
| SEM_PASSIVE_AGGRESSIVE_BEHAVIOR | 10 | Vollstandig, 3 composed_of |
| SEM_PLATFORM_SWITCH | 10 | Plattformwechsel-Manipulation |
| SEM_POSITIVE_SELF_EFFICACY | 20 | Positive Selbstwirksamkeit |
| SEM_PROJECTION_TEXT | 8 | Projektion |
| SEM_REACTION_FORMATION_AUDIO | 8 | Audio-Reaktionsbildung |
| SEM_REACTION_FORMATION_TEXT | 8 | Text-Reaktionsbildung |
| SEM_REPAIR_ATTEMPT_AUDIO | 8 | Repair-Versuch Audio |
| SEM_REPAIR_FAILURE_AUDIO | 8 | Gescheiterter Repair Audio |
| SEM_REPAIR_FAILURE_TEXT | 8 | Gescheiterter Repair Text |
| SEM_RESIGNATION_TENDENCY | 20 | Resignationsmuster |
| SEM_RIVALRY_MENTION | 28 | Geschwister-/Familienrivalitat |
| SEM_SELF_REFLECTION | 10 | Selbstreflexion, 3 composed_of |
| SEM_SELF_RELIANCE_EARLY | 20 | Fruhe Selbststandigkeit |
| SEM_SELF_SUPPORT_STATEMENT | 15 | Selbstunterstutzung |
| SEM_SHAME_PROSODY | 8 | Audio-Scham |
| SEM_SHAME_TEXT | 8 | Text-Scham |
| SEM_SHARED_GOAL_FRAMING | 10+10 | **Einziger mit Pos UND Neg** |
| SEM_SHUTDOWN_EPISODE | 20 | Shutdown-Erkennung |
| SEM_SIMU_LOVE_SCAM_PSYCHO_DISTRACT_YAML_MARKER | 30 | Love-Scam Phasen |
| SEM_SOCIAL_AFFILIATION | 15 | Soziale Zugehorigkeit |
| SEM_STONEWALLING_BEHAVIOR | 10 | Gottman Stonewalling |
| SEM_SYMBOLIC_COMMUNICATION_FOCUS | 10 | Symbolische Kommunikation |
| SEM_TASK_DRIVE | 15 | Aufgabenorientierung |
| SEM_TRANSLATION_ARTIFACT | 20 | Ubersetzungs-Anomalien |
| SEM_TRIANGULATION_PATTERN | 10 | Beziehungsmanipulation |
| SEM_UNCERTAINTY_PROSODY | 8 | Audio-Unsicherheit |
| SEM_URGENCY_SCARCITY | 25 | Manipulation/Persuasion |
| SEM_WEBCAM_EXCUSE_MARKER | 25 | Love-Scam Ausreden |
| + 10 weitere | 7-15 | Diverse vollstandige Marker |

#### Rating 2 = Good (168 Marker)

**Systemisches Problem:** Fast alle brauchen dasselbe:
- **Fehlende Beschreibung** (~200 Marker ohne Description)
- **Fehlende Negativ-Beispiele** (nur 3 von 318 haben Negatives)
- **Duplikate:** WEBCAM_EXCUSE/WEBCAM_EXCUSE_MARKER, LOVE_BOMBING/M_LOVE_BOMBING, BLAME_SHIFT/BLAME_SHIFTING, PASSIVE_AGGRESION/PASSIVE_AGGRESSIVE_BEHAVIOR
- **Typos:** APATHATICLU_REPLY, PASSIVE_AGGRESION, PLEASANT_PULS, SIMU_LAVE_SCAM

#### Rating 3 = Needs Work (76 Marker)

Kritische Gruppen:
- **0-Beispiele-Marker** (22x): BLAME_SHIFT, DOUBLE_BIND_DISCLAIMER_BUT, DRAMA_TRIANGLE, FOGGING, GUILT_FRAMING, IDEALIZATION_DEVALUATION, REALITY_DISTORTION_FIELD, SILENT_TREATMENT, etc.
- **Spiral Dynamics Nische** (12x): SD_BLUE, SD_GREEN, SD_ORANGE, SD_RED, SD_TURQUOISE, SD_YELLOW, BEIGE_SURVIVAL, BLAU_ORDER, DYAD_MANIFESTO, etc.
- **Strukturell leer** (9x): CONSIST_EVAL_EXTERNAL, DEF_DRIFT, MODAL_FLIP, TASK_DOMINANCE, etc.

#### Rating 4 = Not Usable (2 Marker)

| Marker | Grund |
|--------|-------|
| SEM_BLAME_SHIFTING | 101-Byte Stub, komplett leer |
| SEM_SOFT_COMMITMENT_MARKER | 109-Byte Stub, komplett leer |

**SEM Summary: 72x Rating-1 | 168x Rating-2 | 76x Rating-3 | 2x Rating-4**

---

### CLU_ CLUSTER MARKERS -- Manuelles Detail-Audit (70 aus Root+LD3.4)

> **Hinweis:** Insgesamt gibt es **143 kanonische CLU-Marker** nach Deduplizierung
> (110 Approved, 26 Good, 7 Not Usable).

#### Rating 1 = Approved (15 Marker)

| Marker | Quelle | Besonderheit |
|--------|--------|-------------|
| CLU_DEFENSIVE_RETREAT | Root | 20+ Pos (DE+EN), 10 Neg, exzellent |
| CLU_INTUITION_COMMITMENT | Root/LD3.4 | 10 Pos/10 Neg, produktionsreif |
| CLU_INTUITION_CONFLICT | Root/LD3.4 | 10 Pos/10 Neg, Inline-Erklarungen |
| CLU_INTUITION_GRIEF | Root/LD3.4 | 10 Pos/10 Neg, gut kalibriert |
| CLU_INTUITION_SUPPORT | Root/LD3.4 | 10 Pos/10 Neg, klare Abgrenzung |
| CLU_DYSREGULATION_PATTERN | LD3.4 | 10 Beispiele, Cooldown, Absence-Detection |
| CLU_INTUITION_POSITIVE_AFFECT | LD3.4 | 12+ Beispiele, Confirm/Decay-Logik |
| CLU_CONFLICT_ESCALATION | spiral | 5 Beispiele, composed_of, Scoring (1.2) |

#### Rating 2 = Good (35 Marker)

| Marker | Aktion |
|--------|--------|
| CLU_AVOIDED_DISCLOSURE | +10 Pos/Neg Beispiele |
| CLU_RAPPORT_BUILDING | +10 Pos/Neg Beispiele |
| CLU_RUPTURE_TENSION | +Beispiele fur Misalignment/Stalemate/Withdrawal |
| CLU_INTUITION_UNCERTAINTY | +10 Negativ-Beispiele |
| CLU_SHUTDOWN_DISSOCIATION_CLUSTER | +Negatives, Rename (kein "Dissociation") |
| CLU_INTUITION_PARASITIC_PATTERN | +diverse Beispiele, AI-Safety-relevant |
| CLU_CIRCULAR_REASONING | +5 Beispiele, Negatives |
| CLU_GOALPOST_SHIFT | +Negatives, +5 Beispiele |
| CLU_SD_STAGE_BLUE/GREEN/ORANGE/RED/TURQUOISE/YELLOW | je +Negatives, +5 Beispiele |
| CLU_SPIRAL_PERSONA_* (8x) | +echte Konversationsbeispiele |
| CLU_TOPIC_DRIFT | +Negatives, Abgrenzung zu normaler Progression |
| CLU_UNCERTAINTY_CASCADE | +Negatives, +5 Beispiele |

#### Rating 3 = Needs Work (15 Marker)

| Marker | Problem |
|--------|---------|
| CLU_ATTACHMENT_STYLE_ANXIOUS | 0 Beispiele, referenziert nicht-existierende Sub-Marker |
| CLU_ATTACHMENT_STYLE_AVOIDANT | 0 Beispiele, gleiche Problem |
| CLU_ATTACHMENT_STYLE_SECURE | 0 Beispiele, gleiche Problem |
| CLU_DESTRUCTIVE_SELF_PROTECTION | 0 Beispiele, klinisches Label |
| CLU_NEEDINESS_GUILT_BIND | 0 Beispiele, klinisch beladen |
| CLU_THERAPEUTIC_AWARENESS | 0 Beispiele |
| CLU_THERAPEUTICLU_MIRRORING | Typo im Dateinamen, 0 Beispiele |
| CLU_SELF_PROTECTION_TACTICS | Duplikat von DESTRUCTIVE_SELF_PROTECTION |
| CLU_ADAPTIVE_POLARIZATION_MARKER | Vage Signalworter, referenziert nicht-existierende Marker |
| CLU_EMOTIONAL_SUPPORT | Zu generisch, keine Abgrenzung |
| CLU_EMOTION_VOLATILITY | Platzhalter-Beispiele |
| CLU_MODE_SWITCH | Unuberzeugende Komposition |
| CLU_SELF_CONTRADICTION | Schwache Komposition |
| CLU_AUTHORITY_SHIFT | Platzhalter-Beispiele |

#### Rating 4 = Not Usable (5 Marker)

| Marker | Grund |
|--------|-------|
| CLU_BEHAVIOR_MARKER_SYSTEM | 40-Byte Stub |
| CLU_GROWING_CONNECTION_CLUSTER | Leer |
| CLU_INDIRECT_CONFLICT_AVOIDANCE | Leer |
| CLU_MISUNDERSTANDING_AUDIO | Leer, Audio-only ohne Pipeline |
| CLU_PROCRASTINATION_LOOP (root) | Leer |

**CLU Summary: 15x Rating-1 | 35x Rating-2 | 15x Rating-3 | 5x Rating-4**

---

### MEMA_ META MARKERS -- Manuelles Detail-Audit (20 aus Root+LD3.4)

> **Hinweis:** Insgesamt gibt es **80 kanonische MEMA-Marker** nach Deduplizierung
> (69 Approved, 10 Good, 1 Not Usable).

#### Rating 1 = Approved (7 Marker)

| Marker | Quelle | Besonderheit |
|--------|--------|-------------|
| MEMA_ABSENCE_OF_EMOTION_LABELS_IN_CONFLICT | LD3.4 | 10 volle Dialog-Beispiele, Workplace-Kontext |
| MEMA_ABSENCE_OF_GOAL_CLARITY_IN_CONFLICT | LD3.4 | 10 Dialog-Beispiele |
| MEMA_ABSENCE_OF_RESPONSIBILITY_IN_CONFLICT | LD3.4 | 10 Dialog-Beispiele, Blame-Loop |
| MEMA_ABSENCE_OF_SELF_REFERENCE_IN_CONFLICT | LD3.4 | 10 Dialog-Beispiele |
| MEMA_ABSENCE_OF_VULNERABILITY_IN_CONFLICT | LD3.4 | 10 Dialog-Beispiele, Armored Conflict |

#### Rating 2 = Good (8 Marker)

| Marker | Aktion |
|--------|--------|
| MEMA_COMMITMENT_RESOLUTION_PATTERN | Schematische Beispiele -> volle Dialoge |
| MEMA_CONFLICT_RESOLUTION_PATTERN | Schematische Beispiele -> volle Dialoge |
| MEMA_DESTRUCTIVE_CONFLICT_DYNAMICS_MARKER | Gut strukturiert, braucht mehr Beispiele |
| MEMA_DISSOCIATIVE_COMPARTMENTALIZATION | Rename (kein "Dissociative"), +Beispiele |
| MEMA_MEANING_CRISIS_MARKER | Gutes Konzept, +Beispiele |
| MEMA_PAPAGEI_ECHO | 5 echte Beispiele, +Negatives |
| MEMA_SD_TRANSITION | +Negatives, +Dialog-Beispiele |
| MEMA_ZERO_PUNISHMENT_GUARD | Einzigartiges Policy-Hook-Konzept |

#### Rating 3 = Needs Work (4 Marker)

| Marker | Problem |
|--------|---------|
| MEMA_EVOLUTIONARY_PRESSURE | Abstrakte Beispiele, undefinierte detect_class |
| MEMA_KRISTALL_SPEICHER | Esoterisch, generische Platzhalter |
| MEMA_META_DRIFT | Platzhalter-Beispiele |
| MEMA_STRUDEL_PATTERN | Braucht mehr Beispiele |

#### Rating 4 = Not Usable (1 Marker)

| Marker | Grund |
|--------|-------|
| MEMA_RAPPORT_DYNAMICS | 0 Bytes, komplett leer |

**MEMA Summary: 7x Rating-1 | 8x Rating-2 | 4x Rating-3 | 1x Rating-4**

---

## GESAMT-UBERSICHT (nach Bias-Cleanup + Negative-Enrichment)

| Layer | Rating 1 | Rating 2 | Total |
|-------|----------|----------|-------|
| ATO | 327 | 72 | 399 |
| SEM | 212 | 23 | 235 |
| CLU | 105 | 23 | 128 |
| MEMA | 61 | 7 | 68 |
| **TOTAL** | **705** | **125** | **830** |

**705 Marker (85%) sind produktionsreif. 125 brauchen kleine Fixes. 0 Stubs, 0 Not Usable.**

### Was wurde bereinigt (Bias-Cleanup Sprint, abgeschlossen 2026-02-16)

| Aktion | Anzahl | Status |
|--------|--------|--------|
| " 2" Duplikate entfernt | 111 | Erledigt |
| Orphan " 2" Dateien umbenannt | 23 | Erledigt |
| Klinische Labels umbenannt (BPD_, ADHD_, etc.) | 12 | Erledigt |
| Dateinamen-Typos korrigiert | 4 | Erledigt |
| `_corrected` Suffixe bereinigt | 4 | Erledigt |
| Rating-4 Stubs geloscht | 18 | Erledigt |
| **Negative Beispiele generiert** | **741** | Erledigt |
| Marker die schon Negatives hatten | 78 | Unverandert |
| **Gesamt: Marker mit Negatives** | **819 von 830 (98.8%)** | -- |

**Vor Cleanup:** 966 Marker, 86 mit Negatives (10.6%), 12 klinische Labels, 119 Duplikate
**Nach Cleanup:** 830 Marker, 819 mit Negatives (98.8%), 0 klinische Labels, 0 Duplikate

### Klinische Label-Renames (EU AI Act Compliance)

| Alt (diagnostisch) | Neu (verhaltensbasiert) |
|-----|-----|
| ATO_BPD_FEAR_OF_ABANDONMENT | ATO_ABANDONMENT_ANXIETY |
| ATO_BPD_INTENSE_EMOTIONS | ATO_INTENSE_EMOTION_SWING |
| ATO_ADHD_DISORGANIZED_THOUGHTS | ATO_DISORGANIZED_THOUGHT_PATTERN |
| ATO_BIPOLAR_MANIC_SPEECH | ATO_MANIC_SPEECH_PATTERN |
| ATO_AUTISM_LITERAL_LANGUAGE | ATO_LITERAL_LANGUAGE_PATTERN |
| ATO_SCHIZOPHRENIA_DISORGANIZED_SPEECH | ATO_DISORGANIZED_SPEECH_PATTERN |
| ATO_OCD_REPETITIVE_LANGUAGE | ATO_REPETITIVE_CHECKING_LANGUAGE |
| ATO_PTSD_AVOIDANCE_LANGUAGE | ATO_TRAUMA_AVOIDANCE_LANGUAGE |
| ATO_DEPRESSIVE_NEGATIVE_TALK | ATO_NEGATIVE_SELF_TALK |
| CLU_DEPRESSIVE_TRIAD | CLU_NEGATIVE_COGNITIVE_TRIAD |
| MEMA_DISSOCIATIVE_COMPARTMENTALIZATION | MEMA_EMOTIONAL_COMPARTMENTALIZATION |
| MEMA_DEPRESSIVE_LANGUAGE_PROFILE | MEMA_NEGATIVE_LANGUAGE_PROFILE |

Kanonische Marker liegen in `build/markers_rated/` mit Unterordnern nach Qualitat und Layer.
Tools: `tools/cleanup_duplicates.py`, `tools/fix_typos.py`, `tools/rename_clinical_labels.py`, `tools/delete_stubs.py`, `tools/enrich_negatives.py`

---

## TEIL 2: BIAS-CLEANUP SPRINT -- ABGESCHLOSSEN

> **Status: ERLEDIGT (2026-02-16)**
> Alle Aufgaben in diesem Abschnitt wurden per Skript automatisiert durchgefuhrt.
> Detaillierter Plan: `docs/plans/2026-02-16-bias-cleanup-semantic-enrichment.md`
> Gesamtdauer: ~60 Minuten (inkl. Negative-Enrichment fur 741 Marker)

### Prioritat 1: Klinische Labels entfernen -- ERLEDIGT

Alle Renames in einem Batch durchfuhren:

| Alt | Neu |
|-----|-----|
| ATO_BPD_FEAR_OF_ABANDONMENT | ATO_ABANDONMENT_ANXIETY |
| ATO_BPD_INTENSE_EMOTIONS | ATO_INTENSE_EMOTION_SWING |
| ATO_ADHD_DISORGANIZED_THOUGHTS | ATO_DISORGANIZED_THOUGHT_PATTERN |
| ATO_OCD_REPETITIVE_LANGUAGE | ATO_REPETITIVE_CHECKING_LANGUAGE |
| ATO_DEPRESSIVE_NEGATIVE_TALK | ATO_NEGATIVE_SELF_TALK |
| CLU_SHUTDOWN_DISSOCIATION_CLUSTER | CLU_EMOTIONAL_SHUTDOWN_PATTERN |
| CLU_DESTRUCTIVE_SELF_PROTECTION | CLU_RESPONSIBILITY_DEFLECTION_PATTERN |
| CLU_NEEDINESS_GUILT_BIND | CLU_OBLIGATION_PRESSURE_PATTERN |
| MEMA_DISSOCIATIVE_COMPARTMENTALIZATION | MEMA_EMOTIONAL_COMPARTMENTALIZATION |
| SEM_SOCIAL_BORDERLINES_MARKER_MIX_YAML_MARKER | SEM_SOCIAL_BOUNDARY_PATTERN |

In allen Markern: Tags "diagnostic", "psychiatric" entfernen. Ersetzen durch "behavioral_pattern".

### Prioritat 2: Typos und Duplikate bereinigen (Tag 2-3)

**Typo-Fixes:**
- SEM_PASSIVE_AGGRESION -> SEM_PASSIVE_AGGRESSION (oder loschen, da SEM_PASSIVE_AGGRESSIVE_BEHAVIOR existiert)
- SEM_APATHATICLU_REPLY -> SEM_APATHETIC_REPLY
- SEM_PLEASANT_PULS -> SEM_PLEASANT_PULSE
- SEM_SIMU_LAVE_SCAM_SEMANTIC -> SEM_SIMU_LOVE_SCAM_SEMANTIC
- CLU_THERAPEUTICLU_MIRRORING -> CLU_THERAPEUTIC_MIRRORING

**Duplikate loschen (den schwacheren entfernen):**
- SEM_WEBCAM_EXCUSE -> loschen (WEBCAM_EXCUSE_MARKER behalten)
- SEM_M_LOVE_BOMBING -> loschen (LOVE_BOMBING behalten)
- SEM_BLAME_SHIFTING -> loschen (BLAME_SHIFT behalten)
- SEM_PASSIVE_AGGRESION -> loschen (PASSIVE_AGGRESSIVE_BEHAVIOR behalten)
- SEM_MAINTENANCE_RITUAL_corrected -> loschen (MAINTENANCE_RITUAL behalten)
- CLU_SELF_PROTECTION_TACTICS -> loschen (mit DESTRUCTIVE_SELF_PROTECTION mergen)

### Prioritat 3: Stubs loschen (Tag 3)

18 Marker als Rating-4 identifiziert (6 ATO, 4 SEM, 7 CLU, 1 MEMA).
Vollstandige Liste: `build/markers_rated/4_not_usable/`

Bereits bekannte Stubs aus manuellem Audit:
```
ATO_C_SOFT_COMMITMENT_MARKER.yaml
ATO_DEFENSIVENESS_SHIFT_MARKER.yaml
ATO_EMOTIONAL_INVALIDATION.yaml
ATO_GUILT_TRIPPING_MARKER.yaml
ATO_S_BLAME_SHIFT_EXPRESSIONS_MARKER.yaml
ATO_LONG_RESPONSE_GAP.yaml
SEM_BLAME_SHIFTING.yaml
SEM_SOFT_COMMITMENT_MARKER.yaml
CLU_BEHAVIOR_MARKER_SYSTEM.yaml
CLU_GROWING_CONNECTION_CLUSTER.yaml
CLU_INDIRECT_CONFLICT_AVOIDANCE.yaml
CLU_MISUNDERSTANDING_AUDIO.yaml
CLU_PROCRASTINATION_LOOP.yaml
MEMA_RAPPORT_DYNAMICS.yaml
+ 4 weitere (siehe RATING_SUMMARY.tsv fur vollstandige Liste mit Begrundung)
```

### Prioritat 4: Valenz-Balance (Woche 2)

Fur jeden "toxischen" Top-Marker einen positiven Gegenpol sicherstellen:

| Toxischer Marker | Positiver Gegenpol | Status |
|-----------------|-------------------|--------|
| SEM_GASLIGHTING | SEM_REALITY_VALIDATION | **Neu erstellen** |
| SEM_BLAME_SHIFT | SEM_ACCOUNTABILITY_TAKING | **Neu erstellen** |
| SEM_STONEWALLING | SEM_REPAIR_ATTEMPT_AUDIO (existiert) | OK |
| SEM_LOVE_BOMBING | SEM_GENUINE_APPRECIATION | **Neu erstellen** |
| SEM_SILENT_TREATMENT | SEM_CONSTRUCTIVE_PAUSE | **Neu erstellen** |
| SEM_PASSIVE_AGGRESSIVE_BEHAVIOR | SEM_ASSERTIVE_COMMUNICATION | **Neu erstellen** |
| CLU_ATTACHMENT_STYLE_ANXIOUS | CLU_ATTACHMENT_STYLE_SECURE (existiert) | OK |

### Prioritat 5: Kontext-Diversifizierung (Woche 2, ongoing)

Neues Pflichtfeld in Marker-Schema:

```yaml
context_applicability:
  - romantic
  - professional
  - therapeutic
  - familial
  - friendship
power_dynamic: equal | authority_speaker | subordinate_speaker | therapist_client
```

---

## TEIL 3: MARKER-AUSBAU (Woche 2-4, massiv reduziert)

> **Update:** Durch das volle Repo-Audit sind 813 Marker bereits Rating-1. Der Marker-Ausbau
> reduziert sich von ~6 Wochen auf ~2 Wochen -- Fokus liegt auf Schema-Harmonisierung und
> den 135 Rating-2 Markern.

### Phase A: 813 Rating-1 Marker API-ready machen (Woche 2-3)

Die Marker sind inhaltlich gut, brauchen aber Schema-Vereinheitlichung:
- [ ] Beide Schema-Formate (Root + SSoTh) auf einheitliches API-Schema normalisieren
- [ ] Alle Marker in `build/markers_rated/1_approved/` als kanonische Quelle nutzen
- [ ] Englische Beispiele sicherstellen (SSoTh-Marker haben oft schon DE+EN)
- [ ] Context-Tags hinzufugen (romantic, professional, therapeutic, familial, friendship)
- [ ] `marker_registry.json` generieren fur API-Engine

### Phase B: 135 Rating-2 auf Rating-1 heben (Woche 3-4)

Priorisiert nach kommerziellem Wert:

**Tier 1 -- Hero Features (falls noch Rating-2):**
- Manipulation-Detection-Marker: GASLIGHTING, LOVE_BOMBING, STONEWALLING, TRIANGULATION
- Attachment-Marker: ANXIOUS, AVOIDANT, SECURE
- Therapy-Marker: THERAPEUTIC_AWARENESS, REPAIR_ATTEMPT

**Tier 2 -- Batch-Upgrade (systematisch):**
Die meisten Rating-2 Marker brauchen nur:
- +5 Beispiele (Pos oder Neg)
- Frame/Description Feld erganzen
- Schema auf v3.4 vereinheitlichen

Batch-Skript: `tools/upgrade_rating2.py` (noch zu erstellen)

### Phase C: Deduplizierung ist abgeschlossen

> **Erledigt:** Das Dedup-Skript (`tools/deduplicate_audit.sh`) hat bereits:
> - 11.108 Dateien auf 966 kanonische reduziert
> - MAIN_LeanDeep3.5 Chaos aufgelost (Kopien identifiziert, beste Version gewahlt)
> - SSoTh als kanonische Quelle erkannt und priorisiert
> - Ergebnis in `build/markers_rated/` organisiert
>
> **Nachste Aktion:** MAIN_LeanDeep3.5 und andere Backup-Dirs konnen archiviert/geloscht werden

---

## TEIL 4: API-ARCHITEKTUR (Woche 2-4)

### Tech Stack

```
[Client] -> [API Gateway / Rate Limiter]
                    |
            [Serverless Function]
                    |
        [Marker Detection Engine]
           /              \
  [MiniLM-L6-v2]    [marker_registry.json]
  (Embeddings)       (Pattern-Matching)
```

### Endpoints

```
POST /v1/analyze
  Body: { "text": "...", "language": "en|de", "layers": ["ATO","SEM","CLU","MEMA"] }
  Response: { "markers": [...], "meta": { "processing_ms": 42, "version": "5.1" } }

POST /v1/analyze/conversation
  Body: { "messages": [{"role":"A","text":"..."},{"role":"B","text":"..."}], "language": "en|de" }
  Response: { "markers": [...], "temporal_patterns": [...], "attachment_signals": {...} }

GET /v1/markers
  Response: { "total": 830, "layers": {...}, "version": "5.1" }

GET /v1/markers/{id}
  Response: { "id": "SEM_GASLIGHTING", "frame": {...}, "examples": [...] }
```

### Deployment

- **Runtime:** Cloudflare Workers oder Vercel Edge Functions
- **Model:** MiniLM-L6-v2 als ONNX (6.4MB, passt in Edge)
- **Registry:** marker_registry.json als KV-Store oder eingebettet
- **Auth:** API-Keys via Stripe-Integration
- **Metering:** Usage-Based Billing (Stripe Metered Subscriptions)

### Pricing

| Tier | Preis/Monat | Calls inkludiert | Uberschuss |
|------|------------|-----------------|-----------|
| Free | 0 EUR | 1.000 | -- |
| Starter | 49 EUR | 10.000 | 0,003 EUR/Call |
| Growth | 199 EUR | 100.000 | 0,002 EUR/Call |
| Enterprise | Custom | Unlimited | Verhandlung |

---

## TEIL 5: LAUNCH-STRATEGIE (Woche 5-8)

### Woche 5-6: Playground & Docs

1. **Interaktives Web-Playground** (Next.js/Vercel):
   - Text-Eingabe -> Marker leuchten farbig auf
   - Slider fur Confidence-Threshold
   - Export als JSON
   - "Try it" mit Beispiel-Konversationen (Gaslighting, Healthy Conflict, Love Bombing)

2. **API-Dokumentation** (Mintlify oder Readme.io):
   - Quickstart in 5 Minuten
   - Marker-Katalog mit Suchfunktion
   - Code-Beispiele (Python, JS, cURL)

### Woche 7: Soft Launch

1. RapidAPI Listing
2. Product Hunt vorbereiten
3. 3-5 Beta-Tester aus Therapie-Tech-Bereich

### Woche 8: Public Launch

1. Product Hunt Launch
2. Hacker News Show HN
3. Twitter/X Thread: "We built an API that detects manipulation patterns in text"
4. Reddit: r/MachineLearning, r/therapy, r/relationships

### Parallel (ab Woche 4): B2B Pipeline

1. SimplePractice, TherapyNotes, BetterHelp kontaktieren
2. Bumble Trust & Safety Team
3. DV-Hotline-Organisationen

---

## TEIL 6: TIMELINE-UBERSICHT (aktualisiert -- 7 Wochen, Bias-Cleanup erledigt)

```
Woche 1:     [BIAS CLEANUP] ████████████ ERLEDIGT (Renames, Stubs, Duplikate, 741 Negatives)
Woche 1:     [SCHEMA] 705 Rating-1 auf einheitliches API-Schema normalisieren
Woche 1-2:   [MARKER UPGRADE] 125 Rating-2 auf Rating-1 heben (Batch-Skript)
Woche 1-3:   [API BUILD] REST API, Auth, Metering, Edge Deployment (parallel)
Woche 3-4:   [TESTING] Integration Tests, False-Positive-Rate, Threshold-Tuning
Woche 4-5:   [PLAYGROUND] Web-Demo, Docs, Beispiel-Konversationen
Woche 6:     [SOFT LAUNCH] Beta-Tester, RapidAPI
Woche 7:     [PUBLIC LAUNCH] Product Hunt, HN, Social Media, B2B Pipeline
```

**Fortschritt:**
- Bias-Cleanup: FERTIG (12 Renames, 111 Dups, 18 Stubs, 4 Typos, 741 Negatives)
- 98.8% der Marker haben jetzt Negative Examples fur Prasizion
- 0 klinische Labels verbleibend (EU AI Act compliant)
- Nachster Schritt: Schema-Normalisierung + API-Build parallel starten

---

## TEIL 7: METRIKEN & ERFOLGSKRITERIEN

| Meilenstein | Kriterium | Ziel |
|-------------|-----------|------|
| Woche 1 | Bias-Cleanup abgeschlossen | **ERLEDIGT** -- 0 Labels, 0 Stubs, 98.8% Negatives |
| Woche 1 | Schema-Normalisierung | 705 Marker in einheitlichem API-Schema |
| Woche 2 | API-ready Marker | 800+ Rating-1 Marker (inkl. upgegraded R2) |
| Woche 3 | API deployed | < 200ms Response Time |
| Woche 5 | Playground live | Conversion > 5% Besucher -> Free Tier |
| Woche 6 | Beta-Feedback | NPS > 30 bei Beta-Testern |
| Woche 7 | Launch | 100 Free-Tier, 5 Paid |
| Monat 6 | MRR | 500 EUR+ |
| Monat 12 | MRR | 2.000-5.000 EUR |

---

## TEIL 8: RISIKEN & MITIGATION

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|-----------|
| EU AI Act verbietet Emotion Recognition | Mittel | Hoch | Als "Communication Pattern Analysis" positionieren, nicht "Emotion Recognition". Text != Biometrie |
| False-Positive-Rate zu hoch | Hoch | Hoch | Threshold-Tuning mit devset.jsonl, EWMA-Precision, konservative Defaults |
| Kein Product-Market-Fit | Mittel | Fatal | Playground als Validation BEVOR API-Build. Wenn kein Playground-Interest -> Pivot |
| Ethik-Backlash ("Uberwachungs-Tool") | Mittel | Hoch | Transparency: Open Marker Catalog, "Decision Support" Framing, Consent-Requirements |
| Skalierung der Marker-Qualitat | Hoch | Mittel | Automatisiertes Validierungs-CI, Community-Beitrage uber Review-GUI |
