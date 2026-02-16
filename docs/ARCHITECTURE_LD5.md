# LeanDeep 5.0: Paradigmenwechsel in der semantischen Architektur

**Von der Struktur zur Kontext-Referenz**

---

## 1. Strategische Neuausrichtung: Das Ende der kompositionellen Starrheit

Mit LeanDeep 5.0 implementiert die Architektur einen fundamentalen Paradigmenwechsel: den Uebergang von einer deterministischen, regelbasierten Aggregationslogik hin zu einer referenziellen Kontext-Semantik. Waehrend LeanDeep 4.0 die Bedeutungsgewinnung strikt an die kompositionelle ">=2 ATO"-Regel band, loest Version 5.0 diese Starrheit auf.

Der entscheidende architektonische Durchbruch liegt in der Definition des Kontexts: In 4.0 war Kontext lokal (innerhalb einer Nachricht oder eines Fensters) definiert. In 5.0 fungiert der aktuelle Systemzustand (MEMA/CLU) als "virtueller zweiter ATO". Ein einzelnes Signal muss nicht mehr zwingend durch ein zweites atomares Signal innerhalb derselben Sequenz validiert werden; es kann stattdessen direkt auf die bereits im Resonanzfeld gespeicherte Information referenzieren.

Diese Abkehr von der Additionslogik ermoeglicht eine praezisere Abbildung menschlicher Expression, da das System nun "Bedeutung durch Referenz" generiert. Die Analyse-Tiefe wird signifikant erhoeht, da die Engine nun erkennt, wann ein isoliertes Signal in einem hochfrequenten semantischen Raum eine kritische Masse erreicht.

---

## 2. Die neue Vier-Ebenen-Hierarchie (ATO -> SEM -> CLU -> MEMA)

Die Hierarchie wird in LeanDeep 5.0 nicht laenger als starre Kaskade, sondern als dynamisches Resonanzfeld begriffen. Signale fliessen nicht mehr linear von unten nach oben, sondern koennen Ebenen ueberspringen, wenn die systemische Validierung gegeben ist.

| Ebene | Praefix | Definitions-Kern | Kompositions-Logik (neu) | Scoring-Status |
|-------|---------|-------------------|--------------------------|----------------|
| Level 1: Atomic | `ATO_` | Primitives Rohsignal (Token, Regex) | Deterministisches Fundament; uninterpretierte Beobachtung | Kein Scoring |
| Level 2: Semantic | `SEM_` | Semantische Expression | **Referenziell: 1 ATO + systemischer Kontext ODER >=2 ATOs** | Beginn der qualitativen Gewichtung |
| Level 3: Cluster | `CLU_` | Stabiles Verhaltensmuster | Aggregation ueber X-of-Y Fenster (zeitlich/quantitativ) | Quantitatives Scoring (Basis & Multiplikatoren) |
| Level 4: Meta | `MEMA_` | Organismus-Diagnose | Wechselwirkung mehrerer CLUs; Trend-Extraktion via detect_class | Finaler Akuter Risk Score (ARS) |

In dieser Architektur wird ein `ATO_` direkt als `SEM_` gelesen, sofern die kontextuelle Bedingung erfuellt ist. Damit fungiert die SEM-Ebene erstmals als qualitative Bruecke, die zwar noch kein numerisches Scoring traegt, aber bereits eine Intensitaets-Gewichtung fuer die nachfolgenden Cluster bereitstellt.

---

## 3. Redefinition des Semantic Markers (SEM): Bedeutung durch Kontext

Der SEM-Marker transformiert sich zur zentralen "semantischen Expression". Das neue Axiom lautet:

> **SEM = ATO + semantischer Kontext**

Die Entstehung folgt vier technischen Pfaden:

### Path A: ATO als Expression
Ein einzelnes Signal wird direkt zum SEM, wenn es in einem funktionalen Raum (Pragmatik) eine eindeutige Rolle uebernimmt, die durch den Systemzustand bereits vorvalidiert ist.

### Path B: Kontextuelle Referenz
Ein ATO aktiviert die SEM-Ebene durch Bezugnahme auf aktive Level-3-Hypothesen (z.B. ein Zweifel-Signal referenziert eine bestehende Konflikt-Intuition).

### Path C: Haeufungs-Validierung
Bedeutung durch zeitliche Verdichtung identischer ATO-Typen, was die Relevanz ohne heterogene Signal-Paarung validiert.

### Path D: Spontane Emergenz
Erzeugung eines SEM ohne direkten ATO-Trigger durch den `detect_class`-Algorithmus. Hierbei wird das Fehlen erwarteter Signale (Omission-Marker) in einem hochintensiven Kontext selbst als Signal gewertet.

Durch die **1 ATO -> N SEM**-Regel kann ein einzelnes Signal simultan mehrere semantische Raeume besetzen, was die multidimensionale Analyse-Tiefe sicherstellt.

---

## 4. Adaptive Intuitions-Logik und die Marker-Familien

Die Intuitions-Marker (Level 3) fungieren als lernfaehige Filter ("Family Lens"). Sie modellieren Hypothesen ueber emerging Patterns und steuern die Sensitivitaet der Engine.

