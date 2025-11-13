# New York Diabetes Data

## 1. Import Overview

This project processes and imports data on the percentage of adults with diagnosed diabetes in New York, provided by the New York State Department of Health. The dataset provides annual county-level estimates for the years 2016, 2018, and 2021.

*   **Source URL**: [https://www.health.ny.gov/statistics/brfss/](https://www.health.ny.gov/statistics/brfss/)
*   **Import Type**: Manual
*   **Source Data Availability**: Data is available for 2016, 2018, and 2021.
*   **Release Frequency**: No fixed frequency.
*   **Notes**: This dataset provides county-level estimates of the percentage of adults with diagnosed diabetes. The data originates from the Behavioral Risk Factor Surveillance System (BRFSS).

---

## 2. Preprocessing Steps

The import process involves running a processing script on manually downloaded source data to generate the final artifacts for ingestion.

*   **Input files**:
    *   `input_files/`: This directory contains the raw data files for each year (2016, 2018, 2021).
    *   `*_metadata.csv`: Configuration files for the data processing script for each year.
    *   `*_pv_map.csv`: Property-value mapping files used by the processor for each year.
    *   `*_place_resolver.csv`: Files to map place names to DCIDs for each year.

*   **Transformation pipeline**:
    1.  The raw data for each year is manually downloaded and placed in the `input_files/` directory.
    2.  The `stat_var_processor.py` tool is run separately for each year's data.
    3.  The processor uses the corresponding `_metadata.csv`, `_pv_map.csv`, and `_place_resolver.csv` files to generate the final `_output_YYYY.csv` and a common `_output.tmcf` file, placing them in the `output_files/` directory.

*   **Data Quality Checks**:
    *   The `dc_generated/` directory contains `report.json` and `summary_report.html`, which provide validation and summary statistics for the generated data.

---

## 3. Manual Import

This import is **not** designed to be autorefreshed. The data is downloaded and processed manually. Any future updates will require repeating the manual download and processing steps.

---

## 4. Script Execution Details

To run the import manually, execute the processing scripts as detailed below.

### Process the Data

These scripts process the input files for each year to generate the final `_output_YYYY.csv` files and the `_output.tmcf` template.

**Usage**:
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/NY_Percentage_of_adults_with_diagnosed_diabetes_by_county_2016-data.csv \
  --pv_map=NY_Percentage_of_adults_with_diagnosed_diabetes_by_county_2016_pv_map.csv \
  --config_file=NY_Percentage_of_adults_with_diagnosed_diabetes_by_county_2016_metadata.csv \
  --places_resolved_csv=NY_Percentage_of_adults_with_diagnosed_diabetes_by_county_2016_place_resolver.csv \
  --output_path=output_files/NY_Percentage_of_adults_with_diagnosed_diabetes_by_county_output_2016

python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/NY_Percentage_of_adults_with_diagnosed_diabetes_by_county_2018_data.csv \
  --pv_map=NY_Percentage_of_adults_with_diagnosed_diabetes_by_county_2018_pv_map.csv \
  --config_file=NY_Percentage_of_adults_with_diagnosed_diabetes_by_county_2018_meta_data.csv \
  --places_resolved_csv=NY_Percentage_of_adults_with_diagnosed_diabetes_by_county_2018_place_resolver.csv \
  --output_path=output_files/NY_Percentage_of_adults_with_diagnosed_diabetes_by_county_output_2018

python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/NY_Percentage_of_adults_with_diagnosed_diabetes_by_county_2021_data.csv \
  --pv_map=NY_Percentage_of_adults_with_diagnosed_diabetes_by_county_2021_pv_map.csv \
  --config_file=NY_Percentage_of_adults_with_diagnosed_diabetes_by_county_2021_metadata.csv \
  --places_resolved_csv=NY_Percentage_of_adults_with_diagnosed_diabetes_by_county_2021_place_resolver.csv \
  --output_path=output_files/NY_Percentage_of_adults_with_diagnosed_diabetes_by_county_output_2021
```

---

### Step 5: Validate the Output Files

This command validates the generated files for formatting and semantic consistency before ingestion.

**Usage**:
```bash
java -jar /path/to/datacommons-import-tool.jar lint -d 'output_files/'
```
This step ensures that the generated artifacts are ready for ingestion into Data Commons.

---

