Nachfolgend eine klare, überprüfbare Definition of Done (DoD) für das Gesamtprojekt – gegliedert in drei Iterationen. Jede Iteration beschreibt (a) was funktional besser/anders ist, (b) welche Artefakte entstehen, (c) wie das Ergebnis objektiv überprüft wird. Normative Regeln (z. B. SEM composed_of ≥ 2 distinkte ATO, CLU aggregiert SEM über X‑of‑Y, Intuition als CLU mit Confirm/Decay/Multiplier) sind aus der LeanDeep‑SSoT abgeleitet.

Übergreifende Mindestkriterien (gelten für alle Iterationen)

YAML valide, Schema-konform. Alle Markerdateien parsen fehlerfrei; Pflichtfelder gesetzt; examples erfüllen Mindestanzahl je Iteration. (3.3/3.4 Schema‑Regeln inkl. CI‑Checks)

Ebenenregeln eingehalten. SEM haben ≥ 2 distinkte ATO in composed_of; CLU aggregieren SEM via X‑of‑Y‑Fenster; keine CLU→ATO‑Direktverweise. (Architektur & CI‑Regeln)

Dokumentation aktualisiert. SSoT‑Abschnitte (Families/Intuition, Linting/Naming, Examples/Negativbeispiele) sind konsistent zur Implementierung.

Iteration 1 — Familien‑Packs geschlossen & Intuition funktionsfähig
Was funktional besser/anders ist

Intuition arbeitet zustandsbehaftet: Für jede Familie (INCONSISTENCY, CONSISTENCY, EFFICACY, SHUTDOWN, SUPPORT) existiert ein CLU*INTUITION*<FAMILY>, der Family‑SEMs über ein Fenster (X‑of‑Y) zu provisional → confirmed → decayed überführt. Multiplier auf familiennahe SEM/CLU‑Scores ist bei confirmed aktiv. Das verbessert die Kontextschärfe und reduziert Rauschen in Folgelogik.

Telemetry & Lernen live: counter_confirmed, counter_retracted, ewma_precision sind verdrahtet; Regeln können datengetrieben nachgeschärft werden (Fenster/Confirm‑Targets).

Zuliefer‑SEMs sind robust: Alle SEMs, die Intuition speisen, erfüllen ≥ 2 distinkte ATO (keine „Ein‑ATO‑SEM“ mehr), was die Signalgüte erhöht.

Artefakte (müssen vorhanden sein)

Für jede genannte Familie: eine Markerdatei CLU*INTUITION*<FAMILY>.yaml mit
activation.rule (X‑of‑Y), metadata.intuition.{confirm_window,confirm_rule,decay_window,multiplier_on_confirm,telemetry_keys}, ≥ 5 Beispiele.

Kuratierte Family‑SEMs (Input der CLUs) mit composed_of ≥ 2 ATO, ≥ 5 Beispielen je SEM.

Kurze Smoke‑Korpora (5–10 Sequenzen je Familie) zur Funktionsprobe.

Wie es überprüfbar ist (objektive Checks)

Regelkonformität: CI/Validator meldet 0 Verstöße gegen SEM≥2 ATO und CLU aggregiert SEM. (3.3‑CI‑Regel)

Zustandsverlauf: Auf den Smoke‑Korpora wird je Familie mindestens eine Sequenz confirmed (Zähler _.confirmed ≥ 1), anschließend decayed bei ausbleibenden Family‑SEMs (Zähler _.retracted ≥ 1). Telemetrie‑Schlüssel exakt wie im Marker gesetzt.

Dok‑Abgleich: SSoT‑Kapitel „Families & Intuition“ enthält die finalen Fensterwerte/Confirm‑Targets und stimmt 1:1 mit YAML überein.

Akzeptanzkriterium (DoD‑Haken):
„Alle fünf CLU*INTUITION*<FAMILY> existieren und funktionieren; zugehörige SEMs sind 2‑ATO‑konform; Telemetrie zählt confirmed/retracted auf bereitgestellten Testsequenzen; Beispiele ≥ 5 sind vorhanden.“

Iteration 2 — Anti‑Pattern entfernt, Naming migriert, CI härtet Architektur
Was funktional besser/anders ist

Strikte Ebenentrennung erzwingbar: 0 CLU→ATO‑Direktverweise; 0 unzulässige SEM→SEM‑Kompositionen (oder sauber dokumentierte Einzel‑Allowlist). Ergebnis: stabilere Fensterlogik, weniger falsch positive Aggregationen.

Konsistente IDs & Dateien: Alle Marker führen standardisierte Präfixe (ATO*/SEM*/CLU*/MEMA*); Dateiname = id; optional metadata.aliases für Alt‑IDs. Reduziert Referenzbrüche und erleichtert Tooling.

CI als Türsteher: Pipeline schlägt hart an bei Verstößen (Prefix‑Lint, SEM≥2 ATO, „CLU nur SEM“, Examples‑Pflichten). Qualität wird „by default“ gehalten.

Artefakte (müssen vorhanden sein)

Refaktorierte CLUs: Alle vormals ATO‑referenzierenden CLUs sind auf SEM‑Wrapper oder echte SEMs umgehängt; Diff/Mapping liegt im PR bei.

