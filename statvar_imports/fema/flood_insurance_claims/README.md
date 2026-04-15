# US FEMA - National Flood Insurance Program Claims

This document outlines the process for downloading and importing flood insurance claims data from the Federal Emergency Management Agency (FEMA).

- **Source**: [FEMA NFIP Redacted Claims](https://www.fema.gov/openfema-data-page/fima-nfip-redacted-claims-v2)
- **Place Type**: US States and Counties
- **Statvars**: Flood Insurance Claims, Payments, and related statistics.
- **Years**: Varies by location.

## Usage

The process involves two main steps: downloading the source data and then processing it to generate the final import files.

### 1. Download Data

A Python script is provided to download the necessary data files from the FEMA API. The script downloads and combines the data into a single CSV file in the `input_file` directory.

**Command:**
From the `statvar_imports/fema/flood_insurance_claims` directory, run the following command:
```bash
python3 fema_download.py
```
This will create the `input_file/fema_nfip_claims.csv` file.

### 2. Process Data

After downloading the data, use the `process.py` script to process the raw CSV and generate the final statistical variables and MCF files.

**Command:**
From the `statvar_imports/fema/flood_insurance_claims` directory, run the following command:
```bash
python3 process.py \
    --input_data='input_file/fema_nfip_claims.csv' \
    --config_file='us_flood_nfip_config.py' \
    --pv_map='us_flood_nfip_pv_map_floodzone.py,ratedFloodZone:us_flood_nfip_floodzone_pv_map.py,observationAbout:us_state_codes.py' \
    --output_path='output/nfip_output'
```
This will generate the cleaned CSV and template MCF files in the `output` directory.
