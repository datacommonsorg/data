# MOSPI_IndiaPLFS_DailyWages

## Overview

- **Description**: Average daily wage earnings (in INR) from casual labour work other than public works at the national (`country/IND`) and state/union territory levels in India, disaggregated by gender (`Male`, `Female`, total) and residence sector (`Rural`, `Urban`, combined).
- **Source Portal**: [MoSPI eSankhyiki — Periodic Labour Force Survey (PLFS)](https://esankhyiki.mospi.gov.in/macroindicators?product=plfs)
- **REST API Endpoint**: `https://api.mospi.gov.in/api/plfs/getData` (`indicator_code=7`, `frequency_code=1`, `year_type_code=1,2`)
- **GCS Historical Baseline**: `gs://unresolved_mcf/india_mospi/daily_wages/input_files/daily_wages_input.csv`
- **Import Type**: Automated Refresh (`manifest.json`, scheduled weekly)
- **Data Coverage**:
  - `2017-05` to `2024-02` (`P3M` quarterly breakdowns across Agriculture Years `2017-18`–`2023-24`)
  - `2022` to `2025`+ (`P1Y` Calendar Year series)

## Directory Layout

- `download.py`: Loads the historical baseline CSV from GCS, paginates live updates from the MoSPI eSankhyiki PLFS REST API (`limit=200`), merges records without losing historical observations, and writes `input_files/daily_wages_input.csv` atomically.
- `download_test.py`: Unit tests for pagination, retry/error propagation, baseline merging, and atomic CSV output.
- `daily_wages_pvmap.csv`: Property-value mappings for `stat_var_processor.py`.
- `daily_wages_metadata.csv`: Processor configuration parameters (`header_rows`, `output_columns`).
- `daily_wages_places.csv`: Resolved place DCID mappings for India and all states/UTs.
- `dailywages_stat_vars.mcf` & `dailywages_stat_vars_schema.mcf`: Custom `StatisticalVariable` and `WorkerOtherThanPublicWorker` schema definitions included via `"node_mcf": "*.mcf"`.
- `manifest.json`: Cloud Batch import automation specification.
- `validation_config.json`: Import validation rules (`0%` deleted records, uniform `MaxDate`, freshness lag check, non-negative values, observation count floor, and StatVar count check).
- `test_data/`: Sample input (`daily_wages_input.csv`) and expected output (`daily_wages_output.csv`, `daily_wages_output.tmcf`).

## Running Locally

From this import directory (`statvar_imports/india_mospi/plfs_wages/mospi_india_plfs_daily_wages/`), run using the repository's `.env` Python environment:

```bash
# 1. Download and merge GCS baseline + live MoSPI eSankhyiki API data
../../../../.env/bin/python download.py

# 2. Run StatVarProcessor
../../../../.env/bin/python ../../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/daily_wages_input.csv \
  --pv_map=daily_wages_pvmap.csv \
  --config_file=daily_wages_metadata.csv \
  --places_resolved_csv=daily_wages_places.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf,dailywages_stat_vars.mcf \
  --output_path=output/daily_wages_output \
  --output_counters=counters/daily_wages_counters.csv
```

## Running Tests

From the repository root:

```bash
./run_tests.sh -p statvar_imports/india_mospi/plfs_wages/mospi_india_plfs_daily_wages
```
