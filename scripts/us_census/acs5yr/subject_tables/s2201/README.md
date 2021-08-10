# Importing Census ACS5Year Table S2201

## Input Data

The data is downloaded from
`https://www.census.gov/acs/www/data/data-tables-and-tools/subject-tables/` and
is stored in GCS at
`datcom-csv/census/acs5yr/subject_tables/s2201/`.
Currently, we have data from 2010-2019 and observations for the Statistical
Variables listed in
`stat_vars.csv`.

## Generate Import Files

To generate tMCF and CSV files:

```
python3 process.py
```

The outputs will be
`s2201.tmcf` and `s2201.csv`.

To run unit tests:

```
python3 process_test.py
```
