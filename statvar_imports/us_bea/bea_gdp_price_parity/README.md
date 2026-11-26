# BEA Regional Price Parities & County/Metro GDP (`BEAGDPPriceParity`)

## Overview & Dataset Coverage

This import (`BEAGDPPriceParity`) automates US Bureau of Economic Analysis (BEA) Regional Price Parities (RPPs) and County/Metropolitan Area GDP summary series across US national, state, MSA (`geoId/C*`), and county (`geoId/<5-digit FIPS>`) geographies using **`download.py` + `stat_var_processor.py` directly (no Python preprocessing script)**:

- **Live BEA Regional ZIP Archives** (`https://apps.bea.gov/regional/zip/` -> `input_files/raw/`):
  - `SARPP.zip` (`SARPP_STATE_*.csv`): State & US Regional Price Parities (`2008–present`) across All Items (`LineCode=1`), Goods (`LineCode=2`), Services: Housing (`LineCode=3`), Services: Utilities (`LineCode=4`), and Services: Other (`LineCode=5`).
  - `MARPP.zip` (`MARPP_MSA_*.csv`): Metropolitan Statistical Area RPPs (`2008–present`).
  - `CAGDP1.zip` (`CAGDP1__ALL_AREAS_*.csv`): County Real GDP (`grossDomesticProduct`, `LineCode=1`, `2001–present`, scaled from thousands of chained dollars via `#Multiply: 1000`).
  - `CAGDP11.zip` (`CAGDP11__ALL_AREAS_*.csv`): County Real GDP annual percent change (`dc/p9w3tzjzyqrr`, `LineCode=1`, `2002–present`).
- **Historical MSA GDP Baselines (`historic/` GCS folder)**:
  - Pre-generated resolved node MCF (`table_mcf_nodes_bea_metro_gdp_output.mcf`, `6,511` observations across `383` MSAs, `2012–2017`) is stored under `<import_bucket>/statvar_imports/us_bea/bea_gdp_price_parity/BEAGDPPriceParity/historic/` and automatically copied into `<version>/historic/genmcf/` on each run by `ImportExecutor._ingest_historic_data`, preserving discontinued standalone BEA MSA GDP series (`grossDomesticProduct` in `2012`, `dc/c3wwfwyx45v5h` and `dc/p9w3tzjzyqrr` in `2013–2017`, and `nominalGrossDomesticProduct` in `2012–2017`) with `0.00%` deletion across all `28,302` production observations.

## Prerequisites & Working Directory

1. Initialize the repository virtual environment from the repository root:
   ```bash
   ./run_tests.sh -r
   ```
2. Configure Application Default Credentials (`gcloud auth application-default login`) for read access to `gs://unresolved_mcf/scripts/statvar/stat_vars.mcf`.
3. All `manifest.json` script commands execute with `statvar_imports/us_bea/bea_gdp_price_parity/` as the working directory.

## Pipeline Architecture & PVMap Rules

1. **`download.py`**:
   - Fetches `MARPP.zip`, `SARPP.zip`, `CAGDP1.zip`, and `CAGDP11.zip` over HTTPS with connection reuse, HTTP status logging, `zipfile.is_zipfile()` validation (catching soft-404 HTML responses), transient-only retry/backoff, atomic writes for raw `.zip` and extracted `.csv` files, and cleanup of superseded year-ranged CSVs.
2. **`stat_var_processor.py` (`bea_*_pvmap.csv`, `bea_years_pvmap.csv`, `bea_*_metadata.csv`)**:
   - **RPP (`bea_rpp_pvmap.csv` + `bea_years_pvmap.csv` + `bea_rpp_metadata.csv`)**: Maps `SARPP_STATE_*.csv` and `MARPP_MSA_*.csv` (`latin1`, `mapped_columns=5`), using `#Eval` + `#Filter` on `TableName`/`LineCode` to resolve `"00000"` -> `country/USA`, state `XX000` -> `geoId/XX`, and MSA `10000 <= XXXXX < 90000` -> `geoId/CXXXXX` while excluding synthetic `"00999"` (*"United States (Nonmetropolitan Portion)"*) and BEA regions (`91000–98000`).
   - **County GDP (`bea_county_gdp_pvmap.csv` + `bea_years_pvmap.csv` + `bea_county_gdp_metadata.csv`)**: Maps `CAGDP1__ALL_AREAS_*.csv` (`CAGDP1` + `LineCode:1` -> `#Multiply=1000`, `unit=dcs:USDollar`, `grossDomesticProduct`) and `CAGDP11__ALL_AREAS_*.csv` (`CAGDP11` + `LineCode:1` -> unitless `dc/p9w3tzjzyqrr`), short-circuiting non-summary rows (`Quantity index`, `Thousands of dollars`, `Percentage points`) via `#IgnoreRow` with `mapped_columns="4,5,8"` and `word_delimiter=""` so chained-dollar reference-year updates never collide with year column keys.
