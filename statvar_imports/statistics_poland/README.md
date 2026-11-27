# Statistics Poland (GUS) Demographics Import

## Overview
- **Import Name:** `statistics_poland`
- **Import Type:** Automated (Scheduled via Cloud Batch cron: `30 11 * * 3`)
- **Curator:** `support@datacommons.org`

This import processes demographic population statistics for Poland from the official Central
Statistical Office of Poland (Główny Urząd Statystyczny - GUS) Bank Danych Lokalnych (BDL) API.

## Data Source
- **Source Portal:** https://bdl.stat.gov.pl/bdl/dane/podgrup/tablica
- **API Endpoint:** `https://bdl.stat.gov.pl/api/v1`
- **Subject ID:** `P3447` (Ludność wg grup wieku / Population by age group)
- **Place Types Covered (17 entities):**
  - Country level: `country/POL`
  - Voivodeship (`AdministrativeArea1`) level: 16 voivodeships (`14` `wikidataId/Q*` + `nuts/PL71` + `nuts/PL72`)
- **Variables Covered (108 StatVars):**
  - Age groups: `0-2`, `3-6`, `7-12`, `13-15`, `16-19`, `20-24`, `25-34`, `35-44`, `45-54`,
    `55-64`, `65 and more`, `total`
  - Gender: `males`, `females`, `total`
  - Residence Classification: `in urban areas`, `in rural areas`, `total`
- **Temporal Coverage:** Queries `2003` through `current_year + 1` (currently `2025`); `StatisticsPoland_pvmap.csv` pre-maps years `2003–2050` and `download_input_data.py` asserts every downloaded year is mapped in the PVMap.

## Configuration & Credentials
- **API Quota & Secret Manager:** `download_input_data.py` queries `/api/v1/data/by-unit/{unit_id}` in
  50-variable batches (~37 HTTP GET requests per full run), staying well under GUS BDL's anonymous
  `100 req / 15m` limit without requiring credentials. In Cloud Batch, if higher quota is desired,
  provision the key in GCP Secret Manager and set `BDL_API_SECRET_RESOURCE` (e.g.
  `projects/datcom-import-automation-prod/secrets/statistics-poland-bdl-api-key/versions/latest`).
  **Do NOT pass `BDL_API_KEY` via `ExecutorConfig.user_script_env`**, because
  `import-automation/executor/main.py` logs `Import config` in cleartext to Cloud Logging. For local
  CLI runs only, `BDL_API_KEY` may be exported:
  ```bash
  export BDL_API_KEY="<your-gus-bdl-api-key>"
  ```
- **Canonical Output Schema:** `download_input_data.py` constructs the 17 `(Code, Name)` rows and all
  108 `(Age, Sex, Location)` columns directly from canonical constants (optional GCS override via
  `BDL_GCS_TEMPLATE_PATH`), enforcing full batch/unit/age-cohort completeness across all downloaded
  years before atomically updating `source_files/`.
- **StatVar Resolution:** All 108 StatVars are pre-registered in Data Commons
  (`https://github.com/datacommonsorg/schema/blob/main/stat_vars/poland_stat_vars.mcf` plus base
  schema): `45 / 108` resolve offline from `gs://unresolved_mcf/scripts/statvar/stat_vars.mcf` and
  `63 / 108` Polish functional age-cohort StatVars resolve via live `api.datacommons.org`
  reconciliation, emitting `0` runtime-minted StatVars.

## Processing Instructions

### 1. Download and Preprocess Source Files
Run from the repository root:
```bash
python3 statvar_imports/statistics_poland/download_input_data.py
```
This queries the GUS BDL API and writes annual input CSV files into
`statvar_imports/statistics_poland/source_files/StatisticsPoland_input_<year>.csv`.

### 2. Run StatVarProcessor (Main Data Run)
```bash
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data='statvar_imports/statistics_poland/source_files/*.csv' \
  --pv_map=statvar_imports/statistics_poland/StatisticsPoland_pvmap.csv \
  --output_path=statvar_imports/statistics_poland/StatisticsPoland_output \
  --config_file=statvar_imports/statistics_poland/StatisticsPoland_metadata.csv \
  --output_counters=\
statvar_imports/statistics_poland/counters/StatisticsPoland_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

### 3. Run StatVarProcessor on Test Data
```bash
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/statistics_poland/test/StatisticsPoland_input.csv \
  --pv_map=statvar_imports/statistics_poland/StatisticsPoland_pvmap.csv \
  --output_path=statvar_imports/statistics_poland/test/StatisticsPoland_output \
  --config_file=statvar_imports/statistics_poland/StatisticsPoland_metadata.csv \
  --output_counters=\
statvar_imports/statistics_poland/test/StatisticsPoland_output_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

## Testing
Run the hermetic unit tests via the repository test runner:
```bash
./run_tests.sh -p statvar_imports/statistics_poland
```

## Validation & Quality Rules
Validation is configured in `validation_config.json` (plus repository defaults such as
`check_deleted_records_percent` at `threshold: 0.1%`):
1. `check_all_statvars_freshness` (`SQL_VALIDATOR`): Asserts
   `COALESCE(TRY_CAST(MaxDate AS INTEGER), 0) >= EXTRACT(YEAR FROM CURRENT_DATE - INTERVAL '6 months') - 1 AND total_svs = 108`
   (with an `EMPTY_STATS_GUARD` row so empty/null `stats` tables fail loudly).
2. `check_min_date_consistent` (`SQL_VALIDATOR`): Asserts
   `COALESCE(CAST(MinDate AS VARCHAR), '') = '2003' AND total_svs = 108` (with `EMPTY_STATS_GUARD`).
3. `check_max_date_consistent` (`MAX_DATE_CONSISTENT`): Enforces uniform `MaxDate` across all 108 StatVars.
4. `check_num_places_count` (`NUM_PLACES_COUNT`): Enforces `17` places (`country/POL` + 16 `AdministrativeArea1` voivodeships) per StatVar.
5. `check_num_observations` (`NUM_OBSERVATIONS_CHECK`): Enforces `>= 391` observations per StatVar (`17 places x 23 years`).
