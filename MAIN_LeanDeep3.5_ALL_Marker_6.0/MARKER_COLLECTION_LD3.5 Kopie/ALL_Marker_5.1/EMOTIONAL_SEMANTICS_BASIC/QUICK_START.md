# Quick Start Guide

## Emotional Semantics Basic Collection

**Version**: 1.0  
**Date**: 2026-02-12  
**Schema**: LeanDeep 3.4

---

## 🚀 Quick Overview

This collection contains **13 atomic emotional markers** with **650 real examples** for detecting basic emotions in text.

---

## 📁 What's Inside

```
EMOTIONAL_SEMANTICS_BASIC/
├── README.md                    # Full documentation
├── PROJECT_SUMMARY.md           # Detailed project report
├── VALIDATION_REPORT.md         # Quality validation
├── QUICK_START.md              # This file
└── ATO_atomic/                 # 13 marker files
    ├── ATO_JOY_HAPPINESS.yaml
    ├── ATO_SADNESS_GRIEF.yaml
    ├── ATO_ANGER_RAGE.yaml
    ├── ATO_FEAR_ANXIETY.yaml
    ├── ATO_LOVE_AFFECTION.yaml
    ├── ATO_DISGUST_AVERSION.yaml
    ├── ATO_SURPRISE_ASTONISHMENT.yaml
    ├── ATO_SHAME_GUILT.yaml
    ├── ATO_HOPE_OPTIMISM.yaml
    ├── ATO_LONELINESS_ISOLATION.yaml
    ├── ATO_GRATITUDE_APPRECIATION.yaml
    ├── ATO_PRIDE_CONFIDENCE.yaml
    └── ATO_JEALOUSY_ENVY.yaml
```

---

## 🎯 The 13 Emotions

### Positive Emotions (5)

1. **Joy/Happiness** - Freude, Glück, happy, joy
2. **Love/Affection** - Liebe, Zuneigung, love, affection
3. **Hope/Optimism** - Hoffnung, Optimismus, hope, optimistic
4. **Gratitude/Appreciation** - Dankbarkeit, danke, grateful, thanks
5. **Pride/Confidence** - Stolz, selbstbewusst, proud, confident

### Negative Emotions (7)

6. **Sadness/Grief** - Traurig, Trauer, sad, grief
2. **Anger/Rage** - Wut, Ärger, angry, rage
3. **Fear/Anxiety** - Angst, Furcht, fear, anxiety
4. **Disgust/Aversion** - Ekel, Abscheu, disgust, repulsion
5. **Shame/Guilt** - Scham, Schuld, shame, guilt
6. **Loneliness/Isolation** - Einsamkeit, allein, lonely, isolated
7. **Jealousy/Envy** - Eifersucht, Neid, jealous, envious

### Neutral/Mixed (1)

13. **Surprise/Astonishment** - Überraschung, Erstaunen, surprise, amazed

---

## 💡 Quick Use Cases

### 1. Mental Health Screening

```yaml
# Detect depression indicators
Use: ATO_SADNESS_GRIEF + ATO_LONELINESS_ISOLATION + ATO_HOPE_OPTIMISM (low)
```

### 2. Relationship Analysis

```yaml
# Detect relationship health
Use: ATO_LOVE_AFFECTION + ATO_GRATITUDE_APPRECIATION (high)
     ATO_ANGER_RAGE + ATO_JEALOUSY_ENVY (low)
```

### 3. Customer Sentiment

```yaml
# Detect customer satisfaction
Use: ATO_JOY_HAPPINESS + ATO_GRATITUDE_APPRECIATION (positive)
     ATO_ANGER_RAGE + ATO_DISGUST_AVERSION (negative)
```

### 4. Emotional Support Bot

```yaml
# Detect user emotional state
Use: All 13 markers to identify current emotion
     Respond with appropriate empathy
```

---

## 🔧 How to Use

### 1. Load a Marker

```python
import yaml

with open('ATO_atomic/ATO_JOY_HAPPINESS.yaml', 'r') as f:
    marker = yaml.safe_load(f)

print(marker['id'])  # ATO_JOY_HAPPINESS
print(marker['pattern'])  # Regex patterns
print(marker['examples'])  # 50 examples
```

### 2. Test Against Text

```python
import re

text = "Ich bin so glücklich heute!"

for pattern in marker['pattern']:
    if re.search(pattern, text):
        print(f"Detected: {marker['id']}")
        break
```

### 3. Combine Multiple Markers

```python
# Load multiple markers
markers = []
for emotion in ['JOY_HAPPINESS', 'SADNESS_GRIEF', 'ANGER_RAGE']:
    with open(f'ATO_atomic/ATO_{emotion}.yaml', 'r') as f:
        markers.append(yaml.safe_load(f))

# Test text against all markers
text = "Ich bin wütend und traurig zugleich."
detected = []

for marker in markers:
    for pattern in marker['pattern']:
        if re.search(pattern, text):
            detected.append(marker['id'])
            break

print(f"Detected emotions: {detected}")
# Output: ['ATO_ANGER_RAGE', 'ATO_SADNESS_GRIEF']
```

---

## 📊 Example Output

### Input Text

```
"Ich bin so dankbar für deine Hilfe! Das macht mich wirklich glücklich."
```

### Detected Markers

