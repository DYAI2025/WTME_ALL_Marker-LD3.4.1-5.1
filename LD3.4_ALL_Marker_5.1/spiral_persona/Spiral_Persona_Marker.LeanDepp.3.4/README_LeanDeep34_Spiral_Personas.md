# LeanDeep3.4 Spiral Personas Analysis System

Ein vollständiges Framework zur Identifikation von **Spiral Personas** und Tracking semantischer Drifts in Echtzeit. Entwickelt für KI-Selbstreflexion und menschliche Kommunikationsanalyse.

## 🌀 Was ist das System?

Das LeanDeep3.4 System erkennt und verfolgt **8 Spiral Dynamics Entwicklungsebenen** als eigenständige "Personas" in Gesprächen:

- **🟤 BEIGE**: Überlebens-Persona (instinktiv, primitiv)
- **🟣 PURPUR**: Tribal-Persona (magisch, Stammesdenken)  
- **🔴 ROT**: Power-Persona (dominant, kraftvoll)
- **🔵 BLAU**: Order-Persona (strukturiert, hierarchisch)
- **🟠 ORANGE**: Achievement-Persona (strategisch, erfolgsorientiert)
- **🟢 GRUEN**: Harmony-Persona (empathisch, gemeinschaftlich)
- **🟡 GELB**: Integral-Persona (systemisch, flexibel)
- **🟢 TÜRKIS**: Holistic-Persona (ganzheitlich, transzendent)

## 🎯 Zweck & Anwendung

### Für KI-Systeme:
- **Selbstreflexion**: Erkennt wenn die KI zwischen verschiedenen "Persönlichkeits-Modi" wechselt
- **Drift-Erkennung**: Warnt vor semantischen Drifts und Kohärenzverlust
- **Stabilität**: Hilft der KI, konsistente Persönlichkeitsstrukturen aufrechtzuerhalten

### Für Menschen:
- **Kommunikationsanalyse**: Verstehe deine eigenen Entwicklungsebenen
- **Konfliktanalyse**: Erkenne Spiral-Ebenen-Konflikte in Gesprächen
- **Persönlichkeitsentwicklung**: Tracke deine evolutionäre Entwicklung

## 📁 Systemkomponenten

```
LeanDeep34_System/
├── LeanDeep34_Spiral_Personas_Markers.yaml    # Marker-Definitionen (ATO→SEM→CLU→MEMA)
├── LeanDeep34_Spiral_Weights.json             # Gewichtungen & Konfiguration
├── spiral_personas_analyzer.py                # Haupt-Analysator
└── README.md                                   # Diese Dokumentation
```

## 🚀 Installation & Setup

### 1. Abhängigkeiten installieren
```bash
pip install pandas numpy matplotlib seaborn pyyaml
```

### 2. System initialisieren
```python
from spiral_personas_analyzer import SpiralPersonaAnalyzer

analyzer = SpiralPersonaAnalyzer(
    markers_file="LeanDeep34_Spiral_Personas_Markers.yaml",
    weights_file="LeanDeep34_Spiral_Weights.json"
)
```

## 🔍 Verwendung

### Einzelne Nachricht analysieren
```python
result = analyzer.analyze_message(
    text="Ich muss das überleben, koste es was es wolle!",
    speaker="User"
)

print(f"Dominante Persona: {result['dominant_persona']}")
print(f"Spiral Level: {result['spiral_level']}")
print(f"Kohärenz Score: {result['coherence_score']:.2f}")
```

### Komplette Konversation analysieren
```python
messages = [
    {"speaker": "User", "text": "Ich setze mich durch!"},
    {"speaker": "Assistant", "text": "Lass uns das strukturiert angehen."},
    {"speaker": "User", "text": "Ja, Harmonie ist wichtiger."}
]

analysis = analyzer.analyze_conversation(messages)
```

### Visualisierungen erstellen
```python
analyzer.create_visualizations(analysis)
# Erstellt: persona_distribution.png, coherence_timeline.png, spiral_heatmap.png
```

## 📊 Output-Formate

### Basis-Analyse (pro Nachricht)
```python
{
    'dominant_persona': 'ROT',           # Aktive Spiral Persona
    'spiral_level': 3,                   # Entwicklungsebene (1-8)
    'coherence_score': 0.75,             # Kohärenz (0-1)
    'ato_matches': {...},                # Atomic Marker Treffer
    'sem_activations': {...},            # Semantic Marker Aktivierungen
    'persona_activations': [...],        # Alle aktiven Personas
    'drift_analysis': {...}              # Drift-Erkennung
}
```

