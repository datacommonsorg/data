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
  - `input/oecd_gdp_data.csv`: Raw input data (created by `download.sh`)
  - `pvmap.csv`: Property-value mapping
  - `metadata.csv`: StatVar metadata (used by `process.sh`)

- **Transformation pipeline**:
  - The `download.sh` script creates an `input` folder for the raw data file.
  - Data is processed using `process.sh`.

### 3. Autorefresh

This import is fully automated.

- **Steps**:
  1. A Cloud Run / Cloud Batch job, defined in `manifest.json`, runs on the first day of each quarter at 8:00 AM UTC.
  2. The job first executes `download.sh` to retrieve the latest data from the OECD SDMX API.
  3. It then runs `process.sh`, which processes the downloaded raw data and generates the final `OECDQuarterlyGDP.csv`, `OECDQuarterlyGDP.tmcf`, and `OECDQuarterlyGDP_stat_vars.mcf` files.
  4. The final, validated output files are uploaded to a GCS bucket for ingestion into the Data Commons Knowledge Graph.

### 4. Script Execution Details

To run the import manually, follow these steps in order.

#### Step 1: Download Raw Data

This script downloads the latest data from the source.

**Usage**:
```bash
# Run with default start year (2020) and end year (current year)
bash statvar_imports/oecd/quarterly_gdp/download.sh

# Run with custom start and end years
START_YEAR=2018 END_YEAR=2022 bash statvar_imports/oecd/quarterly_gdp/download.sh
```

#### Step 2: Process the Data

The `process.sh` script processes the downloaded data to generate the final `OECDQuarterlyGDP.csv`, `OECDQuarterlyGDP.tmcf`, and `OECDQuarterlyGDP_stat_vars.mcf`.

**Usage**:
```bash
bash statvar_imports/oecd/quarterly_gdp/process.sh
```

