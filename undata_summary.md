# UN Data Import Strategy & Implementation Summary

## Overview
This document summarizes the strategy discussed in the May 20th transcript and its technical realization within the `undata` directory. The primary objective is to transition from an AI-agent-dependent mapping process to a **deterministic Python-based ETL pipeline**.

## Strategic Intent
The goal is to automate the mapping of UN dataset headers (e.g., `SERIES`, `AGE`, `SEX`) to Data Commons property-value (PV) pairs. By using a deterministic script, the team ensures:
- **Scalability**: Processing 57+ datasets consistently.
- **Reliability**: Eliminating repetitive errors often introduced by LLM agents.
- **Transparency**: Every mapping is traceable back to a reviewed "Concept Library" (CL).

---

## Core Pipeline (The `undata` Folder)

The implementation consists of two main Python scripts and a set of reviewed codelists that orchestrate the transformation.

### 1. Metadata Generation (`generate_metadata.py`)
This script acts as the "discovery" phase of the pipeline.
- **Logic**: It scans raw CSV files in `undata/data/` and identifies columns that have corresponding reviewed codelists in `undata/cl_reviewed/`.
- **Output**: For each dataset, it generates a `metadata.csv` (e.g., `undata/metadata/DESA-GENDER_..._metadata.csv`).
- **Transcript Reference**: Matches the requirement to create a "metadata CSV file for each data file, containing unique values for columns like geography, age, and sex."

### 2. PV Mapping Logic (`generate_pvmap.py`)
This script implements the "transformation" phase, converting metadata into final importer-ready PV maps.
- **Deterministic Mappings**:
    - **Geography**: Maps to `observationAbout` (normalized from `geographyCounterpart`).
    - **Time Period**: Maps to `observationDate`.
    - **Observation Value**: Maps to `value`.
- **Dataset-Specific Overrides**: It can inject mandatory properties for specific series (e.g., setting `populationType: Person` for `ANC_COV`).
- **Output**: Generates a `pvmap.csv` which is used by the Data Commons importer to interpret the data columns.

### 3. Import Configuration (`IMPORT_GUIDE.md`)
The guide defines how the final data is consumed by the Data Commons infrastructure.
- **Approach B (Recommended)**: Uses the "Transcoded" (processed) data where headers are already standardized (`variableMeasured`, `observationAbout`, etc.), making the import process seamless and requiring no manual file manipulation.

---

## Conclusion
The current code in the `undata` folder successfully realizes the vision outlined in the May 20th transcript. It replaces speculative AI mappings with a robust, dictionary-based lookup system that uses intermediate metadata files to ensure every data point is correctly attributed within the Data Commons knowledge graph.