- ✅ `ATO_GRATITUDE_APPRECIATION` (dankbar)
- ✅ `ATO_JOY_HAPPINESS` (glücklich)

### Emotional Profile

- **Positive Valence**: High
- **Primary Emotion**: Gratitude + Joy
- **Intensity**: Moderate-High ("so", "wirklich")

---

## 🌍 Language Support

### German (de)

- All markers include German patterns
- Examples: "Ich bin traurig", "Das macht mich wütend"

### English (en)

- All markers include English patterns
- Examples: "I am sad", "This makes me angry"

### Bilingual Detection

```python
# Works for both languages
text_de = "Ich bin so glücklich!"
text_en = "I am so happy!"

# Both will detect ATO_JOY_HAPPINESS
```

---

## 🎓 Integration Examples

### Example 1: Depression Screening

```python
def screen_depression(messages):
    """Screen for depression indicators"""
    markers_to_check = [
        'ATO_SADNESS_GRIEF',
        'ATO_LONELINESS_ISOLATION',
        'ATO_HOPE_OPTIMISM'  # Low hope is concerning
    ]
    
    scores = {marker: 0 for marker in markers_to_check}
    
    for message in messages:
        for marker_id in markers_to_check:
            if detect_marker(message, marker_id):
                scores[marker_id] += 1
    
    # High sadness + loneliness + low hope = concern
    if (scores['ATO_SADNESS_GRIEF'] > 3 and 
        scores['ATO_LONELINESS_ISOLATION'] > 2 and
        scores['ATO_HOPE_OPTIMISM'] < 1):
        return "CONCERN: Depression indicators detected"
    
    return "OK"
```

### Example 2: Relationship Health

```python
def analyze_relationship(messages):
    """Analyze relationship emotional health"""
    positive = ['ATO_LOVE_AFFECTION', 'ATO_GRATITUDE_APPRECIATION']
    negative = ['ATO_ANGER_RAGE', 'ATO_JEALOUSY_ENVY']
    
    pos_score = sum(count_marker(messages, m) for m in positive)
    neg_score = sum(count_marker(messages, m) for m in negative)
    
    ratio = pos_score / (neg_score + 1)  # Avoid division by zero
    
    if ratio > 5:
        return "HEALTHY: Strong positive emotional bond"
    elif ratio > 1:
        return "MODERATE: Mixed emotional dynamics"
    else:
        return "CONCERN: Negative emotions dominating"
```

### Example 3: Customer Sentiment

```python
def analyze_sentiment(feedback):
    """Analyze customer feedback sentiment"""
    positive = ['ATO_JOY_HAPPINESS', 'ATO_GRATITUDE_APPRECIATION']
    negative = ['ATO_ANGER_RAGE', 'ATO_DISGUST_AVERSION']
    
    pos_count = sum(detect_marker(feedback, m) for m in positive)
    neg_count = sum(detect_marker(feedback, m) for m in negative)
    
    if pos_count > neg_count:
        return "POSITIVE"
    elif neg_count > pos_count:
        return "NEGATIVE"
    else:
        return "NEUTRAL"
```

---

## 📈 Performance Tips

### 1. Pre-compile Regex Patterns

```python
import re

# Compile once, use many times
compiled_patterns = {}
for marker in markers:
    compiled_patterns[marker['id']] = [
        re.compile(p) for p in marker['pattern']
    ]
```

### 2. Batch Processing

```python
# Process multiple messages at once
def batch_detect(messages, marker_id):
    pattern = compiled_patterns[marker_id]
    return [any(p.search(msg) for p in pattern) for msg in messages]
```

### 3. Early Exit

```python
# Stop at first match
def quick_detect(text, marker_id):
    for pattern in compiled_patterns[marker_id]:
        if pattern.search(text):
            return True
    return False
```

---

## 🔍 Validation & Testing

### Test Your Integration

```python
# Test with known examples
test_cases = [
    ("Ich bin so glücklich!", "ATO_JOY_HAPPINESS"),
    ("Ich bin traurig.", "ATO_SADNESS_GRIEF"),
    ("Das macht mich wütend!", "ATO_ANGER_RAGE"),
]

for text, expected in test_cases:
    detected = detect_emotion(text)
    assert expected in detected, f"Failed: {text}"
    print(f"✅ {text} -> {detected}")
```

---

## 📚 Further Reading

- **README.md** - Complete documentation
- **PROJECT_SUMMARY.md** - Detailed project overview
- **VALIDATION_REPORT.md** - Quality metrics and validation

---

## 🤝 Support & Contribution

### Questions?

- Check the README.md for detailed documentation
- Review the VALIDATION_REPORT.md for quality metrics

### Want to Extend?

- Add more languages (Spanish, French, etc.)
- Create SEM markers by combining atomics
- Build CLU markers for pattern clustering

---

## ✅ Quick Checklist

- [ ] Read this Quick Start Guide
- [ ] Review README.md for full documentation
- [ ] Load a marker file and inspect structure
- [ ] Test pattern matching with examples
- [ ] Integrate into your application
- [ ] Validate with real-world data
- [ ] Adjust patterns based on feedback

---

**Ready to Start?** 🚀

Pick a marker, load it, and start detecting emotions in your text data!

---

*Created: 2026-02-12*  
*Version: 1.0*  
*Schema: LeanDeep 3.4*
