# CRDC Instructional WiFi Devices Import

## Overview
This import processes survey data from the **Civil Rights Data Collection (CRDC)** published by the U.S. Department of Education Office for Civil Rights (OCR). Specifically, it ingests data regarding the number of Wi-Fi enabled instructional devices used by students across public schools and juvenile justice facilities.

- **Source URL:** https://civilrightsdata.ed.gov/data
- **Place Type:** School (`CensusSchool` / NCES ID)
- **Place Resolution:** Automated resolution using 12-digit NCES IDs formatted from `COMBOKEY` (`nces/{Data:0>12}`)
- **Years Covered:** 2021 onwards (biennial survey cycles, including 2020-21 through 2023-24)
- **Release Frequency:** Biennial (P2Y)
- **Refresh Type:** Fully Autorefresh

## StatVars Measured
This import generates observations for two canonical statistical variables:
1. `Count_School_JuvenileJusticeFacility_WifiEnabledDevice`: Total number of Wi-Fi enabled devices used for student instruction in juvenile justice school facilities.
2. `Count_School_NotJuvenileJusticeFacility_WifiEnabledDevice`: Total number of Wi-Fi enabled devices used for student instruction in regular (non-juvenile justice) school facilities.

Canonical schema definition: `//depot/google3/third_party/datacommons/schema/stat_vars/crdc_instructional_wifi_devices.mcf`.

## How to Run

Execute all commands from this directory (`data/statvar_imports/crdc/instructional_wifi_devices/`):

### 1. Download Input Datasets
Downloads, extracts, and standardizes the CRDC survey CSV files into `input_files/`:
```bash
python3 download.py
```

### 2. Generate StatVars and Observations
Processes the raw survey CSVs into cleaned observation CSV and TMCF files:
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data='input_files/*.csv' \
  --pv_map=common_pvmap.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --config_file=common_metadata.csv \
  --output_path=output/instructional_wifi_devices \
  --output_counters=counters/instructional_wifi_devices_counters.csv
```

## Validation
Validation checks are configured in [validation_config.json](validation_config.json):
- `check_deleted_records_percent`: Ensures deleted records remain under the standard 0.1% threshold across refreshes.
- `check_max_date_consistent`: Verifies that latest observation dates match across all generated StatVars.
- `check_latest_date_freshness`: Asserts that observation dates reach at least 2024.
