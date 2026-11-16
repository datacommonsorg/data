# CDCWonder_NNDSS_InfectiousWeekly

## Overview
Notifiable Infectious Diseases Data: Weekly tables from CDC WONDER containing incident counts of infectious diseases reported by US states, New York City, the District of Columbia, US territories, and US Census divisions.

This `stat_var_processor` + `pvmap` pipeline:
1. Preprocesses `x9gk-5huc` (`Current week` numeric values, `observationDate`, NY+NYC sum) via `preprocess.py`.
2. Maps 2022–present observations to canonical StatVars via `stat_var_processor.py` and `nndss_weekly_pvmap.csv`.
3. Merges the 2006–2021 historical archive from `gs://unresolved_mcf/cdc/nndss_infectious_diseases_weekly/20250206/cdc_nndss_weekly_tables.csv` via `merge_historical.py`.

## Processing Instructions
```bash
python3 preprocess.py
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/NNDSS_Weekly_Data.csv \
  --pv_map=nndss_weekly_pvmap.csv \
  --config_file=nndss_weekly_metadata.csv \
  --output_path=output/nndss_weekly_output \
  --output_counters=counters/nndss_weekly_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
python3 merge_historical.py
```

## Running Unit Tests
```bash
python3 -m unittest preprocess_test.py
```