Migrations‑Map: id_migration_map mit Alt→Neu inklusive kurzer Begründung; in YAML metadata.aliases ergänzt.

CI‑Konfiguration: Workflow/Validatoren, die die o. g. Regeln prüfen (inkl. Prefix‑Lint).

Wie es überprüfbar ist (objektive Checks)

Audit‑Bericht: Tool‑Report weist 0 CLU→ATO‑Direct, 0 unzulässige SEM→SEM (außer Whitelist) aus; 0 Präfix‑/Datei‑Mismatches.

CI‑Lauf: Vollständiger grüner Lauf auf Branch‑Head; bewusst eingestreute Gegenproben (Test‑Marker mit Fehler) lassen CI rot werden → Nachweis der Wirksamkeit.

Dok‑Abgleich: SSoT‑Abschnitt „Naming & Linting“ dokumentiert Präfixe, Allowlist‑Policy und CI‑Regeln, konsistent zu den Tools.

Akzeptanzkriterium (DoD‑Haken):
„Keine Anti‑Pattern mehr im Korpus, alle IDs/Pfade normiert, CI greift hart – demonstriert durch einen grünen Regel‑Run und einen roten Negativ‑Test.“

Iteration 3 — Alle fehlenden Marker erzeugt, mit ≥ 10 Positiv‑ & ≥ 10 Negativbeispielen
Was funktional besser/anders ist

Inhaltliche Vollständigkeit: Alle zuvor im Audit identifizierten fehlenden ATO und fehlenden SEM sind vorhanden. CLUs, die unbekannte SEMs referenzierten, sind nun vollständig bedient. Das schließt Detektionslücken und stabilisiert Folge‑Cluster.

Beispiel‑Robustheit: Jeder neue Marker enthält ≥ 10 realistische positive examples und ≥ 10 realistische Negativbeispiele (in metadata.neg_examples). Das erhöht Trennschärfe, Testbarkeit und künftige Trainings‑/Eval‑Möglichkeiten. (Das Ablegen zusätzlicher Felder im metadata‑Block ist mit der 3.3/3.4‑Spezifikation kompatibel; ggf. local‑Schema für metadata freischalten.)

Artefakte (müssen vorhanden sein)

Vollständige YAMLs für alle fehlenden ATO (mit Pattern, ≥ 10 examples, ≥ 10 metadata.neg_examples).

Vollständige YAMLs für alle fehlenden SEM (composed_of ≥ 2 ATO, Activation/Scoring, ≥ 10 examples, ≥ 10 metadata.neg_examples).

Aktualisierte CLUs, die diese SEMs verwenden (keine „dangling refs“ mehr).

Wie es überprüfbar ist (objektive Checks)

Vollständigkeits‑Audit: Report weist 0 unbekannte Referenzen (ATO/SEM) aus; 0 SEM‑Kompositionsfehler.

Beispiel‑Checks: Validator bestätigt pro neuem Marker: len(examples) ≥ 10, len(metadata.neg_examples) ≥ 10, keine Duplikate, YAML‑Quoting sauber.

Regelkonformität beibehalten: Alle Iteration‑2‑Lint‑Regeln weiterhin grün (Prefix‑Lint, CLU‑Regeln, SEM≥2 ATO).

Dok‑Abgleich: SSoT‑Appendix „Negative Beispiele im metadata‑Block“ dokumentiert Format & Prüflogik; konsistent zur CI.

Akzeptanzkriterium (DoD‑Haken):
„Sämtliche zuvor fehlenden ATO/SEM existieren und sind mit ≥ 10 Positiv‑ und ≥ 10 Negativbeispielen bestückt; alle CLUs referenzieren nur existierende SEM; alle Checks grün.“

Abschluss‑DoD (Gesamtabschluss)

Funktionslage nach Iteration 3:

Intuition arbeitet evidenzbasiert mit Confirm/Decay/Multiplier und Telemetrie pro Familie (praktisch nachweisbar auf Testsequenzen).

Architektur ist technisch erzwungen (CI) und sauber geschichtet: ATO → SEM (≥ 2 ATO) → CLU (X‑of‑Y, nur SEM) → MEMA.

Korpus ist vollständig, reich an Beispielen (inkl. Negativbeispiele), und dadurch wartbar, evaluierbar und erweiterbar.

Messbare Abschluss‑Nachweise (alle erforderlich):

Grüner CI‑Run über alle Lint‑Regeln (Schema, Prefix, SEM/CLU‑Regeln, Example‑Mindestmengen).

Audit‑Report ohne Fehlereinträge (keine unbekannten Referenzen, keine Anti‑Pattern).

Smoke‑/Integration‑Protokoll: Für jede Familie mindestens ein confirmed und ein decayed Ereignis inkl. Telemetrie‑Zähler.

SSoT‑Abgleich: Dokumentierte Fenster/Confirm‑Targets, Naming‑Konventionen und Example‑Policies deckungsgleich zu YAML.

Damit ist sichtbar: besser (präzisere, lernfähige Intuition), anders (sauber erzwungene Ebenentrennung & Namenskonventionen), überprüfbar (CI/Audit/Telemetry liefern harte, reproduzierbare Belege).