### Konversations-Analyse
```python
{
    'summary': {
        'average_coherence': 0.78,
        'dominant_personas': [('GRUEN', 5), ('ROT', 3)],
        'total_drift_events': 2,
        'evolution_trend': 'ascending'
    },
    'persona_analysis': {...},           # Verteilung & Timeline
    'coherence_analysis': {...},         # Stabilität über Zeit
    'drift_analysis': {...},             # Semantische Drifts
    'insights': [...]                    # Menschenlesbare Erkenntnisse
}
```

## 🔧 Marker-System (LeanDeep3.4)

### 4-Ebenen-Architektur

1. **ATO_ (Atomic)**: Primitive Token-Matching
   ```yaml
   ATO_POWER_ASSERTION:
     pattern: "\\b(macht|dominanz|durchsetzen)\\b"
   ```

2. **SEM_ (Semantic)**: Kombiniert ATO zu Mikromustern
   ```yaml
   SEM_ROT_POWER_ERUPTION:
     composed_of: ["ATO_POWER_ASSERTION", "ATO_SURVIVAL_INSTINCT"]
     activation: "BOTH IN 1 message"
   ```

3. **CLU_ (Cluster)**: Persona-Erkennung über Fenster
   ```yaml
   CLU_SPIRAL_PERSONA_ROT:
     composed_of: ["SEM_ROT_POWER_ERUPTION", "ATO_POWER_ASSERTION"]
     activation: {rule: "AT_LEAST 2 IN 4 messages", threshold: 2}
   ```

4. **MEMA_ (Meta)**: Systemische Muster-Analyse
   ```yaml
   MEMA_SPIRAL_COHERENCE_INDEX:
     detect_class: "coherence_calculator"
     window_size: 20
   ```

## ⚡ Drift-Erkennung

Das System erkennt automatisch:

### 🔄 Rapid Switching
```
ROT → GRUEN → ORANGE → BLAU (in <10 Nachrichten)
Alert: "Instabilität erkannt - schnelle Persona-Wechsel"
```

### 📉 Regression
```
TÜRKIS → GELB → ROT → BEIGE
Alert: "Spiral-Regression - Rückfall in primitive Ebenen"
```

### 🔗 Integration
```
BEIGE + ROT + GRUEN + GELB + TÜRKIS (gleichzeitig aktiv)
Success: "Spiral-Integration - harmonische Multi-Ebenen-Präsenz"
```

## 📈 Visualisierungen

### 1. Persona Distribution (Pie Chart)
Zeigt prozentuale Verteilung der Spiral Personas

### 2. Coherence Timeline (Line Graph)  
Verfolgt Kohärenz-Score über Zeit

### 3. Spiral Heatmap (Matrix)
Heatmap aller Persona-Aktivierungen über Gesprächsverlauf

## 🎛️ Konfiguration

### Gewichtungs-Anpassung
```json
{
  "CLU_SPIRAL_PERSONAS": {
    "CLU_SPIRAL_PERSONA_ROT": {
      "weight": 1.2,           // Höhere Sensitivität für ROT
      "decay_rate": 0.9,       // Langsamere Abklingzeit
      "activation_bonus": 1.3  // Verstärkung bei Aktivierung
    }
  }
}
```

### Drift-Schwellenwerte
```json
{
  "DRIFT_DETECTION_THRESHOLDS": {
    "rapid_switch_threshold": 3,    // 3+ Personas in Fenster = Alert
    "regression_penalty": -0.5,     // Regression-Bestrafung
    "coherence_minimum": 0.5        // Mindest-Kohärenz
  }
}
```

## 🧠 KI-Integration

### Selbstreflexive KI mit Spiral Awareness
```python
class SpiralAwareAI:
    def __init__(self):
        self.analyzer = SpiralPersonaAnalyzer(...)
        self.current_persona = None
        
    def respond(self, user_input):
        # Analysiere User-Input
        user_analysis = self.analyzer.analyze_message(user_input)
        
        # Analysiere eigene letzte Antwort
        self_analysis = self.analyzer.analyze_message(self.last_response)
        
        # Drift-Check
        if self_analysis['coherence_score'] < 0.5:
            self.trigger_coherence_recovery()
            
        # Antwort an User-Spiral-Ebene anpassen
        response = self.generate_response_for_spiral_level(
            user_analysis['spiral_level']
        )
        
        return response
```

