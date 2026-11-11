drive.web-frontend_20251204.06_p0
Folder highlights
Mortality data processing involves importing NIH HD*Pulse county-level data via CSV/JSON, detailed in the run.sh script.

# NIH HD*Pulse Mortality Data

## Import Overview

This project processes and imports county-level mortality data from the NIH HD*Pulse Data Portal. The dataset provides Data on mortality rates and trends, focusing on health disparities based on factors such as age, sex, race/ethnicity, and geographic location at state level.

*   **Source URL**: [https://hdpulse.nimhd.nih.gov/data-portal/mortality/table](https://hdpulse.nimhd.nih.gov/data-portal/mortality/table)
*   **Import Type**: Semi Automated
*   **Source Data Availability**: Data is available from the NIH HD*Pulse portal.
*   **Release Frequency**: Annual
*   **Notes**: Based on a detailed data analysis, the strategy is to proceed with county-level data for each state. This approach incorporates granular-level data points, including Cause of Death, Race, Age Group, Sex, and Rural/Urban classification. The vast number of potential combinations from this granular data results in a massive volume of datasets , making manual download and preparation infeasible.

---

## Preprocessing Steps

The import process is divided into three main stages: downloading the raw data, pre-processing it, and then generating the final artifacts for ingestion.

*   **Input files**:
    *   `run.sh`: Downloads all raw data files from `gs://unresolved_mcf/USA_Health_MortalityRate/input_files/` to the local `input_files` folder.
    *   `metadata.csv`: Configuration file for the data processing script.
    *   `pvmap.csv`: Property-value mapping file used by the processor.

*   **Transformation pipeline**:
    1.  `run.sh` downloads all possible data combinations from GCS to the local `input_files` directory.
    2.  The `stat_var_processor.py` tool (from the parent `tools` directory) is run directly on the input files. All downloaded files will be located into the gcs path `gs://unresolved_mcf/USA_Health_MortalityRate/input_files/` and by using `run.sh` file, files will be copied into local `input_files` folder and can be directly read from it while processing.
    3.  The processor uses the `metadata.csv` and `pvmap.csv` files to generate the final `output.csv` and `output.tmcf` files, placing them in the `output_files/` directory.

*   **Data Quality Checks**:
    *   Linting is performed on the generated output files using the DataCommons import tool.
    *   There are no known warnings or errors.

---

## Autorefresh

This import is considered semi-automated because the data download requires manual intervention to validate the parameters. In case of a download failure, the script needs to be manually restarted. The script is designed to resume downloading from where it stopped.

*   **Steps**:
    1.  Execute the `run.sh` script to fetch the raw data files from GCS. These files will be saved in the `input_files` directory.
    2.  Run the `stat_var_processor.py` tool, which processes the cleaned files and generates the final artifacts for ingestion.

---

## Script Execution Details

To run the import manually, follow these steps in order.

### Step 1: Download Raw Data

This script downloads the raw data files from GCS to the local `input_files` directory.

**Usage**:

```shell
./run.sh
```

---

### Step 2: Process the Data for Final Output

This script processes the cleaned input files to generate the final `output.csv` and `output.tmcf`.

**Usage**:

```shell
python3 ../../tools/statvar_importer/stat_var_processor.py --existing_statvar_mcf=scripts/scripts_statvar_stat_vars.mcf --input_data=input_files/*csv --pv_map=pvmap.csv --config_file=metadata.csv --output_path=output_files/output --statvar_dcid_remap_csv=statvar_remapped.csv
```

---

### Step 3: Validate the Output Files

This command validates the generated files for formatting and semantic consistency before ingestion.

**Usage**:

```shell
java -jar /path/to/datacommons-import-tool.jar lint -d 'output_files/'
```

This step ensures that the generated artifacts are ready for ingestion into Data Commons.