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
  * `census_sahie_schema.mcf`: Statistical variable definitions.

* **Transformation pipeline**:
  1. `download_script.py` downloads the annual data releases for all years from 2018 to the current year. It then unzips the files and cleans the CSV headers, saving the results in the `gcs_output/input_files/` directory.
  2. After the download is complete, the `stat_var_processor.py` tool is run on all cleaned CSV files.
  3. The processor uses the `census_sahie_metadata.csv` and `census_sahie_pv_map.csv` files to generate the final `census_sahie.csv` and `census_sahie.tmcf` files, placing them in the `gcs_output/output_files/` directory.

* **Data Quality Checks**:
  * Linting is performed on the generated output files using the DataCommons import tool.
  * There are no known warnings or errors.

---

## 3. Autorefresh

This import is designed to be autorefreshed.

* **Steps**:
  1. A Cloud Scheduler job, defined in `manifest.json`, runs annually at 00:00 on December 15th.
  2. The job first executes `download_script.py` to automatically download the latest annual data release.
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
The cleaned source files will be located in `gcs_output/input_files/`.

---


### Step 2: Process the Data

This script processes all cleaned input files to generate the final `census_sahie.csv` and `census_sahie.tmcf`.

**Usage**:
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data='gcs_output/input_files/*.csv' \
  --pv_map='census_sahie_pv_map.csv' \
  --config_file='census_sahie_metadata.csv' \
  --output_path='gcs_output/output_files/census_sahie'
```

---


### Step 3: Validate the Output Files

This command validates the generated files for formatting and semantic consistency before ingestion.

**Usage**:
```bash
java -jar /path/to/datacommons-import-tool.jar lint -d 'output/'
```
This step ensures that the generated artifacts are ready for ingestion into Data Commons.
