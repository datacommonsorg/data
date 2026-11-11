# Israel Census (`Israel_Census`)

## Overview
This directory contains the automated import pipeline for the **Israel Central Bureau of Statistics (CBS / למ"ס)** Census, vital statistics, and demographic datasets (`Israel_Census`).

The pipeline replaces the legacy manual CNS import (`/cns/jv-d/home/datcom/v3_mcf/country/israel/`) by downloading all 9 source files directly from `https://apis.cbs.gov.il/series/data/path` and `https://boardsgenerator.cbs.gov.il/` into `input_files/`, formatting them into the 11 wide/2D sheet-format CSV tables in `staged_inputs/*.csv` via [`preprocess.py`](file:///usr/local/google/home/gabrol/dcwork/27oct/israel_census/data/statvar_imports/israel_census/preprocess.py), and running [`stat_var_processor.py`](file:///usr/local/google/home/gabrol/dcwork/27oct/israel_census/data/tools/statvar_importer/stat_var_processor.py) in a single process with the unified [`israel_census_pv_map.csv`](file:///usr/local/google/home/gabrol/dcwork/27oct/israel_census/data/statvar_imports/israel_census/israel_census_pv_map.csv).

## Geographic & Statistical Coverage
- **Geographic Levels**:
  - Country: Israel (`country/ISR`)
  - Administrative Area 1 (7 CBS Districts): Jerusalem (`wikidataId/Q192232`), Northern (`wikidataId/Q189942`), Haifa (`wikidataId/Q185845`), Central (`wikidataId/Q188785`), Tel Aviv (`wikidataId/Q192811`), Southern (`wikidataId/Q188781`), and Judea and Samaria Area (`wikidataId/Q513200`).
  - Administrative Area 2 (11 CBS Subdistricts): Safed (`wikidataId/Q5423089`), Acre (`wikidataId/Q5423103`), Golan (`wikidataId/Q5423040`), Haifa (`wikidataId/Q5423411`), Hadera (`wikidataId/Q5423414`), Hasharon (`wikidataId/Q152379`), Petah Tikva (`wikidataId/Q46993019`), Ramla (`wikidataId/Q5419070`), Rehovot (`wikidataId/Q46992983`), Ashkelon (`wikidataId/Q5423623`), and Beersheba (`wikidataId/Q5423629`).
- **Statistical Variables (304 unique StatVars)**:
  - Population by religion (`id=2,1,1,1` on `apis.cbs.gov.il`, 1949–2024+: Series IDs `3700`, `3701`, `3702`, `3703`, `3704`)
  - Live births, infant deaths, and total deaths by religion (`id=2,3,1` on `apis.cbs.gov.il`, 1996–2024+: Series IDs `3751`, `3752`, `3755`, `3759`, `3762`, `3729`, `3747`)
  - Cause-of-death mortality rates per 100,000 by religion and gender (`id=4,2,1` on `apis.cbs.gov.il`, 1950–2022+: 36 series across 6 causes × 6 demographic groups)
  - Population by age group, gender, and marital status (2008 Census)
  - Employed population by age group, gender, and marital status (2008 Census)
  - Urban/rural, District, and Subdistrict population by gender and age bracket (2008 Census)

## Pipeline Architecture
1. **[`download_script.py`](file:///usr/local/google/home/gabrol/dcwork/27oct/israel_census/data/statvar_imports/israel_census/download_script.py)**:
   - Downloads all 9 source files directly from `https://apis.cbs.gov.il/series/data/path` and `https://boardsgenerator.cbs.gov.il/` into `input_files/`:
     - `cbs_series_population_religion.csv`, `cbs_series_vital_statistics.csv`, `cbs_series_cause_of_death.csv` (`format=csv&download=true`)
     - `cbs_census_2008_regions.csv` (`YishuvHandler.ashx?mode=GetCensusData` across `Machoz` `999,1..7` and `Nafa` `21..62`)
     - `dem1_2.xls`, `dem1_14.xls`, `lab4_14.xls`, `lab4_14_1.xls`, `lab4_14_2.xls`
2. **[`preprocess.py`](file:///usr/local/google/home/gabrol/dcwork/27oct/israel_census/data/statvar_imports/israel_census/preprocess.py)**:
   - Reads the raw source files in `input_files/` and writes the 11 wide/2D sheet-format CSV tables into `staged_inputs/*.csv`:
     - `isr_population_religion_1949_2021.csv`
     - `isr_livebirth_infantdeath_deaths_religion_1996_2021.csv`
     - `isr_causeofdeath_religion_1950_2020.csv`
     - `isr_agebracket_gender_aa1_2008.csv`
     - `isr_subdistrict_age_gender_2008.csv`
     - `isr_subdistrict_population_gender_2008.csv`
     - `isr_urban_rural_gender_aa1_2008.csv`
     - `isr_age_maritalstatus_2008.csv`
     - `isr_menemployed_age_martialstatus_2008.csv`
     - `isr_totalemployed_age_martialstatus_2008.csv`
     - `isr_womenemployed_age_martialstatus_2008.csv`
3. **[`stat_var_processor.py`](file:///usr/local/google/home/gabrol/dcwork/27oct/israel_census/data/tools/statvar_importer/stat_var_processor.py)**:
   - Invoked directly from [`manifest.json`](file:///usr/local/google/home/gabrol/dcwork/27oct/israel_census/data/statvar_imports/israel_census/manifest.json) in a single process over `staged_inputs/*.csv` using [`israel_census_pv_map.csv`](file:///usr/local/google/home/gabrol/dcwork/27oct/israel_census/data/statvar_imports/israel_census/israel_census_pv_map.csv) and [`israel_census_metadata.csv`](file:///usr/local/google/home/gabrol/dcwork/27oct/israel_census/data/statvar_imports/israel_census/israel_census_metadata.csv) to generate `output_files/israel_census_output.{csv,tmcf,mcf}` and `counters/israel_census_counters.csv`.

## Test Data (`test_data/`)
- [`test_data/sample_input.csv`](file:///usr/local/google/home/gabrol/dcwork/27oct/israel_census/data/statvar_imports/israel_census/test_data/sample_input.csv): Sample staged input CSV table.
- [`test_data/sample_output.csv`](file:///usr/local/google/home/gabrol/dcwork/27oct/israel_census/data/statvar_imports/israel_census/test_data/sample_output.csv): Expected cleaned CSV output generated by `stat_var_processor.py`.
- [`test_data/sample_output.tmcf`](file:///usr/local/google/home/gabrol/dcwork/27oct/israel_census/data/statvar_imports/israel_census/test_data/sample_output.tmcf): Expected template MCF generated by `stat_var_processor.py`.

## Running Locally

```bash
# 1. Download all raw source files into input_files/
python3 download_script.py

# 2. Format the raw files into the 11 sheet-format tables in staged_inputs/
python3 preprocess.py --input_dir=input_files --output_dir=staged_inputs

# 3. Run stat_var_processor.py directly in a single process
python3 ../../tools/statvar_importer/stat_var_processor.py \
    --input_data="staged_inputs/*.csv" \
    --pv_map=israel_census_pv_map.csv \
    --config_file=israel_census_metadata.csv \
    --output_path=output_files/israel_census_output \
    --output_counters=counters/israel_census_counters.csv

# 4. Run stat_var_processor.py against test_data/sample_input.csv
python3 ../../tools/statvar_importer/stat_var_processor.py \
    --input_data=test_data/sample_input.csv \
    --pv_map=israel_census_pv_map.csv \
    --config_file=israel_census_metadata.csv \
    --output_path=test_data/sample_output

# 5. Run unit tests
python3 -m unittest discover -s . -p "*_test.py" -v
```
