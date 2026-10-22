# Importing Census ACS5Year Table S2201

## Input Data

The data is downloaded from
`https://www.census.gov/acs/www/data/data-tables-and-tools/subject-tables/` and is organized by year.
Currently, we have data from 2010-2024 and observations for the Statistical
Variables listed in
`stat_vars.csv` for US states, counties, and places (cities).

## Download data Files

To download the data as a zip file, get the api key and run in directory `scripts/us_census/api_utils`:

```
python census_api_data_downloader.py --dataset=acs/acs5/subject --table_id=S2201 --start_year=2010 --end_year=2024 --summary_levels=010,030,040,050,060,140,160,310,500,860,950,960,970 --output_path=~/us_census --api_key=<your_api_key>
```

## Generate Import Files

Copy the downloaded `~/us_census/acs/acs5/subject/S2201/S2201.zip` to `input_data/S2201.zip` (or pass `--input_zip=~/us_census/acs/acs5/subject/S2201/S2201.zip`). To generate TMCF and CSV files, from this directory (`s2201`), run:

```
python3 process.py --input_zip=input_data/S2201.zip --output=output --features=features.json --stat_vars=stat_vars.csv
```

The outputs will be `s2201/output/output.tmcf` and `s2201/output/output.csv`.

To run unit tests, from this directory, run:

```
python3 process_test.py
```
