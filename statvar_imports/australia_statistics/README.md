# AustraliaStatistics (`statvar_imports/australia_statistics`)

## 1. Overview
This import ingests demographic, health, household income, life expectancy, and monthly labour force statistics for **Australia (`country/AUS`)** and its **8 States and Territories** (`wikidataId/Q3224`, `wikidataId/Q36687`, `wikidataId/Q36074`, `wikidataId/Q35715`, `wikidataId/Q3206`, `wikidataId/Q34366`, `wikidataId/Q3235`, `wikidataId/Q3258`) from the **Australian Bureau of Statistics (ABS)**:

- **Labour Force, Australia (ABS Cat. 6202.0):** Monthly employment, unemployment, and unemployment rate by sex (`1978-02` to latest monthly release) across `6202001.xlsx` (Australia) and `6202004.xlsx`–`6202011.xlsx` (8 States/Territories).
- **Life Tables, Australia (ABS Cat. 3302.0.55.001):** Life expectancy by single year of age (`0`–`99`) and sex (`1890` to latest 3-year period) and by State/Territory (`1971` to latest 3-year period) from `3302055001DO001` and `3302055001DO002`.
- **Census of Population and Housing (`1901`–`2021`):** Historical and 2021 Census population counts by age group and sex for Australia and its States/Territories.
- **National Health Survey (`2001`–`2022`):** Long-term health conditions (arthritis, asthma, cancer, dementia, diabetes, heart disease, kidney disease, lung conditions, mental health conditions, stroke) by age group, sex, and State/Territory.
- **Household Income and Wealth, Australia (`2008`–`2020`):** Weekly household income by income quintile and decile.

## 2. Pipeline Architecture
- `preprocess_abs_labour_force.py`: Discovers the latest monthly release at `https://www.abs.gov.au/statistics/labour/employment-and-unemployment/labour-force-australia/latest-release`, downloads `6202001.xlsx` and `6202004.xlsx`–`6202011.xlsx` using `requests.Session()` with retries and timeout, extracts the `Original` series from sheet `Data1`, and merges new monthly observations into `intermediate_files/aus_employment_int.csv` while preserving historical baseline records (`1978-02`–`2023-01`).
- `preprocess_abs_life_expectancy.py`: Discovers the latest 3-year Life Tables release at `https://www.abs.gov.au/statistics/people/population/life-expectancy/latest-release`, downloads `3302055001DO001` and `3302055001DO002`, and appends new 3-year period columns (`2016-2018` through `2022-2024+`) to `intermediate_files/life_expectancy_age_aus.csv` and `intermediate_files/life_expectancy_aus_states.csv`.
- `australia_import.py`: Orchestrates the ABS download/merge steps, runs `tools/statvar_importer/stat_var_processor.py` across all 8 intermediate tables using `intermediate_files/aus_config.conf` and `intermediate_files/existing_stat_vars.mcf`, emits per-table counter files to `counters/`, and stages the 2021 Census CSV/TMCF files and `schema.mcf` into `output_files/`.
- `run.sh`: Entrypoint script invoked by the Data Commons Import Automation framework (`manifest.json`).

## 3. Running Locally
```bash
bash statvar_imports/australia_statistics/run.sh
```

To run unit tests:
```bash
./run_tests.sh -p statvar_imports/australia_statistics
```
