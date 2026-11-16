# US census ACS5YR S2702PR Subject Table import

This subject table gives the population count and selected characteristics of the uninsured civilian noninstitutionalized population in Puerto Rico, constrained by age, sex, race and Hispanic or Latino origin, nativity and U.S. citizenship status, disability status, residence 1 year ago, educational attainment, employment status, work experience, class of worker, industry, occupation, earnings, household income, and ratio of income to poverty level.

Years: 2013-2024

Geo : All geographic levels in Puerto Rico from state to census tracts.

## Download Step

Run `census_api_data_downloader.py` from `scripts/us_census/api_utils` to download the survey data:

```bash
cd scripts/us_census/api_utils

python3 census_api_data_downloader.py \
  --dataset=acs/acs5/subject \
  --table_id=S2702PR \
  --start_year=2013 \
  --end_year=2024 \
  --all_summaries \
  --output_path=/tmp/census_download \
  --api_key=<YOUR_API_KEY>
```

Copy only the generated `.zip` file into `input_data/`:

```bash
mkdir -p scripts/us_census/acs5yr/subject_tables/s2702pr/input_data
cp /tmp/census_download/acs/acs5/subject/S2702PR/S2702PR.zip scripts/us_census/acs5yr/subject_tables/s2702pr/input_data/S2702PR.zip
```

## Process Step

Run the subject table processor from `scripts/us_census/acs5yr/subject_tables`:

```bash
cd scripts/us_census/acs5yr/subject_tables

python3 process.py \
  --option=all \
  --table_prefix=s2702pr \
  --has_percent=True \
  --debug=False \
  --spec_path=s2702pr/s2702pr_spec.json \
  --input_path=s2702pr/input_data/S2702PR.zip \
  --output_dir=s2702pr
```

- `--option=all`: Runs both column map generation (`column_map.json`) and observation processing (`s2702pr_cleaned.csv`, `s2702pr_output.mcf`, `s2702pr_output.tmcf`, `s2702pr_summary.json`).
- `--has_percent=True`: Converts percentage values in the dataset to counts using the `denominators` mapping in `s2702pr_spec.json`.

## Notes

1. For Puerto Rico, Municipio is treated as the equivalent of County, and Puerto Rico itself as a state.
2. Percentage values for uninsured population breakdowns are converted into corresponding counts using the `denominators` configuration in `s2702pr_spec.json`.
3. There has been a change in the age brackets from [2017](https://www.census.gov/programs-surveys/acs/technical-documentation/table-and-geography-changes/2017/5-year.html) onwards (`Under 18 years` / `18 to 64 years` in 2013–2016 vs. `Under 19 years` / `19 to 64 years` from 2017 onwards).
4. Estimate and Margin of Error columns for household income between `$50,000 to $74,999` (2019–2024) are ignored in `ignoreColumns` to maintain consistency with historical years (2013–2018) and avoid collisions with the `$50,000 to $74,999` earnings bracket.
5. Margin of Error columns for median measurements (`Median age (years)`, `Median earnings (dollars)`, and `Median household income of householders`) are ignored across all years.
