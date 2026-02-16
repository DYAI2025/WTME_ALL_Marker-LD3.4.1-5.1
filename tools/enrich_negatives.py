#!/usr/bin/env python3
"""
Enrich markers with negative examples for semantic precision.

Strategy per marker type:
- Manipulation markers: healthy communication equivalents
- Emotion markers: neutral/calm statements
- Positive markers: transactional/neutral statements
- Neutral: calm constructive communication

For each marker, generates 5-10 negatives based on its category and positives.
"""
import re
import sys
from pathlib import Path
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 200

QUALITY_DIR = Path("/Users/benjaminpoersch/Projects/Marker- entbiazed/WTME_ALL_Marker-LD3.4.1-5.1/build/markers_rated")

# === Transformation Functions ===

def hedge_absolutizer(text):
    """Replace absolute terms with hedged versions."""
    swaps = [
        (r'\bimmer\b', 'manchmal'), (r'\bnie\b', 'selten'),
        (r'\bständig\b', 'ab und zu'), (r'\bjedes Mal\b', 'oft'),
        (r'\balways\b', 'sometimes'), (r'\bnever\b', 'rarely'),
        (r'\beverything\b', 'some things'), (r'\bnothing\b', 'not much'),
        (r'\bcompletely\b', 'partially'), (r'\btotally\b', 'somewhat'),
        (r'\bdefinitely\b', 'probably'), (r'\babsolutely\b', 'mostly'),
        (r'\ball\b', 'some'), (r'\bnobody\b', 'few people'),
        (r'\beverybody\b', 'many people'), (r'\balle\b', 'einige'),
        (r'\bkein\w*\b', 'wenige'),
    ]
    result = text
    for pattern, replacement in swaps:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result if result != text else None

def neutralize_emotion(text):
    """Remove emotional charge from a sentence."""
    swaps = [
        (r'\bich hasse\b', 'ich mag nicht besonders'),
        (r'\bich liebe\b', 'ich finde gut'),
        (r'\bI hate\b', "I'm not fond of"),
        (r'\bI love\b', 'I appreciate'),
        (r'\bfurchtbar\b', 'nicht ideal'),
        (r'\bschrecklich\b', 'schwierig'),
        (r'\bwunderbar\b', 'ganz gut'),
        (r'\bterrible\b', 'not great'),
        (r'\bamazing\b', 'decent'),
        (r'\bhorrible\b', 'difficult'),
        (r'\bawful\b', 'not ideal'),
    ]
    result = text
    for pattern, replacement in swaps:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result if result != text else None

def add_agency(text):
    """Shift from passive/helpless to agentic language."""
    swaps = [
        (r'\bich kann nicht\b', 'ich entscheide mich gegen'),
        (r'\bI can\'t\b', 'I choose not to'),
        (r'\bich muss\b', 'ich entscheide mich zu'),
        (r'\bI have to\b', 'I choose to'),
        (r'\bes geht nicht\b', 'es ist schwierig, aber machbar'),
        (r'\bI need to\b', 'I want to'),
        (r'\bich brauche\b', 'ich wuensche mir'),
    ]
    result = text
    for pattern, replacement in swaps:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result if result != text else None

def shift_blame_to_ownership(text):
    """Shift blame/accusation to ownership language."""
    swaps = [
        (r'\bdu bist schuld\b', 'ich habe meinen Anteil daran'),
        (r'\bdu machst\b', 'ich erlebe es so, dass'),
        (r'\bit\'s your fault\b', "I take responsibility for my part"),
        (r'\byou always\b', 'I notice that sometimes'),
        (r'\byou never\b', 'I wish we could more often'),
        (r'\bwegen dir\b', 'wir haben gemeinsam'),
        (r'\byou made me\b', 'I felt'),
        (r'\bdu hast mich\b', 'ich habe mich'),
    ]
    result = text
    for pattern, replacement in swaps:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result if result != text else None

# === Category-Specific Negative Banks ===

