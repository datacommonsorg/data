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

This will generate the following files under the `output` directory

1. `fema_nri_schema.mcf` holds the Schema for the StatisticalVariables in the
dataset
2. `fema_nri_counties.tmcf` holds the TMCF nodes for importing the dataset at
the county level (a.k.a. `NRI_Table_Counties.csv`)

## Linting

Code was linted with [yapf](https://github.com/google/yapf/), as recommended by
the [Google Python Style Guide](https://github.com/google/styleguide/blob/gh-pages/pyguide.md).

To lint a file called `some_file.py` in-place (applying modifications to it),
run the following:
```
yapf some_file.py --style=yapf -i
```

# Folder Structure

`source_data` holds original files downloaded from
[the official data download page](https://hazards.fema.gov/nri/data-resources)

`output` holds script outputs (the artifacts)

