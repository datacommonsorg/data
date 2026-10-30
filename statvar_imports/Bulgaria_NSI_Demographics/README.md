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
- **Coverage**: All 28 districts of Bulgaria and national level (`country/BGR`). Multi-decade historical observations (`2001`–`2023`) are preserved statically in Data Commons storage, while this automated pipeline refreshes the annual series (`2024` to present).

## 3. Automated Ingestion Workflow

The annual refresh is automated via scheduled Cloud Batch / Cloud Run execution:

### 3.1 Portal Monitoring & Download (`download_current_year_data.py`)
1. **Live Portal Check**: Queries https://www.nsi.bg/en/statistical-data/206/649 for the latest published reference year.
2. **GCS Inspection**: Checks `gs://unresolved_mcf/country/Bulgaria/input_files/` to see if `BulgariaNSI_Demographics_Year_input_{YEAR}.csv` is already staged. If present, it logs that the data is up to date and exits cleanly.
3. **Parsing & Formatting**: When a new year's release is detected, it parses the HTML table, formats it into the standard single-year CSV schema, validates row counts and arithmetic (`Total = Urban + Rural = Male + Female`), and uploads directly to GCS.

> **Operational Note on Cloudflare Protection**: The live NSI portal (`nsi.bg`) enforces Cloudflare bot protection, which returns HTTP 403 Forbidden to requests originating from cloud/datacenter IP ranges. When invoked with `--allow-staged-fallback` in scheduled runs, `download_current_year_data.py` detects this and falls back to existing verified files staged in `gs://unresolved_mcf/country/Bulgaria/input_files/`. When a new annual release is published by NSI, it can be staged to GCS via an authorized proxy or manual upload.

### 3.2 Automated Ingestion Workflow (`download.sh` & `stat_var_processor.py`)
1. **Download Step (`download.sh`)**: Pulls all staged annual input CSVs (`BulgariaNSI_Demographics_Year_input_*.csv`) from `gs://unresolved_mcf/country/Bulgaria/input_files/` into local `input_files/` (preserved untouched for `source_files`), writes sanitized copies (normalizing quotes, non-breaking spaces, and hyphens) to `sanitized_input_files/`, and validates internal horizontal and vertical arithmetic across all 29 districts and 22 age cohorts.
2. **Transform (`stat_var_processor.py`)**: Transforms `sanitized_input_files/BulgariaNSI_Demographics_Year_input_*.csv` using `BulgariaNSI_Demographics_pvmap.csv` and `BulgariaNSI_Demographics_metadata.csv` into `output/BulgariaNSI_Demographics.csv` and `.tmcf`.
3. **Resolution & Validation (`genmcf`, differ, import_validation)**:
   - Resolves nodes via `genmcf`.
   - Compares against baseline version in GCS using `ImportDiffer`.
   - Validates uniform `MaxDate`, relative 1-year publication lag freshness (`TRY_CAST(MaxDate AS INTEGER) >= year(current_date) - 1`), and deleted records threshold ($\le 0.1\%$) per `validation_config.json`.

## 4. Running the Data Processor Locally

To run the pipeline and unit tests locally, navigate to the import directory:

```bash
cd statvar_imports/Bulgaria_NSI_Demographics

# 0. Check NSI portal for new annual releases (or verify staged GCS files)
../../.env/bin/python download_current_year_data.py --allow-staged-fallback

# 1. Fetch staged annual input files and validate format/arithmetic
bash download.sh

# 2. Process annual demographic refresh files (2024, 2025, ...)
../../.env/bin/python ../../tools/statvar_importer/stat_var_processor.py \
  --input_data=sanitized_input_files/BulgariaNSI_Demographics_Year_input_*.csv \
  --pv_map=BulgariaNSI_Demographics_pvmap.csv \
  --config_file=BulgariaNSI_Demographics_metadata.csv \
  --output_path=output/BulgariaNSI_Demographics \
  --output_counters=counters/BulgariaNSI_Demographics_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# 3. Run unit tests (from repository root)
cd ../..
./run_tests.sh -p statvar_imports/Bulgaria_NSI_Demographics
```

## 5. Validation Configuration
`validation_config.json` enforces:
- `check_max_date_consistent`: Ensures `MaxDate` is uniform across all 207 generated StatVars.
- `check_all_statvars_freshness`: SQL validator verifying that all active StatVars meet `TRY_CAST(MaxDate AS INTEGER) >= year(current_date) - 1`.
- `check_deleted_records_percent`: Ensures deleted records do not exceed `0.1%`.