MANIPULATION_NEG_DE = [
    "Ich sehe das anders, aber ich respektiere deine Sicht.",
    "Ich moechte ehrlich mit dir sein, auch wenn es schwer ist.",
    "Du hast recht, das war mein Fehler. Es tut mir leid.",
    "Lass uns beide unsere Seite erklaeren.",
    "Ich fuehle mich unwohl dabei und moechte darueber reden.",
    "Ich verstehe, warum du das so siehst.",
    "Danke, dass du mir das sagst. Ich denke darueber nach.",
    "Ich war nicht fair zu dir. Wie koennen wir das loesen?",
    "Mir ist wichtig, dass du dich sicher fuehlst.",
    "Ich nehme deine Bedenken ernst.",
]

MANIPULATION_NEG_EN = [
    "I see it differently, but I respect your view.",
    "I want to be honest with you, even though it's hard.",
    "You're right, that was my mistake. I'm sorry.",
    "Let's both explain our side.",
    "I feel uncomfortable about this and want to talk about it.",
    "I understand why you see it that way.",
    "Thank you for telling me that. I'll think about it.",
    "I wasn't fair to you. How can we fix this?",
    "It's important to me that you feel safe.",
    "I take your concerns seriously.",
]

EMOTION_NEG_DE = [
    "Ich denke, wir sollten das sachlich betrachten.",
    "Mir geht es gut, danke der Nachfrage.",
    "Das ist ein interessanter Gedanke.",
    "Ich bin gerade entspannt.",
    "Alles in Ordnung bei mir.",
    "Ich fuehle mich heute ruhig und gelassen.",
    "Das ueberrascht mich, aber es ist okay.",
    "Ich brauche kurz einen Moment, dann bin ich wieder da.",
    "Danke fuer die Information, ich schaue mir das an.",
    "Ich habe darueber nachgedacht und bin jetzt klarer.",
]

EMOTION_NEG_EN = [
    "I think we should look at this objectively.",
    "I'm doing fine, thanks for asking.",
    "That's an interesting thought.",
    "I'm feeling relaxed right now.",
    "Everything is fine with me.",
    "I'm feeling calm and settled today.",
    "That surprises me, but it's okay.",
    "I need a moment, then I'll be back.",
    "Thanks for the information, I'll look into it.",
    "I've thought about it and feel clearer now.",
]

POSITIVE_NEG_DE = [
    "Kannst du mir das Salz reichen?",
    "Der Termin ist um 14 Uhr.",
    "Ich war gestern einkaufen.",
    "Das Wetter soll morgen besser werden.",
    "Hast du die E-Mail gelesen?",
    "Ich muss noch tanken.",
    "Die Besprechung ist im Konferenzraum.",
    "Bitte schick mir die Unterlagen.",
    "Wann faehrt der Zug?",
    "Ich habe die Rechnung bezahlt.",
]

POSITIVE_NEG_EN = [
    "Can you pass the salt?",
    "The meeting is at 2 PM.",
    "I went shopping yesterday.",
    "The weather should be better tomorrow.",
    "Did you read the email?",
    "I need to get gas.",
    "The meeting is in the conference room.",
    "Please send me the documents.",
    "When does the train leave?",
    "I paid the bill.",
]

NEUTRAL_NEG_DE = [
    "Ich finde, wir sollten das in Ruhe besprechen.",
    "Das ist ein guter Punkt, den du da machst.",
    "Ich verstehe deine Perspektive.",
    "Lass uns gemeinsam eine Loesung finden.",
    "Mir ist aufgefallen, dass wir unterschiedlich denken.",
    "Ich moechte verstehen, was du meinst.",
    "Das klingt nach einem wichtigen Thema fuer dich.",
    "Ich schaetze, dass du das ansprichst.",
    "Koennen wir das von einer anderen Seite betrachten?",
    "Ich fuehle mich gerade ruhig und klar.",
]

