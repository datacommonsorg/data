# US BEA GDP and Regional Price Parities (`BEAGDPPriceParity`)

## Overview
This directory contains the unified ingestion pipeline for the **Bureau of Economic Analysis (BEA)** County, Metropolitan Area, and State Gross Domestic Product (GDP) and Regional Price Parities (RPP) datasets (`BEAGDPPriceParity`).

It consolidates the legacy Google3 BEA scripts (`datacommons/mcf/bea/{bea_county_gdp.py,bea_county_gdp_growth.py,bea_metro_gdp.py,bea_metro_nominal_gdp.py,marpp.py}`) into a single deterministic processor (`process_bea_gdp_rpp.py`) backed by a unified template MCF (`bea_gdp_rpp.tmcf`) and schema MCF (`bea_rpp_statvars.mcf`).

## Source Data & Coverage
The processor ingests four official BEA regional bulk ZIP archives from `https://apps.bea.gov/regional/zip/`:
1. **`CAGDP1.zip`** (`CAGDP1__ALL_AREAS_2001_2024.csv`): County, State, and US Gross Domestic Product summary (`2001`–`2024`):
   - `LineCode == 1`: Real GDP in thousands of chained 2017 dollars (scaled by `* 1000` to `USDollar`), emitted for both `dcs:grossDomesticProduct` and `dcid:dc/c3wwfwyx45v5h` with `measurementMethod: dcs:BEASurvey`.
   - `LineCode == 3`: Current-dollar (Nominal) GDP in thousands of dollars (scaled by `* 1000` to `USDollar`), emitted for `dcs:nominalGrossDomesticProduct` with `measurementMethod: dcs:BEAGDPMeasure`.
2. **`CAGDP11.zip`** (`CAGDP11__ALL_AREAS_2002_2024.csv`): Annual percent change in Real GDP (`2002`–`2024`):
   - `LineCode == 1`: Real GDP growth rate (`dcid:dc/p9w3tzjzyqrr`, `measurementMethod: dcs:BEASurvey`).
3. **`MARPP.zip`** (`MARPP_MSA_2008_2024.csv`): Metropolitan Statistical Area Regional Price Parities (`2008`–`2024`, `geoId/C<5-digit MSA code>`).
4. **`SARPP.zip`** (`SARPP_STATE_2008_2024.csv`): State Regional Price Parities (`2008`–`2024`, `geoId/<2-digit state FIPS>`):
   - `LineCode == 1`: `dcid:RegionalPriceParity_AllItems`
   - `LineCode == 2`: `dcid:RegionalPriceParity_Goods`
   - `LineCode == 3`: `dcid:RegionalPriceParity_Services_Rents`
   - `LineCode == 4`: `dcid:RegionalPriceParity_Services_Other`
   - `LineCode == 5`: `dcid:RegionalPriceParity_Services_Housing`

If an optional `input_files/cns_baseline/` folder is present containing the legacy baseline CSVs (`county_gdp_all.csv`, `county_gdp_growth_all.csv`, `metro_gdp.csv`, `metro_nominal_gdp.csv`, `marpp_clean.csv`), those records are loaded first and overlaid with the latest BEA release so historical observations remain intact.

## Directory Layout
- `manifest.json`: Import automation specification for `BEAGDPPriceParity`.
- `run.sh`: Entry-point shell script invoked by the import automation executor.
- `process_bea_gdp_rpp.py`: Main download and transformation script producing `output/bea_gdp_rpp.csv`.
- `bea_gdp_rpp.tmcf`: Template MCF mapping `output/bea_gdp_rpp.csv` to `StatVarObservation` nodes.
- `bea_rpp_statvars.mcf`: Schema definitions for the 5 `RegionalPriceParity_*` `StatisticalVariable` nodes and `regionalPriceParity` property.
- `validation_config.json`: Validation rules for `tools/import_validation/runner.py`.
- `golden_data/`: Golden summary report and observation samples validated by `GOLDENS_CHECK`.
- `process_bea_gdp_rpp_test.py` & `test_data/`: Hermetic unit tests and sample fixtures.

## Usage
From the repository root:

```bash
# 1. Run the processing pipeline
bash scripts/us_bea/gdp_price_parity/run.sh

# 2. Run unit tests
./run_tests.sh -p scripts/us_bea/gdp_price_parity

# 3. Validate MCF generation with import-tool
java -Djava.awt.headless=true -jar import-tool.jar genmcf \
  -o=scripts/us_bea/gdp_price_parity/genmcf_out \
  scripts/us_bea/gdp_price_parity/bea_gdp_rpp.tmcf \
  scripts/us_bea/gdp_price_parity/bea_rpp_statvars.mcf \
  scripts/us_bea/gdp_price_parity/output/bea_gdp_rpp.csv
```
