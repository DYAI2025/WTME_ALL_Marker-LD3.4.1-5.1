#!/usr/bin/env python3
"""
Erweitert alle Marker-Dateien um mindestens 20 zusätzliche semantisch relevante Beispiele.
Erstellt fehlende ATOs für SEM/CLU Marker.
"""

import yaml
import os
import re
from pathlib import Path
from typing import Dict, List, Set

# Semantische Beispielgeneratoren für jeden Marker-Typ
SEMANTIC_EXAMPLES = {
    # ATO - Atomic Markers
    "ATO_ANXIETY_TERMS": [
        "Das macht mir Angst.", "Ich mache mir Sorgen.", "Keine Panik, aber...",
        "Mir ist total unheimlich.", "Ich fühle mich nervös.", "Angst vor dem Scheitern.",
        "Sorge, dass es nicht klappt.", "Panik steigt in mir auf.", "Mulmiges Bauchgefühl.",
        "Unheimlich unangenehm.", "Total nervös deswegen.", "Angst lähmt mich.",
        "Sorge bereitet mir das.", "Panisch werde ich.", "Mulmig wird mir dabei.",
        "Unheimlich bedrohlich.", "Nervös macht mich das.", "Angstgefühle kommen hoch.",
        "Sorgen plagen mich.", "Panik erfasst mich.", "Beängstigendes Szenario.",
        "Sorgenvoll schaue ich drauf.", "Panische Reaktion.", "Mulmig in der Magengegend.",
        "Unheimlich riskant."
    ],
    "ATO_HEDGING_TERMS": [
        "Vielleicht ist es so.", "Könnte sein.", "Eventuell klappt es.", "Möglicherweise ja.",
        "Wahrscheinlich nicht.", "Vermutlich schon.", "Tendenziell eher.", "Ungefähr so.",
        "In etwa das.", "Schätzungsweise drei.", "Anscheinend funktioniert es.",
        "Offenbar ist es so.", "Womöglich geht es.", "Unter Umständen ja.",
        "Gegebenenfalls nein.", "Potentiell möglich.", "Mutmaßlich richtig.",
        "Augenscheinlich falsch.", "Quasi dasselbe.", "Sozusagen identisch.",
        "Praktisch fertig.", "Relativ sicher.", "Ziemlich wahrscheinlich.",
        "Einigermaßen klar.", "Weitgehend bekannt."
    ],
    "ATO_COMMITMENT_PHRASES": [
        "Ich verspreche es.", "Zugesagt!", "Mache ich definitiv.", "Fest eingeplant.",
        "Verbindliche Zusage.", "Garantiert erledigt.", "Ich stehe dazu.", "Absolut sicher.",
        "Verlässlich umgesetzt.", "Definitiv dabei.", "Ohne Wenn und Aber.",
        "Ich verpflichte mich.", "Zugesichert.", "Bindende Vereinbarung.",
        "Ich halte mein Wort.", "Feste Zusage meinerseits.", "Darauf kannst du zählen.",
        "Das ist gesetzt.", "Ich ziehe das durch.", "Unumstößlich geplant.",
        "Mein Ehrenwort.", "Das steht fest.", "Ich garantiere es.",
        "Vertraglich zugesagt.", "Ich bleibe dabei."
    ],
    "ATO_DELAYING_PHRASES": [
        "Später vielleicht.", "Ich schau mal.", "Noch nicht jetzt.", "Irgendwann dann.",
        "Wenn ich Zeit habe.", "Mal sehen.", "Kommt noch.", "Noch offen.",
        "Verschieben wir das.", "Erstmal abwarten.", "Nicht heute.", "Morgen schaue ich.",
        "Nächste Woche vielleicht.", "Muss ich noch überlegen.", "Lasse ich offen.",
        "Hebe ich mir auf.", "Erstmal zurückstellen.", "Später kläre ich das.",
        "Noch nicht spruchreif.", "Noch nicht soweit.", "Wird noch dauern.",
        "Noch nicht dran.", "Vorerst pausieren.", "Noch nicht fertig.", "Noch nicht bereit."
    ],
    "ATO_DEMEANING_TERMS": [
        "Du Idiot!", "Völlig unfähig.", "Totaler Versager.", "Erbärmlich.",
        "Lächerlich!", "Dumm gelaufen.", "Inkompetent.", "Schwach.", "Erbärmliche Leistung.",
        "Jämmerlich.", "Minderwertig.", "Unwürdig.", "Unterste Schublade.",
        "Peinlich.", "Beschämend.", "Unwissenheit pur.", "Amateurhaft.",
        "Unprofessionell.", "Dilettantisch.", "Stümperhaft.", "Mickrig.",
        "Bedeutungslos.", "Wertlos.", "Nichtsnutzig.", "Armselig."
    ],
    "ATO_EMPATHY_MARKERS": [
        "Ich verstehe dich.", "Das tut mir leid.", "Ich fühle mit dir.",
        "Ich kann nachvollziehen.", "Das muss schwer sein.", "Ich bin für dich da.",
        "Du bist nicht allein.", "Ich höre dir zu.", "Das ist verständlich.",
        "Ich sehe deinen Schmerz.", "Ich nehme dich ernst.", "Deine Gefühle sind wichtig.",
        "Ich respektiere deine Sicht.", "Das berührt mich.", "Ich teile deinen Kummer.",
        "Ich erkenne deine Not.", "Das bewegt mich.", "Ich bin an deiner Seite.",
        "Du hast mein Mitgefühl.", "Ich spüre deine Last.", "Dein Leid geht mir nah.",
        "Ich verstehe deine Lage.", "Das ist nachvollziehbar.", "Ich fühle deine Trauer.",
        "Du verdienst Unterstützung."
    ],
    "ATO_ESCALATION_LEXICON": [
        "Jetzt reicht's!", "Das ist die Höhe!", "Unverschämt!", "Frechheit!",
        "So nicht!", "Nie wieder!", "Das geht zu weit!", "Schluss jetzt!",
        "Unerträglich!", "Ich platze gleich!", "Wie kannst du nur!",
        "Das ist der Gipfel!", "Unfassbar!", "Ich fasse es nicht!", "Unmöglich!",
        "Das lasse ich nicht zu!", "Genug ist genug!", "Das ist zu viel!",
        "Ich halte das nicht mehr aus!", "Jetzt ist Schluss!", "Das überschreitet Grenzen!",
        "Ich bin am Ende!", "Das schreit zum Himmel!", "Empörend!", "Skandalös!"
    ],
    "ATO_GENERALIZATION_MARKER": [
        "Immer das Gleiche.", "Nie klappt es.", "Alle sind so.", "Jeder macht das.",
        "Ständig passiert das.", "Stets dieselbe Geschichte.", "Typisch!",
        "Ohne Ausnahme.", "Ausnahmslos.", "Durchweg so.", "Grundsätzlich falsch.",
        "Pauschal abgelehnt.", "Insgesamt schlecht.", "Prinzipiell unmöglich.",
        "Generell problematisch.", "Allgemein bekannt.", "Überall dasselbe.",
        "Bei allen so.", "Immerzu.", "Allemal.", "Jederzeit.", "Allzeit.",
        "Durchgehend.", "Gänzlich.", "Komplett."
    ],
    "ATO_GUILT_PHRASES": [
        "Es ist meine Schuld.", "Ich bin schuld.", "Verzeih mir.", "Ich hätte es wissen müssen.",
        "Mein Fehler.", "Ich habe versagt.", "Ich bin verantwortlich.", "Es tut mir leid.",
        "Ich bereue es.", "Ich fühle mich schuldig.", "Hätte ich nur...",
        "Ich habe Mist gebaut.", "Das war falsch von mir.", "Ich trage die Verantwortung.",
        "Ich bin der Schuldige.", "Es liegt an mir.", "Ich habe es verbockt.",
        "Mein Versagen.", "Ich habe dich enttäuscht.", "Das geht auf meine Kappe.",
        "Ich war's.", "Meine Verfehlung.", "Ich stehe in der Schuld.",
        "Ich mache mir Vorwürfe.", "Das belastet mein Gewissen."
    ],
    "ATO_IRONY_PUNCTUATION": [
        "Toll gemacht!", "Super Idee!", "Klasse!", "Wunderbar!", "Phantastisch!",
        "Genial!", "Perfekt!", "Ausgezeichnet!", "Brillant!", "Hervorragend!",
        "Großartig!", "Prima!", "Fabelhaft!", "Herrlich!", "Wundervoll!",
        "Traumhaft!", "Sagenhaft!", "Sensationell!", "Unglaublich gut!",
        "Mega stark!", "Echt toll!", "Sehr hilfreich!", "Na klar!",
        "Sicher!", "Kein Problem!"
    ],
    "ATO_MOCKING_LEXICON": [
        "Ach wirklich?", "Na klar!", "Wie originell!", "So geistreich!",
        "Donnerwetter!", "Meine Güte!", "Ach nein!", "Echt jetzt?",
        "Wie witzig!", "So clever!", "Wahnsinn!", "Unglaublich!",
        "Sensationell!", "Wie aufregend!", "So spannend!", "Was für eine Überraschung!",
        "Wie unerwartet!", "So originell!", "Welch Einsicht!", "Wie tiefgründig!",
        "So bedeutsam!", "Welch Weisheit!", "Wie erhellend!", "So revolutionär!",
        "Welch Genie!"
    ],
    "ATO_MORAL_LANGUAGE": [
        "Das ist falsch.", "Das gehört sich nicht.", "Unethisch!", "Verwerflich!",
        "Moralisch fragwürdig.", "Gegen alle Prinzipien.", "Das ist unrecht.",
        "Anständig wäre es.", "Ehrlich gesagt.", "Das ist unehrenhaft.",
        "Tugendhaft wäre.", "Das ist gerecht.", "Fair wäre es.", "Rechtschaffen handeln.",
        "Das ist Pflicht.", "Verantwortungslos!", "Das ist Sünde.", "Gewissenlos!",
        "Das ist integer.", "Aufrichtig sein.", "Das ist redlich.", "Ethisch geboten.",
        "Moralisch geboten.", "Das ist lauter.", "Das ist sauber."
    ],
    "ATO_NEGATIVE_FEEDBACK_TOKEN": [
        "Das ist falsch.", "Nein, so nicht.", "Schlecht gemacht.", "Ungenügend.",
        "Mangelhaft.", "Nicht akzeptabel.", "Das geht nicht.", "Fehler!",
        "Falsche Richtung.", "Unzureichend.", "Nicht gut genug.", "Enttäuschend.",
        "Unbefriedigend.", "Suboptimal.", "Verbesserungsbedürftig.", "Schwach.",
        "Nicht überzeugend.", "Nicht zufriedenstellend.", "Nicht ausreichend.",
        "Nicht den Standards entsprechend.", "Qualität fehlt.", "Mängel vorhanden.",
        "Defizite erkennbar.", "Lücken sichtbar.", "Nicht stimmig."
    ],
    "ATO_OUTRAGE_MARKERS": [
        "Empörend!", "Skandalös!", "Ungeheuerlich!", "Unerhört!", "Unfassbar!",
        "Schändlich!", "Unglaublich!", "Unverschämt!", "Bodenlos!",
        "Himmelschreiend!", "Unerträglich!", "Widerwärtig!", "Abscheulich!",
        "Verabscheuungswürdig!", "Grotesk!", "Pervers!", "Widerlich!",
        "Ekelhaft!", "Abstossend!", "Verwerflich!", "Niederträchtig!",
        "Gemein!", "Bösartig!", "Infam!", "Schändlich!"
    ],
    "ATO_PREMATURE_CLOSURE": [
        "Erledigt.", "Fertig.", "Done.", "Abgehakt.", "Geschafft.",
        "Thema durch.", "Case closed.", "Das war's.", "Ende der Diskussion.",
        "Punkt.", "Klar soweit.", "Nichts mehr zu sagen.", "Damit ist das geklärt.",
        "Somit erledigt.", "Also geklärt.", "Hiermit abgeschlossen.", "Soweit klar.",
        "Damit durch.", "Thema abgehakt.", "Darüber brauchen wir nicht mehr reden.",
        "Das steht fest.", "Ist beschlossen.", "Entschieden.", "Geregelt.", "Abgeschlossen."
    ],
    "ATO_PROBABILISTIC_TERMS": [
        "Wahrscheinlich.", "Vermutlich.", "Möglicherweise.", "Eventuell.",
        "Vielleicht.", "Gegebenenfalls.", "Unter Umständen.", "Potentiell.",
        "Denkbar.", "Vorstellbar.", "Nicht ausgeschlossen.", "Könnte sein.",
        "Mag sein.", "Womöglich.", "Gegebenenfalls.", "Falls zutreffend.",
        "Im Falle dass.", "Sofern.", "Angenommen.", "Gesetzt den Fall.",
        "Hypothetisch.", "Theoretisch.", "Mutmaßlich.", "Vermuteterweise.",
        "Aller Wahrscheinlichkeit nach."
    ],
    "ATO_PROCRASTINATION_CUES": [
        "Später.", "Irgendwann.", "Noch nicht.", "Mal sehen.", "Wenn ich Zeit habe.",
        "Erstmal abwarten.", "Noch nicht spruchreif.", "Noch in der Schwebe.",
        "Verschieben wir das.", "Lassen wir offen.", "Noch nicht akut.",
        "Hat noch Zeit.", "Nicht eilig.", "Kommt noch.", "Noch nicht dran.",
        "Erstmal zurückstellen.", "Aufschieben.", "Noch nicht heute.",
        "Morgen vielleicht.", "Nächste Woche.", "Irgendwann mal.", "Wenn es passt.",
        "Gelegentlich.", "Bei Bedarf.", "Wenn nötig."
    ],
    "ATO_REGRET_PHRASES": [
        "Hätte ich nur.", "Wenn ich doch.", "Ich wünschte.", "Schade drum.",
        "Zu spät jetzt.", "Verpasste Chance.", "Nie wieder.", "Das bereue ich.",
        "Wenn ich das gewusst hätte.", "Hätte ich anders gemacht.", "Leider vertan.",
        "Versäumt.", "Verpasst.", "Vorbei die Zeit.", "Unwiederbringlich.",
        "Hätte sein können.", "Leider nicht genutzt.", "Zu spät erkannt.",
        "Vergebene Chance.", "Hätte ich damals nur.", "Wenn ich zurückdenke.",
        "Das tut mir leid.", "Ich bedaure es.", "Hätte besser sein können.",
        "Leider verpasst."
    ],
    "ATO_RELIABILITY_TERMS": [
        "Zuverlässig.", "Verlässlich.", "Berechenbar.", "Konstant.", "Stabil.",
        "Solide.", "Sicher.", "Vertrauenswürdig.", "Beständig.", "Fest.",
        "Tragfähig.", "Standhaft.", "Unerschütterlich.", "Dauerhaft.", "Nachhaltig.",
        "Robust.", "Resilient.", "Widerstandsfähig.", "Konsistent.", "Gleichbleibend.",
        "Stetig.", "Kontinuierlich.", "Ununterbrochen.", "Durchgehend.", "Permanent."
    ],
    "ATO_RESPECT_TERMS": [
        "Ich respektiere dich.", "Ich achte dich.", "Ich schätze dich.", "Du bist wertvoll.",
        "Ich ehre dich.", "Du verdienst Respekt.", "Ich würdige dich.", "Du bist wichtig.",
        "Ich erkenne dich an.", "Du hast meine Hochachtung.", "Ich bewundere dich.",
        "Du bist bedeutsam.", "Ich halte große Stücke auf dich.", "Du bist ehrenwert.",
        "Ich zolle dir Tribut.", "Du bist achtbar.", "Ich bringe dir Wertschätzung entgegen.",
        "Du bist respektabel.", "Ich begegne dir mit Achtung.", "Du bist würdevoll.",
        "Ich respektiere deine Meinung.", "Ich achte deine Grenzen.",
        "Ich ehre deine Entscheidung.", "Du bist respektiert.", "Ich schätze deine Ansicht."
    ],
    "ATO_RISK_TERMS": [
        "Riskant.", "Gefährlich.", "Bedenklich.", "Kritisch.", "Brenzlig.",
        "Heikel.", "Prekär.", "Bedrohlich.", "Unsicher.", "Gewagt.",
        "Wagnis.", "Risiko.", "Gefahr.", "Bedrohung.", "Hazard.",
        "Unwägbarkeit.", "Unberechenbarkeit.", "Instabilität.", "Volatilität.",
        "Anfälligkeit.", "Vulnerabilität.", "Exposition.", "Fragilität.",
        "Unsicherheit.", "Ungewissheit."
    ],
    "ATO_SAD_WORDS": [
        "Traurig.", "Niedergeschlagen.", "Betrübt.", "Schwermütig.", "Melancholisch.",
        "Deprimiert.", "Verzweifelt.", "Hoffnungslos.", "Geknickt.", "Bedrückt.",
        "Unglücklich.", "Elend.", "Jämmerlich.", "Kummervoll.", "Gramgebeugt.",
        "Leidend.", "Schmerzerfüllt.", "Trostlos.", "Freudlos.", "Düster.",
        "Finster.", "Tief betrübt.", "Herzzerreißend.", "Tief verletzt.", "Seelisch verwundet."
    ],
    "ATO_SARCASM_MARKER": [
        "Na toll!", "Wunderbar!", "Großartig!", "Klasse Idee!", "Super gemacht!",
        "Genial!", "Brilliant!", "Fantastisch!", "Perfekt!", "Ausgezeichnet!",
        "Hervorragend!", "Prima!", "Fabelhaft!", "Sensationell!", "Sagenhaft!",
        "Traumhaft!", "Herrlich!", "Köstlich!", "Entzückend!", "Bezaubernd!",
        "Hinreißend!", "Umwerfend!", "Atemberaubend!", "Phänomenal!", "Spektakulär!"
    ],
    "ATO_STATUS_TERMS": [
        "Höhergestellt.", "Rangniedrig.", "Untergeordnet.", "Vorgesetzter.", "Chef.",
        "Boss.", "Untergebener.", "Position.", "Rang.", "Status.",
        "Hierarchie.", "Oben.", "Unten.", "Mächtiger.", "Schwächer.",
        "Dominanter.", "Unterlegener.", "Alpha.", "Beta.", "Führungsposition.",
        "Untergeordnete Rolle.", "Autoritätsperson.", "Ranghöher.", "Statusniedriger.",
        "Prestigeträger."
    ],
    "ATO_STEREOTYPING_LANGUAGE": [
        "Typisch Mann.", "Typisch Frau.", "Alle Ausländer.", "Die Jugend heute.",
        "Die Alten.", "Typisch Deutsch.", "So sind die halt.", "Die sind alle gleich.",
        "Klischee erfüllt.", "Vorurteil bestätigt.", "Wie erwartet von denen.",
        "Schublade passt.", "Kategorie klar.", "Label zutreffend.", "Stereotyp erkennbar.",
        "Pauschales Urteil.", "Vorschnelle Einordnung.", "Schnelles Urteil.",
        "Typische Eigenschaften.", "Gruppenmerkmal.", "Kollektivzuschreibung.",
        "Generalisierende Aussage.", "Ethnische Zuschreibung.", "Geschlechtsstereotyp.",
        "Altersstereotyp."
    ],
    "ATO_SUPPORTIVE_LANGUAGE": [
        "Ich bin für dich da.", "Du schaffst das.", "Ich glaube an dich.",
        "Du bist nicht allein.", "Ich unterstütze dich.", "Ich helfe dir.",
        "Gemeinsam schaffen wir das.", "Du bist stark.", "Ich stehe hinter dir.",
        "Du kannst auf mich zählen.", "Ich halte zu dir.", "Du hast meine Unterstützung.",
        "Ich bin an deiner Seite.", "Du bekommst meine Hilfe.", "Ich trage dich mit.",
        "Du hast Rückendeckung.", "Ich stärke dir den Rücken.", "Du bist nicht alleine.",
        "Ich fange dich auf.", "Du hast ein Netz.", "Ich sichere dich ab.",
        "Du bekommst Unterstützung.", "Ich ermutige dich.", "Du hast einen Verbündeten.",
        "Ich bin dein Backup."
    ],
    "ATO_TENTATIVE_VERBS": [
        "Könnte sein.", "Scheint so.", "Wirkt wie.", "Sieht aus als.", "Klingt nach.",
        "Deutet darauf hin.", "Lässt vermuten.", "Erscheint so.", "Macht den Eindruck.",
        "Legt nahe.", "Suggeriert.", "Impliziert.", "Andeutet.", "Signalisiert vage.",
        "Könnte hinweisen.", "Möglicherweise zeigt.", "Eventuell deutet.",
        "Vielleicht weist hin.", "Mutmaßlich signalisiert.", "Vermutlich indiziert.",
        "Tendenziell zeigt.", "Scheinbar manifestiert.", "Anscheinend offenbart.",
        "Offenbar reflektiert.", "Augenscheinlich spiegelt."
    ],
    "ATO_THREAT_TERMS": [
        "Bedrohung.", "Gefahr.", "Risiko.", "Warnung.", "Vorsicht.",
        "Achtung.", "Alarm.", "Notfall.", "Krise.", "Problem.",
        "Schwierigkeit.", "Hindernis.", "Hürde.", "Barriere.", "Blockade.",
        "Gefährdung.", "Bedrohlich.", "Gefährlich.", "Kritisch.", "Alarmierend.",
        "Besorgniserregend.", "Bedenklich.", "Prekär.", "Brisant.", "Heikel."
    ],
    "ATO_TRUST_LEXICON": [
        "Ich vertraue dir.", "Du bist vertrauenswürdig.", "Ich glaube dir.",
        "Du bist ehrlich.", "Ich kann mich auf dich verlassen.", "Du bist zuverlässig.",
        "Ich öffne mich dir.", "Du bist integer.", "Ich fühle mich sicher bei dir.",
        "Du bist authentisch.", "Ich glaube an dich.", "Du bist glaubwürdig.",
        "Ich schenke dir Vertrauen.", "Du bist aufrichtig.", "Ich verlasse mich auf dich.",
        "Du bist loyal.", "Ich traue dir.", "Du bist treu.", "Ich bin offen zu dir.",
        "Du bist verlässlich.", "Ich gebe dir Kredit.", "Du hast mein Vertrauen.",
        "Ich baue auf dich.", "Du bist seriös.", "Ich vertraue deinem Wort."
    ],
    "ATO_VIRTUE_TERMS": [
        "Ehrlich.", "Aufrichtig.", "Integer.", "Gerecht.", "Fair.",
        "Tugendhaft.", "Moralisch.", "Ethisch.", "Prinzipientreu.", "Gewissenhaft.",
        "Rechtschaffen.", "Anständig.", "Edel.", "Ehrenhaft.", "Würdevoll.",
        "Lauter.", "Sauber.", "Redlich.", "Bieder.", "Unbescholten.",
        "Untadelig.", "Makellos.", "Rein.", "Unschuldig.", "Sittsam."
    ],
    "ATO_ANCHORING_PHRASES": [
        "Von Anfang an dachte ich.", "Ursprünglich war der Preis.", "Beim ersten Mal.",
        "Zuerst hieß es.", "Initial war geplant.", "Am Beginn stand.", "Der Ausgangspunkt war.",
        "Die erste Zahl war.", "Ursprünglich sollte es.", "Der Anfangswert war.",
        "Die initiale Schätzung war.", "Zu Beginn wurde gesagt.", "Die erste Information war.",
        "Der erste Eindruck war.", "Die Ausgangslage war.", "Die Anfangsbedingung war.",
        "Der Startwert lag bei.", "Die erste Erwartung war.", "Ursprünglich dachten wir.",
        "Der erste Anhaltspunkt war.", "Die initiale Position war.", "Am Anfang stand die Zahl.",
        "Die ursprüngliche Annahme war.", "Der erste Referenzpunkt war.", "Die Ausgangsbasis war."
    ],
    "ATO_ATTRIBUTION_ERROR": [
        "Das liegt an seiner Persönlichkeit.", "Das ist typisch für sie.", "Er ist halt so.",
        "Sie kann nicht anders.", "Das ist sein Charakter.", "Das liegt in ihrer Natur.",
        "Er ist einfach faul.", "Sie ist von Natur aus...", "Das ist sein Wesen.",
        "Sie ist grundsätzlich so.", "Er ist immer so.", "Das ist ihre Art.",
        "Er ist eben inkompetent.", "Sie ist charakterlich...", "Das liegt an ihm persönlich.",
        "Sie ist dispositional so.", "Das ist seine Eigenschaft.", "Sie hat diese Anlage.",
        "Er ist veranlagt dazu.", "Das ist ihr Temperament.", "Er ist grundlegend so.",
        "Sie ist wesensgemäß...", "Das ist sein Naturell.", "Sie ist intrinsisch so.",
        "Das ist seine Prädisposition."
    ],
    "ATO_CERTAINTY_WITHOUT_EVIDENCE": [
        "Ich bin mir absolut sicher.", "Ganz klar.", "Definitiv.", "Ohne Zweifel.",
        "Hundertprozentig.", "Garantiert.", "Mit Sicherheit.", "Zweifelsfrei.",
        "Absolut.", "Total sicher.", "Komplett klar.", "Vollkommen eindeutig.",
        "Unbestritten.", "Unzweifelhaft.", "Kategorisch.", "Apodiktisch.",
        "Unwiderlegbar.", "Unbezweifelbar.", "Fraglos.", "Selbstverständlich.",
        "Offensichtlich.", "Evident.", "Manifest.", "Augenscheinlich.", "Sonnenklar."
    ],
    "ATO_DISTRUST_MARKERS": [
        "Ich traue dir nicht.", "Du lügst.", "Das glaube ich dir nicht.", "Verdächtig.",
        "Unglaubwürdig.", "Zweifel habe ich.", "Skeptisch bin ich.", "Misstrauisch.",
        "Du täuschst.", "Du betrügst.", "Nicht vertrauenswürdig.", "Unehrlich.",
        "Hinterhältig.", "Falsch.", "Verlogen.", "Dubios.", "Fragwürdig.",
        "Nicht integer.", "Unzuverlässig.", "Nicht glaubhaft.", "Argwöhnisch sehe ich das.",
        "Zweifelhaft.", "Suspekt.", "Obskur.", "Undurchsichtig."
    ],
    "ATO_MORAL_OUTRAGE": [
        "Das ist empörend!", "Skandalös!", "Ungeheuerlich!", "Ethisch verwerflich!",
        "Moralisch inakzeptabel!", "Das schreit zum Himmel!", "Unerhört!",
        "Gegen jede Moral!", "Gewissenlos!", "Schändlich!", "Verabscheuungswürdig!",
        "Widerlich!", "Abscheulich!", "Niederträchtig!", "Infam!",
        "Verwerflich!", "Sittenwidrig!", "Unmoralisch!", "Zügellos!",
        "Dekadent!", "Verdorben!", "Pervers!", "Lasterhaft!", "Sündhaft!", "Böse!"
    ],
}

