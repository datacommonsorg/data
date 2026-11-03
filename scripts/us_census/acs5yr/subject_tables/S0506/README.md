# ACS 5-Year Subject Table S0506: Selected Characteristics of the Foreign-Born Population by Period of Entry into the United States — Latin America

## Overview

This U.S. Census Bureau American Community Survey (ACS) 5-Year Estimates Subject Table (`S0506`) provides population counts, percentages (converted to counts during processing), medians, means, and corresponding margins of error for the foreign-born population in the United States originating from Latin America, cross-tabulated by region/country of birth:
- **Total Foreign-Born Population** (`dcid:USC_ForeignBorn`)
- **Born in Latin America** (`dcid:LatinAmerica`)
- **Born in Mexico** (`dcid:country/MEX`)
- **Born in Caribbean** (`dcid:Caribbean`)
- **Born in Central America (excluding Mexico)** (`dcid:CentralAmericaExceptMexico`)
- **Born in South America** (`dcid:SouthAmerica`)

Populations are sliced across demographic, social, economic, and housing characteristics including U.S. citizenship status and period of entry, sex and age, race and Hispanic or Latino origin, household type and relationship, marital status, school enrollment, educational attainment, language spoken at home and ability to speak English, employment status, class of worker, occupation (SOC), industry (NAICS), full-time year-round worker earnings, household income and benefits, poverty status (ratio to poverty line), and housing tenure, rooms, vehicles available, and housing costs.

## Dataset Coverage

- **Geography**: Country (`country/USA`), State, County, County Subdivision, Place, Census Tract, ZIP Code Tabulation Area (ZCTA), Congressional District, and School Districts across the United States and Puerto Rico.
- **Temporal Coverage**: `2010` to `Present` (latest ACS 5-Year release: `2024`, `15` vintages `2010`–`2024`, annual refresh cycle).
- **Statistical Variables**: `1,400` StatVars defined in `S0506_output.mcf` (`1,340` unique active StatVars with observations per vintage across `2010`–`2024`, `57,127,539` total observations).

## Prerequisites & Working Directory

From the repository root, create and activate the Python virtual environment with repository dependencies installed (Python 3.10+), then change to the `scripts/us_census/acs5yr/subject_tables` directory:

```bash
./run_tests.sh -r
source .env/bin/activate
cd scripts/us_census/acs5yr/subject_tables
```

## Downloading Raw Data

Raw data overlays (`ACSST5Y<YEAR>.S0506_data_with_overlays_1111-11-11T111111.csv`) are downloaded from the [U.S. Census Bureau data.census.gov S0506 table](https://data.census.gov/table/ACSST5Y2024.S0506?q=S0506) or via the common ACS API downloader utility and packaged into `S0506/S0506.zip`:

```bash
python3 ../../api_utils/census_api_data_downloader.py \
  --dataset=acs/acs5/subject \
  --table_id=S0506 \
  --output_path=S0506/ \
  --api_key=<CENSUS_API_KEY> \
  --start_year=2010 \
  --end_year=2024 \
  --all_summaries
```

## Processing & Generating Artifacts

Run `process.py` from `scripts/us_census/acs5yr/subject_tables` to generate the column map (`column_map.json`), cleaned CSV (`S0506_cleaned.csv`), TMCF (`S0506_output.tmcf`), StatVar MCF (`S0506_output.mcf`), and processing summary (`S0506_summary.json`):

```bash
python3 process.py \
  --option=all \
  --table_prefix=S0506 \
  --has_percent=True \
  --debug=False \
  --spec_path=S0506/S0506_spec.json \
  --input_path=S0506/S0506.zip \
  --output_dir=S0506/output
```

To run the Data Commons import tool (`genmcf`) locally without external API existence-check errors (using the [Data Commons Import Tool JAR](https://github.com/datacommonsorg/import/releases)):

```bash
# Download the latest release JAR from https://github.com/datacommonsorg/import/releases
curl -L -o datacommons-import-tool-0.1-jar-with-dependencies.jar \
  https://github.com/datacommonsorg/import/releases/latest/download/datacommons-import-tool.jar
java -Xmx32g -jar datacommons-import-tool-0.1-jar-with-dependencies.jar genmcf \
  -e=false \
  -r=SUMMARY \
  -p=8 \
  S0506/output/S0506_output.mcf \
  S0506/output/S0506_output.tmcf \
  S0506/output/S0506_cleaned.csv \
  -o=S0506/output/dc_generated
```

## Important Files

- `S0506_spec.json`: JSON specification mapping Census column tokens, place of birth regions/countries, units, scaling denominators, and ignored tokens/columns to Data Commons schema properties.
- `S0506_summary.json`: Summary of per-vintage column counts, row counts, StatVar counts, and observation counts (`2010`–`2024`).
- `testdata/`: Hermetic test fixtures (`S0506_test.zip`, `S0506_cleaned.csv`, `S0506_output.mcf`, `S0506_output.tmcf`, `column_map.json`, and `S0506_summary.json`) validated by `subject_table_test.py`.

## Running Tests

From the repository root, run the common unit tests and end-to-end subject table test suite:

```bash
./run_tests.sh -p scripts/us_census/acs5yr
```

## Refresh Procedure

1. Download the new ACS 5-Year `S0506` vintage CSV and add it to `S0506/S0506.zip`.
2. Update `S0506/S0506_spec.json` to add the new vintage's inflation-adjusted dollar tokens and denominator mappings for `<YEAR>`.
3. Execute `process.py` as shown above and copy `S0506/output/S0506_summary.json` to `S0506/S0506_summary.json`.
4. Run `genmcf` and `import_differ`, then stage the unresolved and resolved MCF artifacts to GCS (`gs://unresolved_mcf/census/acs5yr/subject_tables/S0506/<DATE>/` and `gs://resolved_mcf/census/acs5yr/subject_tables/S0506/<DATE>/`).
