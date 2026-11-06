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

### 3.1 Portal Download, Preprocessing & Extra Processing (`download.sh` & `download_current_year_data.py`)
1. **GCS Sync**: `download.sh` fetches previously staged annual files (`BulgariaNSI_Demographics_Year_input_*`) from `gs://unresolved_mcf/country/Bulgaria/input_files/` into local `input_files/` using `gcloud storage cp`.
2. **Live Portal Download**: Invokes `download_current_year_data.py` (using `absl.flags`), which queries https://www.nsi.bg/en/statistical-data/206/649, saves the raw `.html` page (`BulgariaNSI_Demographics_Year_input_{YEAR}.html`) into `input_files/` for `source_files` archival and debugging, parses `<table class="nsit3">`, and writes the latest `BulgariaNSI_Demographics_Year_input_{YEAR}.csv` (always preferring fresh source data over cached GCS files).
3. **Extra Pre-Processing in Downloader**:
   - **Reference Year Extraction**: Parses the reference year (`AS OF 31.12.YYYY`) directly from `<div id="ttitle">` in the NSI HTML, and constructs the standardized 3-row header expected by `BulgariaNSI_Demographics_pvmap.csv`.
   - **Cell Text Normalization**: Strips non-breaking spaces (`\xa0`), removes trailing footnote asterisks (e.g., `AS OF 31.12.*`), removes trailing `.0` from numeric values, and normalizes age-cohort hyphen spacing (`1-4` -> `1 - 4`, `100+` -> `100 +`). Suppressed/empty cells (`'-'`) are strictly retained as `'-'` so `stat_var_processor.py` drops them via `statvar_dcid_ignore_values,"-"` in `BulgariaNSI_Demographics_metadata.csv` (never converted to `0`).
   - **Pre-Processor Arithmetic Consistency Validation**: Runs `_validate_horizontal_and_vertical_sums` on the generated CSV before upload:
     - *Horizontal Sums*: Enforces `Total = Urban + Rural` and `Total = Male + Female` on both district rows and cohort rows (skipping suppressed `'-'` cells).
     - *Vertical Sums*: Distinguishes district headers (starting with letters) from age cohort rows (starting with digits), groups cohorts under their respective districts, and checks that `District header == sum(age cohorts)` for all columns without suppressed cells.
     - *Justification*: `summary_report.csv` (the `stats` table evaluated by `SQL_VALIDATOR` in `validation_config.json`) only records aggregate `MinValue` and `MaxValue` per StatVar across all places. Consequently, per-district cross-column and cross-row arithmetic relationships cannot be verified in `validation_config.json` and must be validated in Python prior to running `stat_var_processor.py`.
4. **Sanitization**: Writes normalized copies of all annual CSVs into `sanitized_input_files/` while keeping the original downloaded files untouched in `input_files/` for `source_files`.

> **Operational Note on Cloudflare Protection**: The live NSI portal (`nsi.bg`) enforces Cloudflare bot protection, which returns HTTP 403 Forbidden to requests originating from cloud/datacenter IP ranges. When invoked with `--allow_staged_fallback` in scheduled runs, `download_current_year_data.py` detects this (as well as transient 5xx or connection errors) and falls back to existing verified files staged in `gs://unresolved_mcf/country/Bulgaria/input_files/`. When a new annual release is published by NSI, it can be staged to GCS via an authorized proxy or manual upload.

### 3.2 Transformation, Resolution & Validation (`stat_var_processor.py` & `validation_config.json`)
1. **Transform (`stat_var_processor.py`)**: Transforms `sanitized_input_files/BulgariaNSI_Demographics_Year_input_*.csv` using `BulgariaNSI_Demographics_pvmap.csv` (which maps annual header rows through `2050`) and `BulgariaNSI_Demographics_metadata.csv` into `output/BulgariaNSI_Demographics.csv` and `.tmcf`.
2. **Resolution & Validation (`genmcf`, differ, import_validation)**:
   - Resolves nodes via `genmcf`.
   - Compares against baseline version in GCS using `ImportDiffer`.
   - Validates uniform `MaxDate`, relative 1-year publication lag freshness (`TRY_CAST(MaxDate AS INTEGER) >= year(current_date) - 1`), place coverage (`NumPlaces >= 23`), StatVar coverage (`>= 207` StatVars), and deleted records threshold ($\le 0.1\%$) per `validation_config.json`.

## 4. Running the Data Processor Locally

To run the pipeline and unit tests locally, navigate to the import directory:

```bash
cd statvar_imports/Bulgaria_NSI_Demographics

# 1. Fetch staged annual input files, check live NSI portal, and sanitize CSVs
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
- `check_num_places_coverage`: SQL validator verifying that all StatVars cover the expected minimum number of places (`NumPlaces >= 23` for non-centenarian cohorts, `NumPlaces >= 20` for `100+` cohorts).
- `check_statvar_and_age_cohort_coverage`: SQL validator verifying all 207 demographic StatVars are generated with non-negative values.
(Deleted records threshold `<= 0.1%`, empty import, missing refs, and lint checks are enforced via the global `tools/import_validation/validation_config.json`.)
