# Bulgaria Demographics Dataset

## 1. Overview
This dataset contains demographic and population census information for Bulgaria sourced directly from the National Statistical Institute (NSI) of Bulgaria. It provides foundational demographic statistics including population counts broken down by 28 administrative districts, age groups (0 to 100+ years), place of residence (Urban/Rural/Total), and sex (Male/Female/Total).

- **Import Name**: `Bulgaria_Census`
- **Import Type**: `Automated`
- **Curator**: `support@datacommons.org`, `abhishekjaisw@google.com`
- **Schedule**: Weekly (`0 10 * * 1`)

## 2. Data Source
- **Authority**: National Statistical Institute (NSI) of Bulgaria
- **Source URL**: https://www.nsi.bg/en/statistical-data/206/649
- **Coverage**: All 28 districts of Bulgaria and national level (`country/BGR`), 2001 to present (annual series).

## 3. Automated Ingestion Workflow

The import is fully automated via scheduled Cloud Batch / Cloud Run execution:

### 3.1 Portal Monitoring & Download (`download_current_year_data.py`)
1. **Live Portal Check**: Queries https://www.nsi.bg/en/statistical-data/206/649 for the latest published reference year.
2. **GCS Inspection**: Checks `gs://unresolved_mcf/country/Bulgaria/input_files/` to see if `BulgariaNSI_Demographics_Year_input_{YEAR}.csv` is already staged. If present, it logs that the data is up to date and exits cleanly.
3. **Parsing & Formatting**: When a new year's release is detected, it parses the HTML table, formats it into the standard single-year CSV schema (matching the Google Sheet layout), validates row counts and arithmetic (Total = Urban + Rural = Male + Female), and uploads directly to GCS.

### 3.2 Automated Ingestion Workflow (`download.sh` & `stat_var_processor.py`)
1. **Download Step (`download.sh`)**: Pulls all staged input CSVs from `gs://unresolved_mcf/country/Bulgaria/input_files/*.csv` into local `input_files/` and automatically sanitizes quotes, age hyphens, and non-breaking spaces.
2. **Transform (`stat_var_processor.py`)**: Runs `stat_var_processor.py` for both Annual and Historical datasets:
   - Annual Refresh: transforms `input_files/BulgariaNSI_Demographics_Year_input_*.csv` into `output/BulgariaNSI_Demographics.csv` and `.tmcf`.
   - Historical Multi-Decade: transforms `input_files/BulgariaNSI_Demographics_2001to2010_input.csv`, `BulgariaNSI_Demographics_2011_2022_2023_input.csv`, and `..._2012to2021_input.csv` into `output/BulgariaNSI_Demographics_history.csv` and `.tmcf`.
3. **Resolution & Validation (`genmcf`, differ, import_validation)**:
   - Resolves nodes via `genmcf`.
   - Compares against baseline version in GCS using `ImportDiffer`.
   - Validates freshness (`MaxDate >= '2021'`) and checks deleted records threshold ($\le 0.1\%$) per `validation_config.json`.

## 4. Running the Data Processor Locally

To run the pipeline locally from the `data` repository root:

```bash
# 1. Fetch staged input files and sanitize spaces/asterisks
bash statvar_imports/Bulgaria_NSI_Demographics/download.sh

# 2. Process historical multi-decade files (2001 to 2021)
.env/bin/python tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/BulgariaNSI_Demographics_2001to2010_input.csv,input_files/BulgariaNSI_Demographics_2011_2022_2023_input.csv,input_files/BulgariaNSI_Demographics_2012to2021_input.csv \
  --pv_map=BulgariaNSI_Demographics_history_pvmap.csv \
  --config_file=BulgariaNSI_Demographics_history_metadata.csv \
  --output_path=output/BulgariaNSI_Demographics_history \
  --output_counters=counters/BulgariaNSI_Demographics_history_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# 3. Process annual demographic refresh files (2024, 2025, ...)
.env/bin/python tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/BulgariaNSI_Demographics_Year_input_*.csv \
  --pv_map=BulgariaNSI_Demographics_pvmap.csv \
  --config_file=BulgariaNSI_Demographics_metadata.csv \
  --output_path=output/BulgariaNSI_Demographics \
  --output_counters=counters/BulgariaNSI_Demographics_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

## 5. Validation Configuration
`validation_config.json` enforces:
- `check_all_statvars_freshness`: SQL validator verifying that all active StatVars meet `MaxDate >= '2021'` and `total_svs > 0`.
- `check_deleted_records_percent`: Ensures deleted records do not exceed `0.1%`.

