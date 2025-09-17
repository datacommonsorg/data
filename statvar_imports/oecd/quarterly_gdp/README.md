# OECD Quarterly GDP Import

### 1. Import Overview
This project processes and imports quarterly GDP data from the Organisation for Economic Co-operation and Development (OECD).

- **Source URL**: [https://data.oecd.org/gdp/quarterly-gdp.htm](https://data.oecd.org/gdp/quarterly-gdp.htm)
- **Import Type**: Fully Automated
- **Source Data Availability**: Data is available from 2020 to the latest year.
- **Release Frequency**: Quarterly
- **Type of Place**: Country
- **StatVars**: Primarily related to quarterly GDP growth rates.

### 2. Preprocessing Steps

- **Input files**:
  - `output/oecd_gdp_full_data.csv`: Raw input data (created by `download.py`)
  - `pvmap.csv`: Property-value mapping
  - `metadata.csv`: StatVar metadata (used by `stat_var_processor.py`)

- **Transformation pipeline**:
  - The `download.py` script creates an `output` folder for the raw data file.
  - Data is processed using `stat_var_processor.py`.

### 3. Autorefresh

This import is fully automated.

- **Steps**:
  1. A Cloud Run / Cloud Batch job, defined in `manifest.json`, runs on the first day of each quarter at 8:00 AM UTC.
  2. The job first executes `download.py` to retrieve the latest data from the OECD SDMX API.
  3. It then runs the `stat_var_processor.py` tool, which processes the downloaded raw data and generates the final `OECDQuarterlyGDP.csv`, `OECDQuarterlyGDP.tmcf`, and `OECDQuarterlyGDP_stat_vars.mcf` files.
  4. The final, validated output files are uploaded to a GCS bucket for ingestion into the Data Commons Knowledge Graph.

### 4. Script Execution Details

To run the import manually, follow these steps in order.

#### Step 1: Download Raw Data

This script downloads the latest data from the source.

**Usage**:
```bash
# Run with default start (2020) and end (2025) years
python3 download.py

# Run with custom start and end years
START_YEAR=2018 END_YEAR=2022 python3 download.py
```

#### Step 2: Process the Data

The `stat_var_processor.py` script processes the downloaded data to generate the final `OECDQuarterlyGDP.csv`, `OECDQuarterlyGDP.tmcf`, and `OECDQuarterlyGDP_stat_vars.mcf`.

**Usage**:
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=output/oecd_gdp_full_data.csv \
  --pv_map=pvmap.csv \
  --config_file=metadata.csv \
  --output_path=OECDQuarterlyGDP
```
