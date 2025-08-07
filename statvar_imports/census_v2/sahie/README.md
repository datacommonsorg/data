# US Census Small Area Health Insurance Estimates (SAHIE)

## 1. Overview

This directory contains the scripts and configuration for importing the Small Area Health Insurance Estimates (SAHIE) data from the US Census Bureau. This dataset provides annual state- and county-level estimates of health insurance coverage, disaggregated by demographic characteristics such as age, race, sex, and income.

- **Source**: [US Census SAHIE Program](https://www.census.gov/programs-surveys/sahie.html)
- **Import Type**: Fully Automated
- **Frequency**: Annual

## 2. File Descriptions

-   `download_script.py`: Downloads the latest annual SAHIE data from the Census Bureau website.
-   `stat_var_processor.py`: A general-purpose script that processes the raw data to generate cleaned CSV and MCF files.
-   `census_sahie_metadata.csv`: Configuration file used by `stat_var_processor.py` to define processing rules.
-   `census_sahie_pv_map.csv`: Maps input data columns to Data Commons properties and values.
-   `import_configs.json`: Contains import-level configurations, including the source URL for the data.
-   `input_files/`: Directory where the raw downloaded CSV files are stored (e.g., `census_sahie_2023.csv`).
-   `output/`: Directory where the processed, cleaned data and generated MCF files are stored.

## 3. Dependencies

The Python scripts require the following libraries. You can install them using pip:

```bash
pip install absl-py google-cloud-storage python-dateutil pandas requests
```

It is recommended to create a `requirements.txt` file with these dependencies for easier environment setup.

## 4. Preprocessing and Transformation

The import process involves the following steps:

1.  **Data Download**: The `download_script.py` fetches the latest annual data releases from the Census Bureau website and stores them as `input_files/census_sahie_YYYY.csv`.
2.  **Data Processing**: The `stat_var_processor.py` script processes each raw CSV file. It uses `census_sahie_pv_map.csv` for property mapping and `census_sahie_metadata.csv` for configuration. The script generates the following for each year:
    -   `output/census_sahie_output_YYYY.csv`: Cleaned data file.
    -   `output/census_sahie_output_YYYY.tmcf`: Template MCF for the cleaned data.
    -   `output/census_sahie_output_YYYY_stat_vars.mcf`: Statistical variable definitions.
    -   `output/census_sahie_output_YYYY_stat_vars_schema.mcf`: Schema for the statistical variables.
3.  **Data Validation**: The generated files are linted using the Data Commons import tool to ensure they meet schema and quality standards.

## 5. Automated Refresh

This import is configured for automatic annual updates:

-   A Cloud Scheduler job, defined in `manifest.json`, triggers the pipeline annually in mid-December.
-   The scripts run automatically to download and process the new data.
-   The validated output files are uploaded to a GCS bucket for ingestion into the Data Commons Knowledge Graph.

This pipeline is fully automated and requires no manual intervention for periodic refreshes.

## 6. Script Execution

### Download Script

Downloads the latest SAHIE data into the `input_files/` directory.

**Usage**:

```bash
# Run with default configuration from GCS
python3 download_script.py

# Run with a specific configuration file for local testing
python3 download_script.py --config_file_path=import_configs.json
```

### Processing Script

Processes a single year of SAHIE data to generate cleaned CSV and MCF files. The `stat_var_processor.py` is a general tool and is located in a parent directory.

**Usage Example (for 2023 data)**:

```bash
# The processor script is located in a parent directory
PROCESSOR_PATH="../../../tools/statvar_importer/stat_var_processor.py"

python3 ${PROCESSOR_PATH} \
  --input_data='input_files/census_sahie_2023.csv' \
  --pv_map='census_sahie_pv_map.csv' \
  --config_file='census_sahie_metadata.csv' \
  --output_path='output/'
```

### Validation Tool

Lints the generated output files to check for errors before import.

**Usage**:

```bash
# Lint all generated files in the output directory
# Replace /path/to/datacommons-import-tool.jar with the actual path
java -jar /path/to/datacommons-import-tool.jar lint -d 'output/'
```
