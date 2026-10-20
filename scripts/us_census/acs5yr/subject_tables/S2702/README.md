# US census ACS5YR S2702 Subject Table import

This subject table gives the population count and selected characteristics of the uninsured civilian noninstitutionalized population in the United States, constrained by age, sex, race and Hispanic or Latino origin, nativity and U.S. citizenship status, disability status, residence 1 year ago, educational attainment, employment status, work experience, class of worker, industry, occupation, earnings, household income, and ratio of income to poverty level.

Years: 2013-2024

Geo : All geographic levels from country to census tracts in the US.

## Download Step

Run `census_api_data_downloader.py` from `scripts/us_census/api_utils` to download the survey data:

```bash
cd scripts/us_census/api_utils

python3 census_api_data_downloader.py \
  --dataset=acs/acs5/subject \
  --table_id=S2702 \
  --start_year=2013 \
  --end_year=2024 \
  --output_path=/tmp/census_download \
  --api_key=<YOUR_API_KEY>
```

Copy only the generated `.zip` file into `input_data/`:

```bash
cd ../../..
mkdir -p scripts/us_census/acs5yr/subject_tables/S2702/input_data
cp /tmp/census_download/acs/acs5/subject/S2702/S2702.zip scripts/us_census/acs5yr/subject_tables/S2702/input_data/S2702.zip
```

## Process Step

Run the subject table processor from `scripts/us_census/acs5yr/subject_tables`:

```bash
cd scripts/us_census/acs5yr/subject_tables

python3 process.py \
  --option=all \
  --table_prefix=S2702 \
  --has_percent=True \
  --debug=False \
  --spec_path=S2702/S2702_spec.json \
  --input_path=S2702/input_data/S2702.zip \
  --output_dir=S2702
```

- `--option=all`: Runs both column map generation (`column_map.json`) and observation processing (`S2702_cleaned.csv`, `S2702_output.mcf`, `S2702_output.tmcf`, `S2702_summary.json`).
- `--has_percent=True`: Converts percentage values in the dataset to counts using the `denominators` mapping in `S2702_spec.json`.

## Notes

1. Percentage values for uninsured population breakdowns are converted into corresponding counts using the `denominators` configuration in `S2702_spec.json`.
2. There has been a change in the age brackets from [2017](https://www.census.gov/programs-surveys/acs/technical-documentation/table-and-geography-changes/2017/5-year.html) onwards (`Under 18 years` / `18 to 64 years` in 2013–2016 vs. `Under 19 years` / `19 to 64 years` from 2017 onwards).
3. For the `$50,000 to $74,999` household income bracket:
   - In 2013–2018, the raw CSV headers share an identical `$50,000 to $74,999` leaf name with the earnings section; because `generate_col_map.py` reads headers via `csv.reader` (which preserves duplicate column names verbatim rather than appending `.1` like `pd.read_csv`), the `.1` household income entries in `preprocess.find_and_replace` and `denominators` in `S2702_spec.json` (inherited from `common/testdata/spec_s2702.json`) are retained as historical no-ops and are not emitted into `column_map.json` or `S2702_cleaned.csv`.
   - In 2019, the Estimate and Margin of Error columns for household income `$50,000 to $74,999` are ignored in `ignoreColumns`.
   - In 2020–2024, these columns follow the existing `$50,000 to $74,999` `preprocess.find_and_replace` mapping (`Count_Household_16OrMoreYears_Civilian_NoHealthInsurance_IncomeOf50000To74999USDollar_WithEarnings_NonInstitutionalized`) to maintain backward compatibility with previous S2702 releases (`20250211`) and avoid deleting existing StatVar DCIDs.
4. Margin of Error columns for median measurements (`Median age (years)`, `Median earnings (dollars)`, and `Median household income of householders`) are ignored across all years.
5. In `S2702_spec.json`, `"Agriculture, forestry, fishing and hunting, and mining"` is mapped to `"naics": "NAICS/11_21"` (matching `common/testdata/spec_s2702.json`, `S2405_spec.json`, and `S2407_spec.json` for `statvar_dcid_generator.py` DCID generation). The generated StatVar DCIDs (`Count_Person_16OrMoreYears_NoHealthInsurance_NAICSAgricultureForestryFishingHuntingMiningQuarryingOilGasExtraction_Worker` and its `MarginOfError_`) are unchanged from `20250211`, and the production import manifest only ingests `S2702_output.tmcf` and `S2702_cleaned.csv` while relying on `manual_usc_s2702_stat_vars.mcf` (`naics: dcid:NAICS/11&NAICS/21`) for StatVar schema definitions.
