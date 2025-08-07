# US Census Small Area Health Insurance Estimates (SAHIE)

## 1. Import Overview

This project processes and imports the Small Area Health Insurance Estimates (SAHIE) data from the US Census Bureau. The dataset provides annual state- and county-level estimates of health insurance coverage, disaggregated by demographic characteristics such as age, race, sex, and income.

* **Source URL**: [https://www.census.gov/programs-surveys/sahie.html](https://www.census.gov/programs-surveys/sahie.html)
* **Import Type**: Fully Automated
* **Source Data Availability**: Annual releases from the US Census Bureau.
* **Release Frequency**: Annual
* **Notes**: This dataset provides annual state- and county-level estimates of health insurance coverage. Each row represents a specific demographic breakdown for a given county or state.

---

## 2. Preprocessing Steps

Before ingestion, the following preprocessing is done:

* **Input files**:
  * `download_script.py`: Downloads and preprocesses the raw data.
  * `import_configs.json`: Contains the source URL for the data.
  * `census_sahie_metadata.csv`: Configuration for the `stat_var_processor.py`.
  * `census_sahie_pv_map.csv`: Property-value mapping for the StatVar processor.

* **Transformation pipeline**:
  * `download_script.py` downloads the annual data releases, unzips them, and cleans the CSV headers.
  * The script then calls `stat_var_processor.py` for each cleaned CSV file.
  * `stat_var_processor.py` uses the metadata and pv_map files to generate the final cleaned CSVs and MCF files in the `output/` directory.

* **Data Quality Checks**:
  * Linting is performed using the DataCommons import tool JAR.
  * There are no known warnings or errors.

---

## 3. Autorefresh Type

**Autorefresh**

* **Steps**:
  1. A Cloud Scheduler job, defined in `manifest.json`, triggers the `download_script.py` annually in mid-December.
  2. The script automatically downloads the latest data, preprocesses it, and calls the processing script.
  3. The final, validated output files are uploaded to a GCS bucket for ingestion into the Data Commons Knowledge Graph.
* **Note**: This pipeline is fully automated and requires no manual intervention for periodic refreshes.

---

## 4. Script Execution Details

### Script 1: `download_script.py` (Orchestrator)

**Usage**:
```bash
# Run with default configuration from GCS
python3 download_script.py

# Run with a specific configuration file for local testing
python3 download_script.py --config_file_path=import_configs.json
```
**Purpose**: Downloads, cleans, and orchestrates the processing of all yearly data files.

---


### Script 2: `stat_var_processor.py` (Called by `download_script.py`)

**Usage Example (for a single file)**:
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data='input_files/census_sahie_2023.csv' \
  --pv_map='census_sahie_pv_map.csv' \
  --config_file='census_sahie_metadata.csv' \
  --output_path='output/'
```
**Purpose**: Generates StatVar MCF and cleaned observation CSVs.

---


### Script 3: Java Linting Tool

**Usage**:
```bash
java -jar '/path/to/datacommons-import-tool.jar' lint -d 'output/'
```
**Purpose**: Validates all generated files in the `output/` directory for formatting and semantic consistency before ingestion.

```