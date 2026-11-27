# India_NationalAccountsStatistics

## Overview

- **Description**: India National Accounts Statistics (annual national GDP, sectoral Gross Value Added, and state/union territory Gross State Domestic Product and growth rates) at current (nominal) and constant (`2011-12` base year) prices.
- **Source Portal**: [MoSPI eSankhyiki — National Accounts Statistics (NAS)](https://esankhyiki.mospi.gov.in/macroindicators?product=nas)
- **REST API Endpoint**: `https://api.mospi.gov.in/api/nas/getNasData` (unauthenticated JSON REST API, `limit=200` pagination, `series=Current`, `base_year=2011-12`, `frequency_code=1`):
  - `indicator_code=5`: Annual Gross Domestic Product (GDP, `₹ Crore`)
  - `indicator_code=1`: Annual Gross Value Added by economic sector (GVA, `₹ Crore`)
  - `indicator_code=23`: Annual State/UT Gross State Domestic Product (GSDP, `₹ Crore`)
  - `indicator_code=26`: Annual State/UT GSDP Growth Rate (`%`)
- **GCS Historical Baseline**: `gs://unresolved_mcf/india_mospi/economy/baseline/`
- **Import Type**: Automated Refresh (`manifest.json`, scheduled weekly on Mondays at 03:00 UTC)
- **Data Coverage**: `2012` to `2026`+ (`P1Y` Indian fiscal years mapped dynamically to ending calendar year, e.g. `2011-12 -> 2012`, `2025-26 -> 2026`) across `country/IND` and 34 Indian states/union territories (34 StatVars).

## Directory Layout

- `download.py`: Fetches live records from the MoSPI eSankhyiki NAS REST API (using `_LegacyTLSAdapter` with `ssl.OP_LEGACY_SERVER_CONNECT` and full TLS certificate verification), writes unmodified raw JSON pages to `raw_source/`, loads the 9 unmodified legacy `2026-02-02` production CSVs staged in GCS (repairing the `GSDP_CONSTANT.csv` Ladakh/Puducherry misattribution bug in memory), merges live data on top, and atomically writes the 5 tidy input CSVs to `input_files/`.
- `download_test.py`: Hermetic unit tests for `download.py` (pagination, retries, GVA filtering, legacy baseline loading, Ladakh/Puducherry repair, and merge).
- `india_nas_common_pvmap.csv`: Shared dynamic fiscal-year (`YYYY-YY -> YYYY+1`) and MoSPI revision `measurementMethod` mappings.
- `india_nas_gdp_pvmap.csv`: National GDP PVMap (`unit=INR`, `#Multiply=10000000`).
- `india_nas_gva_pvmap.csv`: National sectoral GVA PVMap for First Advance, Second Advance, Provisional, and Second Revised estimates.
- `india_nas_gva_third_revised_pvmap.csv`: Minimal 2-row override PVMap for GVA Third Revised Estimates preserving exact existing production StatVar DCIDs.
- `india_nas_gsdp_pvmap.csv`: State/UT GSDP PVMap (`CurrentPrice_WithBaseYear2011_12` / `ConstantPrice_WithBaseYear2011_12`, `unit=INR`, `#Multiply=10000000`).
- `india_nas_gsdp_growth_pvmap.csv`: State/UT GSDP Growth Rate PVMap (`statType=growthRate`, `unit=Percent`).
- `india_nas_common_metadata.csv`: Shared `stat_var_processor.py` configuration (`header_rows=1`, canonical `output_columns`).
- `india_nas_places.csv`: Verified place DCID mappings for India and all states/UTs (preserving AA1 UT IDs: `Chandigarh -> wikidataId/Q120971341`, `Delhi -> wikidataId/Q9357528`, `Ladakh -> wikidataId/Q200667`, `Puducherry -> wikidataId/Q66743`).
- `manifest.json`: Cloud Batch automation specification.
- `validation_config.json`: Import-specific freshness, StatVar count, place coverage, non-negative INR amount, and observation floor validation rules.
- `test_data/`: Representative raw API JSON sample (`nas_gsdp_raw_sample.json`) and paired `stat_var_processor.py` inputs and expected `.csv`/`.tmcf` outputs for all 5 streams.

## Additional Processing Beyond Schema Mapping

1. **Base-year pinning (`base_year=2011-12`)**: All 4 API queries and GSDP normalizers pin `base_year=2011-12` so MoSPI's `2022-23` rebased constant-price series is never mixed into `2011-12` `measurementMethod` facets.
2. **GVA hierarchy & revision filtering**: `download.py` filters `indicator_code=1` to top-level industry rows (`industry` non-empty, `subindustry` empty, `institutional_sector` empty) to prevent duplicate StatVarObservations from sub-industry and institutional-sector breakdowns, and routes `Third Revised Estimates` to `india_nas_gva_third_revised.csv` while keeping revisions aligned with existing `MeasurementMethodEnum` schema entries.
3. **Hybrid GCS baseline merge**: `indicator_code=23` and `indicator_code=26` currently omit 4 places present in production (`Assam`, `Haryana`, `Ladakh`, `Nagaland`). `download.py` merges non-empty live API cells onto the staged GCS baseline by primary key without overwriting populated baseline cells with `null`/empty API values, and drops rows where both `current_price` and `constant_price` are empty.
4. **Ladakh / Puducherry baseline repair**: When loading the unmodified legacy `GSDP_CONSTANT.csv` baseline in memory, `download.py` automatically repairs the verified `2026-02-02` corruption where an empty Ladakh row shifted all 27 constant-price observations for Puducherry (`wikidataId/Q66743`) onto Ladakh (`wikidataId/Q200667`).

## Prerequisites & One-Time Baseline Staging

Stage the 9 unmodified `2026-02-02` production CSVs directly into `gs://unresolved_mcf/india_mospi/economy/baseline/` (no preprocessing needed):

```bash
gcloud storage cp \
  "gs://unresolved_mcf/india_mospi/economy/20260202/*.csv" \
  gs://unresolved_mcf/india_mospi/economy/baseline/
```

## Running Locally

From this import directory (`statvar_imports/india_mospi/india_national_accounts_statistics/`), with `.env` activated:

```bash
# 1. Download raw JSONs from MoSPI NAS API and merge with GCS baseline
../../../.env/bin/python download.py

# 2. Run StatVarProcessor across all 5 tidy inputs
../../../.env/bin/python ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/india_nas_gdp.csv \
  --pv_map=india_nas_common_pvmap.csv,india_nas_gdp_pvmap.csv \
  --config_file=india_nas_common_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=output/india_nas_gdp \
  --output_counters=counters/india_nas_gdp_counters.csv

../../../.env/bin/python ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/india_nas_gva.csv \
  --pv_map=india_nas_common_pvmap.csv,india_nas_gva_pvmap.csv \
  --config_file=india_nas_common_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=output/india_nas_gva \
  --output_counters=counters/india_nas_gva_counters.csv

../../../.env/bin/python ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/india_nas_gva_third_revised.csv \
  --pv_map=india_nas_common_pvmap.csv,india_nas_gva_pvmap.csv,india_nas_gva_third_revised_pvmap.csv \
  --config_file=india_nas_common_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=output/india_nas_gva_third_revised \
  --output_counters=counters/india_nas_gva_third_revised_counters.csv

../../../.env/bin/python ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/india_nas_gsdp.csv \
  --pv_map=india_nas_common_pvmap.csv,india_nas_gsdp_pvmap.csv \
  --config_file=india_nas_common_metadata.csv \
  --places_resolved_csv=india_nas_places.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=output/india_nas_gsdp \
  --output_counters=counters/india_nas_gsdp_counters.csv

../../../.env/bin/python ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/india_nas_gsdp_growth.csv \
  --pv_map=india_nas_common_pvmap.csv,india_nas_gsdp_growth_pvmap.csv \
  --config_file=india_nas_common_metadata.csv \
  --places_resolved_csv=india_nas_places.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=output/india_nas_gsdp_growth \
  --output_counters=counters/india_nas_gsdp_growth_counters.csv
```

## Running Tests and Lint

From the repository root:

```bash
./run_tests.sh -p statvar_imports/india_mospi/india_national_accounts_statistics
./run_tests.sh -l
```

## Rebased `2022-23` Series Note

MoSPI launched a rebased `2022-23` constant-price GDP/GVA series in February 2026 (`base_year=2022-23` on `ic=1` and `ic=5`). To onboard it without contaminating `2011-12` constant-price observations, first add distinct `MeasurementMethodEnum` nodes (e.g., `MOSPIProvisionalEstimates_BaseYear2022_23`, `MOSPIFirstRevisedEstimates_BaseYear2022_23`, `MOSPIFinalEstimates_BaseYear2022_23`) in `third_party/datacommons/schema/core/measurement_methods.mcf`, then add a separate `2022-23` input stream and PVMap.
