# Importing FEMA National Risk Index (NRI) Data

This directory imports the [FEMA NRI](https://hazards.fema.gov/nri/) dataset into Data Commons. The study includes relative measures of risks from 18 hazards to the US at the county and tract level, as well as data on individual hazards and their estimated risk to those affected.

# Instructions to Generate Artifacts

To generate the schema and the TMCF for the import, run
```
python3 generate_schema_and_tmcf.py
```

This will generate the following files under the `output` directory

1. `fema_nri_schema.mcf` holds the Schema for the StatisticalVariables in the dataset
2. `fema_nri_counties.tmcf` holds the TMCF nodes for importing the dataset at the county level (a.k.a. `NRI_Table_Counties.csv`)


# Folder Structure

`source_data` holds original files downloaded from [the official data download page](https://hazards.fema.gov/nri/data-resources)

`output` holds script outputs (the artifacts)