3. **Historical MSA GDP (`historic/` GCS folder)**:
   - Historical `2012–2017` MSA GDP observations are frozen in `<import_bucket>/statvar_imports/us_bea/bea_gdp_price_parity/BEAGDPPriceParity/historic/table_mcf_nodes_bea_metro_gdp_output.mcf` and ingested automatically into `<version>/historic/genmcf/` by the import executor (not downloaded or re-processed in `download.py` / `manifest.json`).

## Important Files

- `manifest.json`: Cloud Batch specification (`BEAGDPPriceParity`), weekly schedule (`0 6 * * 1`), 3 `stat_var_processor.py` runs (RPP, County GDP, County GDP Growth), wildcard `node_mcf` `import_inputs`, and `source_files` (`input_files/raw/*`, `*_pvmap.csv`, `*_metadata.csv`, `counters/*.csv`, `validation_config.json`).
- `download.py` / `download_test.py` / `test_data/{sample_input,sample_output}/`: Downloader, representative sample inputs and sample output `.csv`/`.tmcf` fixtures, and unit and PVMap/fixture structural tests.
- `bea_years_pvmap.csv`: Shared wide-format year-column mappings (`2001–2050`).
- `bea_rpp_pvmap.csv` / `bea_rpp_metadata.csv`: PVMap and metadata for live Regional Price Parities (`SARPP` & `MARPP`).
- `bea_county_gdp_pvmap.csv` / `bea_county_gdp_metadata.csv`: PVMap and metadata for live County GDP & Growth (`CAGDP1` & `CAGDP11`).
- `validation_config.json`: Scoped `MAX_DATE_CONSISTENT` check for RPP StatVars plus `SQL_VALIDATOR` freshness, minimum place/observation count, and RPP value-bound checks.

## Running & Testing Locally

From `statvar_imports/us_bea/bea_gdp_price_parity/` (using `.env/bin/python` initialized from the repository root):

```bash
../../../.env/bin/python download.py
../../../.env/bin/python ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/raw/SARPP_STATE_*.csv,input_files/raw/MARPP_MSA_*.csv \
  --pv_map=bea_rpp_pvmap.csv,bea_years_pvmap.csv \
  --config_file=bea_rpp_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=output_files/bea_rpp_output \
  --output_counters=counters/bea_rpp_counters.csv
../../../.env/bin/python ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/raw/CAGDP1__ALL_AREAS_*.csv \
  --pv_map=bea_county_gdp_pvmap.csv,bea_years_pvmap.csv \
  --config_file=bea_county_gdp_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=output_files/bea_county_gdp_output \
  --output_counters=counters/bea_county_gdp_counters.csv
../../../.env/bin/python ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/raw/CAGDP11__ALL_AREAS_*.csv \
  --pv_map=bea_county_gdp_pvmap.csv,bea_years_pvmap.csv \
  --config_file=bea_county_gdp_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=output_files/bea_county_gdp_growth_output \
  --output_counters=counters/bea_county_gdp_growth_counters.csv
```

Run unit tests and lint checks from the repository root:

```bash
./run_tests.sh -p statvar_imports/us_bea/bea_gdp_price_parity
./run_tests.sh -l
```

## Refresh Procedure

`BEAGDPPriceParity` runs weekly via Cloud Batch (`cron_schedule: "0 6 * * 1"`). On each refresh, `manifest.json` runs `download.py` followed by the three `stat_var_processor.py` commands, retains raw `.zip`/`.csv`, `*_pvmap.csv`, `*_metadata.csv`, `counters/*.csv`, and `validation_config.json` under `<version>/source_files/`, runs `dc-import genmcf`, validates `summary_report.csv` and differ outputs against `validation_config.json`, and copies historical MSA GDP node MCF files from `historic/` into `<version>/historic/genmcf/`.