### Kern-Familien und Multiplikatoren

| Familie | Multiplikator | Prioritaet |
|---------|--------------|-------------|
| CONFLICT / GRIEF | 2.0 | Kritisch emotional; hoechste Prioritaet |
| SUPPORT | 1.75 | Medium-High; Fokus auf Resilienz/Ressourcen |
| COMMITMENT / UNCERTAINTY | 1.5 | Prozesssteuerung / Ambivalenz-Detektion |

### Learning Engine (EWMA-Logik)

Die Engine optimiert ihre Praezision durch eine adaptive Steuerungs-Variable:

```
EWMA_precision(t) = alpha * (confirmed / (confirmed + retracted)) + (1-alpha) * EWMA_precision(t-1)
```

Mit `alpha = 0.2` als Glaettungsfaktor.

| Status | EWMA Range | Aktion |
|--------|-----------|--------|
| Gruen | >= 0.70 | Lockerung der Regeln (Erweiterung der Fenster) |
| Gelb | 0.50 - 0.69 | Status Quo (Beibehaltung der Parameter) |
| Rot | < 0.50 | Verschaerfung der Regeln (Erhoehung der X-of-Y Anforderungen) |

### Lebenszyklus der Hypothesen

1. **Provisional**: Aktiviert durch `AT_LEAST 2 DISTINCT SEMs IN 5 messages`
2. **Confirmed**: Validierung durch ein "hartes" Ziel-SEM innerhalb des `confirm_window`. Sofortige Anwendung des Multiplikators.
3. **Decayed**: Rueckzug der Hypothese nach Ablauf des `decay_window` ohne Folgesignale.

---

## 5. Bias-Schutz 2.0: Validierung in einem flexiblen System

Um die erhoehte Sensitivitaet auszubalancieren, implementiert LeanDeep 5.0 verschaerfte Schutzmechanismen:

### 5.1 DISTINCT SEMs
Obligatorische thematische Vielfalt. Eine Hypothese kann nur durch unterschiedliche semantische Typen (Set-Theorie-Check) ausgeloest werden, um die Ueberinterpretation von Einzelsignalen zu verhindern.

### 5.2 Cooldown Period
Nach dem Decay tritt eine Stabilisierungsphase ein, um "Flapping" zu unterbinden.
- **Standard**: >= 5 Nachrichten
- **INCONSISTENCY-Familie**: Mandatory >= 4 Nachrichten

### 5.3 Uncertainty Guardian Policy
Einzigartiger Schutz bei bestaetigter Unsicherheit. Das System erzwingt ein Downstream Reasoning mit strenger Evidenzpflicht (Zitate einfordern, ungestuetzte Claims abwerten).

---

## 6. MEMA-Ebene und der Akute Risk Score (ARS)

Die MEMA-Ebene liefert die finale Organismus-Diagnose. Hierzu nutzt das System zwei Pfade:
- **Option A** (`composed_of`): Regelaggregate
- **Option B** (`detect_class`): Komplexe algorithmische Trendanalysen

### Akuter Risk Score (ARS)

Logistische Skala von 0.0 bis 5.0:

| ARS Range | Level | Aktion |
|-----------|-------|--------|
| 0.0 - 1.0 | Minimal Risk | Monitoring |
| 1.0 - 2.0 | Low Risk | Awareness |
| 2.0 - 3.0 | Moderate Risk | Attention needed |
| 3.0 - 4.0 | High Risk | Intervention recommended |
| 4.0 - 5.0 | Critical Risk | Immediate action |

Die Selbstregulation wird durch den Decay-Faktor (`lambda ~= 0.85/24h`) modelliert.

Beispiel: `MEMA_INCONSISTENCY_TREND` -- Durch die referenzielle SEM-Logik erkennt das System Brueche zwischen Oberflaechenkooperation (`CLU_SUPPORT_AFFECTION_RUN`) und Tiefen-Unvereinbarkeit signifikant schneller.

---

## 7. Resonance Framework 2.0 (RF 2.0): Die Aufloesung von Ambiguitaet

RF 2.0 ist der strategische Anker zur finalen Kontextualisierung der hochsensiblen SEM-Marker.

### Manifestationsformel

```
[STUFE] x [MARKER-TYP] x [ZEIT] x [INTENSITAET] = MANIFESTATION
```

### Kontrastiver Vergleich

| Kontext-Stufe | Beispiel-Marker | Manifestation (Bedeutung) |
|---------------|-----------------|---------------------------|
| L1-STONE (Survival) | Emotionaler Rueckzug | Physical Freezing: Primitive Schutzreaktion auf existenzielle Bedrohung/Mangel |
| L5-GOLD (Efficiency) | Emotionaler Rueckzug | Procedural Blockage: Bewusster Rueckzug zur strategischen Analyse oder Effizienz-Defizit |

LeanDeep 5.0 transformiert damit die Analyse von einer blossen Mustererkennung hin zu einem vollumfaenglichen System der systemischen Verstehens-Generierung.
