# IPEDS FTE Enrollment National

## Import Overview

This project processes and imports national-level full-time equivalent (FTE) enrollment data from the Integrated Postsecondary Education Data System (IPEDS).

*   **Import Name**: IPEDS_FTE_Enrollment_National
*   **Source URL**: https://nces.ed.gov/ipeds/trendgenerator/
*   **Provenance Description**: Data focuses on Full-Time Equivalent (FTE) enrollment across U.S. postsecondary institutions
*   **Import Type**: Semi Automated
*   **Source Data Availability**: Data is available from the IPEDS Trend Generator portal from 2009-2010 to present academic year.
*   **Release Frequency**: Annual

---

## Preprocessing Steps

The import process involves downloading raw data, preprocessing it to remove descriptive rows, and then generating the final artifacts for ingestion.

*   **Input files**:
    *   Raw data files are downloaded from the source and stored in a GCP bucket.
    *   `run.sh`: Downloads the raw data files from the GCP bucket into the `input_files/` directory.
    *   `preprocess.py`: Cleans the raw CSV files by removing initial descriptive rows.
    *   `metadata.csv`: Configuration file for the data processing script.
    *   `pvmap/`: Directory containing property-value mapping files used by the processor.

*   **Transformation pipeline**:
    1.  Raw data files are downloaded from the source to a GCP bucket.
    2.  `run.sh` script is executed to download these files to the `input_files/` directory.
    3.  `preprocess.py` script is executed to remove descriptive header rows from the downloaded CSV files.
    4.  The `stat_var_processor.py` tool is run on each cleaned CSV file, as specified in `manifest.json`.
    5.  The processor uses the `metadata.csv` and respective `pvmap.csv` files to generate the final `output.csv` and `output.tmcf` files, placing them in the `output/` directory.

*   **Data Quality Checks**:
    *   Linting is performed on the generated output files using the DataCommons import tool.
    *   There are no errors, as confirmed by the `report.json` analysis.

---

## Autorefresh

This import is considered semi-automated because the initial data download to the GCP bucket might require manual intervention. However, once in the bucket, the `run.sh` and `preprocess.py` scripts automate the download and cleaning process.

*   **Steps**:
    1.  Ensure raw data files are in the specified GCP bucket.
    2.  Execute `run.sh` to fetch the raw data files into `input_files/`.
    3.  Execute `preprocess.py` to clean the input files by removing descriptive header rows.
    4.  The `stat_var_processor.py` tool is then run (as defined in `manifest.json`) on the preprocessed files to generate the final artifacts for ingestion.

---

## Script Execution Details

To run the import manually, follow these steps in order.

### Step 1: Download Raw Data (via `run.sh`)

This script downloads the raw data from the GCP bucket to the `input_files/` directory.

**Usage**:

```shell
bash run.sh
```

---

### Step 2: Preprocess the Data (via `preprocess.py`)

This script cleans the downloaded CSV files in the `input_files/` directory by removing descriptive header rows.

**Usage**:

```shell
python3 preprocess.py
```

---

### Step 3: Process the Data for Final Output

This step involves running the `stat_var_processor.py` for each input file as specified in `manifest.json`. An example command is shown below:

**Usage**:

```shell
python3 ../../tools/statvar_importer/stat_var_processor.py --existing_statvar_mcf=scripts_statvar_stat_vars.mcf --input_data=input_files/controlOfInstitution_data.csv --pv_map=pvmap/controlOfInstitution_pvmap.csv --config_file=metadata.csv --output_path=output/ControlOfInstitution_output
```

_Note: This command needs to be executed for all 10 input files as defined in `manifest.json` under the `scripts` tag._

---

### Step 4: Validate the Output Files

This command validates the generated files for formatting and semantic consistency before ingestion.

**Usage**:

```shell
java -jar /path/to/datacommons-import-tool.jar lint -d 'output/'
```

This step ensures that the generated artifacts are ready for ingestion into Data Commons.