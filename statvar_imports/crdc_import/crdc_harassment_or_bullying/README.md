# Civil Rights Data Collection (CRDC)

## 1. Import Overview

This project processes and imports the Civil Rights Data Collection (CRDC) data from the U.S. Department of Education. The dataset provides biennial school-level data on a variety of topics, including student enrollment, educational programs, chronic absenteeism, and offenses.

* **Source URL**: [https://civilrightsdata.ed.gov/](https://civilrightsdata.ed.gov/)
* **Import Type**: Automated
* **Source Data Availability**: Biennial releases from the U.S. Department of Education.
* **Release Frequency**: Biennial
* **Notes**: This dataset provides school-level data. The import currently focuses on "Harassment or Bullying" data.

---

## 2. Preprocessing Steps

The import process is divided into two main stages: downloading the raw data, preprocessing and then processing it to generate the final artifacts for ingestion.

* **Input files**:
  * `download.py`: Downloads, unzips, filters, renames, and preprocesses the raw data.
  * `harssment_and_bullying_pv_map.csv`: Configuration file for the chronic absenteeism data processing script.
  * `harassment_or_bullying_metadata.csv`: Property-value mapping file used by the processor for chronic absenteeism.

* **Transformation pipeline**:
  1. `download.py` downloads the biennial data releases for all available years in the `source_files` directory, unzips them, filters for relevant files, renames them, and save it as csv files in the `input_files` directory.
  2. `preprocess.py` adds the year column and rename the files.
  3. After the download is complete, the `stat_var_processor.py` tool is run on the cleaned CSV files in the `input_files` directory using the shell script `run.sh`
  4. The processor uses the metadata and pv_map files to generate the final `.csv`,`.tmcf` files, placing them in the `processed_output/` directory.

* **Data Quality Checks**:
  * Linting is performed on the generated output files using the DataCommons import tool.

---

## 3. Autorefresh

This import is designed to be autorefreshed.

* **Steps**:
  1. A Cloud Scheduler job, defined in `manifest.json`, runs biennially.
  2. The job first executes `download.py` to automatically download the latest biennial data release.
  3.The shell script `run.sh` then runs the `stat_var_processor.py` tool, which processes the yearly files and generates the final artifacts for Harassment or Bullying.
  4. The final, validated output files are uploaded to a GCS bucket for ingestion into the Data Commons Knowledge Graph.

---

## 4. Script Execution Details

To run the import manually, follow these steps in order.

### Step 1: Download and Preprocess Raw Data

This script downloads all available biennial data files, unzips them, filters for relevant files, renames them, and adds 'year'.

**Usage**:
```bash
python3 download.py
```
The processed source files will be located in `input_files/`.

---


### Step 2: Process the Data

This script processes all cleaned input files to generate the final CSV and TMCF files.

The shell script `run.sh` runs the `stat_var_processor.py` tool on the all the files in the `input_files` folder (on every year wise data files) and execute them parallely.
### For example:
**Usage**:

```bash
sh run.sh
```

The stat_var_processor.py command in the shell script looks like the below:

```bash
python3 ../../../../tools/statvar_importer/stat_var_processor.py --input_data="input/Harassment and Bullying.csv" --pv_map="harssment_and_bullying_pvmap.csv" --config_file="harassment_or_bullying_metadata.csv" --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path="output/harassment_or_bullying"
```
To check the processing with the test data, run the below command from the project directory:

```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data="test_data/harassment_or_bullying_data.csv" --pv_map="harssment_or_bullying_pv_map.csv" --config_file="harassment_or_bullying_metadata.csv" --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path="test_data/expected_output/harassment_or_bullying"
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