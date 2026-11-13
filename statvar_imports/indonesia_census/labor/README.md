# Indonesia_Census_Labor

## Overview

This package automates the **`Indonesia_Census_Labor`** slice (Labor Force Participation Rate by Sex & Percentage of Formal Labor by Province) from Statistics Indonesia (*Badan Pusat Statistik* — BPS):

1. **Labor Force Participation Rate by Sex** (`var_id = 2200`, `domain = 0000`, `2018–2025`):
   - **Source URL**: `https://www.bps.go.id/en/statistics-table/2/MjIwMCMy/labor-force-participation-rate-by-sex.html`
   - **BPS WebAPI Endpoint**: `https://webapi.bps.go.id/v1/api/list/model/data/lang/eng/domain/0000/var/2200/`
   - **Geographic Coverage**: Country (`country/IDN`), Provinces (`AdministrativeArea1`), and Regencies/Cities (`AdministrativeArea2`) across Indonesia (`546` unique places, `8,672` observations vs `5,342` legacy CNS observations).
   - **Statistical Variables**:
     - `Count_Person_InLaborForce_Male_AsAFractionOf_Count_Person_Male`
     - `Count_Person_InLaborForce_Female_AsAFractionOf_Count_Person_Female`

2. **Percentage of Formal Labor by Province** (`var_id = 1168`, `domain = 0000`, `2015–2025`):
   - **Source URL**: `https://www.bps.go.id/en/statistics-table/2/MTE2OCMy/percentage-of-formal-labor-by-province--percent-.html`
   - **BPS WebAPI Endpoint**: `https://webapi.bps.go.id/v1/api/list/model/data/lang/eng/domain/0000/var/1168/`
   - **Geographic Coverage**: Country (`country/IDN`) and Provinces (`AdministrativeArea1`, `39` unique places including the 4 new Papua provinces introduced in 2024; `407` observations vs `346` legacy CNS observations).
   - **Statistical Variable**:
     - `Count_Person_FormalLabor_AsAFractionOf_Count_Person_InLaborForce` (`unit: Percent`)

Combined across both tables, the automated pipeline produces `9,079` observations (`+3,391` added over the `5,688` legacy CNS baseline observations, `0` modified, `0` deleted).

## Pipeline Files

- `download.py`: Queries the BPS WebAPI (`model/th` and `model/data`) for `var_id=2200` and `var_id=1168` in 3-year chunks with exponential backoff, archives the raw JSON responses (`raw_lfpr_2200.json` and `raw_formal_labor_1168.json`), and writes long-format CSVs atomically:
  - `input_files/labor_force_participation_rate_by_sex.csv`
  - `input_files/percentage_of_formal_labor_by_province.csv`
- `download_test.py`: Unit tests verifying label normalization, API key resolution/redaction, retry/fast-fail HTTP handling, multi-page/multi-chunk stitching, and atomic long-format CSV output.
- `indonesia_lfpr_pvmap.csv` & `indonesia_lfpr_metadata.csv`: Property-Value mapping and processor configuration for LFPR by Sex.
- `indonesia_formal_labor_pvmap.csv` & `indonesia_formal_labor_metadata.csv`: Property-Value mapping and processor configuration for Formal Labor by Province.
- `indonesia_labor_places_resolved.csv`: Deduplicated place name to Data Commons DCID mapping covering Indonesia (`country/IDN`), all 38 provinces (`AdministrativeArea1`), and regencies/cities (`AdministrativeArea2`).
- `manifest.json`: Import automation specification for `Indonesia_Census_Labor`.
- `validation_config.json`: Validation rules checking `MAX_DATE_CONSISTENT`, `NUM_PLACES_CONSISTENT`, and `SQL_VALIDATOR` row-count/freshness bounds.
- `test_data/`: Sample 5-place input and expected output fixtures (`< 100` rows).

## Prerequisites (`BPS_API_KEY`)

`download.py` requires a Badan Pusat Statistik (BPS) WebAPI key, resolved in the following order:
1. `--api_key=<YOUR_BPS_API_KEY>` command-line flag
2. `BPS_API_KEY` environment variable
3. Local mounted config `/tmp/gcs/statvar_imports/indonesia_census/config.json` (`{"bps_api_key": "..."}`)
4. GCS fallback `gs://unresolved_mcf/country/indonesia/config.json` (`{"bps_api_key": "..."}`)

## Running Locally

```bash
# 1. Run unit tests
python3 -m unittest statvar_imports/indonesia_census/labor/download_test.py

# 2. Download raw tables from BPS WebAPI
python3 statvar_imports/indonesia_census/labor/download.py \
  --output_dir=statvar_imports/indonesia_census/labor/input_files

# 3. Process LFPR by Sex with stat_var_processor.py
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/indonesia_census/labor/input_files/labor_force_participation_rate_by_sex.csv \
  --pv_map=statvar_imports/indonesia_census/labor/indonesia_lfpr_pvmap.csv \
  --config_file=statvar_imports/indonesia_census/labor/indonesia_lfpr_metadata.csv \
  --places_resolved_csv=statvar_imports/indonesia_census/labor/indonesia_labor_places_resolved.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=statvar_imports/indonesia_census/labor/output_files/indonesia_lfpr_output \
  --output_counters=statvar_imports/indonesia_census/labor/input_files/indonesia_lfpr_counters.txt

# 4. Process Percentage of Formal Labor by Province with stat_var_processor.py
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/indonesia_census/labor/input_files/percentage_of_formal_labor_by_province.csv \
  --pv_map=statvar_imports/indonesia_census/labor/indonesia_formal_labor_pvmap.csv \
  --config_file=statvar_imports/indonesia_census/labor/indonesia_formal_labor_metadata.csv \
  --places_resolved_csv=statvar_imports/indonesia_census/labor/indonesia_labor_places_resolved.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=statvar_imports/indonesia_census/labor/output_files/indonesia_formal_labor_output \
  --output_counters=statvar_imports/indonesia_census/labor/input_files/indonesia_formal_labor_counters.txt
```
