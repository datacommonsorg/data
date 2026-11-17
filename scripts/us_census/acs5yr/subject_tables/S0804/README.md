# US Census ACS5YR S0804 Subject Table Import

The table provides data on the number of people who commute to work by means of transportation. The movement is classified under one of the following types:

- Car, truck, or van - Drove Alone
- Car, truck, or van - Carpooled
- Public transportation (excluding taxicab) (2010–2023) / Public transportation (2024)
- Worked from home

The data is sliced by the following properties:

- age
- incomeStatus
- gender
- race
- ethnicity
- employmentStatus
- commuteMode
- numberOfVehiclesInHousehold
- commuteTime
- commuteStartTime
- income
- placeOfWork
- languageSpokenAtHome
- abilityToSpeakEnglish
- nativity
- citizenship
- povertyStatus
- occupation
- commuteType
- residenceType
- naics
- workerClassification
- occupancyTenure
- occupancyStatus

## Dataset Coverage

- **Years**: `2010–2024`
- **Geography**: Country (`010`), State (`040`), County (`050`), County Subdivision (`060`), Census Tract (`140`), Block Group (`150`), Place (`160`), Congressional District (`500`), ZCTA (`860`), and School Districts (`950`, `960`, `970`)
- **Source Table**: [US Census Bureau Table S0804: Means of Transportation to Work by Selected Characteristics](https://data.census.gov/table?q=S0804)

## Prerequisites & Working Directory

Install the repository Python dependencies (`pip install -r requirements_all.txt`) and run the processing commands from `scripts/us_census/acs5yr/subject_tables`:

```shell
cd scripts/us_census/acs5yr/subject_tables
```

## Downloading and Packaging Raw Data

Download the raw S0804 table data (`S0804.zip` containing `ACSST5Y<YEAR>.S0804_data_with_overlays_*.csv` for `2010–2024` across all supported summary levels) using `census_api_data_downloader.py` from `scripts/us_census/api_utils` (or directly from [data.census.gov](https://data.census.gov/table?q=S0804)) and place the archive at `scripts/us_census/acs5yr/subject_tables/S0804/S0804.zip`:

```shell
python3 ../../api_utils/census_api_data_downloader.py \
  --dataset=acs/acs5/subject \
  --table_id=S0804 \
  --start_year=2010 \
  --end_year=2024 \
  --all_summaries \
  --output_path=/tmp/census_download \
  --api_key=<YOUR_CENSUS_API_KEY>

cp /tmp/census_download/acs/acs5/subject/S0804/S0804.zip ./S0804/S0804.zip
```

## Commands to Execute the Script

Create the output directory first (`set_column_map` writes `column_map.json` to `--output_dir` before `SubjectTableDataLoaderBase` initializes the directory), then execute `process.py` from `scripts/us_census/acs5yr/subject_tables`:

```shell
mkdir -p ./S0804/output
python3 process.py \
  --option=all \
  --table_prefix=S0804 \
  --has_percent=True \
  --debug=False \
  --spec_path=S0804/S0804_spec.json \
  --input_path=S0804/S0804.zip \
  --output_dir=S0804/output
```

## Output Artifacts and Important Files

Running the command above generates the following files in `S0804/output`:

- `S0804_cleaned.csv`: Cleaned observation data across all years and geographies.
- `S0804_output.mcf`: Generated StatisticalVariable schema nodes.
- `S0804_output.tmcf`: Template MCF mapping `S0804_cleaned.csv` columns to Data Commons schema.
- `S0804_summary.json`: Summary of observation counts and StatVars per year.
- `column_map.json`: Column mapping configuration per release year.

Checked-in files in `S0804/`:

- `S0804_spec.json`: JSON specification mapping S0804 column tokens, units, percentage-to-count denominators, DCID overrides, and ignored columns to Data Commons schema properties.
- `S0804_summary.json`: Year-by-year summary of column counts, row counts, StatVar counts, and observation counts.
- `testdata/`: Hermetic test fixtures (`ACSST5Y2024.S0804_data_with_overlays_1111-11-11T111111.csv`, `column_map.json`, `S0804_cleaned.csv`, `S0804_output.mcf`, `S0804_output.tmcf`, and `S0804_summary.json`) verified by `subject_table_test.py`.

## Running Tests

From the repository root, run the directory-scoped test runner:

```shell
./run_tests.sh -p scripts/us_census/acs5yr/subject_tables
```

## Refresh Procedure

1. Download the new ACS 5-Year `S0804` release CSV (`ACSST5Y<YEAR>.S0804_data_with_overlays_*.csv`) and add it to `S0804/S0804.zip`.
2. Update `S0804/S0804_spec.json`:
   - Add `"EARNINGS IN THE PAST 12 MONTHS (IN <YEAR> INFLATION-ADJUSTED DOLLARS) FOR WORKERS": "Annual"` under `pvs.measurementQualifier`.
   - Add the `<YEAR>` inflation-adjusted earnings denominator blocks under `denominators` (for `Total`, `Car, truck, or van -- drove alone`, `Car, truck, or van -- carpooled`, `Public transportation`, and `Worked from home`).
   - Verify whether any new Census header labels or non-applicable cross-tabulations (such as `Worked from home!!Workers 16 years and over who did not work from home`) require entries in `pvs` or `ignoreColumns`.
3. Create the output directory (`mkdir -p ./S0804/output`), run `process.py` as shown above, and copy `S0804/output/S0804_summary.json` to `S0804/S0804_summary.json`.
4. Run `./run_tests.sh -p scripts/us_census/acs5yr/subject_tables` and validate the generated MCF/TMCF/CSV artifacts with the Data Commons import tool (`genmcf`).
