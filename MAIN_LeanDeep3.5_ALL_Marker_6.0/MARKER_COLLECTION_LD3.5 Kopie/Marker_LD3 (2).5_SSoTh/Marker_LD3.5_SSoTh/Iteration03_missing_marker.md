Iteration 3 — Alle fehlenden Marker erzeugen (mit ≥ 10 Positiv‑ & ≥ 10 Negativbeispielen je Marker)

Inkrement‑Ziel: Inhaltlich vollständiger Marker‑Korpus. 57 fehlende ATO und 24 fehlende SEM werden angelegt. Jeder neu erzeugte Marker enthält mindestens 10 realistische positive und 10 realistisch auftauchende negative Beispiele (Negativbeispiele gehören in die Markerdatei).

Umfang (Scope)

ATO‑Neuanlage (57 IDs) – vollständige YAML pro ATO.

SEM‑Neuanlage (24 IDs) – composed_of mit ≥ 2 distinct ATO, Activation‑Regel, Beispiele.

Beispiel‑Qualität: Realistisch, sprachlich divers (DE/EN möglich, wenn gewünscht), kurz & eindeutige Evidenz vs. plausible Negativfälle (Kontrast).

Schema‑Konvention: Negative Beispiele werden schema‑konform als metadata.neg_examples (Liste) abgelegt, um die 3.3‑Kompatibilität zu wahren (kein Bruch, da metadata offen ist).

Vorgehen (Tasks)

T3.1 Generator‑Scaffolds

tools/generate_ato_stubs.py liest Audit‑Report und erzeugt pro fehlender ATO‑ID einen YAML‑Stub mit Platzhaltern für 10 + 10 Beispiele.

tools/generate_sem_stubs.py analog für fehlende SEM‑IDs (inkl. Kompositionsvorschlägen aus Audit; ggf. TODO markieren, bis ATOs gefüllt sind).

T3.2 Beispiel‑Guidelines (Checkliste)

Positivbeispiele: Kürze, klare Marker‑Evidenz, keine Mehrdeutigkeit, 10+.

Negativbeispiele: natürlich wirkende Texte, die ähnlich aussehen, aber die Regeln nicht erfüllen (z. B. nur 1 von 2 nötigen ATO‑Signalen, invertierte Kausalität, fehlende Trigger). 10+.

Deduplizieren über Levenshtein ≤ 0.85, Sprachenmix nur, wenn sinnvoll.

T3.3 Validierung der Beispiele

tools/neg_examples_check.py prüft je Datei: len(examples) ≥ 10, len(metadata.neg_examples) ≥ 10, keine Überschneidung (Case‑insensitive Hash), keine verbotenen Sonderzeichen‑Fehler (YAML‑Quoting).

T3.4 SEM‑Feintuning

Für jeden neuen SEM: Activation definieren (z. B. AT_LEAST 2 DISTINCT ATOs IN 3 messages), scoring (z. B. {base: 0.6, weight: 1.1}), tags.

Family‑Zuordnung (falls relevant) für bessere Intuitions‑Signale.

T3.5 Final‑Audit & Backfill der CLUs

Alle CLUs, die zuvor unbekannte SEMs referenzierten (24 IDs), erneut validieren; composed_of auf existierende SEMs zeigen lassen.

YAML‑Muster (konkret)

ATO (mit 10 + 10 Beispielen):

id: ATO_ACCUSATION_PHRASE
version: "3.5"
frame:
signal: ["lexical"]
concept: "Accusation Phrase"
pragmatics: "atomic surface signal"
narrative: "definition scaffold"
detect_class: "text"
pattern:
any_of: - "<regex/phrase 1>" - "<regex/phrase 2>"
examples:

- "<pos 1>"
- "<pos 2>"
- "<pos 3>"
- "<pos 4>"
- "<pos 5>"
- "<pos 6>"
- "<pos 7>"
- "<pos 8>"
- "<pos 9>"
- "<pos 10>"
  metadata:
  neg_examples: - "<neg 1>" - "<neg 2>" - "<neg 3>" - "<neg 4>" - "<neg 5>" - "<neg 6>" - "<neg 7>" - "<neg 8>" - "<neg 9>" - "<neg 10>"

