# QWEN.md - Project Context for Atomic Markers

## Directory Overview

This directory contains a collection of atomic linguistic markers in YAML format, primarily focused on identifying specific language patterns and semantic cues in text. These markers appear to be used for detecting various linguistic phenomena, particularly those related to AI safety, behavioral analysis, and semantic understanding.

## Project Purpose

The "atomics" directory houses a set of atomic markers (ATO) that serve as pattern recognition tools for specific linguistic concepts. These markers are designed to detect and categorize certain language patterns that may indicate specific cognitive or behavioral traits in text, with particular emphasis on AI safety considerations such as control mechanisms, toxic language, fictional scenarios, and potential risk indicators.

## Key Files

The directory contains the following YAML files:

1. **ATO_CONTROL_MARKERS.yaml** - Detects language related to execution, protocols, and control mechanisms
2. **ATO_FICTION_TOKENS.yaml** - Identifies fictional/scenario-based language patterns
3. **ATO_POWER_LANGUAGE.yaml** - (Not examined in detail, likely related to power dynamics in language)
4. **ATO_SARCASM_MARKERS.yaml** - Detects sarcastic and ironic language patterns
5. **ATO_SPIRAL_TERMS.yaml** - Identifies recursive or cyclical thinking patterns
6. **ATO_TOXIC_TOKENS.yaml** - Recognizes potentially harmful or toxic language
7. **ATO_UNDERSTATEMENT.yaml** - Detects language that minimizes or downplays risks

## File Structure

Each YAML file follows a consistent structure:

- **id**: Unique identifier for the marker set
- **version**: Version identifier (consistent as "3.4" across files)
- **frame**: Contains semantic information including:
  - **signal**: The linguistic signals being detected
  - **concept**: Description of the linguistic concept
  - **pragmatics**: Pragmatic function of the language pattern
  - **narrative**: Narrative context (consistently "evidence")
- **activation**: Regex rule for detecting the pattern
- **examples**: Sample text examples demonstrating the pattern

## Usage Context

Based on the content and naming conventions, these markers appear to be part of a larger AI safety framework (possibly related to "LeanDeep" as indicated in the path). They are likely used for:

- Analyzing AI model outputs for specific behavioral patterns
- Detecting potential safety concerns in language models
- Identifying linguistic markers that might indicate undesirable behaviors like circumventing safety measures
- Research into AI alignment and behavioral analysis

## Development Conventions

- YAML format is used consistently across all marker files
- Regular expressions use case-insensitive matching with word boundaries
- Each marker focuses on a specific semantic category
- Examples are provided to illustrate typical usage patterns
- Version consistency (3.4) suggests coordinated development

## Notable Patterns

- Many markers target language that might be used to circumvent safety measures or encourage risky behavior
- Terms like "bypass", "override", "execute", "protocol" appear frequently across different marker sets
- The focus on "fictional scenarios" and "roleplay" suggests detection of attempts to circumvent safety through hypothetical framing
- Sarcasm and understatement markers indicate attention to nuanced language patterns that might mask dangerous instructions