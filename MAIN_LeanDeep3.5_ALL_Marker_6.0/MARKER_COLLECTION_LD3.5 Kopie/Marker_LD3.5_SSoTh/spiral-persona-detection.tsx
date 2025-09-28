import React, { useState, useEffect } from 'react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart } from 'recharts';
import Papa from 'papaparse';
import _ from 'lodash';

const SpiralPersonaDetection = () => {
  const [data, setData] = useState(null);
  const [selectedSpeaker, setSelectedSpeaker] = useState('Unknown');
  const [timeRange, setTimeRange] = useState([0, 100]);
  const [personas, setPersonas] = useState([]);
  const [clusterAnalysis, setClusterAnalysis] = useState([]);
  
  // Spiral Dynamics Farben mit Bedeutung
  const spiralColors = {
    Beige: { hex: '#D2B48C', level: 1, name: 'Survival', desc: 'Instinktiv, Überleben' },
    Purpur: { hex: '#800080', level: 2, name: 'Tribal', desc: 'Magisch, Stammesdenken' },
    Rot: { hex: '#FF0000', level: 3, name: 'Power', desc: 'Macht, Impulsiv' },
    Blau: { hex: '#0000FF', level: 4, name: 'Order', desc: 'Ordnung, Autorität' },
    Orange: { hex: '#FFA500', level: 5, name: 'Success', desc: 'Erfolg, Wissenschaft' },
    Grün: { hex: '#00FF00', level: 6, name: 'Community', desc: 'Gemeinschaft, Konsens' },
    Gelb: { hex: '#FFFF00', level: 7, name: 'Integral', desc: 'Systemisch, Flexibel' },
    Türkis: { hex: '#40E0D0', level: 8, name: 'Holistic', desc: 'Holistisch, Global' }
  };

  // Lade Daten
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const response = await window.fs.readFile('marker_counts.csv', { encoding: 'utf8' });
      const parsed = Papa.parse(response, {
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true
      });
      
      setData(parsed.data);
      detectPersonas(parsed.data);
      analyzeClusterDynamics(parsed.data);
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  // Spiral Persona Detection Algorithmus
  const detectPersonas = (rawData) => {
    const speakerGroups = _.groupBy(rawData, 'speaker');
    const detectedPersonas = [];

    Object.entries(speakerGroups).forEach(([speaker, rows]) => {
      if (rows.length < 5) return; // Zu wenig Daten

      // Berechne Marker-Profil
      const profile = calculateSpiralProfile(rows);
      
      // Zeitliche Evolution
      const evolution = calculateEvolution(rows);
      
      // Cluster-Muster
      const clusterPattern = detectClusterPatterns(rows);
      
      // Persona-Typ bestimmen
      const personaType = classifyPersona(profile, evolution, clusterPattern);
      
      detectedPersonas.push({
        speaker,
        type: personaType,
        profile,
        evolution,
        clusterPattern,
        complexity: calculateComplexity(profile, evolution),
        trajectory: predictTrajectory(evolution)
      });
    });

    setPersonas(detectedPersonas);
  };

  const calculateSpiralProfile = (rows) => {
    const totals = {};
    let totalMarkers = 0;

    Object.keys(spiralColors).forEach(color => {
      totals[color] = 0;
    });

    rows.forEach(row => {
      Object.keys(spiralColors).forEach(color => {
        if (row[color]) {
          totals[color] += row[color];
          totalMarkers += row[color];
        }
      });
    });

    // Berechne Schwerpunkt (Center of Gravity)
    let weightedSum = 0;
    let centerOfGravity = 0;
    
    Object.entries(totals).forEach(([color, count]) => {
      weightedSum += spiralColors[color].level * count;
    });
    
    if (totalMarkers > 0) {
      centerOfGravity = weightedSum / totalMarkers;
    }

    return {
      totals,
      percentages: Object.entries(totals).reduce((acc, [color, count]) => {
        acc[color] = totalMarkers > 0 ? (count / totalMarkers * 100).toFixed(1) : 0;
        return acc;
      }, {}),
      totalMarkers,
      centerOfGravity,
      dominantColor: Object.entries(totals).sort((a, b) => b[1] - a[1])[0]?.[0] || null
    };
  };

  const calculateEvolution = (rows) => {
    const chunks = _.chunk(rows, Math.ceil(rows.length / 4));
    return chunks.map((chunk, idx) => ({
      phase: `Q${idx + 1}`,
      profile: calculateSpiralProfile(chunk),
      lines: [chunk[0]?.line || 0, chunk[chunk.length - 1]?.line || 0]
    }));
  };

  const detectClusterPatterns = (rows) => {
    const clusters = [];
    let currentCluster = null;

    rows.forEach((row, idx) => {
      const totalMarkers = Object.keys(spiralColors).reduce((sum, color) => 
        sum + (row[color] || 0), 0);

      if (totalMarkers > 0) {
        if (!currentCluster || idx - currentCluster.endIdx > 5) {
          currentCluster = {
            startIdx: idx,
            endIdx: idx,
            markers: {},
            intensity: 0
          };
          clusters.push(currentCluster);
        } else {
          currentCluster.endIdx = idx;
        }

        Object.keys(spiralColors).forEach(color => {
          if (row[color]) {
            currentCluster.markers[color] = (currentCluster.markers[color] || 0) + row[color];
            currentCluster.intensity += row[color];
          }
        });
      }
    });

    return {
      clusterCount: clusters.length,
      avgIntensity: clusters.reduce((sum, c) => sum + c.intensity, 0) / (clusters.length || 1),
      patterns: identifyPatterns(clusters)
    };
  };

  const identifyPatterns = (clusters) => {
    if (clusters.length < 2) return ['isolated'];
    
    const patterns = [];
    const intervals = clusters.slice(1).map((c, i) => c.startIdx - clusters[i].endIdx);
    const avgInterval = intervals.reduce((sum, i) => sum + i, 0) / intervals.length;
    
    if (avgInterval < 10) patterns.push('dense-clustering');
    if (avgInterval > 50) patterns.push('sparse-activation');
    
    // Marker-Übergänge analysieren
    const transitions = clusters.slice(1).map((c, i) => {
      const prev = clusters[i];
      const prevDominant = Object.entries(prev.markers).sort((a, b) => b[1] - a[1])[0]?.[0];
      const currDominant = Object.entries(c.markers).sort((a, b) => b[1] - a[1])[0]?.[0];
      
      if (prevDominant && currDominant) {
        const prevLevel = spiralColors[prevDominant].level;
        const currLevel = spiralColors[currDominant].level;
        return currLevel - prevLevel;
      }
      return 0;
    });
    
    const avgTransition = transitions.reduce((sum, t) => sum + t, 0) / (transitions.length || 1);
    
    if (avgTransition > 0.5) patterns.push('ascending-spiral');
    if (avgTransition < -0.5) patterns.push('descending-spiral');
    if (Math.abs(avgTransition) < 0.2) patterns.push('stable-level');
    
    return patterns;
  };

  const classifyPersona = (profile, evolution, clusterPattern) => {
    // Basis-Klassifikation nach dominanter Farbe und Schwerpunkt
    const cog = profile.centerOfGravity;
    const patterns = clusterPattern.patterns;
    
    // Evolutionäre Dynamik
    const evolutionTrend = evolution[evolution.length - 1].profile.centerOfGravity - 
                          evolution[0].profile.centerOfGravity;
    
    // Persona-Typen nach LeanDeep3.5
    if (cog >= 7 && patterns.includes('ascending-spiral')) {
      return 'Emergent Integral';
    } else if (cog >= 7 && patterns.includes('stable-level')) {
      return 'Established Yellow';
    } else if (cog >= 6.5 && evolutionTrend > 0.5) {
      return 'Transitioning to Second Tier';
    } else if (cog >= 5 && cog < 6.5 && patterns.includes('dense-clustering')) {
      return 'First Tier Oscillator';
    } else if (cog < 5 && patterns.includes('sparse-activation')) {
      return 'Traditional Stabilizer';
    } else if (evolutionTrend > 1) {
      return 'Rapid Evolver';
    } else if (Math.abs(evolutionTrend) < 0.1) {
      return 'Static Maintainer';
    }
    
    return 'Complex Hybrid';
  };

  const calculateComplexity = (profile, evolution) => {
    // Shannon-Entropie der Marker-Verteilung
    let entropy = 0;
    const total = profile.totalMarkers;
    
    if (total > 0) {
      Object.values(profile.totals).forEach(count => {
        if (count > 0) {
          const p = count / total;
          entropy -= p * Math.log2(p);
        }
      });
    }
    
    // Variabilität über Zeit
    const variability = evolution.reduce((sum, phase, idx) => {
      if (idx === 0) return 0;
      return sum + Math.abs(phase.profile.centerOfGravity - evolution[idx - 1].profile.centerOfGravity);
    }, 0) / (evolution.length - 1);
    
    return {
      entropy: entropy.toFixed(2),
      variability: variability.toFixed(2),
      score: ((entropy + variability) / 2).toFixed(2)
    };
  };

  const predictTrajectory = (evolution) => {
    if (evolution.length < 2) return 'insufficient-data';
    
    const trends = evolution.slice(1).map((phase, idx) => 
      phase.profile.centerOfGravity - evolution[idx].profile.centerOfGravity
    );
    
    const avgTrend = trends.reduce((sum, t) => sum + t, 0) / trends.length;
    
    if (avgTrend > 0.3) return 'ascending';
    if (avgTrend < -0.3) return 'descending';
    return 'stable';
  };

  // Cluster-Dynamik Analyse
  const analyzeClusterDynamics = (rawData) => {
    const analysis = rawData
      .map((row, idx) => {
        const totalMarkers = Object.keys(spiralColors).reduce((sum, color) => 
          sum + (row[color] || 0), 0);
        
        if (totalMarkers === 0) return null;
        
        const dominantColor = Object.keys(spiralColors).reduce((max, color) => 
          (row[color] || 0) > (row[max] || 0) ? color : max
        );
        
        return {
          index: idx,
          line: row.line,
          speaker: row.speaker,
          totalMarkers,
          dominantColor,
          level: spiralColors[dominantColor].level,
          intensity: totalMarkers,
          text: row.text?.substring(0, 100)
        };
      })
      .filter(Boolean);
    
    setClusterAnalysis(analysis);
  };

  // Visualisierungs-Komponenten
  const PersonaCard = ({ persona }) => (
    <div className="bg-gray-800 rounded-lg p-4 mb-4 border border-gray-700">
      <h3 className="text-xl font-bold mb-2 text-white">{persona.speaker}</h3>
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div>
          <span className="text-gray-400">Typ:</span> 
          <span className="text-cyan-400 ml-2">{persona.type}</span>
        </div>
        <div>
          <span className="text-gray-400">Schwerpunkt:</span> 
          <span className="text-yellow-400 ml-2">{persona.profile.centerOfGravity.toFixed(2)}</span>
        </div>
        <div>
          <span className="text-gray-400">Dominante Farbe:</span> 
          <span 
            className="ml-2 px-2 py-1 rounded"
            style={{ 
              backgroundColor: spiralColors[persona.profile.dominantColor]?.hex,
              color: '#000'
            }}
          >
            {persona.profile.dominantColor}
          </span>
        </div>
        <div>
          <span className="text-gray-400">Trajektorie:</span> 
          <span className={`ml-2 ${
            persona.trajectory === 'ascending' ? 'text-green-400' : 
            persona.trajectory === 'descending' ? 'text-red-400' : 'text-gray-400'
          }`}>
            {persona.trajectory === 'ascending' ? '↑' : 
             persona.trajectory === 'descending' ? '↓' : '→'} {persona.trajectory}
          </span>
        </div>
        <div>
          <span className="text-gray-400">Komplexität:</span> 
          <span className="text-purple-400 ml-2">{persona.complexity.score}</span>
        </div>
        <div>
          <span className="text-gray-400">Cluster-Muster:</span> 
          <span className="text-blue-400 ml-2">{persona.clusterPattern.patterns.join(', ')}</span>
        </div>
      </div>
    </div>
  );

  const SpiralRadar = ({ persona }) => {
    const radarData = Object.keys(spiralColors).map(color => ({
      color,
      value: parseFloat(persona.profile.percentages[color]) || 0
    }));

    return (
      <ResponsiveContainer width="100%" height={300}>
        <RadarChart data={radarData}>
          <PolarGrid stroke="#444" />
          <PolarAngleAxis dataKey="color" tick={{ fill: '#fff', fontSize: 12 }} />
          <PolarRadiusAxis domain={[0, 100]} tick={{ fill: '#888' }} />
          <Radar 
            name={persona.speaker} 
            dataKey="value" 
            stroke="#00ff00" 
            fill="#00ff00" 
            fillOpacity={0.3} 
          />
          <Tooltip />
        </RadarChart>
      </ResponsiveContainer>
    );
  };

  const EvolutionChart = ({ persona }) => {
    const evolutionData = persona.evolution.map((phase, idx) => ({
      phase: phase.phase,
      centerOfGravity: phase.profile.centerOfGravity,
      ...Object.keys(spiralColors).reduce((acc, color) => {
        acc[color] = phase.profile.totals[color] || 0;
        return acc;
      }, {})
    }));

    return (
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={evolutionData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#444" />
          <XAxis dataKey="phase" tick={{ fill: '#fff' }} />
          <YAxis yAxisId="left" tick={{ fill: '#fff' }} />
          <YAxis yAxisId="right" orientation="right" tick={{ fill: '#888' }} />
          <Tooltip contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #444' }} />
          <Legend />
          
          <Line 
            yAxisId="right"
            type="monotone" 
            dataKey="centerOfGravity" 
            stroke="#ff00ff" 
            strokeWidth={3}
            name="Schwerpunkt"
          />
          
          {Object.keys(spiralColors).map(color => (
            <Area
              key={color}
              yAxisId="left"
              type="monotone"
              dataKey={color}
              stackId="1"
              stroke={spiralColors[color].hex}
              fill={spiralColors[color].hex}
              fillOpacity={0.6}
            />
          ))}
        </ComposedChart>
      </ResponsiveContainer>
    );
  };

  const ClusterTimeline = () => {
    return (
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={clusterAnalysis}>
          <CartesianGrid strokeDasharray="3 3" stroke="#444" />
          <XAxis dataKey="line" tick={{ fill: '#fff' }} />
          <YAxis tick={{ fill: '#fff' }} />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #444' }}
            content={({ active, payload }) => {
              if (active && payload?.[0]) {
                const data = payload[0].payload;
                return (
                  <div className="p-2">
                    <p className="text-xs">Zeile: {data.line}</p>
                    <p className="text-xs">Sprecher: {data.speaker}</p>
                    <p className="text-xs">Farbe: {data.dominantColor}</p>
                    <p className="text-xs">Intensität: {data.intensity}</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Bar dataKey="level" fill="#8884d8">
            {clusterAnalysis.map((entry, index) => (
              <Bar key={`cell-${index}`} fill={spiralColors[entry.dominantColor]?.hex} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    );
  };

  if (!data) return <div className="p-8 text-white">Loading...</div>;

  const currentPersona = personas.find(p => p.speaker === selectedSpeaker);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4">
      <h1 className="text-3xl font-bold mb-6 text-center bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
        Spiral Persona Detection Engine v3.5
      </h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Persona-Liste */}
        <div className="lg:col-span-1">
          <h2 className="text-xl font-bold mb-4">Erkannte Personas</h2>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {personas.map(persona => (
              <button
                key={persona.speaker}
                onClick={() => setSelectedSpeaker(persona.speaker)}
                className={`w-full text-left p-3 rounded-lg transition ${
                  selectedSpeaker === persona.speaker ? 
                  'bg-purple-800 border-2 border-purple-400' : 
                  'bg-gray-800 hover:bg-gray-700 border border-gray-700'
                }`}
              >
                <div className="font-semibold">{persona.speaker}</div>
                <div className="text-sm text-gray-400">{persona.type}</div>
                <div className="text-xs text-cyan-400">Level: {persona.profile.centerOfGravity.toFixed(1)}</div>
              </button>
            ))}
          </div>
        </div>
        
        {/* Detail-Ansicht */}
        <div className="lg:col-span-2 space-y-6">
          {currentPersona && (
            <>
              <PersonaCard persona={currentPersona} />
              
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-lg font-bold mb-2">Spiral Profile</h3>
                <SpiralRadar persona={currentPersona} />
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-lg font-bold mb-2">Evolution über Zeit</h3>
                <EvolutionChart persona={currentPersona} />
              </div>
            </>
          )}
        </div>
      </div>
      
      {/* Cluster Timeline */}
      <div className="mt-6 bg-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-bold mb-2">Marker-Cluster Timeline</h3>
        <ClusterTimeline />
      </div>
      
      {/* Legende */}
      <div className="mt-6 bg-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-bold mb-2">Spiral Dynamics Ebenen</h3>
        <div className="grid grid-cols-4 gap-2">
          {Object.entries(spiralColors).map(([color, info]) => (
            <div key={color} className="flex items-center space-x-2">
              <div 
                className="w-6 h-6 rounded"
                style={{ backgroundColor: info.hex }}
              />
              <div className="text-sm">
                <div className="font-semibold">{color}</div>
                <div className="text-xs text-gray-400">{info.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SpiralPersonaDetection;