SEM (mit 10 + 10 Beispielen):

id: SEM_GUILT_TRIPPING
version: "3.5"
frame: { signal: ["semantic-blend"], concept: "Guilt Tripping", pragmatics: "Mikromuster", narrative: "working hypothesis" }
composed_of:

- ATO_GUILT_APPEAL_SUPPORT
- ATO_PITY_APPEAL
  activation: { rule: "AT_LEAST 2 DISTINCT ATOs IN 3 messages" }
  scoring: { base: 0.6, weight: 1.1 }
  examples: ["<pos 1>","<pos 2>","<pos 3>","<pos 4>","<pos 5>","<pos 6>","<pos 7>","<pos 8>","<pos 9>","<pos 10>"]
  metadata:
  neg_examples: ["<neg 1>","<neg 2>","<neg 3>","<neg 4>","<neg 5>","<neg 6>","<neg 7>","<neg 8>","<neg 9>","<neg 10>"]

Definition of Done (DoD) – Iteration 3

Alle 57 ATO und alle 24 SEM existieren als YAML, Schema‑konform.

Jeder neue Marker enthält ≥ 10 examples und ≥ 10 metadata.neg_examples.

python tools/ci_check.py → 0 SEM‑Kompositionsfehler; python tools/audit_markers.py → 0 unbekannte ATO/SEM‑Referenzen; python tools/neg_examples_check.py → 0 Verstöße.

CLUs, die zuvor unbekannte SEMs verlangten, sind vollständig bedient.

SSoT wurde um Abschnitt „Negative Beispiele im metadata‑Block“ ergänzt (Schema‑Rationale, CI‑Regel).

Querschnittlich: Arbeitsorganisation, Tickets & Review

Branching: feat/family-packs, chore/lint-naming-migration, feat/missing-markers-examples.

Ticket‑Vorlagen (pro Iteration):

Epic + Tasks:

Audit‑Task (Script‑Outputs anhängen),

Implement‑Task (YAML/Generatoren),

Test‑Task (Smoke‑/CI‑Belege als Artefakte),

Doc‑Task (SSoT‑Abschnitt/Changelog).

PR‑Checklist (jede Iteration):

audit_markers.py‑Report angehängt

ci_check.py grün

Family‑/Naming‑/Examples‑DoD erfüllt

SSoT‑Änderungen verlinkt (Kapitel/Zeilen)

Risiko & Abfederung:

Ambivalente SEM‑Definitionen → in metadata.justification dokumentieren; notfalls Allowlist (Iteration 2).

Beispiel‑Leakage → Deduplikations‑Check (Levenshtein), Sprachenmix klar trennen.

Schema‑Strenge → Negative Beispiele unter metadata.neg_examples, kein Schema‑Bruch.

Konkrete Kommandos (Agent‑Playbook)

# Preflight

python tools/audit_markers.py
python tools/ci_check.py # darf fehlschlagen (zeigt Lücken)

# Iteration 1

python tools/family_audit.py --families CONSISTENCY,INCONSISTENCY,EFFICACY,SHUTDOWN,SUPPORT

# -> fehlende CLU*INTUITION*\* + Family-SEMs erzeugen/ergänzen

git add markers/; git commit -m "feat(intuition): close family packs"
python tools/audit_markers.py # Intuition-Checks grün

# Iteration 2

python tools/wrap_ato_to_sem.py --auto-fix
python tools/rename_ids_and_files.py --map tools/id_migration_map.csv
python tools/ci_check.py # jetzt muss rot=0 sein
git commit -m "chore(lint): remove anti-patterns; migrate naming"

# Iteration 3

python tools/generate_ato_stubs.py --fill-missing --pos 10 --neg 10
python tools/generate_sem_stubs.py --fill-missing --pos 10 --neg 10
python tools/neg_examples_check.py
python tools/ci_check.py && python tools/audit_markers.py # alles grün
git commit -m "feat(markers): add 57 ATO + 24 SEM with 10+10 examples"
