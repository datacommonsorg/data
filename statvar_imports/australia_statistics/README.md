# Australia Bureau of Statistics (ABS) Demographic, Labour, Health, and Income Data

## 1. Import Overview

This project downloads, processes, and imports demographic, labour force, life expectancy, household income, and long-term health condition statistics for Australia across National (`country/AUS`) and State/Territory (`AdministrativeArea1`, `wikidataId/Q...`) geographic levels, provided by the Australian Bureau of Statistics (ABS).

*   **Source URL**: [https://www.abs.gov.au/](https://www.abs.gov.au/)
*   **SDMX API Endpoint**: `https://data.api.abs.gov.au/rest/data/`
*   **Import Type**: Automated
*   **Source Data Availability**:
    *   **Labour Force (National & States/Territories)**: Monthly (`1978-02`–present) via ABS SDMX Dataflow `ABS,LF,1.0.0`.
    *   **Population by Age & Sex (National & States/Territories)**: Historical Census & Estimates (`1901`–`2016`), 2021 Census (`2021`), and Annual 30 June Estimated Resident Population (`2017`–present) via ABS SDMX Dataflow `ABS,ERP_Q,1.0.0`.
    *   **Life Expectancy by Single Age & State/Territory**: Historical Life Tables (`1890`–`2017`) and Annual 3-year Period Life Tables (`2018`–present).
    *   **Long-Term Health Conditions by Age, Sex & State/Territory**: 2021 Census of Population and Housing (`2021`).
    *   **Equivalised Disposable Weekly Household Income (Quintiles & Percentiles)**: Biennial Survey of Income and Housing (`2008`–`2020`).
*   **Release Frequency**: Monthly (Labour Force), Quarterly/Annual (Estimated Resident Population and Life Expectancy), Biennial (Household Income), and Quinquennial (5-year Population & Health Census).
*   **Notes**: This dataset covers 853 StatisticalVariables across Australia (`country/AUS`) and all 8 States and Territories (`New South Wales`, `Victoria`, `Queensland`, `South Australia`, `Western Australia`, `Tasmania`, `Northern Territory`, and `Australian Capital Territory`). To preserve 100% observation parity (`deleted_obs_count: 0`) with legacy production nodes in `aus_count_person_gender_agegrp_2021` and `aus_count_person_gender_agegrp_historic_states`, those two historical tables retain their legacy `dcs:dcs:` place prefix (`AUS_DBL` and `NSW_DBL`..`TAS_DBL`) in `australia_statistics_pv_map.csv`.

---

## 2. Preprocessing Steps

The import pipeline downloads raw ABS SDMX CSVs and statistical Excel workbooks as-is via `download_script.py`, stages and parses them in a temporary directory inside `process.py`, and runs `stat_var_processor.py` in parallel across the staged CSV shards.

*   **Files**:
    *   `download_script.py`: Pure live downloader that fetches monthly Labour Force (`ABS,LF,1.0.0`) and quarterly Estimated Resident Population (`ABS,ERP_Q,1.0.0`) SDMX CSVs alongside ABS Census, Historical Population, Life Expectancy, Health Condition, and Household Income workbooks as-is into `input_files/`.
    *   `process.py`: Extracts raw ABS source indicators and values from `input_files/*` into temporary staged CSV shards, caches `gs://unresolved_mcf/scripts/statvar/stat_vars.mcf` locally once, runs `stat_var_processor.py` in parallel (`--parallelism=2`), and deterministically merges the resulting `.csv`, `.tmcf`, `.mcf`, and `counters.csv` outputs into `output_files/`.
    *   `australia_statistics_metadata.csv`: Configuration file for `stat_var_processor.py` specifying output columns (`observationAbout,observationDate,value,variableMeasured,unit,scalingFactor`), header rows, mapped columns, numeric precision (`output_precision_digits,4`), and provenance URL.
    *   `australia_statistics_pv_map.csv`: Property-value mapping file mapping raw ABS indicator keys (`LF_*`, `ERP_*`, `POP_*`, `HEALTH_*`, `LE_*`, `INC_*`) and region identifiers to Data Commons StatisticalVariables, `#Multiply,1000` scaling (for Labour Force counts reported in thousands), and place DCIDs (`country/AUS` and `wikidataId/Q...`).
    *   `validation_config.json`: Configuration defining historical deletion (`<= 0.1%`), 6 scoped `MAX_DATE_CONSISTENT` rules, value bounds, and date freshness validation rules across all 853 StatisticalVariables.
    *   `test_data/`: Sample input data (`sample_input.csv`) and expected output (`sample_expected_output.csv`) for testing.

*   **Transformation pipeline**:
    1.  `download_script.py` downloads all raw ABS SDMX CSVs and Excel workbooks concurrently using thread-local retry-enabled HTTP sessions, atomic file writes, and stale file cleanup into `input_files/`.
    2.  `process.py` stages the raw files into temporary CSV shards, caches `gs://unresolved_mcf/scripts/statvar/stat_vars.mcf` locally once, and invokes `stat_var_processor.py` in parallel against `australia_statistics_pv_map.csv` and `australia_statistics_metadata.csv`.
    3.  The processor maps all 853 StatisticalVariables and Australian geographic entities, scales Labour Force counts via `#Multiply,1000`, attaches `AUD` unit metadata to weekly household income observations, and writes `output_files/australia_statistics_output.csv` and `output_files/australia_statistics_output.tmcf`.
    4.  Aggregated processor counters are written to `counters/australia_statistics_counters.csv`.

*   **Data Quality Checks**:
    *   Automated validation via `tools/import_validation/runner.py` evaluates the output against `validation_config.json`, enforcing:
        *   `check_deleted_records_percent`: Historical deletion threshold `<= 0.1%`.
        *   `max_date_consistent_*`: 6 scoped `MAX_DATE_CONSISTENT` rules verifying date consistency within each co-released ABS dataset family.
        *   `check_active_indicators_freshness_and_bounds`: Verifies `MaxDate`, `total_svs = 266`, `NumPlaces >= 1`, `MinValue >= 0`, and rate bounds (`MaxValue <= 100` for `UnemploymentRate_Person*`) across all 266 active recurring population, labour force, and life expectancy indicators.
        *   `check_census_and_survey_indicators_bounds`: Verifies `MaxDate >= 2016`, `total_svs = 587`, `NumPlaces >= 1`, and `MinValue >= 0` across all 587 Census health condition, biennial household income, and historical state age-bracket indicators.

---

## 3. Automated Import

This import is configured for automated weekly execution in `manifest.json`.

### Automated Steps
1. The automated job triggers on cron schedule `0 5 * * 1` configured in `manifest.json`.
2. `download_script.py` queries the ABS SDMX API and publication endpoints and populates `input_files/*` with raw source files.
3. `process.py` stages `input_files/*` and runs `stat_var_processor.py` with `--parallelism=2` to generate `output_files/australia_statistics_output.csv` and `output_files/australia_statistics_output.tmcf`.
4. Validation rules in `validation_config.json` are evaluated before publication.

---

## 4. Script Execution Details

To run the import pipeline locally from `statvar_imports/australia_statistics/`:

### Download the Data

```bash
python3 download_script.py
```

### Process the Data

```bash
python3 process.py \
  --input_data="input_files/*" \
  --pv_map=australia_statistics_pv_map.csv \
  --config_file=australia_statistics_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=output_files/australia_statistics_output \
  --output_counters=counters/australia_statistics_counters.csv \
  --parallelism=2
```

### Run Sample Integration Test

```bash
python3 ../../tools/statvar_importer/stat_var_processor.py \
  --input_data=test_data/sample_input.csv \
  --pv_map=australia_statistics_pv_map.csv \
  --config_file=australia_statistics_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=test_data/sample_expected_output
```

### Run Unit Tests

```bash
python3 -m unittest discover -s . -p "*_test.py" -v
```
