Iteration 2 — Anti‑Pattern‑Linting + Naming/Migration + CI‑Härtung

Inkrement‑Ziel: Architektur‑Konformität wird streng erzwungen. Keine CLU→ATO‑Direktverweise, keine SEM→SEM‑Komposition, Norm‑Präfixe überall. CI lässt nur noch saubere Marker durch.

Umfang (Scope)

Anti‑Pattern entfernen:

16 CLU verweisen direkt auf ATO ⇒ für jeden ATO einen SEM‑Wrapper anlegen und CLU auf SEM umhängen.

9 SEM referenzieren SEM ⇒ Referenzen in ATO‑Pärchen/-Sets übersetzen (oder justify‑Ausnahme dokumentieren).

Naming‑Migration:

5 Dateiname↔ID‑Mismatches korrigieren (z. B. SEM_UNRESOLVED_ISSUE liegt in ATO_UNRESOLVED_ISSUE.yaml).

18 unkonventionelle IDs (EMO*, ACT*, SCN*, …) in ATO*/SEM*/CLU*/MEMA\_ migrieren; aliases: optional via metadata (Deprecation‑Hinweis).

CI‑Linting erweitern: Prefix‑Lint, „SEM≥2 distinct ATO“, „CLU nur SEM\*“, examples≥5.

Vorgehen (Tasks)

T2.1 SEM‑Wrapper‑Generator für CLU→ATO
Script tools/wrap_ato_to_sem.py:

Input: Liste von ATO‑IDs (aus Audit).

Output: je ATO ein SEM*<ATO_ID>\_WRAPPER.yaml mit composed_of: [ATO*<…>] + kurzer narrative & ≥ 5 Beispiele (temporär; echte Beispiele in Iteration 3).

Patch‑Phase: CLU‑Dateien refactoren, ATO‑Refs → SEM‑Wrapper‑IDs.

T2.2 SEM→SEM‑Referenzen auflösen
Für 9 betroffene SEM die composed_of durch ATO‑Sets ersetzen; wenn SEM‑zu‑SEM wirklich beabsichtigt, kurze justification in metadata und CI‑Ausnahme nur per Whitelist‑Datei config/ci_sem_sem_allowlist.txt (default leer).

T2.3 Naming‑Migration

Mappingdatei tools/id_migration_map.csv anlegen (old_id,new_id,reason).

Script tools/rename_ids_and_files.py:

passt id: in YAML, Dateinamen, interne Referenzen (in composed_of) an,

legt in metadata.aliases die alte ID ab (für 1 Release‑Zyklus).

CI‑Regel „keine unbekannten Präfixe“.

T2.4 CI‑Härtung

.github/workflows/validate.yml → Steps:

Schema‑Lint,

python tools/ci_check.py,

python tools/family_audit.py,

python tools/neg_examples_check.py (noch soft),

Artefakt‑Upload der Reports (JSON/CSV).

Definition of Done (DoD) – Iteration 2

python tools/audit_markers.py → 0 Fälle „CLU referenziert ATO direkt“.

python tools/audit_markers.py → 0 Fälle „SEM referenziert SEM“ (oder explizit in Allowlist dokumentiert).

Alle IDs haben Präfixe ATO*/SEM*/CLU*/MEMA*; 0 Dateiname↔ID‑Mismatches.

CI‑Pipeline rot bei jeder neuen Verletzung (Fail‑fast).

SSoT‑Update „Naming & Linting“ (Migrationshinweise, Aliases, Allowlist‑Policy).
