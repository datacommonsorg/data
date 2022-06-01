# Importing FEMA National Risk Index (NRI) Data

This directory imports the [FEMA NRI](https://hazards.fema.gov/nri/) dataset
into Data Commons. The study includes relative measures of risks from 18 hazards
to the US at the county and tract level, as well as data on individual hazards
and their estimated risk to those affected.

# Instructions

## Generating Artifacts

To generate the schema and the TMCF for the import, run
```
python3 generate_schema_and_tmcf.py
```

Please download tract level data from the FEMA NRI website, and place the CSV
under the `source_data` folder with the same name. [direct download link](
https://hazards.fema.gov/nri/Content/StaticDocuments/DataDownload//NRI_Table_CensusTracts/NRI_Table_CensusTracts.zip
)
To clean the source data (in CSV format), run
```
python3 process_data.py
```

Running these 2 commands will generate the following files under the `output`
directory

1. `fema_nri_schema.mcf` holds the Schema for the StatisticalVariables in the
dataset
1. `fema_nri_counties.tmcf` holds the TMCF nodes for importing the dataset at
the county level (a.k.a. `NRI_Table_Counties.csv`)
1. `nri_table_counties.csv` holds the actual NRI study data, cleaned and
prepared to be imported
1. `nri_table_tracts.csv` is same as above, but for census tracts

## Linting

Code was linted with [yapf](https://github.com/google/yapf/), as recommended by
the [Google Python Style Guide](https://github.com/google/styleguide/blob/gh-pages/pyguide.md).

To lint all Python files in this directorye, run:
```
sh/lint.sh
```


The underlying command to lint a file called `some_file.py` in-place (applying 
modifications to it) is the following:
```
yapf some_file.py --style='{based_on_style: yapf, indent_width=4}' -i
```

## Running Tests

To run tests, execute

`sh/tests.sh`
 
# Folder Structure

`source_data` holds original files downloaded from
[the official data download page](https://hazards.fema.gov/nri/data-resources)
 - It does not include tract level data, since the file size is roughly 500MB
 zipped. Please download from original source

`output` holds script outputs (the artifacts)

`test_data` holds data files used for testing 
