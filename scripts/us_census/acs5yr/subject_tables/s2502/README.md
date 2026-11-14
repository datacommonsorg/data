# US census ACS5YR S2502 Subject Table import

This subject table provides demographic characteristics for occupied housing units, including householder race, age, educational attainment, and the year the householder moved into the unit across occupied, owner-occupied, and renter-occupied housing units.


Years: 2010-2024

Geo : All geographic levels from country to census tracts in the US.

## Download Step

Run `census_api_data_downloader.py` from `scripts/us_census/api_utils` to download the survey data:

```bash
cd scripts/us_census/api_utils

python3 census_api_data_downloader.py \
  --dataset=acs/acs5/subject \
  --table_id=S2502 \
  --start_year=2010 \
  --end_year=2024 \
  --all_summaries \
  --output_path=/tmp/census_download \
  --api_key=<YOUR_API_KEY>
```

Copy only the generated `.zip` file into `input_data/`:

```bash
cd ../../..
mkdir -p scripts/us_census/acs5yr/subject_tables/s2502/input_data
cp /tmp/census_download/acs/acs5/subject/S2502/S2502.zip scripts/us_census/acs5yr/subject_tables/s2502/input_data/S2502.zip
```

## Process Step

Run the subject table processor from `scripts/us_census/acs5yr/subject_tables`:

```bash
cd scripts/us_census/acs5yr/subject_tables

python3 process.py \
  --option=all \
  --table_prefix=S2502 \
  --has_percent=True \
  --debug=False \
  --spec_path=s2502/s2502_spec.json \
  --input_path=s2502/input_data/S2502.zip \
  --output_dir=s2502
```

- `--option=all`: Runs both column map generation (`column_map.json`) and observation processing (`S2502_cleaned.csv`, `S2502_output.mcf`, `S2502_output.tmcf`, `S2502_summary.json`).
- `--has_percent=True`: Converts percentage estimates into count values using the mapped denominator keys in `s2502_spec.json`.

## Notes

1. This import is based on the characteristics of the population living in occupied housing units. The demographic characteristics include race, age, and educational attainment of householders in owner-occupied housing units and renter-occupied housing units, as well as the year in which the householder moved into the housing unit. The dataset does not include special measurements like mean or median.
2. This dataset has statistics represented as percentages between 2010 and 2016, which are converted to counts using the mapped denominator columns specified under `denominators` in `s2502_spec.json`.
3. For the 2020–2024 releases, the Census Bureau updated the move-in year intervals (`Moved in 2019 or later`, `Moved in 2015 to 2018`, `Moved in 2021 or later`, `Moved in 2018 to 2020`, `Moved in 2010 to 2017`, `Moved in 2023 or later`, `Moved in 2020 to 2022`, and `Moved in 2010 to 2019`), which are mapped under `dateMovedIn` in `s2502_spec.json`.

