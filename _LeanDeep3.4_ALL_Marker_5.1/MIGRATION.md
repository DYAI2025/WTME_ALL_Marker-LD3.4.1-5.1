# LeanDeep 3.4 Migration & Marker-Übersicht

## Ziel
Diese Notiz fasst die neu angelegten und migrierten Marker zusammen und zeigt die Triggerkette von ATO → SEM → CLU → MEMA samt Aktivationsfenstern.

## Neue/aktualisierte ATOs (Auszug)
- ATO_QUESTION, ATO_QUESTIONING, ATO_DEEPER_QUESTIONING, ATO_CONFIRM, ATO_NEGATION
- ATO_SUBJECT_CLOSED, ATO_TOPIC_RAISED, ATO_PACING, ATO_ACKNOWLEDGE, ATO_SOVEREIGNTY_OVER_SUBJECT
- ATO_STYLE_REFERENCE, ATO_SHARED_CONTEXT
- ATO_GRATITUDE, ATO_SHAME, ATO_STRESS
- ATO_VICTIM_LANGUAGE, ATO_PITY_APPEAL, ATO_LEARNED_HELPLESSNESS, ATO_SELF_HANDICAPPING
- ATO_PROBLEM_SOLVING (Empowerment/Agency)
- ATO_BLAME_SHIFT, ATO_GUILT_TRIP (LD3.4)

Alle mit schema: "LeanDeep", version: "3.4" und ≥10 Beispielen (wo ergänzt).

## Neue/aktualisierte SEMs
- SEM_CONTEXT_SWITCH
  - composed_of: ATO_STYLE_REFERENCE + ATO_SHARED_CONTEXT
  - activation: BOTH IN 1 message
- SEM_VALIDATION
  - any_of: ATO_SUPPORTIVE_LANGUAGE | ATO_SUPPORT_MESSAGE | ATO_ACKNOWLEDGE
  - activation: AT_LEAST 2 IN 2 (window 2)
- SEM_GET_SUBJECT_CONTROL
  - any_of: ATO_SOVEREIGNTY_OVER_SUBJECT | ATO_SUBJECT_CLOSED | ATO_TOPIC_RAISED | ATO_QUESTIONING | ATO_DEEPER_QUESTIONING; optional: ATO_PACING, ATO_ACKNOWLEDGE
  - activation: AT_LEAST 3 IN 4 (window 4)
- SEM_PLEASANT_PULS
  - required: ATO_PLACEHOLDER ≥2 IN 10, plus (CONFIRM/ACKNOWLEDGE ≥4 in 10 oder beide ≥2 in 10), exclude unrest/escalation/drift, min_dialog_messages: 10
- SEM_DETECT_HAPPINESS
  - any_of: ATO_JOY | ATO_POSITIVE_RESONANCE | ATO_SUPPORTIVE_LANGUAGE | ATO_GRATITUDE
  - activation: AT_LEAST 14 IN 10 (window 10)
- SEM_DEESCALATION
  - any_of: ATO_DEESCALATION_PHRASE | ATO_REPAIR_REQUEST | ATO_APOLOGY | ATO_ACKNOWLEDGE | ATO_CONFIRM | SEM_VALIDATION
  - activation: AT_LEAST 2 IN 3 (window 3), exclude escalation/outrage
- SEM_REPAIR_SEQUENCE
  - sequence_any: APOLOGY → ACKNOWLEDGE → CONFIRM
  - activation: SEQUENCE IN 3 (window 3)
- SEM_SELF_VICTIMIZATION
  - any_of: ATO_VICTIM_LANGUAGE | ATO_PITY_APPEAL | ATO_LEARNED_HELPLESSNESS | ATO_SELF_HANDICAPPING | ATO_BLAME_SHIFT
  - activation: AT_LEAST 2 IN 3 (window 3)
- SEM_CONFLICT_ESCALATION
  - any_of: DEFENSIVENESS | BLAME_SHIFT | SARCASM | OUTRAGE_MARKERS | CRITICISM_ATTACK_MARKER
  - activation: AT_LEAST 3 IN 4 (window 4)
- SEM_GOTTMAN_CONFLICT_ESCALATION
  - weighted_any_of: CRITICISM(0.4) | CONTEMPT(0.5) | DEFENSIVENESS(0.3) | STONEWALLING(0.4)
  - activation: WEIGHTED_OR ≥ 0.8 (window 6)

## CLU (Auszug)
- CLU_PREEMPTIVE_VICTIMIZATION (LD3.4): präventive Opferpositionierung
  - activation: ANY 1 IN 10 (window 10)

## MEMA
- MEMA_SELF_VICTIMIZATION_CYCLE (LD3.4)
  - required_any: SEM_SELF_VICTIMIZATION | CLU_PREEMPTIVE_VICTIMIZATION
  - supportive: SEM_EMOTIONAL_OVERWHELM | SEM_VALIDATION_SEEKING | CLU_INDIRECT_CONFLICT_AVOIDANCE
  - absence_sets (EMPOWERMENT_SIGNALS): ATO_SET_BOUNDARY | ATO_PROBLEM_SOLVING | SEM_SYSTEMS_THINKING
  - window: 30, gating: min_hits_required 3, require_dialog: true

## Hinweise
- Alle neuen Marker folgen LeanDeep 3.4 und wurden mit ≥10 Beispielen versehen (wo relevant).
- Aktivationsfenster bewusst kurz für Dichte (außer MEMA/PLEASANT_PULS für Stabilitätserkennung).
- Exclusions sichern gegen False Positives in Ruhephasen.
