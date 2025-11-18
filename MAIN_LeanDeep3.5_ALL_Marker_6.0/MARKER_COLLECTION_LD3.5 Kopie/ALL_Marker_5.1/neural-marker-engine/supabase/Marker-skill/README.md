# Marker-Skill Collection: LeanDeep 4.0 Schema

## Überblick

Diese Collection enthält Marker-Definitionen nach dem **LeanDeep 4.0 Schema**, strukturiert in:

- **ATO (Atomic Topic Orientations)**: Atomare Bausteine
- **SEM (Semantic Markers)**: Zusammengesetzte semantische Muster

## Hauptmarker: SEM_LOGISTICAL_PRESSURE

Der Kandidat-Marker `SEM_LOGISTICAL_PRESSURE` identifiziert logistischen Stress, der durch externe Blockaden und gescheiterte Planung entsteht.

### Strikte Kompositionsregel

**SEM_LOGISTICAL_PRESSURE** wird nur aktiviert, wenn **≥2 unterschiedliche ATOs** erkannt werden:

| ATO Typ                   | Beschreibung                                             |
| ------------------------- | -------------------------------------------------------- |
| `ATO_EXTERNAL_CONSTRAINT` | Unkontrollierbare externe Blockaden                      |
| `ATO_PLANNING_FAILURE`    | Gescheiterte Zeitpläne/Vorhaben                          |
| `ATO_FRUSTRATION`         | Emotionale Frustration (muss kontextuell verbunden sein) |

## Marker-Dateien

### ATOs (Bausteine)

1. **ATO_EXTERNAL_CONSTRAINT.json** - Externe Blockaden (Verkehr, Sperrungen, etc.)
2. **ATO_PLANNING_FAILURE.json** - Gescheiterte Zeitpläne und Verzögerungen
3. **ATO_FRUSTRATION.json** - Allgemeine Frustrations-Marker
4. **ATO_DELAY_PHRASE.json** - Verzögerungsphrasen (für Kontrast)
5. **ATO_HEDGING_VOCAB.json** - Abschwächendes Vokabular (für Kontrast)

### SEMs (Semantische Marker)

1. **SEM_LOGISTICAL_PRESSURE.json** - Haupt-Marker: Logistischer Stress
2. **SEM_AVOIDANT_BEHAVIOR.json** - Kontrast-Marker: Interpersonelles Vermeidungsverhalten

## Verwendung

### Aktivierungsbeispiel (Gültig)

```
Text: "Oh Gott der Horror ey. Es ist alles zu. Die komplette Autobahn"

Erkannte ATOs:
- ATO_FRUSTRATION: "Der Horror ey"
- ATO_EXTERNAL_CONSTRAINT: "alles zu"
- ATO_EXTERNAL_CONSTRAINT: "komplette Autobahn"

SEM aktiviert: ✓ SEM_LOGISTICAL_PRESSURE
Grund: ≥2 unterschiedliche ATOs (FRUSTRATION + EXTERNAL_CONSTRAINT)
Intensität: 0.80
```

### Regelbruch (Ungültig)

```
Text: "Berlin ist total zu... wegen irgend nem Marathon. Stecken komplett fest"

Erkannte ATOs:
- ATO_EXTERNAL_CONSTRAINT: "total zu"
- ATO_EXTERNAL_CONSTRAINT: "Marathon"
- ATO_EXTERNAL_CONSTRAINT: "komplett fest"

SEM aktiviert: ✗ Regel verletzt
Grund: Nur 1 ATO-Typ erkannt (nur EXTERNAL_CONSTRAINT)
Benötigt: ≥2 unterschiedliche ATO-Typen
```

## RF-Manifestation

```
Formel: L2-BRONZE × SEM_LOGISTICAL_PRESSURE
Interpretation: Blockierte Handlungsfähigkeit durch externe Hürden
Base Intensity: 0.75
Range: 0.65 - 0.85
```

## SFT-Training

Jeder SEM enthält 10+ SFT-Beispiele (Supervised Fine-Tuning) für:

- Positive Aktivierungen
- Negative Beispiele (Regelverletzungen)
- Edge Cases
- Kontrast-Beispiele (z.B. interpersonell vs. logistisch)

## Metadaten

- **Schema**: LeanDeep 4.0
- **Erstellungsdatum**: 2025-11-10
- **Version**: 1.0
- **Kontext-Fenster**: 3-5 Nachrichten
- **Domänen**: Logistik, Verkehr, Zeitmanagement, Externe Blockaden

## Anwendungsfälle

- Verkehrsstress-Analyse
- Zeitmanagement-Probleme
- Logistik-Blockaden
- Ad-hoc Stress-Erkennung
- Unterscheidung logistischer vs. interpersoneller Frustration

## Lizenz & Credits

LeanDeep 4.0 Schema  
Marker Collection Version 5.1  
Neural Marker Engine
