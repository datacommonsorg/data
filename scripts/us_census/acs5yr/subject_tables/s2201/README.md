# Importing Census ACS5Year Table S2201

## Input Data

The data is downloaded from
`https://www.census.gov/acs/www/data/data-tables-and-tools/subject-tables/` and is organized by year.
Currently, we have data from 2010-2023 and observations for the Statistical
Variables listed in
`stat_vars.csv` for US states, counties, and places (cities).
## Generate Import Files

To generate TMCF and CSV files, from parent directory (`subject_tables`), run:

```
python3 common/process.py --output=s2201 --download_id=df462630dbf2e2a5f4ec4d7768b8338d00f24adc0535e5393b2335ac196d5cd0 --features=s2201/features.json --stat_vars=s2201/stat_vars.csv
```

The outputs will be
`s2201/ouput.tmcf` and `s2201/output.csv`.
 
To run unit tests, from this directory, run:

```
python3 process_test.py
```
