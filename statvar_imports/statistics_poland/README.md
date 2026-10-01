# Statistics Poland (GUS) Demographics Import

## Overview
- **Import Name:** `statistics_poland`
- **Import Type:** Automated (Scheduled via Cloud Batch cron: `0 0 1 1,4,7,10 *`)
- **Curator:** `support@datacommons.org`

This import processes demographic population statistics for Poland from the official Central
Statistical Office of Poland (Główny Urząd Statystyczny - GUS) Bank Danych Lokalnych (BDL) API.

## Data Source
- **Source Portal:** https://bdl.stat.gov.pl/bdl/dane/podgrup/tablica
- **API Endpoint:** `https://bdl.stat.gov.pl/api/v1`
- **Subject ID:** `P3447` (Ludność wg grup wieku / Population by age group)
- **Place Types Covered:**
  - Country level: `country/POL`
  - Voivodship (province) level: `nuts/PL*` (16 voivodships)
- **Variables Covered:**
  - Age groups: `0-2`, `3-6`, `7-12`, `13-15`, `16-19`, `20-24`, `25-34`, `35-44`, `45-54`,
    `55-64`, `65 and more`
  - Gender: `males`, `females`, `total`
  - Residence Classification: `in urban areas`, `in rural areas`, `total`
- **Temporal Coverage:** Dynamic from 2003 through `current_year + 1` (currently 2025).

## Configuration & Credentials
- **API Key:** GUS BDL API key is configured with a default client key and can be overridden
  via the `BDL_API_KEY` environment variable:
  ```bash
  export BDL_API_KEY="<your-gus-bdl-api-key>"
  ```
- **Template CSV:** Download script loads the reference column structure from GCS:
  `gs://datcom-prod-imports/statvar_imports/statistics_poland/poland_data_sample/`
  `StatisticsPoland_input.csv`
  with an automatic offline fallback to `test/StatisticsPoland_input.csv`.
- **StatVar MCF:** Canonical StatVars are resolved against:
  `gs://unresolved_mcf/scripts/statvar/stat_vars.mcf`

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
Run the hermetic unit tests via pytest:
```bash
.env/bin/python -m pytest statvar_imports/statistics_poland -v
```

## Validation & Quality Rules
Validation is configured in `validation_config.json`:
1. `check_all_statvars_freshness` (`SQL_VALIDATOR`): Asserts `MaxDate >= '2024'` across all active
   statistical variables in `stats`.
2. `check_max_date_consistent` (`MAX_DATE_CONSISTENT`): Enforces uniform MaxDate across all
   StatVars.
3. `check_deleted_records_percent` (`DELETED_RECORDS_PERCENT`): Enforces that deleted observations
   do not exceed `0.1%`.
4. `check_lint_error_count` (`LINT_ERROR_COUNT`): Enforces 0 lint errors (`threshold: 0`).

## Troubleshooting & Operations
- **HTTP 429 / Rate Limiting:** The script uses `requests.Session` with `urllib3.util.Retry`
  (backoff factor 1.5, status forcelist 429, 500, 502, 503, 504, 10 retries).
- **API Key Expiration:** If the API key expires, register for a new key on GUS BDL and export it
  via `export BDL_API_KEY="..."`.
- **GCS Offline Access:** If executing in an environment without GCS access, the download script
  automatically falls back to `test/StatisticsPoland_input.csv` for column structure.

