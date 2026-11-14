# ACS 5-Year Subject Table S0801: Commuting Characteristics by Sex

## Overview

This U.S. Census Bureau American Community Survey (ACS) 5-Year Estimates Subject Table (`S0801`) provides socioeconomic and demographic data on commuting characteristics for workers 16 years and over, broken down by sex (Total, Male, and Female).

Table `S0801` covers:
1. **Means of Transportation to Work**: Car, truck, or van (drove alone vs. carpooled by carpool size, and workers per vehicle), public transportation (excluding taxicab), walked, bicycle, taxicab/ride-hailing/motorcycle/other means, and worked from home.
2. **Place of Work**: State of residence (in vs. outside county of residence), outside state of residence, and living in a place (worked in vs. outside place of residence).
3. **Time Leaving Home to Go to Work**: Departure time intervals for workers who did not work from home.
4. **Travel Time to Work**: Commute duration intervals (`Less than 10 minutes` to `60 or more minutes`) and mean travel time to work (in minutes).
5. **Vehicles Available**: Household vehicle availability (`No vehicle available`, `1 vehicle`, `2 vehicles`, `3 or more vehicles`) for workers 16 years and over in households, plus percent allocated for means of transportation, time of departure, travel time, and vehicles available.

## Dataset Coverage

- **Geography**: Country, State, County, County Subdivision, Place, Census Tract, ZIP Code Tabulation Area (ZCTA), Congressional District, Metropolitan/Micropolitan Statistical Area, and American Indian/Alaska Native/Native Hawaiian Areas (`155,630` to `200,299` unique geographies per vintage)
- **Temporal Coverage**: `2010` to `Present` (latest ACS 5-Year release: `2024`, annual refresh cycle)
- **Statistical Variables**: `288` StatVars defined in `S0801_output.mcf` (`282` active StatVars with observations per vintage across `2010`–`2024`)

## Prerequisites & Working Directory

Run all commands from the `scripts/us_census/acs5yr/subject_tables` directory using Python 3.10+ with repository dependencies installed (`pip install -r requirements.txt`):

```bash
cd scripts/us_census/acs5yr/subject_tables
```

## Downloading Raw Data

Raw data overlays (`ACSST5Y<YEAR>.S0801_data_with_overlays_*.csv`) are downloaded from the [U.S. Census Bureau data.census.gov S0801 table](https://data.census.gov/table/ACSST5Y2024.S0801?q=S0801) or via the common ACS API downloader utility (run from `scripts/us_census/api_utils`) and packaged into `S0801/S0801_2010_2024.zip`:

```bash
cd scripts/us_census/api_utils
python3 census_api_data_downloader.py \
  --dataset=acs/acs5/subject \
  --table_id=S0801 \
  --output_path=../acs5yr/subject_tables/S0801/ \
  --api_key=<CENSUS_API_KEY> \
  --start_year=2010 \
  --end_year=2024 \
  --all_summaries
cd ../acs5yr/subject_tables
cp S0801/acs/acs5/subject/S0801/S0801.zip S0801/S0801_2010_2024.zip
```

## Processing & Generating Artifacts

Run `process.py` from `scripts/us_census/acs5yr/subject_tables` to generate the column map (`column_map.json`), cleaned CSV (`S0801_cleaned.csv`), TMCF (`S0801_output.tmcf`), StatVar MCF (`S0801_output.mcf`), and processing summary (`S0801_summary.json`):

```bash
python3 process.py \
  --option=all \
  --table_prefix=S0801 \
  --input_path=S0801/S0801_2010_2024.zip \
  --spec_path=S0801/S0801_spec.json \
  --output_dir=S0801 \
  --has_percent=True
```

To run the Data Commons import tool (`genmcf`) locally without external API existence-check errors:

```bash
java -Xmx16g -jar datacommons-import-tool-0.1-jar-with-dependencies.jar genmcf \
  -e=false \
  -rs=SUMMARY \
  -n=24 \
  S0801/S0801_output.mcf \
  S0801/S0801_output.tmcf \
  S0801/S0801_cleaned.csv \
  -o=S0801/dc_generated
```

## Important Files

- `S0801_spec.json`: JSON specification mapping Census column tokens, units, scaling denominators, and ignored tokens/columns to Data Commons schema properties.
- `S0801_summary.json`: Summary of per-vintage column counts, row counts, StatVar counts, and observation counts.

## Running Tests

From the repository root, run the common unit tests and end-to-end subject table test suite:

```bash
python3 -m unittest discover -v -t . -s scripts/us_census/acs5yr/subject_tables -p "*test.py"
```

## Refresh Procedure

1. Download the new ACS 5-Year `S0801` vintage CSV and add it to the `S0801` zip archive.
2. Verify whether the new vintage introduces any renamed header tokens in `column_map.json` and update `S0801/S0801_spec.json` if needed.
3. Execute `process.py` as shown above and update `S0801/S0801_summary.json`.
4. Run `genmcf`, `flume_resolver:resolver`, and the Dataflow `differ` flex-template job, then update the CNS paths and `end_date_in_kg` in `CensusACS5YearSurvey_SubjectTables_S0801.textproto` and `CensusACS5YearSurvey_SubjectTables_S0801.mcf`.

## Notes

- **2024 Means of Transportation Label Updates**: Starting in the 2024 ACS 5-Year vintage, the U.S. Census Bureau updated two column labels under `MEANS OF TRANSPORTATION TO WORK`:
  - `"Public transportation (excluding taxicab)"` was shortened to `"Public transportation"`.
  - `"Taxicab, motorcycle, or other means"` was updated to `"Taxi or ride-hailing services, motorcycle, or other means"`.
  Both token variants are mapped in `S0801_spec.json` (`commuteMode` and `denominators`) to preserve time-series continuity with the existing `PublicTransportationExcludingTaxicab` and `TaxicabMotorcycleBicycleOrOtherMeans` StatVars and prevent duplicate generic `WorkCommute` column mappings.
