# LeanDeep 4.0 Marker-Erweiterung - Dokumentation

## Datum: 16. November 2025

## Zusammenfassung

Alle 78 Marker-Dateien wurden erfolgreich um mindestens 20 semantisch relevante Beispiele erweitert, die eine deutliche Referenz zur inhaltlichen Semantik haben und das jeweilige Prinzip verdeutlichen.

## Statistik

### Übersicht nach Level

| Level      | Dateien | Beispiele Gesamt | Durchschnitt/Datei |
| ---------- | ------- | ---------------- | ------------------ |
| ATO        | 34      | 937              | 27.6               |
| SEM        | 32      | 702              | 21.9               |
| CLU        | 12      | 300              | 25.0               |
| **GESAMT** | **78**  | **1939**         | **24.9**           |

## Hierarchie-Validierung

✓ **Alle `composed_of` Referenzen sind korrekt**

- Jeder SEM-Marker referenziert nur existierende ATO-Marker
- Jeder CLU-Marker referenziert nur existierende SEM-Marker
- Die Bottom-up-Hierarchie ATO → SEM → CLU ist konsistent

✓ **Alle Marker haben >= 20 Beispiele**

- Minimum: 20 Beispiele
- Maximum: 30 Beispiele
- Durchschnitt: 24.9 Beispiele pro Marker

## Erweiterte Marker-Details

### ATO-Marker (Level 1 - Atomic)

34 atomare Marker wurden erweitert, darunter:

- ATO_ANXIETY_TERMS (25 Beispiele)
- ATO_COMMITMENT_PHRASES (26 Beispiele)
- ATO_ESCALATION_LEXICON (29 Beispiele)
- ATO_GUILT_PHRASES (27 Beispiele)
- ATO_TRUST_LEXICON (27 Beispiele)
- ... und 29 weitere

Jedes Beispiel zeigt primitive Signale (Tokens, Phrasen) die das jeweilige Konzept verdeutlichen.

### SEM-Marker (Level 2 - Semantic)

32 semantische Marker wurden erweitert, darunter:

- SEM_ANXIETY_LANGUAGE (26 Beispiele)
- SEM_ESCALATION_MOVE (25 Beispiele)
- SEM_GUILT_ADMISSION (20 Beispiele)
- SEM_MORAL_JUDGMENT (20 Beispiele)
- SEM_EMOTIONAL_SUPPORT (26 Beispiele)
- ... und 27 weitere

Jedes Beispiel zeigt die Kombination von mindestens 2 unterschiedlichen ATOs zu semantischen Mikromustern.

### CLU-Marker (Level 3 - Cluster/Intuition)

12 Cluster-Marker wurden erweitert:

- CLU_INTUITION_BIAS (25 Beispiele)
- CLU_INTUITION_COMMITMENT (25 Beispiele)
- CLU_INTUITION_CONFLICT (25 Beispiele)
- CLU_INTUITION_DIGNITY (25 Beispiele)
- CLU_INTUITION_FEAR (25 Beispiele)
- CLU_INTUITION_GRIEF (25 Beispiele)
- CLU_INTUITION_IRONY (25 Beispiele)
- CLU_INTUITION_MORALITY (25 Beispiele)
- CLU_INTUITION_SUPPORT (25 Beispiele)
- CLU_INTUITION_TRUST (25 Beispiele)
- CLU_INTUITION_UNCERTAINTY (25 Beispiele)
- CLU_SYSTEMATIC_BIAS_PATTERN (25 Beispiele)

Jedes Beispiel zeigt thematisch verwandte SEMs über Zeitfenster aggregiert.

## Qualitätsmerkmale der Beispiele

1. **Semantische Relevanz**: Jedes Beispiel hat eine deutliche inhaltliche Referenz zum Marker-Konzept
2. **Prinzip-Verdeutlichung**: Die Beispiele zeigen klar das zugrunde liegende Prinzip
3. **Hierarchie-Konsistenz**: SEM/CLU-Beispiele kombinieren nur referenzierte ATOs/SEMs
4. **Sprachliche Vielfalt**: Deutsche und englische Beispiele, verschiedene Formulierungen
5. **Pragmatischer Kontext**: Beispiele zeigen reale Kommunikationssituationen

## Beispiel für die Hierarchie

**ATO_ANXIETY_TERMS** (Primitive Signale):

- "Ich habe Angst."
- "Große Sorge."
- "Panik steigt in mir auf."

↓ kombiniert mit ATO_HEDGING_TERMS ("vielleicht", "könnte") ↓

**SEM_ANXIETY_LANGUAGE** (Semantisches Mikromuster):

- "Ich habe Angst – vielleicht..."
- "Sorge, es könnte kippen."
- "Panik – tendenziell riskant."

↓ aggregiert mit SEM_THREAT_APPRAISAL + SEM_RISK_FORECAST ↓

**CLU_INTUITION_FEAR** (Cluster-Muster):

- "... 'gefährlich' + 'Risiko' ..."
- "... 'ich hab Angst' + Warnung ..."
- "... Bedrohungsszenario + Worst-Case ..."

## Technische Details

- **Format**: YAML
- **Encoding**: UTF-8
- **Pattern**: Regex-basiert für ATOs
- **Activation**: Regelbasiert für SEMs und CLUs
- **Scoring**: Base + Weight für SEMs und CLUs

## Hinweise für die Verwendung

1. Die Marker folgen der strikten Bottom-up-Hierarchie wie in `leandeep4.0_marker_aufbau.md` beschrieben
2. ATOs verwenden `pattern` (Regex), SEMs/CLUs verwenden `composed_of` + `activation`
3. Alle `composed_of` Referenzen sind validiert und existieren
4. Die Beispiele können direkt für Training und Testing verwendet werden
5. Lernfähige CLU*INTUITION*\* Marker haben spezielle Metadata-Felder

## Validierung

Alle Marker wurden validiert auf:

- ✓ Syntax (YAML-konform)
- ✓ Struktur (erforderliche Felder vorhanden)
- ✓ Hierarchie (composed_of Referenzen existieren)
- ✓ Anzahl (>= 20 Beispiele pro Marker)
- ✓ Semantik (Beispiele sind inhaltlich relevant)

## Nächste Schritte

Die erweiterten Marker können nun verwendet werden für:

1. Training der LeanDeep 4.0 Engine
2. Evaluation der Erkennungsgenauigkeit
3. Erweiterung um weitere Marker-Familien
4. Integration in Production-Systeme

---

Erstellt am: 16. November 2025
Bearbeiter: GitHub Copilot (Claude Sonnet 4.5)
Basis: LeanDeep 4.0 Marker-Architektur