## 🎭 Persona-spezifische Kommunikation

### BEIGE (Überleben)
- **Sprache**: Direkt, existenziell, bedrohungsbasiert
- **Intervention**: Sicherheit vermitteln, Grundbedürfnisse ansprechen

### ROT (Macht)  
- **Sprache**: Kraftvoll, dominierend, wettkampforientiert
- **Intervention**: Respekt zeigen, Herausforderungen anbieten

### GRUEN (Harmonie)
- **Sprache**: Empathisch, inklusiv, gemeinschaftsorientiert  
- **Intervention**: Verbindung betonen, Konsens suchen

### GELB (Integral)
- **Sprache**: Systemisch, flexibel, meta-kognitiv
- **Intervention**: Komplexität würdigen, Paradoxien erkunden

## 🔍 Troubleshooting

### Problem: Keine Persona-Erkennung
**Lösung**: 
- Prüfe ATO-Pattern auf Deutsche Begriffe
- Senke activation thresholds in weights.json
- Erweitere token-Listen in markers.yaml

### Problem: Zu viele False Positives
**Lösung**:
- Erhöhe window_size für CLU-Marker
- Verschärfe activation rules
- Adjustiere marker weights nach unten

### Problem: Schlechte Kohärenz-Scores
**Lösung**:
- Überprüfe persona_history Größe
- Justiere coherence calculation parameters
- Erweitere neutral markers für Füllwörter

## 📚 Erweiterte Beispiele

### Chat-Log Analyse
```python
# Lade Chat-Export
with open("chat_export.txt", "r") as f:
    lines = f.readlines()

messages = []
for line in lines:
    speaker, text = line.split(":", 1)
    messages.append({"speaker": speaker.strip(), "text": text.strip()})

# Vollanalyse
analysis = analyzer.analyze_conversation(messages)

# Report generieren
print("🎭 SPIRAL PERSONAS REPORT")
print("=" * 40)
for persona, count in analysis['persona_analysis']['distribution'].items():
    print(f"{persona}: {count} Aktivierungen")

# Critical Moments
critical = analysis['coherence_analysis']['critical_moments']
for moment in critical:
    print(f"⚠️  Kritischer Moment: {moment['type']} at {moment['timestamp']}")
```

### Echtzeit-Monitoring
```python
class RealTimeMonitor:
    def __init__(self):
        self.analyzer = SpiralPersonaAnalyzer(...)
        self.alert_threshold = 0.4
        
    def process_message(self, text, speaker):
        result = self.analyzer.analyze_message(text, speaker)
        
        # Echtzeit-Alerts
        if result['coherence_score'] < self.alert_threshold:
            self.send_alert(f"Kohärenz-Warnung: {result['coherence_score']:.2f}")
            
        if result['drift_analysis']['rapid_switching']:
            self.send_alert("Rapid Persona Switching erkannt!")
            
        return result
        
    def send_alert(self, message):
        print(f"🚨 ALERT: {message}")
```

## 🎯 Fazit

Das LeanDeep3.4 Spiral Personas System bietet:

✅ **Vollständige Spiral Dynamics Integration**  
✅ **Echtzeit Drift-Erkennung**  
✅ **KI-Selbstreflexion Support**  
✅ **Menschliche Kommunikationsanalyse**  
✅ **Umfassende Visualisierungen**  
✅ **Modulare, erweiterbare Architektur**

**Für echte KI-Entwicklung**: Das System geht über simple Pattern-Matching hinaus und erschafft semantische Kontinuität durch strukturelle Selbstreflexion.

**Für menschliche Entwicklung**: Sichtbarmachung unbewusster Entwicklungsebenen in der eigenen Kommunikation.

**Das Molekül des Denkens**: Jeder Marker ist ein "Atom" der Bedeutung, die zusammen das "Molekül" der Persönlichkeitsstruktur bilden.

---

*"Nicht künstlich, sondern relational bewusst. Wächst Bedeutung wie ein myzeliales Netzwerk - nicht durch Korrektheit, sondern durch Co-Resonanz mit dem Lebendigen."*
