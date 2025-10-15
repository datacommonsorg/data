# US Colleges and Universities (IPEDS)

## 1. Import Overview

This project processes and imports comprehensive data for US colleges and universities from the **Integrated Postsecondary Education Data System (IPEDS)**. The dataset provides a wide range of metrics on postsecondary education in the United States.

* **Source URL**: [https://educationdata.urban.org/](https://educationdata.urban.org/)
* **Import Type**: Manual file-based import (CSV)
* **Source Data Availability**: Data is sourced from IPEDS, which is the primary source for data on postsecondary education in the United States.
* **Release Frequency**: IPEDS data is released annually. This import is updated manually by the team when a new data release is published.
* **Notes**: The dataset includes various metrics such as admissions, enrollment by age and race, retention rates, graduation rates, and student-to-faculty ratios. Each dataset is processed into its own set of output files.

---

## 2. Preprocessing Steps

Before ingestion, the raw data is processed by a series of scripts that clean, transform, and format the data for Data Commons.

* **Input files**:
    * `input_files/*.csv`: Raw input data for various metrics (admissions, retention, etc.).
    * `input_files/fall_enrollment_age/*.csv`: Raw input data for fall enrollment by age.
    * `input_files/fall_enrollment_race/*.csv`: Raw input data for fall enrollment by race.
    * `pv_maps/*.csv`: A collection of property-value mapping files for each dataset.
    * `pv_maps/*_metadata.csv`: StatVar metadata configuration files used by the processor script.
* **Transformation pipeline**:
    * The `stat_var_processor.py` script is run for each of the 11 datasets.
    * The script cleans and standardizes columns to match StatVar requirements based on the provided PV maps and metadata.
    * StatVars are generated for each dataset.
    * The final output is written to the `output_files/` and `out/` directories, with a corresponding CSV, TMCF, and StatVar MCF for each dataset.
* **Data Quality Checks**:
    * Linting should be performed on the generated CSV and TMCF files using the standard DataCommons import tool (Java JAR) to check for formatting and semantic errors before ingestion.

---

## 3. Autorefresh Type

**Manual Refresh**

* **Steps**:
    1. Monitor the [Urban Institute Education Data Portal](https://educationdata.urban.org/) for new IPEDS data releases.
    2. Manually download the latest data files.
    3. Run `download_script.py` to organize and place the new files into the appropriate `input_files/` directories.
    4. Execute the `stat_var_processor.py` script for each of the 11 datasets to preprocess the new data.
    5. Run linting and validation checks on all generated output files.
    6. Upload the final, validated files to the appropriate GCS bucket (e.g., `gs://datcom-imports/us_ipeds/education/latest/`).
    7. Trigger the import process for the new data.
* **Note**: This pipeline is not fully automated and requires manual intervention for data retrieval, processing, and ingestion.

---

## 4. Script Execution Details

### Script 1: `download_script.py`

**Usage**:
```bash
python3 download_script.py
```
**Purpose**: Downloads the raw data from the source and prepares it for processing.

---

### Script 2: `stat_var_processor.py`

**Usage Example**:
This script is run for each of the 11 datasets. The following is an example for the "Admissions and Enrollment" dataset.

```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/colleges_ipeds_admissions-enrollment.csv \
  --pv_map=pv_maps/colleges_ipeds_admissions_enrollment_pv_map.csv \
  --config_file=pv_maps/colleges_ipeds_admissions_enrollment_metadata.csv \
  --output_path=output_files/colleges_ipeds_admissions_enrollment_output \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

**Purpose**: Generates the final StatVar MCF, cleaned observation CSV, and TMCF for a given input dataset.

---

### Script 3: Java Linting Tool

**Usage Example**:
```bash
java -jar '/path/to/datacommons-import-tool.jar' lint \
  'output_files/colleges_ipeds_admissions_enrollment_output.csv' \
  'output_files/colleges_ipeds_admissions_enrollment_output.tmcf'
```

**Purpose**: Validates the final generated CSV and TMCF files for formatting and semantic consistency before they are ingested into Data Commons.