NEUTRAL_NEG_EN = [
    "I think we should discuss this calmly.",
    "That's a good point you're making.",
    "I understand your perspective.",
    "Let's find a solution together.",
    "I've noticed we think differently about this.",
    "I want to understand what you mean.",
    "That sounds like an important topic for you.",
    "I appreciate you bringing this up.",
    "Can we look at this from a different angle?",
    "I'm feeling calm and clear right now.",
]

# === Marker Classification ===

MANIPULATION_KEYWORDS = {
    'GASLIGHTING', 'LOVE_BOMBING', 'TRIANGULATION', 'STONEWALLING',
    'BLAME_SHIFT', 'GUILT_TRIP', 'EMOTIONAL_BLACKMAIL', 'SILENT_TREATMENT',
    'PASSIVE_AGGRESS', 'CONTROL', 'ISOLATION', 'FUTURE_FAKING',
    'MINIMIZ', 'PROJECTION', 'DOUBLE_BIND', 'REALITY_DISTORTION',
    'MANIPULATION', 'INVALIDATION', 'SCAM', 'DECEPTION', 'THREAT',
    'COERCION', 'GROOMING', 'VICTIMIZ', 'EXPLOIT', 'DISMISSI',
    'CONTEMPT', 'CRITICISM', 'DEFENSIVENESS', 'ACCUSATION',
    'PLATFORM_SWITCH', 'WEBCAM_EXCUSE', 'MONEY_REQUEST',
}

EMOTION_KEYWORDS = {
    'ANGER', 'FEAR', 'SADNESS', 'JOY', 'DISGUST', 'ANXIETY',
    'SHAME', 'GUILT', 'HELPLESSNESS', 'VULNERABILITY', 'OVERWHELM',
    'RAGE', 'PANIC', 'GRIEF', 'LONELINESS', 'CRAVING', 'DENIAL',
    'MANIC', 'FLAT', 'TREMOLO', 'BREATHINESS', 'CREAKY',
    'STRESS', 'DISTRESS', 'IMPOSTER', 'RESIGNATION',
}

POSITIVE_KEYWORDS = {
    'REPAIR', 'VALIDATION', 'SUPPORT', 'CONNECTION', 'ACCEPTANCE',
    'EMPATHY', 'APPRECIATION', 'AFFECTION', 'CARE', 'BOUNDARY_SET',
    'CONSENSUS', 'ACCOUNTABILITY', 'SELF_REFLECTION', 'ASSERTIVE',
    'APOLOGY', 'GRATITUDE', 'ENCOURAGEMENT', 'COMMITMENT', 'TRUST',
    'RAPPORT', 'AFFILIATION', 'COOPERATIVE', 'NURTUR',
}

def classify_marker(marker_id):
    upper = str(marker_id).upper()
    for keyword in MANIPULATION_KEYWORDS:
        if keyword in upper:
            return 'manipulation'
    for keyword in EMOTION_KEYWORDS:
        if keyword in upper:
            return 'emotion'
    for keyword in POSITIVE_KEYWORDS:
        if keyword in upper:
            return 'positive'
    return 'neutral'

# === Example Extraction ===

def get_positives(data):
    """Extract positive examples from any schema format."""
    examples = data.get('examples', [])
    if examples is None:
        return []

    if isinstance(examples, dict):
        pos = []
        for key in ['positive', 'positive_de', 'positive_en', 'pos']:
            val = examples.get(key, [])
            if val:
                pos.extend([str(p) for p in val if p])
        return pos
    elif isinstance(examples, list):
        return [str(e) for e in examples if e]
    return []

def has_negatives(data):
    """Check if marker already has negative examples."""
    examples = data.get('examples', [])
    if examples is None:
        return False

    if isinstance(examples, dict):
        for key in ['negative', 'negative_de', 'negative_en', 'neg']:
            val = examples.get(key, [])
            if val and len(val) >= 3:
                return True
    return False

