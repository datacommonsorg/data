# US Census Small Area Health Insurance Estimates (SAHIE)

## 1. Import Overview

This project processes and imports the Small Area Health Insurance Estimates (SAHIE) data from the US Census Bureau. The dataset provides annual state- and county-level estimates of health insurance coverage, disaggregated by demographic characteristics such as age, race, sex, and income.

* **Source URL**: [https://www.census.gov/programs-surveys/sahie.html](https://www.census.gov/programs-surveys/sahie.html)
* **Import Type**: Automated
* **Source Data Availability**: Annual releases from the US Census Bureau.
* **Release Frequency**: Annual
* **Notes**: This dataset provides annual state- and county-level estimates of health insurance coverage. Each row represents a specific demographic breakdown for a given county or state.

---

## 2. Preprocessing Steps

The import process is divided into two main stages: downloading the raw data and then processing it to generate the final artifacts for ingestion.

* **Input files**:
  * `download_script.py`: Downloads and performs initial cleaning of the raw data.
  * `census_sahie_metadata.csv`: Configuration file for the data processing script.
  * `census_sahie_pv_map.csv`: Property-value mapping file used by the processor.
  * `validation_config.json`: Validation rules for consistency and date freshness checks.

* **Transformation pipeline**:
  1. `download_script.py` downloads and unzips the annual data releases for all available years from 2018 to the current year into `raw_files/`, and writes the header-cleaned CSV files to the `input_files/` directory.
  2. After the download is complete, the `stat_var_processor.py` tool is run on all cleaned CSV files.
  3. The processor uses the `census_sahie_metadata.csv` and `census_sahie_pv_map.csv` files to generate the final `census_sahie.csv`, `census_sahie.tmcf`, `census_sahie_stat_vars.mcf`, and `census_sahie_counters.csv` files, placing them in the `output_files/` directory.

* **Data Quality Checks**:
  * Linting is performed on the generated output files using the DataCommons import tool.
  * Automated import validation checks `MAX_DATE_CONSISTENT` and date freshness via `validation_config.json`.

---

## 3. Autorefresh

This import is designed to be autorefreshed.

* **Steps**:
  1. A Cloud Scheduler job, defined in `manifest.json`, runs weekly on Thursday at 11:00 UTC (`0 11 * * 4`).
  2. The job first executes `download_script.py` to automatically download all available annual data releases.
  3. It then runs the `stat_var_processor.py` tool, which processes all the yearly files and generates the final artifacts.
  4. The final, validated output files are uploaded to a GCS bucket for ingestion into the Data Commons Knowledge Graph.

---

## 4. Script Execution Details

To run the import manually, follow these steps in order.

### Step 1: Download and Clean Raw Data

This script downloads all available annual data files, unzips them, and cleans their headers.

**Usage**:
```bash
python3 download_script.py
```
The cleaned source files will be located in `input_files/`.

---


### Step 2: Process the Data

This script processes all cleaned input files to generate `census_sahie.csv`, `census_sahie.tmcf`, and `census_sahie_stat_vars.mcf` in `output_files/`.

**Usage**:
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data='input_files/*.csv' \
  --pv_map='census_sahie_pv_map.csv' \
  --config_file='census_sahie_metadata.csv' \
  --output_path='output_files/census_sahie' \
  --output_counters='output_files/census_sahie_counters.csv' \
  --existing_statvar_mcf='gs://unresolved_mcf/scripts/statvar/stat_vars.mcf'
```

---


### Step 3: Validate the Output Files

This command validates the generated files for formatting and semantic consistency before ingestion.

**Usage**:

Lint takes the generated TMCF, MCF, and CSV files per run; `-o` sets the folder for the report (`report.json` and `summary_report.html`).

```bash
java -jar /path/to/datacommons-import-tool.jar lint -o lint_report \
  output_files/census_sahie.csv output_files/census_sahie.tmcf output_files/*.mcf
```
This step ensures that the generated artifacts are ready for ingestion into Data Commons.

---


### Step 4: Run Unit Tests

This script runs unit tests for the `download_script.py` to verify its functionality.

**Usage**:
```bash
python3 download_script_test.py
```
