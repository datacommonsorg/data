# ACS 5-Year Detailed Table B25031: Median Gross Rent by Bedrooms

## Overview

This U.S. Census Bureau American Community Survey (ACS) 5-Year Estimates Detailed Table (`B25031`) provides monthly median gross rent and corresponding margins of error (in U.S. dollars) for renter-occupied housing units paying cash rent, cross-tabulated by the number of bedrooms:
- **Total** (all bedroom categories combined)
- **No bedroom** (`dcid:Bedrooms0`)
- **1 bedroom** (`dcid:Bedrooms1`)
- **2 bedrooms** (`dcid:Bedrooms2`)
- **3 bedrooms** (`dcid:Bedrooms3`)
- **4 bedrooms** (`dcid:Bedrooms4`)
- **5 or more bedrooms** (`dcid:Bedrooms5Onwards`)

## Dataset Coverage

- **Geography**: Country (`country/USA`), State, County, County Subdivision, Place, Census Tract, ZIP Code Tabulation Area (ZCTA), Congressional District, and School Districts across the United States and Puerto Rico.
- **Temporal Coverage**: `2015` to `Present` (latest ACS 5-Year release: `2024`, annual refresh cycle)
- **Statistical Variables**: `14` StatVars defined in `B25031_output.mcf` (`7` median gross rent estimates and `7` margins of error across `2015`–`2024`)

## Prerequisites & Working Directory

From the repository root, create and activate the Python virtual environment with repository dependencies installed (Python 3.10+), then change to the `scripts/us_census/acs5yr/subject_tables` directory:

```bash
./run_tests.sh -r
source .env/bin/activate
cd scripts/us_census/acs5yr/subject_tables
```

## Downloading Raw Data

Raw data overlays (`ACSDT5Y<YEAR>.B25031_data_with_overlays_1111-11-11T111111.csv`) are downloaded from the [U.S. Census Bureau data.census.gov B25031 table](https://data.census.gov/table/ACSDT5Y2024.B25031?q=B25031) or via the common ACS API downloader utility and packaged into `B25031/B25031.zip`:

```bash
python3 ../../api_utils/census_api_data_downloader.py \
  --dataset=acs/acs5 \
  --table_id=B25031 \
  --output_path=B25031/ \
  --api_key=<CENSUS_API_KEY> \
  --start_year=2015 \
  --end_year=2024 \
  --all_summaries
```

## Processing & Generating Artifacts

Run `process.py` from `scripts/us_census/acs5yr/subject_tables` to generate the column map (`column_map.json`), cleaned CSV (`B25031_cleaned.csv`), TMCF (`B25031_output.tmcf`), StatVar MCF (`B25031_output.mcf`), and processing summary (`B25031_summary.json`):

```bash
python3 process.py \
  --option=all \
  --table_prefix=B25031 \
  --input_path=B25031/B25031.zip \
  --spec_path=B25031/B25031_spec.json \
  --output_dir=B25031 \
  --has_percent=False
```

To run the Data Commons import tool (`genmcf`) locally without external API existence-check errors:

```bash
java -jar datacommons-import-tool-0.1-jar-with-dependencies.jar genmcf \
  -e=false \
  B25031/B25031_cleaned.csv \
  B25031/B25031_output.tmcf \
  B25031/B25031_output.mcf \
  -o=B25031/dc_generated
```

To run the differ through Dataflow after staging the current and previous resolved MCF files to GCS:

```bash
gcloud dataflow flex-template run "btable-b25031-dev-differ" \
  --project="datcom-infosys-dev" \
  --region="us-central1" \
  --template-file-gcs-location="gs://datcom-templates/templates/flex/differ.json" \
  --worker-machine-type="n2-highmem-16" \
  --additional-experiments="shuffle_mode=service" \
  --parameters="currentData=<CURRENT_RESOLVED_MCF_GCS_PATH>" \
  --parameters="previousData=<PREVIOUS_RESOLVED_MCF_GCS_PATH>" \
  --parameters="outputLocation=gs://unresolved_mcf/census/acs5yr/subject_tables/B25031/20261028/differ/"
```

## Important Files

- `B25031_spec.json`: JSON specification mapping Census column tokens, bedroom counts, units (`USDollar`), and measurement qualifiers (`Monthly`) to Data Commons schema properties.
- `B25031_summary.json`: Summary of per-vintage column counts, row counts, StatVar counts, and observation counts (`2015`–`2024`).

## Running Tests

From the repository root, run the common unit tests and end-to-end subject table test suite:

```bash
./run_tests.sh -p scripts/us_census/acs5yr
```

## Refresh Procedure

1. Download the new ACS 5-Year `B25031` vintage CSV and add it to `B25031/B25031.zip`.
2. Execute `process.py` as shown above to regenerate `B25031/B25031_summary.json`, `B25031/B25031_cleaned.csv`, `B25031/B25031_output.mcf`, and `B25031/B25031_output.tmcf`.
3. Run `genmcf`, `table2mcf_flume`, `flume_resolver:resolver`, `import_differ`, and `stats_checker`, then update the CNS paths and `end_date_in_kg` in the corresponding import configuration.
