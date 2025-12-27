# Bureau of Economic Analysis (BEA) Annual Gross Domestic Product (GDP) Data Import

## 1. Overview

This project processes and imports the Annual Gross Domestic Product (GDP) data from the US Bureau of Economic Analysis (BEA). The dataset provides annual estimates of GDP by industry for various geographic areas.

*   **Source URL (General)**: [https://www.bea.gov/data/gdp](https://www.bea.gov/data/gdp)
*   **Source Data Download**: [https://apps.bea.gov/regional/zip/SAGDP.zip](https://apps.bea.gov/regional/zip/SAGDP.zip)
*   **Import Type**: Automated
*   **Source Data Availability**: Annual releases from the BEA.
*   **Release Frequency**: Annual
*   **Notes**: This dataset provides annual GDP estimates at various levels of geographic detail.

## 2. Preprocessing Steps

The import process is divided into two main stages: downloading the raw data and then processing it to generate the final artifacts for ingestion.

*   **Input files**:
    *   `download_script.py`: Script to download and preprocess the raw data.
    *   `input_files/sagdpX__all_areas_YYYY_2024.csv`: Raw data files after download and initial cleanup.
    *   `pv_map/sagdpX__all_areas_1997_2024_pvmap.csv`: Property-value mapping files.
    *   `pv_map/sagdpX__all_areas_1997_2024_metadata.csv`: Configuration files for data processing.
    *   `pv_map/sagdpX__all_areas_1997_2024_remap.csv`: Statvar DCID remapping files.
    *   `pv_map/sagdp_places_resolved.csv`: Resolved places data.

*   **Transformation pipeline**:
    1.  `download_script.py` downloads the `SAGDP.zip` file, extracts its contents into the `input_files/` directory, filters for files containing 'ALL_AREAS', converts filenames to lowercase, and strips spaces from key columns in CSV files.
    2.  The `run.sh` script then orchestrates the execution of the `stat_var_processor.py` tool for each of the preprocessed input CSV files.
    3.  The processor uses the metadata, pv-map, and remapping files to generate the final `.csv` and `.tmcf` files, placing them in the `output_files/` directory.

*   **Data Quality Checks**:
    *   Linting is performed on the generated output files using the DataCommons import tool.
    *   There are no known warnings or errors.

## 3. Autorefresh

This import is designed to be autorefreshed.

*   **Steps**:
    1.  A Cloud Scheduler job, defined in `manifest.json`, runs on a schedule of "`0 5 3,17 * *`" (05:00 AM on the 3rd and 17th of every month).
    2.  The job first executes `download_script.py` to automatically download the latest annual data release.
    3.  It then runs `run.sh` (which in turn calls `stat_var_processor.py` multiple times), processing the yearly files and generating the final artifacts.
    4.  The final, validated output files are uploaded to a GCS bucket for ingestion into the Data Commons Knowledge Graph.

## 4. Script Execution Details

To run the import manually, follow these steps in order.

### Step 1: Download and Preprocess Raw Data

This script downloads the `SAGDP.zip` file, extracts the contents, cleans up irrelevant files, and preprocesses the CSV data.

**Usage**:
```bash
python3 download_script.py
```
The preprocessed source files will be located in `input_files/`.

### Step 2: Process the Data

This script processes the preprocessed input files to generate the final `.csv` and `.tmcf` output files for each SAGDP table.

**Usage**:
```bash
bash run.sh
```
The output files will be located in `output_files/`.

### Step 3: Validate the Output Files

This command validates the generated files for formatting and semantic consistency before ingestion.

**Usage**:
```bash
java -jar /path/to/datacommons-import-tool.jar lint -d 'output_files/'
```
This step ensures that the generated artifacts are ready for ingestion into Data Commons.

### Step 4: Run Unit Tests

This script runs unit tests for the `download_script.py` to verify its functionality.

**Usage**:
```bash
python3 download_script_test.py
```
