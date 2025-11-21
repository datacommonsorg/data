# Civil Rights Data Collection (CRDC)

## 1. Import Overview

This project processes and imports the Civil Rights Data Collection (CRDC) data from the U.S. Department of Education. The dataset provides biennial school-level data on a variety of topics, including student enrollment, educational programs, chronic absenteeism, and offenses.

* **Source URL**: [https://civilrightsdata.ed.gov/](https://civilrightsdata.ed.gov/)
* **Import Type**: Automated
* **Source Data Availability**: Biennial releases from the U.S. Department of Education.
* **Release Frequency**: Biennial
* **Notes**: This dataset provides school-level data. The import currently focuses on "Chronic Absenteeism", "Offenses", "Restraint and Seclusion" data.

---

## 2. Preprocessing Steps

The import process is divided into two main stages: downloading the raw data and then processing it to generate the final artifacts for ingestion.

* **Input files**:
  * `download_script.py`: Downloads, unzips, filters, renames, and preprocesses the raw data.
  * `pv_map/chronic_absenteeism_metadata.csv`: Configuration file for the chronic absenteeism data processing script.
  * `pv_map/chronic_absenteeism_pvmap.csv`: Property-value mapping file used by the processor for chronic absenteeism.
  * `pv_map/offenses_metadata.csv`: Configuration file for the offenses data processing script.
  * `pv_map/offenses_pvmap.csv`: Property-value mapping file used by the processor for offenses.
  * `pv_map/restraint_and_seclusion_metadata.csv`: Configuration file for the restraint and seclusion data processing script.
  * `pv_map/restraint_and_seclusion_pvmap.csv`: Property-value mapping file used by the processor for restraint and seclusion.

* **Transformation pipeline**:
  1. `download_script.py` downloads the biennial data releases for all available years, unzips them, filters for relevant files, renames them, and adds 'year'.
  2. After the download is complete, the `stat_var_processor.py` tool is run on the cleaned CSV files for Chronic Absenteeism, Offenses, and Restraint and Seclusion separately.
  3. The processor uses the metadata and pv_map files to generate the final `crdc_chronic_absenteeism.csv`, `crdc_chronic_absenteeism.tmcf`, `crdc_offenses.csv`, `crdc_offenses.tmcf`, `crdc_restraint_and_seclusion.csv`, and `crdc_restraint_and_seclusion.tmcf` files, placing them in the `output/` directory.

* **Data Quality Checks**:
  * Linting is performed on the generated output files using the DataCommons import tool.
  * Unit tests are provided in `download_script_test.py` to verify the functionality of the download and preprocessing script.

---

## 3. Autorefresh

This import is designed to be autorefreshed.

* **Steps**:
  1. A Cloud Scheduler job, defined in `manifest.json`, runs biennially.
  2. The job first executes `download_script.py` to automatically download the latest biennial data release.
  3. It then runs the `stat_var_processor.py` tool, which processes the yearly files and generates the final artifacts for both Chronic Absenteeism and Offenses.
  4. The final, validated output files are uploaded to a GCS bucket for ingestion into the Data Commons Knowledge Graph.

---

## 4. Script Execution Details

To run the import manually, follow these steps in order.

### Step 1: Download and Preprocess Raw Data

This script downloads all available biennial data files, unzips them, filters for relevant files, renames them, and adds 'year'.

**Usage**:
```bash
python3 download_script.py
```
The processed source files will be located in `input_files/`.

---


### Step 2: Process the Data

This script processes all cleaned input files to generate the final CSV and TMCF files. It should be run twice: once for Chronic Absenteeism and once for Offenses.

**Usage for Chronic Absenteeism**:
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data='input_files/*_chronic_absenteeism.csv' \
  --pv_map='pv_map/chronic_absenteeism_pvmap.csv' \
  --config_file='pv_map/chronic_absenteeism_metadata.csv' \
  --output_path='output/crdc_chronic_absenteeism'
```

**Usage for Offenses**:
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data='input_files/*_offenses.csv' \
  --pv_map='pv_map/offenses_pvmap.csv' \
  --config_file='pv_map/offenses_metadata.csv' \
  --output_path='output/crdc_offenses'
```

**Usage for Restraint and Seclusion**:
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data='input_files/*_restraint_and_seclusion.csv' \
  --pv_map='pv_map/restraint_and_seclusion_pvmap.csv' \
  --config_file='pv_map/restraint_and_seclusion_metadata.csv' \
  --output_path='output/crdc_restraint_and_seclusion'
```

---


### Step 3: Validate the Output Files

This command validates the generated files for formatting and semantic consistency before ingestion.

**Usage**:
```bash
java -jar /path/to/datacommons-import-tool.jar lint -d 'output/'
```
This step ensures that the generated artifacts are ready for ingestion into Data Commons.

---


### Step 4: Run Unit Tests

This script runs unit tests for the `download_script.py` to verify its functionality.

**Usage**:
```bash
python3 download_script_test.py
```

---

