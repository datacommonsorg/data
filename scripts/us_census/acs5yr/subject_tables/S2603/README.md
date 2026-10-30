# ACS 5-Year Subject Table S2603: Characteristics of the Group Quarters Population by Group Quarters Type (5 Types)

## Overview

This U.S. Census Bureau American Community Survey (ACS) 5-Year Estimates Subject Table (`S2603`) details the counts and socioeconomic/demographic characteristics of people residing in group quarters as defined in the [ACS Group Quarters Definitions Manual](https://www2.census.gov/programs-surveys/acs/tech_docs/group_definitions/2019GQ_Definitions.pdf).

Table `S2603` cross-tabulates the Total Population, Total Group Quarters Population, and **5 specific Group Quarters types**:
1. **Adult Correctional Facilities** (Institutionalized)
2. **Nursing Facilities / Skilled-Nursing Facilities** (Institutionalized)
3. **Juvenile Facilities** (Institutionalized)
4. **College / University Student Housing** (Noninstitutionalized)
5. **Military Quarters / Military Ships** (Noninstitutionalized)

Residents are sliced by age, sex, race and Hispanic origin, marital status, educational attainment, veteran status, disability status, citizenship and nativity, language spoken at home, employment status, occupation, earnings, poverty/SNAP (Food Stamps) status, and geographical mobility.

> **Related Tables**: Because `S2603` is published by the U.S. Census Bureau at the national (`country/USA`) level only, state-level breakdowns for a subset of 3 group quarters types are available in `S2602` / `S2602PR`, and broader Institutionalized vs. Noninstitutionalized breakdowns are available in `S2601A` / `S2601APR`.

## Dataset Coverage

- **Geography**: Country (`country/USA` / Census GeoID `0100000US`)
- **Temporal Coverage**: `2017` to `Present` (latest ACS 5-Year release: `2024`, annual refresh cycle)
- **Statistical Variables**: `1,365` StatVars defined in `S2603_output.mcf` (`1,251` unique active StatVars with observations across `2017`–`2024`)

## Prerequisites & Working Directory

Run all commands from the `scripts/us_census/acs5yr/subject_tables` directory using Python 3.10+ with repository dependencies installed (`pip install -r requirements.txt`):

```bash
cd scripts/us_census/acs5yr/subject_tables
```

## Downloading Raw Data

Raw data overlays (`ACSST5Y<YEAR>.S2603-Data.csv`) are downloaded from the [U.S. Census Bureau data.census.gov S2603 table](https://data.census.gov/table/ACSST5Y2024.S2603?q=S2603) or via the common ACS API downloader utility and packaged into `S2603/S2603.zip`:

```bash
python3 ../../api_utils/census_api_data_downloader.py \
  --table_id=S2603 \
  --output_path=S2603/ \
  --api_key=<CENSUS_API_KEY> \
  --start_year=2017 \
  --end_year=2024
```

## Processing & Generating Artifacts

Run `process.py` from `scripts/us_census/acs5yr/subject_tables` to generate the column map (`column_map.json`), cleaned CSV (`S2603_cleaned.csv`), TMCF (`S2603_output.tmcf`), StatVar MCF (`S2603_output.mcf`), and processing summary (`S2603_summary.json`):

```bash
python3 process.py \
  --option=all \
  --table_prefix=S2603 \
  --input_path=S2603/S2603.zip \
  --spec_path=S2603/S2603_spec.json \
  --output_dir=S2603/output \
  --has_percent=True
```

To run the Data Commons import tool linter (`genmcf`) locally without external API existence-check errors:

```bash
java -jar datacommons-import-tool-0.1-jar-with-dependencies.jar genmcf \
  -e=false \
  S2603/output/S2603_cleaned.csv \
  S2603/output/S2603_output.tmcf \
  S2603/output/S2603_output.mcf \
  -o=S2603/dc_generated
```

## Important Files

- `S2603_spec.json`: JSON specification mapping Census column tokens, units, scaling denominators, and ignored tokens/columns to Data Commons schema properties.
- `S2603_summary.json`: Summary of per-vintage column counts, row counts, StatVar counts, and observation counts.
- `testdata/`: Hermetic test fixtures (`S2603_test.zip`, `S2603_cleaned.csv`, `S2603_output.mcf`, `S2603_output.tmcf`, `column_map.json`, and `S2603_summary.json`) validated by `subject_table_test.py`.

## Running Tests

From the repository root, run the common unit tests and end-to-end subject table test suite:

```bash
python3 -m unittest discover -v -t . -s scripts/us_census/acs5yr/subject_tables -p "*test.py"
```

## Refresh Procedure

1. Download the new ACS 5-Year `S2603` vintage CSV and add it to `S2603/S2603.zip`.
2. Update `S2603/S2603_spec.json` to add the new vintage's inflation-adjusted dollar token (`"INCOME AND BENEFITS IN THE PAST 12 MONTHS (IN <YEAR> INFLATION-ADJUSTED DOLLARS)"`) to `ignoreTokens` and the 28 Margin of Error earnings columns for `<YEAR>` to `ignoreColumns`.
3. Execute `process.py` as shown above and copy `S2603/output/S2603_summary.json` to `S2603/S2603_summary.json`.
4. Run `genmcf`, `table2mcf_flume`, `flume_resolver:resolver`, `import_differ`, and `stats_checker`, then update the CNS paths and `end_date_in_kg` in `CensusACS5YearSurvey_SubjectTables_S2603.textproto` and `CensusACS5YearSurvey_SubjectTables_S2603.mcf`.

## Notes

- **National-Level Coverage Only (`country/USA`)**: Although the raw Census overlay CSVs include rows for sub-national geographies (`191,344`–`205,958` rows per vintage), the U.S. Census Bureau suppresses all sub-national cells in `S2603` (`"N"` or `"-"`) due to sample size and disclosure thresholds across the 5 group quarters types. Only `0100000US` (`country/USA`) contains numeric observations.
- **Bottom-Coded Median Earnings (`"2,500-"`)**: In the `2017`, `2018`, and `2019` vintages, the Census Bureau reported bottom-coded median earnings strings (`"2,500-"`) for `Median_Earnings_Person_Male_ResidesInJuvenileFacilities` and `Median_Earnings_Person_Female_ResidesInJuvenileFacilities`. For backward compatibility with prior production imports (`20250127/S2603_cleaned.csv`) and to prevent historical observation deletions without modifying the shared `common/data_loader.py` loader, those 6 cells are normalized to `2500` in the packaged `S2603.zip` input CSVs (`2500.0` in `S2603_cleaned.csv`).
- **Repeated Census Denominator Rows**: The raw Census `S2603` table repeats the total population denominator across 4 sections (rows `001`, `045`, `060`, and `099`) and the `65 years and over` population across 2 sections (rows `017` and `050`), producing `1,299` total CSV rows (`1,251` unique StatVars plus `48` repeated denominator rows in `2019`–`2024`, and `42` in `2017`–`2018`) that resolve to `1,251` unique `(Place, Year, StatVar)` observations in the final TFRecord.
