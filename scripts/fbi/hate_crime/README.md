# Importing FBI Hate Crime Data

This directory imports [FBI Hate Crime Data](https://ucr.fbi.gov/hate-crime) into Data Commons. It includes data at US, state and city level.
Original publications downloaded from ucr.fbi.gov are copied into the repository under source_data.

## Data Caveats:
- New Jersey is missing data for year 2012 in publications 11 and 12.
- Data for a few locations of crime (publication 10) are missing for certain years.

## Generating Artifacts:
To generate `cleaned.csv`, `output.mcf` for a publication. run:

```bash
cd table<publication number>
python3 preprocess.py
```