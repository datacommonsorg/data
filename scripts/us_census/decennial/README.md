# Decennnial Census Redistricting Files Import

Includes cleaning scripts to process the 2010 and 2020 Decennial Census'
Redistricting File. This is a preliminary release before the full Summary Files
are released and before the data is updated on https://data.census.gov.

The import contains new data for about 11 existing StatVars (see
`_DATAF_STATVAR_MAP` in code) from two tables.  The corresponding tables from
2010 Decennial Census are:
*  [DECENNIALPL2010.P1](https://data.census.gov/cedsci/table?q=p1&tid=DECENNIALPL2010.P1&hidePreview=true)
*  [DECENNIALPL2010.H1](https://data.census.gov/cedsci/table?q=p1&tid=DECENNIALPL2010.H1&hidePreview=true)

## File Format

These files have a very specific coded format, containing a geo-file that has
the "local-record-id" for all geos.  There are 3 data-files that are keyed by
that "local-record-id", followed by a hundred or so StatVar values. Such a set
of files exist for every year and state/US.

## Download

The data is available at the Census FTP site:
* [2010](https://www2.census.gov/programs-surveys/decennial/2010/data/01-Redistricting_File--PL_94-171/)
* [2020](https://www2.census.gov/programs-surveys/decennial/2020/data/01-Redistricting_File--PL_94-171/)

It is saved in GCS at gs://datcom-csv/census/decennial.

## Generation

1. Run the `download.sh`, which fetches the files from GCS to your local
   computer under `scratch/` directory

2. Run the `process.py` script, as:

  ```python3 process.py```

  This will generate all the CSVs under `output/<year>/<state|National>.csv`.

