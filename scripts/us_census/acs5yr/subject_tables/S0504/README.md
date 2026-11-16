# US Census ACS5YR S0504 Subject Table Import

The table provides data on the selected characteristics of the foreign-born population in the United States by world region of birth:

- Foreign born; Born in Africa
- Foreign born; Born in Northern America
- Foreign born; Born in Oceania

The data is sliced by the following properties:

- nativity
- placeOfBirth
- citizenship
- dateOfEntry
- gender
- age
- race
- householdType
- maritalStatus
- schoolEnrollment
- levelOfSchool
- educationalAttainment
- languageSpokenAtHome
- abilityToSpeakEnglish
- employmentStatus
- armedForcesStatus
- employment
- establishmentOwnership
- workerClassification
- occupation
- naics
- incomeStatus
- earnings
- workStatus
- benefitsStatus
- povertyStatus
- memberStatus
- occupancyStatus
- occupancyTenure
- numberOfRooms
- numberOfOccupants
- numberOfVehicles
- telephoneServiceAvailability
- grossRent
- ownerCost

## Dataset Coverage

- **Years**: `2010–2024`
- **Geography**: Country (`010`), Census Division (`030`), State (`040`), County (`050`), County Subdivision (`060`), Census Tract (`140`), Block Group (`150`), Place (`160`), Metropolitan/Micropolitan Statistical Area (`310`), Congressional District (`500`), ZCTA (`860`), and School Districts (`950`, `960`, `970`)
- **Source Table**: [US Census Bureau Table S0504: Selected Characteristics of the Native and Foreign-Born Populations](https://data.census.gov/table?q=S0504)

## Prerequisites & Working Directory

Install the repository Python dependencies (`pip install -r requirements_all.txt`) and run the processing commands from `scripts/us_census/acs5yr/subject_tables`:

```shell
cd scripts/us_census/acs5yr/subject_tables
```

## Downloading and Packaging Raw Data

Download the raw S0504 table data (`S0504.zip` containing `ACSST5Y<YEAR>.S0504_data_with_overlays_*.csv` for `2010–2024` across all supported summary levels) using `census_api_data_downloader.py` from `scripts/us_census/api_utils` (or directly from [data.census.gov](https://data.census.gov/table?q=S0504)) and place the archive at `scripts/us_census/acs5yr/subject_tables/S0504/S0504.zip`:

```shell
python3 ../../api_utils/census_api_data_downloader.py \
  --dataset=acs/acs5/subject \
  --table_id=S0504 \
  --start_year=2010 \
  --end_year=2024 \
  --all_summaries \
  --output_path=/tmp/census_download \
  --api_key=<YOUR_CENSUS_API_KEY>

cp /tmp/census_download/acs/acs5/subject/S0504/S0504.zip ./S0504/S0504.zip
```

## Commands to Execute the Script

Create the output directory first (`set_column_map` writes `column_map.json` to `--output_dir` before `SubjectTableDataLoaderBase` initializes the directory), then execute `process.py` from `scripts/us_census/acs5yr/subject_tables`:

```shell
mkdir -p ./S0504/output
python3 process.py \
  --option=all \
  --table_prefix=S0504 \
  --has_percent=True \
  --debug=False \
  --spec_path=S0504/S0504_spec.json \
  --input_path=S0504/S0504.zip \
  --output_dir=S0504/output
```

## Output Artifacts and Important Files

Running the command above generates the following files in `S0504/output`:

- `S0504_cleaned.csv`: Cleaned observation data across all years and geographies.
- `S0504_output.mcf`: Generated StatisticalVariable schema nodes.
- `S0504_output.tmcf`: Template MCF mapping `S0504_cleaned.csv` columns to Data Commons schema.
- `S0504_summary.json`: Summary of observation counts and StatVars per year.
- `column_map.json`: Column mapping configuration per release year.

Checked-in files in `S0504/`:

- `S0504_spec.json`: JSON specification mapping S0504 column tokens, units, percentage-to-count denominators, and ignored columns to Data Commons schema properties.
- `testdata/`: Hermetic test fixtures (`ACSST5Y2024.S0504_data_with_overlays_1111-11-11T111111.csv`, `column_map.json`, `S0504_cleaned.csv`, `S0504_output.mcf`, `S0504_output.tmcf`, and `S0504_summary.json`) verified by `subject_table_test.py`.

## Running Tests

From the repository root, run the directory-scoped test runner:

```shell
./run_tests.sh -p scripts/us_census/acs5yr/subject_tables
```

## Refresh Procedure

1. Download the new ACS 5-Year `S0504` release CSV (`ACSST5Y<YEAR>.S0504_data_with_overlays_*.csv`) and add it to `S0504/S0504.zip`.
2. Update `S0504/S0504_spec.json`:
   - Add `"INCOME IN THE PAST 12 MONTHS (IN <YEAR> INFLATION-ADJUSTED DOLLARS)": "Annual"` / `"EARNINGS IN THE PAST 12 MONTHS (IN <YEAR> INFLATION-ADJUSTED DOLLARS) FOR FULL-TIME, YEAR-ROUND WORKERS": "Annual"` (if new header variants appear) and `"InflationAdjustedUSD_<YEAR>"` under `pvs.unit` / `measurement` as needed.
   - Add the `<YEAR>` inflation-adjusted earnings and household income denominator blocks under `denominators` (for `Foreign born; Born in Africa`, `Foreign born; Born in Northern America`, and `Foreign born; Born in Oceania`).
   - Verify whether any new Census header labels or non-applicable cross-tabulations require entries in `pvs` or `ignoreColumns`.
3. Create the output directory (`mkdir -p ./S0504/output`) and run `process.py` as shown above.
4. Run `./run_tests.sh -p scripts/us_census/acs5yr/subject_tables` and validate the generated MCF/TMCF/CSV artifacts with the Data Commons import tool (`dc-import` / `genmcf`) and `import_differ`.

