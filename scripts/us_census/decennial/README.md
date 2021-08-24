# Decennnial Census - Redistricting Files

Includes cleaning scripts to process the 2010 and 2020 Decennial Census'
Redistricting Files. This is a preliminary release before the full Summary Files
are released and before the data is available on https://data.census.gov.

The import contains new data for about 11 existing StatVars (see
`_DATAF_STATVAR_MAP` in code) from two tables.  The corresponding tables from
2010 Decennial Census are:
*  [DECENNIALPL2010.P1](https://data.census.gov/cedsci/table?q=p1&tid=DECENNIALPL2010.P1&hidePreview=true)
*  [DECENNIALPL2010.H1](https://data.census.gov/cedsci/table?q=p1&tid=DECENNIALPL2010.H1&hidePreview=true)

Includes the following place types in the US:
* Country
* State
* County
* County Subdivision
* Census Tract
* Census Block Group
* Place (aka City)

Notably, Census ZCTA is missing from this dataset, and there doesn't seem to be
a reference to it in the docs (linked below).

## File Format

These files have a very specific coded format, containing a geo-file that has
the "local-record-id" for all geos.  There are 3 data-files that are keyed by
that "local-record-id", followed by a set of values, one per StatVar. This set
of files repeats for every year and every state/US.

The format of the geo-file and data-files are described in these documents:
* [2010](https://www.census.gov/prod/cen2010/doc/pl94-171.pdf)
* [2020](https://www2.census.gov/programs-surveys/decennial/2020/technical-documentation/complete-tech-docs/summary-file/2020Census_PL94_171Redistricting_NationalTechDoc.pdf)

Generally, between 2010 and 2020, the Data tables and data-file formats have
stayed the same (except for a change in delimiter), but the geo-file format is
quite different. Thus, the code has different maps for 2010 and 2020 geo-files.

## Download

The data is available at the Census FTP site:
* [2010](https://www2.census.gov/programs-surveys/decennial/2010/data/01-Redistricting_File--PL_94-171/)
* [2020](https://www2.census.gov/programs-surveys/decennial/2020/data/01-Redistricting_File--PL_94-171/)

It is saved in GCS at `gs://datcom-csv/census/decennial`.

## Generation

1. Run the `download.sh` script, which copies the raw files from GCS to your
   computer under `scratch/` directory.

2. Run the `process.py` script, as:

   `python3 process.py`

   This will generate all the CSVs in `output/<year>/*.csv`.  Together with
   `decennial_us_census.tmcf`, they can be validated and imported into Data
   Commons.

