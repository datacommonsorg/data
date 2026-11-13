# US Census ACS5YR S1903 Subject Table Import

This subject table provides household count and median income (in the past 12 months) broken down by the householder's race/Hispanic origin and age.

- **Years**: 2010–2024
- **Geo**: All geographic levels from country to census tracts in the US (Country, State, County, County Subdivision, Census Tract, Place/City, Congressional District, ZCTA, School District).

## Download Step

Run `census_api_data_downloader.py` from `scripts/us_census/api_utils` to download the survey data:

```bash
cd scripts/us_census/api_utils

python3 census_api_data_downloader.py \
  --dataset=acs/acs5/subject \
  --table_id=S1903 \
  --start_year=2010 \
  --end_year=2024 \
  --all_summaries \
  --output_path=/tmp/census_download \
  --api_key=<YOUR_API_KEY>
```

Copy the generated `.zip` file into `input_data/`:

```bash
cd ../../..
mkdir -p scripts/us_census/acs5yr/subject_tables/S1903/input_data
cp /tmp/census_download/acs/acs5/subject/S1903/S1903.zip scripts/us_census/acs5yr/subject_tables/S1903/input_data/S1903.zip
```

## Process Step

Run the subject table processor from `scripts/us_census/acs5yr/subject_tables`:

```bash
cd scripts/us_census/acs5yr/subject_tables

python3 process.py \
  --option=all \
  --table_prefix=S1903 \
  --has_percent=True \
  --debug=False \
  --spec_path=S1903/S1903_spec.json \
  --input_path=S1903/input_data/S1903.zip \
  --output_dir=S1903
```

- `--option=all`: Runs both column map generation (`column_map.json`) and observation processing (`S1903_cleaned.csv`, `S1903_output.mcf`, `S1903_output.tmcf`, `S1903_summary.json`).

## Running Tests

Run the subject table unit tests from the repository root:

```bash
python3 -m unittest scripts/us_census/acs5yr/subject_tables/subject_table_test.py
```

## Notes

1. Median household income is measured in `InflationAdjustedUSD_CurrentYear`.
2. Family income, nonfamily household income, percent distribution, margin of error, and percent imputed/allocated columns are ignored in `S1903_spec.json`.
