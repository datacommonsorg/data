# Israel Census (`Israel_Census`)

## Overview
- **Import Name:** `Israel_Census`
- **Source:** Central Bureau of Statistics of Israel (CBS / למ"ס) — https://www.cbs.gov.il/
- **API Endpoints:** `https://apis.cbs.gov.il/series/data/path` and `https://boardsgenerator.cbs.gov.il/`
- **Import Type:** Fully Autorefresh (Scheduled weekly via `manifest.json`: `0 5 * * 1`)
- **Data Availability:** `1949` to `2024+` (annual time-series) and `2008` (Population and Housing Census)
- **Release Frequency:** `P1Y` (Annual)

This directory contains the automated import pipeline for the **Israel Central Bureau of Statistics (CBS)** Census, employment by marital status, vital statistics, and cause-of-death mortality datasets. `download_script.py` downloads the raw unmodified CBS Series API CSV responses (`cbs_series_*.csv`), raw 2008 Census regional JSON payloads (`cbs_yishuv_census_2008.json`), and the 5 raw `.xls` Mifkad tables into `input_files/`. `preprocess.py` transforms all raw files in `input_files/` into the 11 unscaled CSV tables in `staged_inputs/*.csv`, and `stat_var_processor.py` processes all 11 CSVs using `israel_census_pv_map.csv` (which applies `#Multiply,1000`, `#Multiply,100`, place mapping, and StatVar mapping).

## Geographic & Statistical Coverage
- **Geographic Levels & Place Resolution (19 Places)**:
  - **Country:** Israel (`country/ISR`)
  - **Administrative Area 1 (7 CBS Districts):** Jerusalem (`wikidataId/Q192232`), Northern (`wikidataId/Q189942`), Haifa (`wikidataId/Q185845`), Central (`wikidataId/Q188785`), Tel Aviv (`wikidataId/Q192811`), Southern (`wikidataId/Q188781`), and Judea and Samaria Area (`wikidataId/Q513200`).
  - **Administrative Area 2 (11 CBS Sub-districts):** Safed (`wikidataId/Q5423089`), Acre (`wikidataId/Q5423103`), Golan (`wikidataId/Q5423040`), Haifa (`wikidataId/Q5423411`), Hadera (`wikidataId/Q5423414`), Hasharon (`wikidataId/Q152379`), Petah Tikva (`wikidataId/Q46993019`), Ramla (`wikidataId/Q5419070`), Rehovot (`wikidataId/Q46992983`), Ashkelon (`wikidataId/Q5423623`), and Beersheba (`wikidataId/Q5423629`).
  - CBS region codes (`ISR`, `DIST_1`..`DIST_7`, and `SUBDIST_21`..`SUBDIST_62`) are mapped to `country/ISR` and `wikidataId/Q*` DCIDs in `israel_census_pv_map.csv`.
- **Statistical Variables (304 unique StatVars)**:
  - Population by religion (`id=2,1,1,1` on `apis.cbs.gov.il`, `1949`–`2024+`: Series IDs `3700`, `3701`, `3702`, `3703`, `3704`)
  - Live births (`1996`–`2023+`), infant deaths (`1996`–`2024+`), and total deaths (`1996`–`2024+`) by religion (`id=2,3,1` on `apis.cbs.gov.il`: Series IDs `3751`, `3752`, `3755`, `3759`, `3762`, `3729`, `3747`)
  - Cause-of-death mortality rates per 100,000 by religion and gender (`id=4,2,1` on `apis.cbs.gov.il`, `1950`–`2022+`: 36 series across 6 causes × 6 demographic groups)
  - Population by age group, gender, and marital status (`2008` Census)
  - Employed population by age group, gender, and marital status (`2008` Census)
  - Urban/rural, District, and Sub-district population by gender and age bracket (`2008` Census)

## Important Files
- `manifest.json`: Import specification, script execution order, `source_files`, `import_inputs`, and weekly cron schedule (`0 5 * * 1`).
- `download_script.py`: Downloads the raw CBS Series CSV responses (`cbs_series_*.csv`), raw 2008 Census regional JSON (`cbs_yishuv_census_2008.json`), and 5 raw Mifkad `.xls` tables into `input_files/`.
- `preprocess.py`: Transforms the raw `.csv`, `.json`, and `.xls` files in `input_files/` into the 11 staged CSV tables in `staged_inputs/*.csv`.
- `israel_census_pv_map.csv`: Unified Property-Value mapping file (including `#Multiply,1000`, `#Multiply,100`, place resolution, and StatVar mappings) for all 11 CSV datasets and 304 StatVars.
- `israel_census_metadata.csv`: Configuration parameters for `stat_var_processor.py`.
- `validation_config.json`: Validation rules (`MAX_DATE_CONSISTENT` and `SQL_VALIDATOR`) for `tools/import_validation/runner.py`.
- `download_script_test.py` & `preprocess_test.py`: Hermetic unit tests for downloading and preprocessing.
- `test_data/`: Sample test fixtures (`sample_raw_input.csv` matching `input_files/cbs_series_2_1_1_1.csv`, `sample_input.csv` matching `staged_inputs/isr_population_religion_1949_2021.csv`, `sample_output.csv`, and `sample_output.tmcf`).

## Pipeline Architecture & Data Processing Notes
1. **`download_script.py`**:
   - Downloads the raw unmodified source payloads from `https://apis.cbs.gov.il/series/data/path` and `https://boardsgenerator.cbs.gov.il/` into `input_files/`:
     - `cbs_series_2_1_1_1.csv`, `cbs_series_2_3_1.csv`, `cbs_series_4_2_1.csv` (raw CBS Time-Series DataBank CSV exports).
     - `cbs_yishuv_census_2008.json` (raw 2008 Census regional `GetCensusData` JSON payloads for all 19 regions).
     - `dem1_2.xls`, `dem1_14.xls`, `lab4_14.xls`, `lab4_14_1.xls`, `lab4_14_2.xls` (raw 2008 Census Mifkad spreadsheets).
2. **`preprocess.py`**:
   - Transforms the raw payloads in `input_files/` into all 11 unscaled CSV tables in `staged_inputs/`:
     - `isr_population_religion_1949_2021.csv` (from `cbs_series_2_1_1_1.csv`): Computes `Others` (`Count_Person_CBSIsraelNonJudaismOrNonArabChristianOrNoReligion`) as `Jews and Others (3703) - Jews (3701)` and skips incomplete/anomalous provisional years where `Total (3700) < Jews and Others (3703) + Arab (3704) - 1.0`.
     - `isr_livebirth_infantdeath_deaths_religion_1996_2021.csv` (from `cbs_series_2_3_1.csv`): Preserves the `1996`–`2008` historical Arab Christian live-birth counts (`_CBS_ARAB_CHRISTIAN_LIVE_BIRTHS_FALLBACK`) when the API series `3755` starts in `2009`.
     - `isr_causeofdeath_religion_1950_2020.csv` (from `cbs_series_4_2_1.csv`): Preserves the 36 official `2019` CBS mortality rates (`_CBS_2019_CAUSE_OF_DEATH_FALLBACK`) omitted by the `id=4,2,1` API feed between `2018` and `2020`.
     - `isr_agebracket_gender_aa1_2008.csv`, `isr_subdistrict_age_gender_2008.csv`, `isr_subdistrict_population_gender_2008.csv` (from `cbs_yishuv_census_2008.json`).
     - `isr_urban_rural_gender_aa1_2008.csv`, `isr_age_maritalstatus_2008.csv`, `isr_menemployed_age_martialstatus_2008.csv`, `isr_totalemployed_age_martialstatus_2008.csv`, `isr_womenemployed_age_martialstatus_2008.csv` (from `dem1_2.xls`, `dem1_14.xls`, `lab4_14.xls`, `lab4_14_1.xls`, `lab4_14_2.xls`). Suppresses the national `2008` `Grand totalTotal` cell in `dem1_2.xls` and the `(All ages, Total)` cell in `dem1_14.xls` so they do not conflict with the authoritative `2008` national `Count_Person` observation from `isr_population_religion_1949_2021.csv`.
3. **`stat_var_processor.py`**:
   - Invoked from `manifest.json` in a single process over `staged_inputs/*.csv` using `israel_census_pv_map.csv` and `israel_census_metadata.csv` to generate `output_files/israel_census_output.{csv,tmcf,mcf}` and `counters/israel_census_counters.csv`.

## Prerequisites & Working Directory
- **Prerequisites:** Python 3.10+ with `requests`, `pandas`, `xlrd`, `openpyxl`, and `absl-py` (installed automatically via `./run_tests.sh`).
- **Working Directory:** Run the pipeline commands below from `statvar_imports/israel_census/`.

## How to Run Locally

```bash
# 1. Download the raw CBS Series CSVs, 2008 Census JSON, and 5 .xls files into input_files/
python3 download_script.py

# 2. Transform all raw files in input_files/ into the 11 CSV tables in staged_inputs/
python3 preprocess.py --input_dir=input_files --output_dir=staged_inputs

# 3. Run stat_var_processor.py directly in a single process
python3 ../../tools/statvar_importer/stat_var_processor.py \
    --input_data="staged_inputs/*.csv" \
    --pv_map=israel_census_pv_map.csv \
    --config_file=israel_census_metadata.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path=output_files/israel_census_output \
    --output_counters=counters/israel_census_counters.csv

# 4. Run stat_var_processor.py against test_data/sample_input.csv
python3 ../../tools/statvar_importer/stat_var_processor.py \
    --input_data=test_data/sample_input.csv \
    --pv_map=israel_census_pv_map.csv \
    --config_file=israel_census_metadata.csv \
    --output_path=test_data/sample_output
```

## Testing & Validation

```bash
# Run unit tests from the repository root
./run_tests.sh -p statvar_imports/israel_census

# Or run unit tests directly from statvar_imports/israel_census/
python3 -m unittest discover -s . -p "*_test.py" -v
```

## Refresh Procedure
The import is configured for automated weekly refresh (`0 5 * * 1` in `manifest.json`). On each run, `download_script.py` fetches the latest raw annual series from `apis.cbs.gov.il` and the 2008 Census payloads from `boardsgenerator.cbs.gov.il` into `input_files/`, `preprocess.py` transforms all raw inputs into the 11 CSV tables in `staged_inputs/*.csv`, `stat_var_processor.py` generates `output_files/israel_census_output.{csv,tmcf}`, and `validation_config.json` verifies date consistency and value bounds.
