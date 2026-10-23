# US census ACS5YR S2408 Subject Table import

This subject table provides data on the class of workers by sex.

Years: 2010-2024  
Geo: Country, State, County, County Subdivision, Census Tract, Place (City), Congressional District, ZCTA, and School Districts (Summary Levels: `010`, `040`, `050`, `060`, `140`, `150`, `160`, `500`, `860`, `950`, `960`, `970`)

## Download Data

To download the raw S2408 table data (`S2408.zip`) from the US Census API for 2010–2024 across all available summary levels, run from `scripts/us_census/api_utils`:

```shell
python3 census_api_data_downloader.py \
  --dataset=acs/acs5/subject \
  --table_id=S2408 \
  --start_year=2010 \
  --end_year=2024 \
  --all_summaries \
  --output_path=<output_dir> \
  --api_key=<your_api_key>
```

## Process Data

To generate the `column_map.json`, `S2408_cleaned.csv`, `S2408_output.mcf`, and `S2408_output.tmcf` files using the custom `S2408SubjectTableLoader`, run from `scripts/us_census/acs5yr/subject_tables/s2408`:

```shell
python3 process.py \
  --option=all \
  --table_prefix=S2408 \
  --has_percent=True \
  --debug=False \
  --spec_path=S2408_spec.json \
  --input_path=<output_dir>/acs/acs5/subject/S2408/S2408.zip \
  --output_dir=.
```

## Running Tests

To run the unit tests for S2408 from the repository root (`data/`):

```shell
python3 -m unittest scripts/us_census/acs5yr/subject_tables/s2408/subject_table_s2408_test.py
```

## Notes
1. The data on 'Median Earnings' for 2010-2014 is available in table S2408. From 2015 onwards, this data is available in the table S2418.
2. Only percentages are provided for Male and Female counts from 2010-2014. This will be converted to counts through the code (`S2408SubjectTableLoader` in `s2408/process.py`).
