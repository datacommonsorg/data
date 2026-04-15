# US Census Small Area Income and Poverty Estimates (SAIPE) - School Districts

## 1. Import Overview

This project processes and imports the Small Area Income and Poverty Estimates (SAIPE) data for school districts from the US Census Bureau. The dataset provides annual estimates of income and poverty for school districts.

* **Source URL**: [https://www.census.gov/programs-surveys/saipe.html](https://www.census.gov/programs-surveys/saipe.html)
* **Import Type**: Automated
* **Source Data Availability**: Annual releases from the US Census Bureau.
* **Release Frequency**: Annual
* **Notes**: This dataset provides annual school district level estimates of poverty.

---

## 2. Preprocessing Steps

The import process is divided into two main stages: downloading the raw data and then processing it to generate the final artifacts for ingestion.

* **Input files**:
  * `download_script.py`: Downloads the raw data.
  * `saipe_metadata.csv`: Configuration file for the data processing script for 2023 data.
  * `saipe_pvmap.csv`: Property-value mapping file used by the processor for 2023 data.

* **Transformation pipeline**:
  1. `download_script.py` downloads the annual data releases for all available years.
  2. After the download is complete, the `stat_var_processor.py` tool is run on the downloaded files.
  3. The processor uses the metadata and pv-map files to generate the final `.csv` and `.tmcf` files, placing them in the `output_files/` directory.

* **Data Quality Checks**:
  * Linting is performed on the generated output files using the DataCommons import tool.
  * There are no known warnings or errors.

---

## 3. Autorefresh

This import is designed to be autorefreshed.

* **Steps**:
  1. A Cloud Scheduler job, defined in `manifest.json`, runs on a schedule of "`0 5 3,17 * *`" (05:00 AM on the 3rd and 17th of every month).
  2. The job first executes `download_script.py` to automatically download the latest annual data release.
  3. It then runs the `stat_var_processor.py` tool, which processes the yearly files and generates the final artifacts.
  4. The final, validated output files are uploaded to a GCS bucket for ingestion into the Data Commons Knowledge Graph.

---

## 4. Script Execution Details

To run the import manually, follow these steps in order.

### Step 1: Download Raw Data

This script downloads all available annual data files.

**Usage**:
```bash
python3 download_script.py
```
The source files will be located in `input_files/`.

---


### Step 2: Process the Data

This script processes input files to generate the final `census_saipe_output.csv` and `census_saipe.tmcf`. Note that metadata and pvmap files are year-specific.

**Usage**:
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data='input_files/*.xlsx' \
  --pv_map='saipe_pvmap.csv' \
  --config_file='saipe_metadata.csv' \
  --output_path='output_files/census_saipe_output'
```

---


### Step 3: Validate the Output Files

This command validates the generated files for formatting and semantic consistency before ingestion.

**Usage**:
```bash
java -jar /path/to/datacommons-import-tool.jar lint -d 'output_files/'
```
This step ensures that the generated artifacts are ready for ingestion into Data Commons.

---


### Step 4: Run Unit Tests

This script runs unit tests for the `download_script.py` to verify its functionality.

**Usage**:
```bash
python3 download_script_test.py
```
