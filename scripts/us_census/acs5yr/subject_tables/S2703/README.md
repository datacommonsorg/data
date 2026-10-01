# US census ACS5YR S2703 Subject Table import

This subject table gives the population count on private health insurance coverage constrained by age, poverty status and type of private insurance.


Years: 2015-2024

Geo : All geographic levels from country to census tracts in the US.

## Download Step

Run `census_api_data_downloader.py` from `scripts/us_census/api_utils` to download the survey data:

```bash
cd scripts/us_census/api_utils

python3 census_api_data_downloader.py \
  --dataset=acs/acs5/subject \
  --table_id=S2703 \
  --start_year=2015 \
  --end_year=2024 \
  --all_summaries \
  --output_path=/tmp/census_download \
  --api_key=<YOUR_API_KEY>
```

Copy only the generated `.zip` file into `input_data/`:

```bash
mkdir -p scripts/us_census/acs5yr/subject_tables/S2703/input_data
cp /tmp/census_download/S2703.zip scripts/us_census/acs5yr/subject_tables/S2703/input_data/S2703.zip
```

## Process Step

Run the subject table processor from `scripts/us_census/acs5yr/subject_tables`:

```bash
cd scripts/us_census/acs5yr/subject_tables

python3 process.py \
  --option=all \
  --table_prefix=S2703 \
  --has_percent=False \
  --debug=False \
  --spec_path=S2703/S2703_spec.json \
  --input_path=S2703/input_data/S2703.zip \
  --output_dir=S2703
```

- `--option=all`: Runs both column map generation (`column_map.json`) and observation processing (`S2703_cleaned.csv`, `S2703_output.mcf`, `S2703_output.tmcf`, `S2703_summary.json`).

## Notes

1. This subject table gives the population count on private health insurance coverage constrained by age, poverty status and type of private insurance.
2. There has been a change in the age brackets from [2017](https://www.census.gov/programs-surveys/acs/technical-documentation/table-and-geography-changes/2017/5-year.html) onwards.
3. In the 2024 release, the Census Bureau introduced the subcategory "Subsidized market place coverage alone" under private health insurance alone; this column is ignored to prevent duplicate observations and maintain time-series consistency.

