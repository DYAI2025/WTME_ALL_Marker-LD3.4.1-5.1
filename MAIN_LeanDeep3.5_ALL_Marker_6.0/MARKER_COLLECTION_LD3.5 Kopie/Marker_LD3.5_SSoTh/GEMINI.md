# GEMINI.md - LeanDeep 3.5

## Directory Overview

This directory contains the "LeanDeep 3.5" project, a sophisticated system for analyzing text and voice for psychological and emotional markers. The project is highly structured and data-driven, using a custom-defined set of "markers" to identify complex patterns in communication. The ultimate goal of the project is to provide a tool for analyzing and visualizing communication patterns based on the "Spiral Dynamics" model.

The project is not a typical software application with a user-facing interface, but rather a system for defining and detecting patterns. However, it does include a React component for visualizing the analysis results.

## Key Files

*   `LeanDeep_3.5.md`: The Single Source of Truth (SSoT) documentation for the project. It provides a detailed explanation of the project's architecture, concepts, and marker definitions.
*   `ATO_atomic/`, `SEM_semantic/`, `CLU_cluster/`, `MEMA_meta/`: These directories contain the core of the project: the marker definitions in YAML format. The markers are organized into a four-layer architecture, from atomic tokens (ATO) to complex meta-analyses (MEMA).
*   `markers_loader.py`: A Python script for loading, validating, and processing the marker definitions from the YAML files. It includes logic for evaluating activation rules and managing the state of "intuition" clusters.
*   `spiral-persona-detection.tsx`: A React component written in TypeScript that provides a user interface for visualizing the results of the "Spiral Persona Detection Engine". It uses the `recharts` library to create various charts and `papaparse` for parsing CSV data.
*   `CARL_engine.json`, `core_bundle_manifest.json`: Configuration files for the project.
*   `EXPLAINABILITY_TEMPLATE.yaml`: A template for explaining the system's output.
*   `system_prompt.txt`: A text file containing a system prompt.

## Usage

The project is designed to be used as a library or a backend service for analyzing text and voice data. The `markers_loader.py` script can be used to load the marker definitions and apply them to a given conversation. The output of the analysis can then be visualized using the `spiral-persona-detection.tsx` component.

### Running the analysis

To run the analysis, you would typically perform the following steps:

1.  **Load the markers:** Use the `load_all_markers` function in `markers_loader.py` to load the marker definitions from the YAML files.
2.  **Validate the markers:** Use the `validate_spec` function to ensure that the marker definitions are valid.
3.  **Process the conversation:** For each message in the conversation, identify the triggered markers.
4.  **Evaluate activation rules:** Use the `evaluate_activation` function to determine which of the higher-level markers (SEM, CLU, MEMA) are activated.
5.  **Generate output:** The output of the analysis would typically be a list of triggered markers for each message, which can then be used to generate a `marker_counts.csv` file for visualization.

### Visualizing the results

The `spiral-persona-detection.tsx` component can be used to visualize the results of the analysis. To use the component, you would need to:

1.  **Generate a `marker_counts.csv` file:** This file should contain the counts of each "Spiral Dynamics" color for each message in the conversation.
2.  **Integrate the component into a React application:** The component can be imported and used like any other React component.
3.  **Load the data:** The component will automatically load the data from the `marker_counts.csv` file and display the visualizations.

## Development Conventions

The project follows a set of well-defined development conventions:

*   **Marker definitions:** All markers are defined in YAML files and follow a specific schema.
*   **Validation:** The `markers_loader.py` script includes a comprehensive validation function to ensure the quality of the marker definitions.
*   **Modularity:** The markers are organized into different "packs" for specific domains, which can be enabled or disabled as needed.
*   **Testing:** The project includes a `demo` function in `markers_loader.py` that can be used for testing the marker loading and activation logic.
