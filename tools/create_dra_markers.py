#!/usr/bin/env python3
"""
Create DRA Mode emotion markers: 12 base emotions + 3 intensity + 3 negation/guard + 2 emoticons + 1 hearsay = 21 markers.
Updates YAML files and marker_registry.json.
"""
import json
from pathlib import Path
from ruamel.yaml import YAML

yaml_rw = YAML()
yaml_rw.default_flow_style = False
yaml_rw.width = 200
yaml_rw.allow_unicode = True

REPO = Path("/Users/benjaminpoersch/Projects/Marker- entbiazed/WTME_ALL_Marker-LD3.4.1-5.1")
ATO_DIR = REPO / "build" / "markers_normalized" / "ATO"
REGISTRY_PATH = REPO / "build" / "markers_normalized" / "marker_registry.json"

# ─── All 21 DRA markers ───────────────────────────────────────────────

MARKERS = [
    # ═══ 1) Base Emotions ═══
    {
        "id": "ATO_EMO_LEX_ANGER",
        "schema": "LeanDeep",
        "version": "5.1",
        "layer": "ATO",
        "lang": "de",
        "description": "Lexikon: Wut/\u00c4rger/Aggression.",
        "frame": {
            "signal": ["anger", "rage", "wut", "aerger", "zorn"],
            "concept": "negative valence: anger",
            "pragmatics": "konflikt-affekt",
            "narrative": "emotion_lex"
        },
        "patterns": [
            {"type": "regex", "value": "(?i)\\b(wut|zorn|hass|rage|anger)\\b"},
            {"type": "regex", "value": "(?i)\\b(w\u00fctend|wuetend|wutend|zornig|erz\u00fcrnt|aggressiv)\\b"},
            {"type": "regex", "value": "(?i)\\b(\u00e4rger\\w*|aerger\\w*|genervt\\w*|gereizt\\w*|frustriert\\w*)\\b"},
            {"type": "regex", "value": "(?i)\\b(stinksauer|sauer\\s+auf|ich\\s+raste\\s+aus|ich\\s+ticke\\s+aus|ich\\s+flippe\\s+aus)\\b"},
        ],
        "examples": {
            "positive": ["Ich bin w\u00fctend.", "Das nervt mich total.", "Ich raste gleich aus."],
            "negative": ["Ich bin ruhig.", "Das st\u00f6rt mich nicht.", "Alles gut."]
        },
        "tags": ["emotion", "lexicon", "anger"],
        "rating": 1
    },
    {
        "id": "ATO_EMO_LEX_SADNESS",
        "schema": "LeanDeep",
        "version": "5.1",
        "layer": "ATO",
        "lang": "de",
        "description": "Lexikon: Trauer/Niedergeschlagenheit/Weinen.",
        "frame": {
            "signal": ["sadness", "grief", "trauer", "traurig"],
            "concept": "negative valence: sadness",
            "pragmatics": "verlust/bedauern",
            "narrative": "emotion_lex"
        },
        "patterns": [
            {"type": "regex", "value": "(?i)\\b(traurig\\w*|trauer\\w*|kummer\\w*|niedergeschlagen\\w*|melanchol\\w*)\\b"},
            {"type": "regex", "value": "(?i)\\b(weinen|geweint|tr\u00e4nen|traenen|schluchz\\w*)\\b"},
            {"type": "regex", "value": "(?i)\\b(vermiss\\w*|sehnsucht\\w*|verlust\\w*|tut\\s+mir\\s+leid)\\b"},
        ],
        "examples": {
            "positive": ["Ich bin traurig.", "Ich vermisse dich.", "Ich habe geweint."],
            "negative": ["Mir geht es gut.", "Ich bin entspannt."]
        },
        "tags": ["emotion", "lexicon", "sadness"],
        "rating": 1
    },
    {
        "id": "ATO_EMO_LEX_FEAR_ANXIETY",
        "schema": "LeanDeep",
        "version": "5.1",
        "layer": "ATO",
        "lang": "de",
        "description": "Lexikon: Angst/Panik/Sorge.",
        "frame": {
            "signal": ["fear", "anxiety", "angst", "panik"],
            "concept": "negative valence: fear/anxiety",
            "pragmatics": "bedrohung/unsicherheit",
            "narrative": "emotion_lex"
        },
        "patterns": [
            {"type": "regex", "value": "(?i)\\b(angst\\w*|panik\\w*|furcht\\w*|schiss|bammel)\\b"},
            {"type": "regex", "value": "(?i)\\b(\u00e4ngstlich\\w*|aengstlich\\w*|nerv\u00f6s\\w*|nervoes\\w*|besorgt\\w*|beunruhigt\\w*)\\b"},
            {"type": "regex", "value": "(?i)\\b(sorge\\w*|ich\\s+f\u00fcrchte\\w*|ich\\s+habe\\s+angst)\\b"},
        ],
        "examples": {
            "positive": ["Ich habe Angst.", "Ich bin nerv\u00f6s.", "Ich kriege Panik."],
            "negative": ["Ich f\u00fchle mich sicher.", "Alles ist entspannt."]
        },
        "tags": ["emotion", "lexicon", "fear"],
        "rating": 1
    },
    {
        "id": "ATO_EMO_LEX_DISGUST",
        "schema": "LeanDeep",
        "version": "5.1",
        "layer": "ATO",
        "lang": "de",
        "description": "Lexikon: Ekel/Abscheu.",
        "frame": {
            "signal": ["disgust", "ekel"],
            "concept": "negative valence: disgust",
            "pragmatics": "ablehnung/aversiv",
            "narrative": "emotion_lex"
        },
        "patterns": [
            {"type": "regex", "value": "(?i)\\b(ekel\\w*|eklig\\w*|widerlich\\w*|absto\u00dfend\\w*|abstossend\\w*)\\b"},
            {"type": "regex", "value": "(?i)\\b(bah+|ihh+|zum\\s+kotzen)\\b"},
        ],
        "examples": {
            "positive": ["Das ist widerlich.", "Ich finde das eklig.", "Bah."],
            "negative": ["Das ist okay.", "Das ist neutral."]
        },
        "tags": ["emotion", "lexicon", "disgust"],
        "rating": 1
    },
    {
        "id": "ATO_EMO_LEX_JOY",
        "schema": "LeanDeep",
        "version": "5.1",
        "layer": "ATO",
        "lang": "de",
        "description": "Lexikon: Freude/Gl\u00fcck/Begeisterung.",
        "frame": {
            "signal": ["joy", "happiness", "freude"],
            "concept": "positive valence: joy",
            "pragmatics": "bindung/belohnung",
            "narrative": "emotion_lex"
        },
        "patterns": [
            {"type": "regex", "value": "(?i)\\b(freude\\w*|froh\\w*|gl\u00fccklich\\w*|gluecklich\\w*|happy|yay|super)\\b"},
            {"type": "regex", "value": "(?i)\\b(begeistert\\w*|toll|mega|hammer|geil)\\b"},
            {"type": "regex", "value": "(?i)\\b(ich\\s+freue\\s+mich|das\\s+macht\\s+mich\\s+gl\u00fccklich|das\\s+macht\\s+mich\\s+gluecklich)\\b"},
        ],
        "examples": {
            "positive": ["Ich freue mich.", "Ich bin gl\u00fccklich.", "Yay!"],
            "negative": ["Das ist schlimm.", "Ich bin traurig."]
        },
        "tags": ["emotion", "lexicon", "joy"],
        "rating": 1
    },
    {
        "id": "ATO_EMO_LEX_SURPRISE",
        "schema": "LeanDeep",
        "version": "5.1",
        "layer": "ATO",
        "lang": "de",
        "description": "Lexikon: \u00dcberraschung/Erstaunen.",
        "frame": {
            "signal": ["surprise", "wow"],
            "concept": "neutral/positive: surprise",
            "pragmatics": "unerwartet",
            "narrative": "emotion_lex"
        },
        "patterns": [
            {"type": "regex", "value": "(?i)\\b(\u00fcberrascht\\w*|ueberrascht\\w*|erstaunt\\w*|verbl\u00fcfft\\w*|verbluefft\\w*)\\b"},
            {"type": "regex", "value": "(?i)\\b(wow|echt\\?|krass|nicht\\s+zu\\s+fassen|h\u00e4tte\\s+ich\\s+nicht\\s+gedacht)\\b"},
        ],
        "examples": {
            "positive": ["Wow, das \u00fcberrascht mich.", "Damit h\u00e4tte ich nicht gerechnet."],
            "negative": ["Das war erwartbar.", "War klar."]
        },
        "tags": ["emotion", "lexicon", "surprise"],
        "rating": 1
    },
    {
        "id": "ATO_EMO_LEX_SHAME_GUILT",
        "schema": "LeanDeep",
        "version": "5.1",
        "layer": "ATO",
        "lang": "de",
        "description": "Lexikon: Scham/Schuld/Reue/Peinlichkeit.",
        "frame": {
            "signal": ["shame", "guilt", "schuld"],
            "concept": "negative valence: shame/guilt",
            "pragmatics": "selbstbewertung",
            "narrative": "emotion_lex"
        },
        "patterns": [
            {"type": "regex", "value": "(?i)\\b(scham\\w*|ich\\s+sch\u00e4me\\s+mich|ich\\s+schaeme\\s+mich|peinlich\\w*|besch\u00e4mt\\w*|beschaemt\\w*)\\b"},
            {"type": "regex", "value": "(?i)\\b(schuld\\w*|schuldig\\w*|schlechtes\\s+gewissen|bereu\\w*|reue\\w*)\\b"},
        ],
        "examples": {
            "positive": ["Das ist mir peinlich.", "Ich habe ein schlechtes Gewissen.", "Ich bereue das."],
            "negative": ["Ich stehe dazu neutral.", "Das ist mir egal."]
        },
        "tags": ["emotion", "lexicon", "shame_guilt"],
        "rating": 1
    },
    {
        "id": "ATO_EMO_LEX_LOVE_AFFECTION",
        "schema": "LeanDeep",
        "version": "5.1",
        "layer": "ATO",
        "lang": "de",
        "description": "Lexikon: Liebe/Zuneigung/N\u00e4he.",
        "frame": {
            "signal": ["love", "affection"],
            "concept": "positive valence: love/attachment",
            "pragmatics": "bindung/naehe",
            "narrative": "emotion_lex"
        },
        "patterns": [
            {"type": "regex", "value": "(?i)\\b(liebe\\w*|verliebt\\w*|zuneigung\\w*|ich\\s+mag\\s+dich|hab\\s+dich\\s+gern)\\b"},
            {"type": "regex", "value": "(?i)\\b(umarm\\w*|kusch\\w*|w\u00e4rme|naehe|geborgen\\w*)\\b"},
            {"type": "regex", "value": "(?i)\\b(ich\\s+vermiss\\w*\\s+dich|du\\s+fehlst\\s+mir)\\b"},
        ],
        "examples": {
            "positive": ["Ich hab dich gern.", "Du fehlst mir.", "Ich liebe dich."],
            "negative": ["Ich hasse dich.", "Mir ist das egal."]
        },
        "tags": ["emotion", "lexicon", "love"],
        "rating": 1
    },
    {
        "id": "ATO_EMO_LEX_ENVY_JEALOUSY",
        "schema": "LeanDeep",
        "version": "5.1",
        "layer": "ATO",
        "lang": "de",
        "description": "Lexikon: Neid/Eifersucht.",
        "frame": {
            "signal": ["envy", "jealousy"],
            "concept": "negative valence: social comparison",
            "pragmatics": "besitz/konkurrenz",
            "narrative": "emotion_lex"
        },
        "patterns": [
            {"type": "regex", "value": "(?i)\\b(neid\\w*|neidisch\\w*|eifersucht\\w*|eifers\u00fcchtig\\w*|eifersuechtig\\w*)\\b"},
        ],
        "examples": {
            "positive": ["Ich bin eifers\u00fcchtig.", "Da bin ich neidisch."],
            "negative": ["Ich g\u00f6nne es dir.", "Freut mich f\u00fcr dich."]
        },
        "tags": ["emotion", "lexicon", "envy_jealousy"],
        "rating": 1
    },
    {
        "id": "ATO_EMO_LEX_PRIDE",
        "schema": "LeanDeep",
        "version": "5.1",
        "layer": "ATO",
        "lang": "de",
        "description": "Lexikon: Stolz/Leistung/Zufriedenheit.",
        "frame": {
            "signal": ["pride", "stolz"],
            "concept": "positive valence: pride",
            "pragmatics": "selbstwirksamkeit",
            "narrative": "emotion_lex"
        },
        "patterns": [
            {"type": "regex", "value": "(?i)\\b(stolz\\w*|geschafft|erreicht|ich\\s+bin\\s+so\\s+stolz|ich\\s+bin\\s+zufrieden\\s+mit\\s+mir)\\b"},
        ],
        "examples": {
            "positive": ["Ich bin stolz auf mich.", "Ich hab das geschafft."],
            "negative": ["Ich f\u00fchle mich schlecht.", "Das war ein Fehler."]
        },
        "tags": ["emotion", "lexicon", "pride"],
        "rating": 1
    },
    {
        "id": "ATO_EMO_LEX_HOPE_RELIEF",
        "schema": "LeanDeep",
        "version": "5.1",
        "layer": "ATO",
        "lang": "de",
        "description": "Lexikon: Hoffnung/Erleichterung/Zuversicht.",
        "frame": {
            "signal": ["hope", "relief"],
            "concept": "positive valence: hope/relief",
            "pragmatics": "spannung->loesung",
            "narrative": "emotion_lex"
        },
        "patterns": [
            {"type": "regex", "value": "(?i)\\b(hoffnung\\w*|ich\\s+hoffe\\w*|zuversicht\\w*|wird\\s+schon)\\b"},
            {"type": "regex", "value": "(?i)\\b(erleichtert\\w*|endlich|zum\\s+gl\u00fcck|zum\\s+glueck|gott\\s+sei\\s+dank)\\b"},
        ],
        "examples": {
            "positive": ["Ich bin erleichtert.", "Zum Gl\u00fcck ist es vorbei.", "Ich hoffe, das klappt."],
            "negative": ["Es ist aussichtslos.", "Ich gebe auf."]
        },
        "tags": ["emotion", "lexicon", "hope", "relief"],
        "rating": 1
    },
    {
        "id": "ATO_EMO_LEX_LONELINESS",
        "schema": "LeanDeep",
        "version": "5.1",
        "layer": "ATO",
        "lang": "de",
        "description": "Lexikon: Einsamkeit/Verlassenheit.",
        "frame": {
            "signal": ["lonely", "einsam", "allein"],
            "concept": "negative valence: loneliness",
            "pragmatics": "bindungsmangel",
            "narrative": "emotion_lex"
        },
        "patterns": [
            {"type": "regex", "value": "(?i)\\b(einsam\\w*|allein\\w*|isoliert\\w*|verlassen\\w*)\\b"},
            {"type": "regex", "value": "(?i)\\b(niemand\\s+da|ich\\s+bin\\s+allein\\s+damit|alleine\\s+gelassen)\\b"},
        ],
        "examples": {
            "positive": ["Ich f\u00fchle mich einsam.", "Ich bin allein damit."],
            "negative": ["Ich f\u00fchle mich verbunden.", "Ich habe Unterst\u00fctzung."]
        },
        "tags": ["emotion", "lexicon", "loneliness"],
        "rating": 1
    },

    # ═══ 2) Intensity Modifiers ═══
    {
        "id": "ATO_EMO_INTENSIFIER_HIGH",
        "schema": "LeanDeep",
        "version": "5.1",
        "layer": "ATO",
        "lang": "de",
        "description": "Intensivierer hoch (boost).",
        "frame": {
            "signal": ["sehr", "extrem", "total"],
            "concept": "intensity_high",
            "pragmatics": "verstaerkung",
            "narrative": "modifier"
        },
        "patterns": [
            {"type": "regex", "value": "(?i)\\b(sehr|extrem|total|komplett|absolut|unfassbar|wahnsinnig|mega|ultra|krass|heftig|richtig|voll)\\b"},
        ],
        "examples": {
            "positive": ["Das nervt extrem.", "Ich bin total traurig."],
            "negative": ["Das ist etwas schade."]
        },
        "tags": ["emotion", "intensity", "modifier"],
        "rating": 1
    },
    {
        "id": "ATO_EMO_INTENSIFIER_LOW",
        "schema": "LeanDeep",
        "version": "5.1",
        "layer": "ATO",
        "lang": "de",
        "description": "Intensivierer niedrig (downscale).",
        "frame": {
            "signal": ["bisschen", "etwas", "kaum"],
            "concept": "intensity_low",
            "pragmatics": "abwaertung",
            "narrative": "modifier"
        },
        "patterns": [
            {"type": "regex", "value": "(?i)\\b(ein\\s+bisschen|bisschen|etwas|leicht|minimal|kaum|so\\s+halb)\\b"},
        ],
        "examples": {
            "positive": ["Ich bin etwas genervt.", "Das macht mich ein bisschen traurig."],
            "negative": ["Ich bin extrem w\u00fctend."]
        },
        "tags": ["emotion", "intensity", "modifier"],
        "rating": 1
    },
    {
        "id": "ATO_EMO_PUNCT_INTENSITY",
        "schema": "LeanDeep",
        "version": "5.1",
        "layer": "ATO",
        "lang": "de",
        "description": "Interpunktions-Intensit\u00e4t (!!!, ???, ...).",
        "frame": {
            "signal": ["!!", "??", "..."],
            "concept": "punctuation_intensity",
            "pragmatics": "prosody_text",
            "narrative": "modifier"
        },
        "patterns": [
            {"type": "regex", "value": "(!{2,}|\\?{2,}|\\?!|!\\?|\\.{3,})"},
        ],
        "examples": {
            "positive": ["Was soll das???", "Nein!!!", "Oh man..."],
            "negative": ["Ok.", "Ja."]
        },
        "tags": ["emotion", "intensity", "modifier"],
        "rating": 1
    },

    # ═══ 3) Negation ═══
    {
        "id": "ATO_NEGATION_TOKEN",
        "schema": "LeanDeep",
        "version": "5.1",
        "layer": "ATO",
        "lang": "de",
        "description": "Negationsmarker (Token/Phrasen).",
        "frame": {
            "signal": ["nicht", "kein", "nie"],
            "concept": "negation",
            "pragmatics": "scope negation",
            "narrative": "modifier"
        },
        "patterns": [
            {"type": "regex", "value": "(?i)\\b(nicht|nie|niemals|nix|nichts|ohne|weder)\\b"},
            {"type": "regex", "value": "(?i)\\b(kein(?:e|en|em|er)?|keineswegs)\\b"},
            {"type": "regex", "value": "(?i)\\b(\u00fcberhaupt\\s+nicht|gar\\s+nicht|auf\\s+keinen\\s+fall|in\\s+keinster\\s+weise)\\b"},
        ],
        "examples": {
            "positive": ["Ich bin nicht traurig.", "Gar nicht.", "Nie wieder."],
            "negative": ["Ich bin traurig.", "Ich bin froh."]
        },
        "tags": ["negation", "modifier"],
        "rating": 1
    },

    # ═══ 4) Reported Speech / Quotes / Hearsay ═══
    {
        "id": "ATO_REPORTED_SPEECH_VERB",
        "schema": "LeanDeep",
        "version": "5.1",
        "layer": "ATO",
        "lang": "de",
        "description": "Verben des Sagens/Schreibens (reported speech cue).",
        "frame": {
            "signal": ["sagte", "meinte", "schrieb"],
            "concept": "reported_speech",
            "pragmatics": "attribution",
            "narrative": "context_guard"
        },
        "patterns": [
            {"type": "regex", "value": "(?i)\\b(sagte|meinte|schrieb|textete|postete|antwortete|fragte|rief|fl\u00fcsterte|fluesterte|erkl\u00e4rte|behauptete|gestand|gab\\s+zu)\\b"},
            {"type": "regex", "value": "(?i)\\b(er\\s+so\\s*:|sie\\s+so\\s*:|ich\\s+so\\s*:)\\b"},
        ],
        "examples": {
            "positive": ["Er sagte: \"Ich bin traurig.\"", "Sie meinte, ich sei w\u00fctend."],
            "negative": ["Ich bin traurig.", "Ich f\u00fchle mich w\u00fctend."]
        },
        "tags": ["reported_speech", "guard"],
        "rating": 1
    },
    {
        "id": "ATO_QUOTE_MARK",
        "schema": "LeanDeep",
        "version": "5.1",
        "layer": "ATO",
        "lang": "de",
        "description": "Quote delimiters (Anf\u00fchrungszeichen).",
        "frame": {
            "signal": ["\"", "'", "quotes"],
            "concept": "quote_delimiter",
            "pragmatics": "quotation",
            "narrative": "context_guard"
        },
        "patterns": [
            {"type": "regex", "value": "[\"\u2019\u201e\u201c\u00ab\u00bb]"},
        ],
        "examples": {
            "positive": ["\"Ich bin traurig\"", "Er nannte mich 'w\u00fctend'."],
            "negative": ["Ich bin traurig."]
        },
        "tags": ["reported_speech", "guard"],
        "rating": 1
    },
    {
        "id": "ATO_HEARSAY_CUE",
        "schema": "LeanDeep",
        "version": "5.1",
        "layer": "ATO",
        "lang": "de",
        "description": "H\u00f6rensagen/Attributions-Cues (angeblich, laut X, wie X sagt).",
        "frame": {
            "signal": ["angeblich", "laut"],
            "concept": "hearsay",
            "pragmatics": "uncertain attribution",
            "narrative": "context_guard"
        },
        "patterns": [
            {"type": "regex", "value": "(?i)\\b(angeblich|hei\u00dft\\s+es|heisst\\s+es|ger\u00fccht\\w*|geruecht\\w*|laut\\s+ihm|laut\\s+ihr|wie\\s+er\\s+sagt|wie\\s+sie\\s+sagt)\\b"},
        ],
        "examples": {
            "positive": ["Angeblich war er w\u00fctend.", "Laut ihr ist er traurig."],
            "negative": ["Ich bin w\u00fctend.", "Ich bin traurig."]
        },
        "tags": ["reported_speech", "guard"],
        "rating": 1
    },

    # ═══ 5) ASCII Emoticons ═══
    {
        "id": "ATO_EMOTICON_POS",
        "schema": "LeanDeep",
        "version": "5.1",
        "layer": "ATO",
        "lang": "de",
        "description": "ASCII-Emoticons positiv.",
        "frame": {
            "signal": [":)", ":D", "<3"],
            "concept": "emoticon_positive",
            "pragmatics": "affect",
            "narrative": "emotion_lex"
        },
        "patterns": [
            {"type": "regex", "value": "(:-\\)|:\\)|:D|xD|<3)"},
        ],
        "examples": {
            "positive": ["Haha :D", "Danke <3", "Ok :)"],
            "negative": ["Oh nein :(", "Mist..."]
        },
        "tags": ["emotion", "emoticon"],
        "rating": 1
    },
    {
        "id": "ATO_EMOTICON_NEG",
        "schema": "LeanDeep",
        "version": "5.1",
        "layer": "ATO",
        "lang": "de",
        "description": "ASCII-Emoticons negativ.",
        "frame": {
            "signal": [":(", "T_T", ":'("],
            "concept": "emoticon_negative",
            "pragmatics": "affect",
            "narrative": "emotion_lex"
        },
        "patterns": [
            {"type": "regex", "value": "(:-\\(|:\\(|:'\\(|T_T|D:|>:\\(|:-/|:/)"},
        ],
        "examples": {
            "positive": ["Oh man :(", "T_T", "Warum nur :'("],
            "negative": ["Alles gut :)", "Yay :D"]
        },
        "tags": ["emotion", "emoticon"],
        "rating": 1
    },
]


