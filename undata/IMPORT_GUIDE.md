# UN Data Commons Import Configuration Guide

This document summarizes the research, strategy, and implementation of the `config.json` files for the UN DESA Gender dataset import.

## Overview
The goal was to create a `config.json` file for the Data Commons importer that references all 57 CSV datasets while ensuring the associated MCF (Statistical Variable definitions) and TMCF (Mapping) files are correctly identified.

## Data Structures
We identified two stages of data available in the workspace:

1.  **Raw Data (`undata/data/`):** Original CSV files with UN-specific headers (`SERIES`, `GEOGRAPHY`, etc.).
2.  **Transcoded Data (`undata/output/`):** Processed folders containing:
    *   `output.csv`: Standardized headers (`variableMeasured`, `observationAbout`, etc.).
    *   `output_stat_vars.mcf`: Property definitions.
    *   `output.tmcf`: Column-to-Property mappings.

---

## Configuration Approaches

Two versions of the configuration were generated in `undata/data/` to provide flexibility based on the import preference.

### Approach A: Importing Raw Data
**File:** `config_approach_a.json`
*   **Source:** `undata/data/*.csv`
*   **Mapping Strategy:** Maps original UN headers to Data Commons attributes.
*   **Column Mappings:**
    *   `variable` → `SERIES`
    *   `entity` → `GEOGRAPHY`
    *   `date` → `TIME_PERIOD`
    *   `value` → `OBS_VALUE`
    *   `unit` → `UNIT_MEASURE`
*   **Requirement:** To use this, you must copy the `.mcf` and `.tmcf` files from their respective `undata/output/` subfolders into `undata/data/` so the importer can "auto-identify" them.

### Approach B: Importing Transcoded (Processed) Data
**File:** `config_approach_b.json`
*   **Source:** `../output/<Dataset_Folder>/output.csv` (Relative to `undata/data/`)
*   **Mapping Strategy:** Uses standardized Data Commons headers already present in the processed files.
*   **Column Mappings:**
    *   `variable` → `variableMeasured`
    *   `entity` → `observationAbout`
    *   `date` → `observationDate`
    *   `value` → `value`
    *   `measurementMethod` → `measurementMethod`
    *   `unit` → `unit`
*   **Advantage:** No file moving is required. The MCF and TMCF files are already in the same folders as the `output.csv` files, making them immediately discoverable by the importer.

### Approach C: Concise Wildcard Configuration (Experimental)
**File:** `config_approach_c.json`
*   **Source:** Uses `*.csv` as a wildcard key.
*   **Advantage:** Extremely short and easy to read.
*   **Note:** Use this only if the Data Commons importer environment supports wildcard expansion in the config file.

---

## How to Use

1.  **Review with Manager:** Decide whether to import the raw source files or the cleaned output files.
2.  **Activate Configuration:** Rename your preferred version to `config.json` in the `undata/data` directory.

```bash
# To use the Transcoded Data (Recommended):
cd undata/data
cp config_approach_b.json config.json

# To use the Raw Data:
cd undata/data
cp config_approach_a.json config.json
```

3.  **Run Importer:** Execute the Data Commons import tool pointing to the `undata/data` directory.

## Metadata Summary
*   **Provenance:** `UN_DESA`
*   **Source URL:** [UN Statistics Division - Gender Data](https://unstats.un.org/unsd/gender/data.html)
*   **Total Files:** 57 datasets
*   **Grouping:** `groupStatVarsByProperty` is enabled to ensure related variables are grouped in the Statistical Variable Explorer.
