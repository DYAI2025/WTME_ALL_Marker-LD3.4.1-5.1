# Emotional Semantics Basic Collection

## Overview

This collection contains **12 comprehensive atomic markers** for detecting basic emotional semantic patterns in text-based communication. Each marker includes **30-50 real, authentic examples** in both German and English, following the LeanDeep 3.4 schema specification.

## Purpose

These markers form the foundation for emotional pattern detection in conversational analysis, providing precise linguistic patterns for identifying fundamental human emotions across multiple languages.

## Marker Collection

### 1. **ATO_JOY_HAPPINESS**

- **Concept**: Positive emotional valence - joy and happiness
- **Examples**: 50 real examples
- **Patterns**: Freude, Glück, fröhlich, begeistert, happy, joy
- **Use Cases**: Detecting expressions of happiness, delight, enthusiasm

### 2. **ATO_SADNESS_GRIEF**

- **Concept**: Negative emotional valence - sadness and grief
- **Examples**: 50 real examples
- **Patterns**: Traurig, Trauer, Melancholie, betrübt, sad, grief
- **Use Cases**: Detecting expressions of sadness, loss, melancholy

### 3. **ATO_ANGER_RAGE**

- **Concept**: Negative emotional valence - anger and aggression
- **Examples**: 50 real examples
- **Patterns**: Wut, Ärger, Zorn, wütend, angry, rage
- **Use Cases**: Detecting expressions of anger, frustration, rage

### 4. **ATO_FEAR_ANXIETY**

- **Concept**: Negative emotional valence - fear and anxiety
- **Examples**: 50 real examples
- **Patterns**: Angst, Furcht, Sorge, ängstlich, fear, anxiety
- **Use Cases**: Detecting expressions of fear, worry, panic

### 5. **ATO_LOVE_AFFECTION**

- **Concept**: Positive emotional valence - love and affection
- **Examples**: 50 real examples
- **Patterns**: Liebe, Zuneigung, zärtlich, liebevoll, love, affection
- **Use Cases**: Detecting expressions of love, tenderness, affection

### 6. **ATO_DISGUST_AVERSION**

- **Concept**: Negative emotional valence - disgust and aversion
- **Examples**: 50 real examples
- **Patterns**: Ekel, Abscheu, Widerwillen, angewidert, disgust, repulsion
- **Use Cases**: Detecting expressions of disgust, repulsion, aversion

### 7. **ATO_SURPRISE_ASTONISHMENT**

- **Concept**: Neutral-to-positive emotional valence - surprise and astonishment
- **Examples**: 50 real examples
- **Patterns**: Überraschung, Erstaunen, Verwunderung, überrascht, surprise, amazed
- **Use Cases**: Detecting expressions of surprise, wonder, amazement

### 8. **ATO_SHAME_GUILT**

- **Concept**: Negative emotional valence - shame and guilt
- **Examples**: 50 real examples
- **Patterns**: Scham, Schuld, peinlich, schämen, shame, guilt
- **Use Cases**: Detecting expressions of shame, guilt, embarrassment

### 9. **ATO_HOPE_OPTIMISM**

- **Concept**: Positive emotional valence - hope and optimism
- **Examples**: 50 real examples
- **Patterns**: Hoffnung, Optimismus, Zuversicht, hoffen, hope, optimistic
- **Use Cases**: Detecting expressions of hope, optimism, positive expectations

### 10. **ATO_LONELINESS_ISOLATION**

- **Concept**: Negative emotional valence - loneliness and isolation
- **Examples**: 50 real examples
- **Patterns**: Einsamkeit, allein, isoliert, einsam, lonely, isolated
- **Use Cases**: Detecting expressions of loneliness, social disconnection

### 11. **ATO_GRATITUDE_APPRECIATION**

- **Concept**: Positive emotional valence - gratitude and appreciation
- **Examples**: 50 real examples
- **Patterns**: Dankbarkeit, danke, dankbar, Wertschätzung, grateful, thankful
- **Use Cases**: Detecting expressions of gratitude, appreciation, thankfulness

### 12. **ATO_PRIDE_CONFIDENCE**

- **Concept**: Positive emotional valence - pride and confidence
- **Examples**: 50 real examples
- **Patterns**: Stolz, selbstbewusst, selbstsicher, proud, confident
- **Use Cases**: Detecting expressions of pride, self-confidence, self-assurance

