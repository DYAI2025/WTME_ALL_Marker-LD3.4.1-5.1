#!/usr/bin/env python3
"""
LeanDeep3.4 Spiral Personas Analyzer
Identifiziert Spiral Personas und verfolgt semantische Drifts in Echtzeit
"""

import json
import yaml
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
import re
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

@dataclass
class PersonaActivation:
    """Repräsentiert eine aktive Spiral Persona"""
    persona: str
    level: int
    confidence: float
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    markers_triggered: List[str] = field(default_factory=list)

@dataclass
class DriftEvent:
    """Repräsentiert ein semantisches Drift-Ereignis"""
    event_type: str  # 'switch', 'regression', 'integration'
    from_persona: Optional[str]
    to_persona: Optional[str]
    severity: float
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)

class SpiralPersonaAnalyzer:
    """
    Hauptanalyzer für Spiral Personas und semantische Drifts
    Kompatibel mit LeanDeep3.4 Framework
    """
    
    def __init__(self, markers_file: str, weights_file: str):
        """Initialize analyzer with marker definitions and weights"""
        self.markers = self._load_markers(markers_file)
        self.weights = self._load_weights(weights_file)
        
        # Spiral level hierarchy
        self.spiral_hierarchy = {
            'BEIGE': 1, 'PURPUR': 2, 'ROT': 3, 'BLAU': 4,
            'ORANGE': 5, 'GRUEN': 6, 'GELB': 7, 'TUERKIS': 8
        }
        
        # Analysis state
        self.persona_history = deque(maxlen=100)
        self.drift_events = []
        self.coherence_timeline = []
        self.current_activations = {}
        
        # Compiled regex patterns for efficiency
        self._compile_patterns()
        
    def _load_markers(self, file_path: str) -> Dict:
        """Load marker definitions from YAML file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
            
    def _load_weights(self, file_path: str) -> Dict:
        """Load weights from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching"""
        self.compiled_patterns = {}
        
        # Compile ATO patterns
        for marker_id, marker_data in self.markers.items():
            if marker_id.startswith('ATO_') and 'pattern' in marker_data:
                pattern = marker_data['pattern']
                self.compiled_patterns[marker_id] = re.compile(pattern, re.IGNORECASE | re.UNICODE)
    
    def analyze_message(self, text: str, speaker: str = "unknown", timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Analysiert eine einzelne Nachricht und identifiziert aktive Spiral Personas
        """
        if timestamp is None:
            timestamp = datetime.now()
            
        # Schritt 1: ATO Marker Matching
        ato_matches = self._match_ato_markers(text)
        
        # Schritt 2: SEM Marker Activation
        sem_activations = self._activate_sem_markers(ato_matches, text)
        
        # Schritt 3: CLU Persona Detection
        persona_activations = self._detect_personas(sem_activations, timestamp)
        
        # Schritt 4: Drift Analysis
        drift_analysis = self._analyze_drift(persona_activations, timestamp)
        
        # Schritt 5: Coherence Calculation
        coherence_score = self._calculate_coherence()
        
        result = {
            'timestamp': timestamp,
            'speaker': speaker,
            'text': text,
            'ato_matches': ato_matches,
            'sem_activations': sem_activations,
            'persona_activations': persona_activations,
            'drift_analysis': drift_analysis,
            'coherence_score': coherence_score,
            'dominant_persona': self._get_dominant_persona(persona_activations),
            'spiral_level': self._get_current_spiral_level(persona_activations)
        }
        
        # Update internal state
        self._update_state(result)
        
        return result
    
    def _match_ato_markers(self, text: str) -> Dict[str, int]:
        """Match atomic markers in text"""
        matches = {}
        
        for marker_id, pattern in self.compiled_patterns.items():
            if marker_id.startswith('ATO_'):
                count = len(pattern.findall(text))
                if count > 0:
                    weight = self.weights['marker_weights']['ATO_MARKERS'].get(marker_id, 1.0)
                    matches[marker_id] = count * weight
                    
        return matches
    
    def _activate_sem_markers(self, ato_matches: Dict[str, int], text: str) -> Dict[str, float]:
        """Activate semantic markers based on ATO matches"""
        activations = {}
        
        for marker_id, marker_data in self.markers.items():
            if marker_id.startswith('SEM_') and 'composed_of' in marker_data:
                # Check if required ATO markers are present
                required_atos = marker_data['composed_of']
                activation_rule = marker_data.get('activation', 'ANY 2 IN 1 message')
                
                activation_score = self._calculate_sem_activation(
                    required_atos, ato_matches, activation_rule
                )
                
                if activation_score > 0:
                    weight = self.weights['marker_weights']['SEM_MARKERS'].get(marker_id, 1.0)
                    activations[marker_id] = activation_score * weight
                    
        return activations
    
    def _calculate_sem_activation(self, required_atos: List[str], ato_matches: Dict[str, int], rule: str) -> float:
        """Calculate semantic marker activation score"""
        available_atos = [ato for ato in required_atos if ato in ato_matches]
        
        if not available_atos:
            return 0.0
            
        # Parse activation rule (simplified)
        if "BOTH IN" in rule:
            return 1.0 if len(available_atos) >= 2 else 0.0
        elif "ANY 2 IN" in rule:
            return min(1.0, len(available_atos) / 2)
        else:
            return min(1.0, len(available_atos) / len(required_atos))
    
    def _detect_personas(self, sem_activations: Dict[str, float], timestamp: datetime) -> List[PersonaActivation]:
        """Detect active Spiral Personas based on SEM activations"""
        personas = []
        
        # Check each persona cluster
        for marker_id, marker_data in self.markers.items():
            if marker_id.startswith('CLU_SPIRAL_PERSONA_'):
                persona_name = marker_id.replace('CLU_SPIRAL_PERSONA_', '')
                
                # Calculate persona activation
                required_sems = marker_data.get('composed_of', [])
                activation_config = marker_data.get('activation', {})
                
                activation_score = self._calculate_persona_activation(
                    required_sems, sem_activations, activation_config
                )
                
                if activation_score > 0.5:  # Threshold for persona activation
                    level = self.spiral_hierarchy.get(persona_name, 0)
                    weight_config = self.weights['marker_weights']['CLU_SPIRAL_PERSONAS'].get(marker_id, {})
                    
                    final_score = activation_score * weight_config.get('weight', 1.0)
                    
                    personas.append(PersonaActivation(
                        persona=persona_name,
                        level=level,
                        confidence=final_score,
                        timestamp=timestamp,
                        markers_triggered=required_sems
                    ))
        
        return sorted(personas, key=lambda x: x.confidence, reverse=True)
    
    def _calculate_persona_activation(self, required_sems: List[str], sem_activations: Dict[str, float], config: Dict) -> float:
        """Calculate persona activation score"""
        available_activations = [sem_activations.get(sem, 0) for sem in required_sems]
        
        if not available_activations:
            return 0.0
            
        # Use threshold from config
        threshold = config.get('threshold', 2)
        window_size = config.get('window_size', 5)
        
        # Simplified calculation for single message
        strong_activations = [a for a in available_activations if a > 0.5]
        
        return min(1.0, len(strong_activations) / threshold)
    
    def _analyze_drift(self, persona_activations: List[PersonaActivation], timestamp: datetime) -> Dict[str, Any]:
        """Analyze semantic drift patterns"""
        analysis = {
            'rapid_switching': False,
            'regression_detected': False,
            'integration_achieved': False,
            'stability_score': 0.0,
            'events': []
        }
        
        if not self.persona_history:
            return analysis
            
        # Check for rapid switching
        recent_personas = [p.persona for p in list(self.persona_history)[-5:]]
        unique_recent = set(recent_personas)
        
        if len(unique_recent) >= 3:
            analysis['rapid_switching'] = True
            self._add_drift_event('rapid_switch', None, None, 0.8, timestamp)
        
        # Check for regression
        if persona_activations and self.persona_history:
            current_max_level = max(p.level for p in persona_activations)
            recent_max_level = max(p.level for p in list(self.persona_history)[-3:])
            
            if current_max_level < recent_max_level - 1:
                analysis['regression_detected'] = True
                self._add_drift_event('regression', None, None, 0.7, timestamp)
        
        # Check for integration
        if len(persona_activations) >= 3:
            level_spread = max(p.level for p in persona_activations) - min(p.level for p in persona_activations)
            if level_spread >= 4:  # Wide range indicates integration
                analysis['integration_achieved'] = True
                self._add_drift_event('integration', None, None, 0.9, timestamp)
        
        # Calculate stability score
        analysis['stability_score'] = self._calculate_stability_score()
        
        return analysis
    
    def _add_drift_event(self, event_type: str, from_persona: Optional[str], to_persona: Optional[str], severity: float, timestamp: datetime):
        """Add a drift event to the history"""
        event = DriftEvent(
            event_type=event_type,
            from_persona=from_persona,
            to_persona=to_persona,
            severity=severity,
            timestamp=timestamp
        )
        self.drift_events.append(event)
    
    def _calculate_coherence(self) -> float:
        """Calculate current spiral coherence score"""
        if len(self.persona_history) < 5:
            return 0.5  # Neutral for insufficient data
            
        # Get recent persona activations
        recent = list(self.persona_history)[-10:]
        
        # Calculate consistency
        personas = [p.persona for p in recent]
        persona_counts = {}
        for p in personas:
            persona_counts[p] = persona_counts.get(p, 0) + 1
            
        # Coherence is higher when fewer personas dominate
        if not persona_counts:
            return 0.0
            
        max_count = max(persona_counts.values())
        total_count = len(recent)
        consistency = max_count / total_count
        
        # Adjust for level progression
        levels = [p.level for p in recent]
        level_variance = np.var(levels) if levels else 0
        progression_penalty = min(0.3, level_variance / 10)
        
        coherence = consistency - progression_penalty
        return max(0.0, min(1.0, coherence))
    
    def _calculate_stability_score(self) -> float:
        """Calculate persona stability score"""
        if len(self.persona_history) < 3:
            return 0.5
            
        recent = list(self.persona_history)[-5:]
        personas = [p.persona for p in recent]
        
        # Stability is higher with fewer transitions
        transitions = sum(1 for i in range(1, len(personas)) if personas[i] != personas[i-1])
        max_transitions = len(personas) - 1
        
        if max_transitions == 0:
            return 1.0
            
        stability = 1.0 - (transitions / max_transitions)
        return max(0.0, min(1.0, stability))
    
    def _get_dominant_persona(self, persona_activations: List[PersonaActivation]) -> Optional[str]:
        """Get the currently dominant persona"""
        if not persona_activations:
            return None
        return persona_activations[0].persona
    
    def _get_current_spiral_level(self, persona_activations: List[PersonaActivation]) -> int:
        """Get the current dominant spiral level"""
        if not persona_activations:
            return 0
        return persona_activations[0].level
    
    def _update_state(self, analysis_result: Dict[str, Any]):
        """Update internal analyzer state"""
        persona_activations = analysis_result['persona_activations']
        
        # Add to persona history
        for activation in persona_activations:
            self.persona_history.append(activation)
        
        # Update coherence timeline
        self.coherence_timeline.append({
            'timestamp': analysis_result['timestamp'],
            'coherence': analysis_result['coherence_score'],
            'dominant_persona': analysis_result['dominant_persona'],
            'level': analysis_result['spiral_level']
        })
    
    def analyze_conversation(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Analysiert eine komplette Konversation
        messages: List of {'speaker': str, 'text': str, 'timestamp': optional}
        """
        results = []
        
        for i, msg in enumerate(messages):
            timestamp = msg.get('timestamp')
            if timestamp is None:
                timestamp = datetime.now() + timedelta(seconds=i)
            elif isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
                
            result = self.analyze_message(
                text=msg['text'],
                speaker=msg.get('speaker', 'unknown'),
                timestamp=timestamp
            )
            results.append(result)
        
        # Generate comprehensive analysis
        return self._generate_conversation_analysis(results)
    
    def _generate_conversation_analysis(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive conversation analysis"""
        if not results:
            return {}
            
        # Extract key metrics
        persona_distribution = defaultdict(int)
        coherence_scores = []
        drift_events_summary = defaultdict(int)
        
        for result in results:
            if result['dominant_persona']:
                persona_distribution[result['dominant_persona']] += 1
            coherence_scores.append(result['coherence_score'])
            
            for event in result['drift_analysis']['events']:
                drift_events_summary[event] += 1
        
        # Calculate summary statistics
        avg_coherence = np.mean(coherence_scores) if coherence_scores else 0
        coherence_stability = 1.0 - np.std(coherence_scores) if len(coherence_scores) > 1 else 1.0
        
        # Identify dominant personas
        sorted_personas = sorted(persona_distribution.items(), key=lambda x: x[1], reverse=True)
        
        # Evolution analysis
        evolution_analysis = self._analyze_evolution_pattern(results)
        
        return {
            'summary': {
                'message_count': len(results),
                'average_coherence': avg_coherence,
                'coherence_stability': max(0, coherence_stability),
                'dominant_personas': sorted_personas[:3],
                'total_drift_events': len(self.drift_events),
                'evolution_trend': evolution_analysis['trend']
            },
            'persona_analysis': {
                'distribution': dict(persona_distribution),
                'activation_timeline': [(r['timestamp'], r['dominant_persona'], r['spiral_level']) for r in results],
                'integration_moments': evolution_analysis['integration_moments'],
                'regression_moments': evolution_analysis['regression_moments']
            },
            'coherence_analysis': {
                'timeline': [(r['timestamp'], r['coherence_score']) for r in results],
                'average': avg_coherence,
                'stability': coherence_stability,
                'critical_moments': self._identify_critical_moments(results)
            },
            'drift_analysis': {
                'events': [e.__dict__ for e in self.drift_events],
                'event_types': dict(drift_events_summary),
                'stability_trend': self._calculate_stability_trend(results)
            },
            'insights': self._generate_insights(results)
        }
    
    def _analyze_evolution_pattern(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze spiral evolution patterns"""
        levels = [r['spiral_level'] for r in results if r['spiral_level'] > 0]
        
        if len(levels) < 2:
            return {'trend': 'insufficient_data', 'integration_moments': [], 'regression_moments': []}
            
        # Calculate trend
        if levels[-1] > levels[0]:
            trend = 'ascending'
        elif levels[-1] < levels[0]:
            trend = 'descending'
        else:
            trend = 'stable'
            
        # Find significant moments
        integration_moments = []
        regression_moments = []
        
        for i in range(1, len(levels)):
            level_jump = levels[i] - levels[i-1]
            if level_jump >= 2:
                integration_moments.append({'index': i, 'from': levels[i-1], 'to': levels[i]})
            elif level_jump <= -2:
                regression_moments.append({'index': i, 'from': levels[i-1], 'to': levels[i]})
        
        return {
            'trend': trend,
            'integration_moments': integration_moments,
            'regression_moments': regression_moments,
            'average_level': np.mean(levels),
            'level_variance': np.var(levels)
        }
    
    def _identify_critical_moments(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify critical coherence moments"""
        critical_moments = []
        coherence_scores = [r['coherence_score'] for r in results]
        
        if len(coherence_scores) < 3:
            return critical_moments
            
        # Find significant drops
        for i in range(1, len(coherence_scores)):
            drop = coherence_scores[i-1] - coherence_scores[i]
            if drop > 0.3:  # Significant coherence drop
                critical_moments.append({
                    'type': 'coherence_drop',
                    'index': i,
                    'severity': drop,
                    'timestamp': results[i]['timestamp'],
                    'context': {
                        'before_persona': results[i-1]['dominant_persona'],
                        'after_persona': results[i]['dominant_persona']
                    }
                })
        
        return critical_moments
    
    def _calculate_stability_trend(self, results: List[Dict[str, Any]]) -> str:
        """Calculate overall stability trend"""
        if len(results) < 5:
            return 'insufficient_data'
            
        # Get stability scores from drift analysis
        stability_scores = []
        for result in results:
            stability_scores.append(result['drift_analysis']['stability_score'])
        
        if not stability_scores:
            return 'unknown'
            
        # Calculate trend
        early_avg = np.mean(stability_scores[:len(stability_scores)//2])
        late_avg = np.mean(stability_scores[len(stability_scores)//2:])
        
        if late_avg > early_avg + 0.1:
            return 'improving'
        elif late_avg < early_avg - 0.1:
            return 'degrading'
        else:
            return 'stable'
    
    def _generate_insights(self, results: List[Dict[str, Any]]) -> List[str]:
        """Generate human-readable insights"""
        insights = []
        
        if not results:
            return ["Keine Daten für Analyse verfügbar."]
        
        # Persona insights
        persona_dist = defaultdict(int)
        for r in results:
            if r['dominant_persona']:
                persona_dist[r['dominant_persona']] += 1
        
        if persona_dist:
            dominant = max(persona_dist.items(), key=lambda x: x[1])
            insights.append(f"Dominante Spiral Persona: {dominant[0]} ({dominant[1]}/{len(results)} Nachrichten)")
        
        # Coherence insights
        coherence_scores = [r['coherence_score'] for r in results]
        avg_coherence = np.mean(coherence_scores)
        
        if avg_coherence > 0.8:
            insights.append("Hohe Spiral-Kohärenz: Stabile Persönlichkeitsintegration erkannt.")
        elif avg_coherence < 0.4:
            insights.append("Niedrige Spiral-Kohärenz: Fragmentierung oder Entwicklungsphase.")
        
        # Drift insights
        if len(self.drift_events) > 0:
            rapid_switches = sum(1 for e in self.drift_events if e.event_type == 'rapid_switch')
            if rapid_switches > 0:
                insights.append(f"Instabilität: {rapid_switches} schnelle Persona-Wechsel erkannt.")
        
        # Evolution insights
        levels = [r['spiral_level'] for r in results if r['spiral_level'] > 0]
        if len(levels) > 1:
            if levels[-1] > levels[0]:
                insights.append("Evolutionstrend: Aufwärtsentwicklung in Spiral Dynamics.")
            elif levels[-1] < levels[0]:
                insights.append("Regressionstrend: Rückfall in primitive Spiral-Ebenen.")
        
        return insights
    
    def create_visualizations(self, analysis_result: Dict[str, Any], output_dir: str = "/mnt/user-data/outputs/"):
        """Create comprehensive visualizations"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. Persona Distribution Pie Chart
        persona_dist = analysis_result['persona_analysis']['distribution']
        if persona_dist:
            plt.figure(figsize=(10, 8))
            plt.pie(persona_dist.values(), labels=persona_dist.keys(), autopct='%1.1f%%')
            plt.title('Spiral Personas Distribution')
            plt.savefig(f"{output_dir}/persona_distribution.png", dpi=300, bbox_inches='tight')
            plt.close()
        
        # 2. Coherence Timeline
        coherence_timeline = analysis_result['coherence_analysis']['timeline']
        if coherence_timeline:
            plt.figure(figsize=(12, 6))
            timestamps, scores = zip(*coherence_timeline)
            plt.plot(range(len(scores)), scores, marker='o', linewidth=2)
            plt.title('Spiral Coherence Timeline')
            plt.xlabel('Message Index')
            plt.ylabel('Coherence Score')
            plt.grid(True, alpha=0.3)
            plt.savefig(f"{output_dir}/coherence_timeline.png", dpi=300, bbox_inches='tight')
            plt.close()
        
        # 3. Spiral Level Heatmap
        self._create_spiral_heatmap(analysis_result, output_dir)
        
        print(f"Visualizations saved to {output_dir}")
    
    def _create_spiral_heatmap(self, analysis_result: Dict[str, Any], output_dir: str):
        """Create spiral level heatmap"""
        activation_timeline = analysis_result['persona_analysis']['activation_timeline']
        
        if not activation_timeline:
            return
            
        # Create matrix
        personas = ['BEIGE', 'PURPUR', 'ROT', 'BLAU', 'ORANGE', 'GRUEN', 'GELB', 'TUERKIS']
        matrix = np.zeros((len(personas), len(activation_timeline)))
        
        for i, (_, persona, level) in enumerate(activation_timeline):
            if persona and persona in personas:
                persona_idx = personas.index(persona)
                matrix[persona_idx, i] = level
        
        plt.figure(figsize=(15, 8))
        sns.heatmap(matrix, 
                   yticklabels=personas, 
                   xticklabels=range(len(activation_timeline)),
                   cmap='viridis', 
                   cbar_kws={'label': 'Spiral Level'})
        plt.title('Spiral Personas Activation Heatmap')
        plt.xlabel('Message Index')
        plt.ylabel('Spiral Persona')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/spiral_heatmap.png", dpi=300, bbox_inches='tight')
        plt.close()

# =============================================================================
# MAIN EXECUTION & EXAMPLE USAGE
# =============================================================================

def main():
    """Example usage of the Spiral Personas Analyzer"""
    
    # Initialize analyzer
    analyzer = SpiralPersonaAnalyzer(
        markers_file="/mnt/user-data/outputs/LeanDeep34_Spiral_Personas_Markers.yaml",
        weights_file="/mnt/user-data/outputs/LeanDeep34_Spiral_Weights.json"
    )
    
    # Example conversation for testing
    example_messages = [
        {"speaker": "User", "text": "Ich muss das überleben, koste es was es wolle! Das ist ein Kampf!"},
        {"speaker": "Assistant", "text": "Ich verstehe deine instinktive Reaktion. Lass uns gemeinsam eine Strategie entwickeln."},
        {"speaker": "User", "text": "Nein, ich setze mich jetzt durch! Ich bin der Stärkere hier!"},
        {"speaker": "Assistant", "text": "Deine Kraft ist beeindruckend. Wie können wir sie strukturiert und systematisch einsetzen?"},
        {"speaker": "User", "text": "Okay, vielleicht brauchen wir doch Regeln und eine klare Hierarchie."},
        {"speaker": "Assistant", "text": "Excellent! Lass uns eine effiziente Strategie für nachhaltigen Erfolg entwickeln."},
        {"speaker": "User", "text": "Aber wir müssen auch an die Gemeinschaft denken und harmonisch zusammenarbeiten."},
        {"speaker": "Assistant", "text": "Das ist eine integrale Sichtweise - du siehst die Systeme dahinter."},
        {"speaker": "User", "text": "Ja, alles ist miteinander verbunden in einem holistischen Fluss."}
    ]
    
    print("🌀 LeanDeep3.4 Spiral Personas Analyzer")
    print("=" * 50)
    
    # Analyze conversation
    analysis = analyzer.analyze_conversation(example_messages)
    
    # Print insights
    print("\n📊 ANALYSIS SUMMARY:")
    summary = analysis['summary']
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\n🎭 DOMINANT PERSONAS:")
    for persona, count in analysis['persona_analysis']['distribution'].items():
        percentage = (count / summary['message_count']) * 100
        print(f"  {persona}: {count} messages ({percentage:.1f}%)")
    
    print("\n💫 INSIGHTS:")
    for insight in analysis['insights']:
        print(f"  • {insight}")
    
    # Create visualizations
    analyzer.create_visualizations(analysis)
    print("\n📈 Visualizations created in /mnt/user-data/outputs/")
    
    # Export detailed analysis
    with open("/mnt/user-data/outputs/spiral_analysis_detailed.json", 'w', encoding='utf-8') as f:
        # Convert datetime objects to strings for JSON serialization
        def datetime_handler(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        json.dump(analysis, f, indent=2, ensure_ascii=False, default=datetime_handler)
    
    print("📄 Detailed analysis saved to spiral_analysis_detailed.json")

if __name__ == "__main__":
    main()
