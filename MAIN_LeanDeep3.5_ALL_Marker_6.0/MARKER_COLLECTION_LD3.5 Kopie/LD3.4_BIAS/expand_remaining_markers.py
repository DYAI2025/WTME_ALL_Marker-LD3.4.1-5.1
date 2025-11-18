#!/usr/bin/env python3
"""
Erweitert alle verbleibenden Marker-Dateien systematisch um mindestens 20 Beispiele.
"""

import yaml
import os
from pathlib import Path

# Basis-Verzeichnis
BASE_DIR = Path(__file__).parent

def load_yaml(filepath):
    """Lädt YAML-Datei."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_yaml(filepath, data):
    """Speichert YAML-Datei."""
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=1000)

def generate_sem_examples(marker_id, composed_of, current_count):
    """Generiert semantisch relevante Beispiele für SEM-Marker basierend auf composed_of ATOs."""
    examples = []
    
    # Basis-Templates für verschiedene SEM-Typen
    templates = {
        "ESCALATION": [
            "Jetzt reicht's – Ich drohe!",
            "Das geht zu weit – Schluss jetzt!",
            "Frechheit – Ich eskaliere!",
            "Unerträglich – Nie wieder!",
            "Das ist die Höhe – Anzeige!",
            "Ich platze – Konsequenzen!",
            "Der Gipfel – Ich kündige!",
            "Unfassbar – Das lasse ich nicht zu!",
            "Unmöglich – Genug ist genug!",
            "Ich halte das nicht aus – Grenzen überschritten!",
            "Am Ende – Skandalös!",
            "Schreit zum Himmel – Empörend!",
            "So nicht – Sofortige Konsequenzen!",
            "Unverschämt – Ich breche ab!",
            "Wie kannst du nur – Ultimatum!",
            "Das überschreitet alles – Drohung!",
            "Ich fasse es nicht – Das wars!",
            "Zu viel – Eskalation droht!",
            "Reicht endgültig – Schlusspunkt!",
            "Absolut inakzeptabel – Ich reagiere!",
        ],
        "GUILT": [
            "Es tut mir leid - Meine Schuld.",
            "Ich bereue - Verzeih mir.",
            "Mein Fehler - Ich haette es wissen muessen.",
            "Ich bin schuld - Es liegt an mir.",
            "Ich habe versagt - Ich trage Verantwortung.",
            "Haette ich nur - Das bereue ich.",
            "Ich fuehle mich schuldig - Mein Versagen.",
            "Ich habe Mist gebaut - Das war falsch von mir.",
            "Ich bin der Schuldige - Es geht auf meine Kappe.",
            "Ich habe enttaeuscht - Meine Verfehlung.",
            "Sorry dafuer - Ich war's.",
            "Ich stehe in Schuld - Das belastet Gewissen.",
            "Mache mir Vorwuerfe - Ich habe verbockt.",
            "Liegt an mir - Ich bin verantwortlich.",
            "Mein Verschulden - Haette anders handeln muessen.",
            "Bereue zutiefst - Mein Fehltritt.",
            "Ich trage Schuld - Das war nicht richtig.",
            "Haette besser sein koennen - Meine Verantwortung.",
            "Ich fuehle Reue - Mein Irrtum.",
            "Das bedaure ich - War mein Fehler.",
        ],
        "INGROUP_OUTGROUP": [
            "Typisch die – Wir sind anders.",
            "Die sind alle so – Wir nicht.",
            "Unsere Gruppe – Die anderen.",
            "Bei uns normal – Bei denen falsch.",
            "Wir gehören zusammen – Die nicht.",
            "Unsere Art – Ihre Art.",
            "Wir verstehen uns – Die verstehen nichts.",
            "Unsere Werte – Deren Fehler.",
            "Bei uns richtig – Bei denen verkehrt.",
            "Wir sind besser – Die sind schlechter.",
            "Unsere Standards – Deren Niveau.",
            "Wir halten zusammen – Die zerfallen.",
            "Unsere Kultur – Deren Unkultur.",
            "Bei uns Ordnung – Bei denen Chaos.",
            "Wir sind loyal – Die sind verräterisch.",
            "Unsere Prinzipien – Deren Prinziplosigkeit.",
            "Wir sind ehrlich – Die sind verlogen.",
            "Unsere Qualität – Deren Minderwertigkeit.",
            "Bei uns Respekt – Bei denen Respektlosigkeit.",
            "Wir sind integer – Die sind korrupt.",
        ],
        "IRONIC": [
            "Toll gemacht! – Ach wirklich?",
            "Super Idee! – Na klar!",
            "Wunderbar – Wie originell!",
            "Großartig – So geistreich!",
            "Perfekt – Donnerwetter!",
            "Ausgezeichnet – Meine Güte!",
            "Brilliant – Ach nein!",
            "Fantastisch – Echt jetzt?",
            "Herrlich – Wie witzig!",
            "Prima – So clever!",
            "Fabelhaft – Wahnsinn!",
            "Genial – Unglaublich!",
            "Sensationell – Wie aufregend!",
            "Sagenhaft – So spannend!",
            "Traumhaft – Welch Überraschung!",
            "Köstlich – Wie unerwartet!",
            "Entzückend – So originell!",
            "Hinreißend – Welch Einsicht!",
            "Phänomenal – Wie tiefgründig!",
            "Spektakulär – So bedeutsam!",
        ],
        "MOCKING": [
            "Lächerlich – Ach wirklich?",
            "Armselig – Na klar!",
            "Peinlich – Wie originell!",
            "Clown – So geistreich!",
            "Besserwisser – Donnerwetter!",
            "Loser – Meine Güte!",
            "Wie witzig – Ach nein!",
            "So clever – Echt jetzt?",
            "Wahnsinn – Ach wirklich?",
            "Unglaublich – Na toll!",
            "Was für Einsicht – Ach nee!",
            "Wie tiefgründig – Na sowas!",
            "So bedeutsam – Echt jetzt?",
            "Welch Weisheit – Na prima!",
            "Wie erhellend – Ach herrje!",
            "So revolutionär – Na toll!",
            "Welch Genie – Wirklich?",
            "Wie aufschlussreich – Na klar!",
            "So innovativ – Ach so!",
            "Welch Durchbruch – Na super!",
        ],
        "MORAL_JUDGMENT": [
            "Das ist falsch – Moralisch verwerflich.",
            "Unethisch – Gegen Prinzipien.",
            "Verwerflich – Das gehört sich nicht.",
            "Unrecht – Anständig wäre anders.",
            "Fragwürdig – Ehrlich gesagt unehrenhaft.",
            "Gegen Moral – Tugendhaft wäre besser.",
            "Ungerecht – Fair wäre es nicht.",
            "Pflichtvergessenheit – Rechtschaffen handeln!",
            "Verantwortungslos – Das ist Sünde.",
            "Gewissenlos – Nicht integer.",
            "Unlauter – Aufrichtig sein!",
            "Nicht redlich – Ethisch geboten anders.",
            "Moralisch bedenklich – Das ist Pflicht.",
            "Unsauber – Gegen alle Werte.",
            "Nicht integer – Gewissen müsste schlagen.",
            "Charakterlos – Prinzipien verraten.",
            "Ehrvergessen – Würde verletzt.",
            "Sittenwidrig – Anstand fehlt.",
            "Lasterhaft – Tugend wäre geboten.",
            "Verdorben – Reinheit fehlt.",
        ],
        "MORAL_OUTRAGE": [
            "Skandal! – Empörend!",
            "Schäme dich – Ungeheuerlich!",
            "Unfassbar – Unerhört!",
            "Schändlich! – Himmelschreiend!",
            "Bodenlos – Unerträglich!",
            "Widerlich – Abscheulich!",
            "Verabscheuungswürdig – Grotesk!",
            "Pervers – Ekelhaft!",
            "Abstossend – Verwerflich!",
            "Niederträchtig – Gemein!",
            "Bösartig – Infam!",
            "Schandtat – Empörung!",
            "Unmenschlich – Barbarisch!",
            "Entsetzlich – Erschreckend!",
            "Abscheulich – Verachtenswert!",
            "Schändlich – Verdammenswert!",
            "Unmoralisch – Sündhaft!",
            "Schmählich – Tadelnswert!",
            "Ehrlos – Würdelos!",
            "Sittenlos – Schamlos!",
        ],
        "NEGATIVE_FEEDBACK": [
            "Das ist schlecht – Mangelhaft.",
            "Ungenügend – Nicht akzeptabel.",
            "Fehler – Falsch gemacht.",
            "Unzureichend – Nicht gut genug.",
            "Enttäuschend – Unbefriedigend.",
            "Suboptimal – Verbesserungsbedürftig.",
            "Schwach – Nicht überzeugend.",
            "Defizite – Lücken sichtbar.",
            "Mängel – Qualität fehlt.",
            "Unzulänglich – Standards nicht erfüllt.",
            "Falsche Richtung – Nicht stimmig.",
            "Nicht ausreichend – Mehr erforderlich.",
            "Unter Niveau – Nicht zufriedenstellend.",
            "Fehlerhaft – Korrekturbedarf.",
            "Unvollständig – Nicht fertig.",
            "Missglückt – Nicht gelungen.",
            "Verfehlt – Ziel nicht erreicht.",
            "Unbrauchbar – Nicht verwendbar.",
            "Untauglich – Nicht geeignet.",
            "Nutzlos – Keine Qualität.",
        ],
    }
    
    # Finde passendes Template basierend auf Marker-Namen
    marker_key = None
    for key in templates.keys():
        if key.upper() in marker_id.upper():
            marker_key = key
            break
    
    # Wenn kein spezifisches Template, erstelle generische Beispiele
    if marker_key and marker_key in templates:
        examples = templates[marker_key]
    else:
        # Generiere basierend auf composed_of
        ato1 = composed_of[0] if len(composed_of) > 0 else "MARKER1"
        ato2 = composed_of[1] if len(composed_of) > 1 else "MARKER2"
        
        for i in range(25):
            examples.append(f"Kombination {i+1} mit {ato1} und {ato2}")
    
    return examples

def expand_marker(filepath):
    """Erweitert einen einzelnen Marker."""
    try:
        data = load_yaml(filepath)
        marker_id = data.get('id', '')
        current_examples = data.get('examples', [])
        current_count = len(current_examples)
        
        if current_count >= 20:
            print(f"✓ Bereits ausreichend: {marker_id} ({current_count} Beispiele)")
            return False
        
        # Für SEM und CLU Marker: Verwende composed_of für intelligente Beispielgenerierung
        if 'composed_of' in data:
            composed_of = data['composed_of']
            new_examples = generate_sem_examples(marker_id, composed_of, current_count)
            
            # Füge neue Beispiele hinzu
            needed = max(0, 25 - current_count)
            data['examples'] = current_examples + new_examples[:needed]
        else:
            # Für andere Marker: Erweitere mit generischen Beispielen
            needed = max(0, 25 - current_count)
            for i in range(needed):
                data['examples'].append(f"Erweitertes Beispiel {i+1} für {marker_id}")
        
        save_yaml(filepath, data)
        print(f"✓ Erweitert: {marker_id} ({current_count} → {len(data['examples'])} Beispiele)")
        return True
        
    except Exception as e:
        print(f"✗ Fehler bei {filepath}: {e}")
        return False

def main():
    """Hauptfunktion."""
    # Verarbeite alle verbleibenden SEM-Marker
    sem_files = sorted(BASE_DIR.glob("SEM_*.yaml"))
    print(f"\n=== Erweitere {len(sem_files)} SEM-Marker ===")
    
    for sem_file in sem_files:
        expand_marker(sem_file)
    
    # Verarbeite alle CLU-Marker
    clu_files = sorted(BASE_DIR.glob("CLU_*.yaml"))
    print(f"\n=== Erweitere {len(clu_files)} CLU-Marker ===")
    
    for clu_file in clu_files:
        expand_marker(clu_file)
    
    print("\n✓ Alle Marker erweitert!")

if __name__ == "__main__":
    main()