def detect_lang(data, positives):
    """Detect primary language."""
    lang = data.get('lang', '')
    if lang and lang in ('de', 'en'):
        return lang
    text = ' '.join(positives[:3]) if positives else ''
    if re.search(r'\b(ich|du|wir|nicht|und|das|ist|ein|der|die|mein|dein)\b', text, re.IGNORECASE):
        return 'de'
    return 'en'

# === Negative Generation ===

def generate_negatives(marker_id, positives, lang):
    """Generate negative examples combining transforms and category bank."""
    category = classify_marker(marker_id)
    negatives = []

    # Step 1: Transform existing positives (up to 3)
    transforms = [hedge_absolutizer, neutralize_emotion, add_agency, shift_blame_to_ownership]
    for pos in positives[:5]:
        for transform in transforms:
            result = transform(pos)
            if result and result not in negatives and result != pos:
                negatives.append(result)
                if len(negatives) >= 3:
                    break
        if len(negatives) >= 3:
            break

    # Step 2: Add category-specific negatives
    if lang == 'de':
        bank = {
            'manipulation': MANIPULATION_NEG_DE,
            'emotion': EMOTION_NEG_DE,
            'positive': POSITIVE_NEG_DE,
            'neutral': NEUTRAL_NEG_DE,
        }[category]
    else:
        bank = {
            'manipulation': MANIPULATION_NEG_EN,
            'emotion': EMOTION_NEG_EN,
            'positive': POSITIVE_NEG_EN,
            'neutral': NEUTRAL_NEG_EN,
        }[category]

    # Add enough from bank to reach 5-7 total
    for neg in bank:
        if neg not in negatives:
            negatives.append(neg)
        if len(negatives) >= 7:
            break

    # Deduplicate
    seen = set()
    unique = []
    for neg in negatives:
        norm = neg.strip().lower()
        if norm not in seen:
            seen.add(norm)
            unique.append(neg)

    return unique[:7]

def inject_negatives(data, negatives):
    """Add negatives to marker, respecting schema format."""
    examples = data.get('examples')

    if examples is None:
        data['examples'] = {'positive': [], 'negative': negatives}
        return

    if isinstance(examples, dict):
        # Already dict format
        if 'negative' not in examples or not examples.get('negative'):
            examples['negative'] = negatives
        else:
            existing = set(str(n).lower() for n in examples['negative'])
            for neg in negatives:
                if neg.lower() not in existing:
                    examples['negative'].append(neg)
    elif isinstance(examples, list):
        # Flat list -> convert to dict
        data['examples'] = {
            'positive': list(examples),
            'negative': negatives,
        }

# === Main ===

def process():
    enriched = 0
    skipped = 0
    errors = 0

    for tier in ['1_approved', '2_good']:
        tier_dir = QUALITY_DIR / tier
        if not tier_dir.exists():
            continue

        for layer_dir in sorted(tier_dir.iterdir()):
            if not layer_dir.is_dir():
                continue

            for yaml_file in sorted(layer_dir.glob("*.yaml")):
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        data = yaml.load(f)

                    if data is None:
                        skipped += 1
                        continue

                    if has_negatives(data):
                        skipped += 1
                        continue

                    positives = get_positives(data)
                    marker_id = data.get('id', data.get('name', yaml_file.stem))
                    lang = detect_lang(data, positives)

                    negatives = generate_negatives(str(marker_id), positives, lang)
                    if not negatives:
                        skipped += 1
                        continue

                    inject_negatives(data, negatives)

                    with open(yaml_file, 'w', encoding='utf-8') as f:
                        yaml.dump(data, f)

                    enriched += 1
                    if enriched % 100 == 0:
                        print(f"  ...enriched {enriched} markers", file=sys.stderr)

                except Exception as e:
                    errors += 1
                    print(f"ERROR: {yaml_file.name}: {e}", file=sys.stderr)

    print(f"\nDone. Enriched {enriched}, skipped {skipped} (already had negatives), errors {errors}.")

if __name__ == '__main__':
    process()
