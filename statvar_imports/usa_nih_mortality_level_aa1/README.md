# NIH HD*Pulse Mortality Data

## Import Overview

This project processes and imports county-level mortality data from the NIH HD*Pulse Data Portal. The dataset provides Data on mortality rates and trends, focusing on health disparities based on factors such as age, sex, race/ethnicity, and geographic location at state level.

*   **Source URL**: [https://hdpulse.nimhd.nih.gov/data-portal/mortality/table](https://hdpulse.nimhd.nih.gov/data-portal/mortality/table)
*   **Import Type**: Semi Automated
*   **Source Data Availability**: Data is available from the NIH HD*Pulse portal.
*   **Release Frequency**: Annual
*   **Notes**: Based on a detailed data analysis, the strategy is to proceed with county-level data for each state. This approach incorporates granular-level data points, including Cause of Death, Race, Age Group, Sex, and Rural/Urban classification. The vast number of potential combinations from this granular data results in a massive volume of datasets (estimated 8,415 CSV files per state), making manual download and preparation infeasible.

---

## Preprocessing Steps

The import process is divided into three main stages: downloading the raw data, pre-processing it, and then generating the final artifacts for ingestion.

*   **Input files**:
    *   `download_script.py`: Automates the download of granular-level data from the source.
    *   `pre_process_script.py`: Combines, cleans, and filters the raw downloaded data.
    *   `metadata.csv`: Configuration file for the data processing script.
    *   `pvmap.csv`: Property-value mapping file used by the processor.

*   **Transformation pipeline**:
    1.  `download_script.py` downloads all possible data combinations.
    2.  `pre_process_script.py` is run to clean and prepare the data.
    3.  The `stat_var_processor.py` tool (from the parent `tools` directory) is run on the cleaned CSV files.
    4.  The processor uses the `metadata.csv` and `pvmap.csv` files to generate the final `output.csv` and `output.tmcf` files, placing them in the `output_files/` directory.

*   **Data Quality Checks**:
    *   Linting is performed on the generated output files using the DataCommons import tool.
    *   There are no known warnings or errors.

---

## Autorefresh

This import is considered semi-automated because the data download requires manual intervention to validate the parameters. In case of a download failure, the script needs to be manually restarted. The script is designed to resume downloading from where it stopped.

*   **Steps**:
    1.  Execute the `download_script.py` to fetch the raw data files. These files will be saved in the `raw_folders` directory, organized by state.
    2.  Execute the `pre_process_script.py` to clean and combine the raw data into final CSV files in the `processed_data` directory.
    3.  Run the `stat_var_processor.py` tool, which processes the cleaned files and generates the final artifacts for ingestion.

---

## Script Execution Details

To run the import manually, follow these steps in order.

### Step 1: Download Raw Data

This script downloads the raw data.

**Usage**:

```shell
python3 download_script.py
```

---

### Step 2: Pre-process and Clean Data

This script processes the raw files to generate cleaned `*.csv` files.

**Usage**:

```shell
python3 pre_process_script.py
```

---

### Step 3: Process the Data for Final Output

This script processes the cleaned input files to generate the final `output.csv` and `output.tmcf`.

**Usage**:

```shell
python3 ../../tools/statvar_importer/stat_var_processor.py --existing_statvar_mcf=scripts/scripts_statvar_stat_vars.mcf --input_data=input_files/*csv --pv_map=pvmap.csv --config_file=metadata.csv --output_path=output_files/output --statvar_dcid_remap_csv=statvar_remapped.csv
```

---

### Step 4: Validate the Output Files

This command validates the generated files for formatting and semantic consistency before ingestion.

**Usage**:

```shell
java -jar /path/to/datacommons-import-tool.jar lint -d 'output_files/'
```

This step ensures that the generated artifacts are ready for ingestion into Data Commons.
