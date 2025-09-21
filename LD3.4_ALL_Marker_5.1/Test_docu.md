## Marker Scan & Test – Inconsistency & Plausibility

### Zusammenfassung
- Gesamtdateien: 48
- ATO geprüft: 9
- SEM geprüft: 6
- CLU geprüft: 4

### Fehler / Inkonsistenzen
- /Users/benjaminpoersch/Projekte/XEXPERIMENTE/WTME_LD3.4_Marker_5.1/LD3.4_ALL_Marker_5.1/ALL_Marker_5.1/CLU_cluster/CLU_INTUITION_COMMITMENT.yaml::CLU_INTUITION_COMMITMENT: composed_of referenziert unbekannt: ['SEM_CLEAR_COMMITMENT', 'SEM_DELAYING_MOVE', 'SEM_PROCRASTINATION_BEHAVIOR']

### ATO Ergebnis (Regex‑Abdeckung & Negation)
- ATO_ACTIVITY_VERB: Beispiele 30/33, Negationen blockiert 0/1
- ATO_CONDITION_CUE: Beispiele 30/30, Negationen blockiert 0/1
- ATO_JOY_EXPRESSION: Beispiele 33/35, Negationen blockiert 1/3
- ATO_NONVERBAL_JOY_VERB: Beispiele 17/30, Negationen blockiert 0/1
- ATO_POSITIVE_OUTLOOK_CUE: Beispiele 16/34, Negationen blockiert 0/1
- ATO_POSITIVE_PREFERENCE: Beispiele 25/33, Negationen blockiert 1/2
- ATO_REWARD_RESPONSE: Beispiele 20/34, Negationen blockiert 0/2
- ATO_SATISFACTION_STATE: Beispiele 16/34, Negationen blockiert 0/2
- ATO_SPONTANEITY_CUE: Beispiele 27/30, Negationen blockiert 0/1

### SEM Ergebnis (approx. ATO‑Treffer pro Beispiel)
- SEM_ACTIVE_ENJOYMENT: 10/12 Beispiele erfüllen Komposition (benötigt 2)
  - Schwach: hits=1 :: Ich **bastle gern** an Elektronikprojekten.
  - Schwach: hits=1 :: Ich **mag** es, morgens **spazieren zu gehen**.
- SEM_EXPRESSED_SATISFACTION: 11/11 Beispiele erfüllen Komposition (benötigt 1)
- SEM_POSITIVE_EMOTION_REGULATION: 2/10 Beispiele erfüllen Komposition (benötigt 1)
  - Schwach: hits=0 :: Ich konnte **positivere Gefühle** gezielt **herbeiführen**.
  - Schwach: hits=0 :: Ich **erzeuge** mir **gute Stimmung**.
  - Schwach: hits=0 :: Ich **kultiviere** **Zuversicht** im Alltag.
- SEM_POSITIVE_OUTLOOK: 3/11 Beispiele erfüllen Komposition (benötigt 1)
  - Schwach: hits=0 :: Ich **blicke positiv** in die Zukunft.
  - Schwach: hits=0 :: Ich **glaube** an einen guten Ausgang.
  - Schwach: hits=0 :: Ich **sehe** viele Möglichkeiten.
- SEM_REPORTED_NONVERBAL_JOY: 6/10 Beispiele erfüllen Komposition (benötigt 1)
  - Schwach: hits=0 :: Wir **lachen** miteinander und werden ruhiger.
  - Schwach: hits=0 :: Sie **lächeln** einander freundlich an.
  - Schwach: hits=0 :: Alle **lachen** laut vor Glück.
- SEM_STATE_OF_HAPPINESS: 11/11 Beispiele erfüllen Komposition (benötigt 2)

### Familien‑Hint‑Machbarkeit
- positive_affect → Hint HINT_POSITIVE_AFFECT: machbar mit 3 ATOs ohne ANY‑1‑SEM: NEIN
  - ANY‑1‑SEMs: SEM_EXPRESSED_SATISFACTION, SEM_POSITIVE_OUTLOOK, SEM_REPORTED_NONVERBAL_JOY, SEM_POSITIVE_EMOTION_REGULATION
  - ATOs ohne ANY‑1‑Bindung: ATO_JOY_EXPRESSION, ATO_POSITIVE_PREFERENCE
- affect_regulation → Hint HINT_AFFECT_REGULATION: machbar mit 3 ATOs ohne ANY‑1‑SEM: NEIN
  - ANY‑1‑SEMs: SEM_SELF_SUPPORT_STATEMENT
  - ATOs ohne ANY‑1‑Bindung: ATO_EMOTIONAL_INTENSITY, ATO_ACCEPTANCE_PHRASE

### Komplexe Testfälle (generiert)
- Erwartet: SEM_ACTIVE_ENJOYMENT :: SEM Komposition (>=2) kombiniert
  Text: Ich **mag** Rätsel Ich **gehe** gern laufen.
- Erwartet: SEM_STATE_OF_HAPPINESS :: SEM Komposition (>=2) kombiniert
  Text: Ich empfinde **Freude** **Wenn** ich mich geborgen fühle .

### Live-Beispielfunde (Reddit)

- Quelle: data/raw/reddit/ (letzter Crawl)
- Umfang: 500 Posts (new)
- Felder: id, subreddit, title, selftext, created_utc, permalink, score, num_comments, over_18

Beispielzeilen (gekürzt, JSONL):

```json
{"id":"...","subreddit":"relationships","title":"...","selftext":"...","permalink":"https://reddit.com/r/relationships/..."}
{"id":"...","subreddit":"TrueOffMyChest","title":"...","selftext":"...","permalink":"https://reddit.com/r/TrueOffMyChest/..."}
```

Nutzungsvorschlag:
- Sampling nach Subreddits und Heuristiken (Länge, Emo-Wörter)
- Manuelle Annotation von 50–100 Sätzen gegen ATO/SEM
- Vergleich mit Engine-Ausgaben (scoreSentence) für Präzision/Recall grob schätzen
