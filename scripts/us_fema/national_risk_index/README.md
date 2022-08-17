# Importing FEMA National Risk Index (NRI) Data

This directory imports the [FEMA NRI](https://hazards.fema.gov/nri/) dataset
into Data Commons. The study includes relative measures of risks from 18 hazards
to the US at the county and tract level, as well as data on individual hazards
and their estimated risk to those affected.

Source data can be downloaded from this [download page](
https://hazards.fema.gov/nri/Content/StaticDocuments/DataDownload//NRI_Table_CensusTracts/NRI_Table_CensusTracts.zip
).

# Instructions

## Generating Artifacts

Run `sh/e2e.sh`

Under the hood, this will download the files from source using `sh/download_data.sh` and process
them using `sh/process_data.sh`.

As a result, the following files will be in the `output` directory

1. `fema_nri_schema.mcf` holds the Schema for the StatisticalVariables in the
dataset
1. `fema_nri_counties.tmcf` holds the TMCF nodes for importing the dataset at
the county level (a.k.a. `nri_table_counties.csv`)
1. `nri_table_counties.csv` holds the actual NRI study data, cleaned and
prepared to be imported
1. `nri_table_tracts.csv` is same as above, but for census tracts

## Linting

Follow instructions in the root of the repo, namely, run `./run_tests.sh -f`
in the base of the repo.

## Running Tests

Follow instructions in the root of the repo, namely, run
```
python3 -m unittest discover -v -s ../ -p "*_test.py"
```
in this folder.

To replace the test goldens under `test_data` with the format `expected_test_*`,
run `sh/gen_test_golden.sh` while the current directory is `data/scripts/fema/nri`

# Folder Structure

`source_data` holds original files downloaded from
[the official data download page](https://hazards.fema.gov/nri/data-resources)
 - It does not include tract level data, since the file size is roughly 500MB
 zipped. Please download from original source

`output` holds script outputs (the artifacts)

`test_data` holds data files used for testing

`sh` is for convenience scripts

`util` is for common constants for Python scripts