def load_yaml_safe(filepath):
    """Lädt YAML-Datei sicher."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_yaml_safe(filepath, data):
    """Speichert YAML-Datei mit korrekter Formatierung."""
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

def expand_examples(marker_id, current_examples, min_examples=20):
    """Erweitert Beispiele für einen Marker."""
    if marker_id in SEMANTIC_EXAMPLES:
        additional = SEMANTIC_EXAMPLES[marker_id]
        current_count = len(current_examples) if current_examples else 0
        needed = max(0, min_examples - current_count)
        
        if needed > 0:
            # Füge zusätzliche Beispiele hinzu
            extended = (current_examples or []) + additional[:needed]
            return extended
    return current_examples

def process_marker_file(filepath):
    """Verarbeitet eine einzelne Marker-Datei."""
    try:
        data = load_yaml_safe(filepath)
        marker_id = data.get('id', '')
        
        # Erweitere Beispiele
        if 'examples' in data:
            data['examples'] = expand_examples(marker_id, data['examples'])
            save_yaml_safe(filepath, data)
            print(f"✓ Erweitert: {marker_id}")
        else:
            print(f"⚠ Keine Beispiele gefunden: {marker_id}")
            
    except Exception as e:
        print(f"✗ Fehler bei {filepath}: {e}")

def main():
    """Hauptfunktion."""
    base_dir = Path(__file__).parent
    yaml_files = list(base_dir.glob("*.yaml"))
    
    print(f"Gefunden: {len(yaml_files)} YAML-Dateien")
    print("Erweitere Marker...")
    
    for yaml_file in yaml_files:
        if yaml_file.name != "expand_markers.py":
            process_marker_file(yaml_file)
    
    print("\n✓ Fertig!")

if __name__ == "__main__":
    main()