### 13. **ATO_JEALOUSY_ENVY**

- **Concept**: Negative emotional valence - jealousy and envy
- **Examples**: 50 real examples
- **Patterns**: Eifersucht, Neid, eifersüchtig, neidisch, jealous, envious
- **Use Cases**: Detecting expressions of jealousy, envy, possessiveness

## Schema Compliance

All markers follow the **LeanDeep 3.4** schema specification:

```yaml
schema: "LeanDeep"
version: "3.4"
namespace: "ld34_text_social_grammar"
lang: de
category: ATOMIC

frame:
  signal: [observable linguistic signals]
  concept: "Abstract emotional concept"
  pragmatics: "Pragmatic function in conversation"
  narrative: "emotional_expression"

pattern:
  - '(?i)\b(regex patterns)\b'

activation_logic: "ANY 1"

examples:
  - "Real example 1"
  - "Real example 2"
  # ... 30-50 examples total

tags: [atomic, emotion, category, specific_emotion, v3.4]

metadata:
  created: "2026-02-12"
  author: "DYAI Emotional Semantics Collection"
  purpose: "Basic emotional pattern detection"
```

## Technical Specifications

### Pattern Design

- **Case-insensitive**: All patterns use `(?i)` flag
- **Word boundaries**: Patterns use `\b` for precise matching
- **Multi-language**: Supports German and English
- **Regex-based**: Flexible pattern matching for variations

### Activation Logic

- **Type**: `ANY 1` - Single pattern match triggers activation
- **Threshold**: Low threshold for high sensitivity
- **Window**: Single message analysis

### Example Quality

- **Authenticity**: All examples are realistic, natural language expressions
- **Variety**: Examples cover different intensities and contexts
- **Bilingual**: Mix of German and English examples
- **Quantity**: 50 examples per marker (exceeding the 30-50 requirement)

## Integration with LeanDeep System

These atomic markers can be:

1. **Used directly** for basic emotional detection
2. **Combined into SEM markers** for semantic bundles (e.g., SEM_MIXED_EMOTIONS)
3. **Aggregated into CLU markers** for pattern clusters (e.g., CLU_EMOTIONAL_VOLATILITY)
4. **Integrated into MEMA markers** for meta-analysis (e.g., MEMA_EMOTIONAL_PROFILE)

## Use Cases

### Clinical Applications

- Depression screening (sadness, hopelessness, loneliness)
- Anxiety assessment (fear, worry patterns)
- Emotional regulation analysis
- Therapeutic progress tracking

### Relationship Analysis

- Communication pattern detection
- Emotional dynamics mapping
- Conflict identification (anger, jealousy)
- Connection strength (love, gratitude)

### Content Analysis

- Sentiment analysis
- Emotional tone detection
- User experience research
- Social media monitoring

## Quality Assurance

✅ **Schema Compliance**: All markers follow LeanDeep 3.4 specification  
✅ **Example Count**: Each marker has 50 real examples (exceeds 30-50 requirement)  
✅ **Pattern Coverage**: Comprehensive regex patterns for each emotion  
✅ **Bilingual Support**: German and English examples  
✅ **Frame Semantics**: Complete frame structure (signal, concept, pragmatics, narrative)  
✅ **Metadata**: Creation date, author, purpose documented  

## Future Extensions

Potential semantic (SEM) markers to build from these atomics:

- `SEM_EMOTIONAL_AMBIVALENCE` (joy + sadness)
- `SEM_ANXIOUS_HOPE` (fear + hope)
- `SEM_GRATEFUL_LOVE` (gratitude + love)
- `SEM_ANGRY_SHAME` (anger + shame)
- `SEM_PROUD_CONFIDENCE` (pride + confidence)

## Author & Date

**Created**: 2026-02-12  
**Author**: DYAI Emotional Semantics Collection  
**Version**: 1.0  
**Schema**: LeanDeep 3.4  

## License & Usage

These markers are part of the LeanDeep Marker Collection and follow the same licensing and usage terms as the parent collection.

---

**Total Markers**: 13  
**Total Examples**: 650+ (50 per marker)  
**Languages**: German (de), English (en)  
**Category**: ATOMIC  
**Domain**: Emotional Semantics