def main():
    # Load registry
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    created = 0
    updated = 0

    for marker in MARKERS:
        mid = marker["id"]

        # Write YAML file
        yaml_path = ATO_DIR / f"{mid}.yaml"
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml_rw.dump(marker, f)

        # Build registry entry
        entry = {
            "layer": marker["layer"],
            "lang": marker.get("lang", "de"),
            "description": marker.get("description", ""),
            "tags": marker.get("tags", []),
            "rating": marker.get("rating", 1),
            "patterns": marker.get("patterns", []),
            "examples": marker.get("examples", {}),
            "frame": marker.get("frame", {}),
        }

        if mid in registry["markers"]:
            updated += 1
        else:
            created += 1

        registry["markers"][mid] = entry

    # Update registry counts
    layer_counts = {}
    for m in registry["markers"].values():
        l = m.get("layer", "UNKNOWN")
        layer_counts[l] = layer_counts.get(l, 0) + 1

    registry["total"] = len(registry["markers"])

    # Write registry
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    print(f"=== DRA Marker Creation Complete ===")
    print(f"Created: {created}")
    print(f"Updated: {updated}")
    print(f"Total markers now: {registry['total']}")
    for l in sorted(layer_counts):
        print(f"  {l}: {layer_counts[l]}")


if __name__ == "__main__":
    main()
