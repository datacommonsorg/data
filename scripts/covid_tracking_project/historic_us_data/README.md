# Importing The COVID Tracking Project's Historic US Data

This directory contains artifacts required for importing
The COVID Tracking Project's Historic US Data
into Data Commons, along with scripts used to generate these artifacts.

## Artifacts:

- [COVIDTracking_US.csv](COVIDTracking_US.csv): the cleaned CSV.
- [COVIDTracking_US.tmcf](COVIDTracking_US.tmcf): the mapping file (Template MCF).
- [COVIDTracking_US_StatisticalVariables.mcf](COVIDTracking_US_StatisticalVariables.mcf):
  the new StatisticalVariables defined for this dataset.

## Generating Artifacts:

`COVIDTracking_US_StatisticalVariable.mcf` was handwritten.

To generate `COVIDTracking_US.tmcf` and `COVIDTracking_US.csv`, run:

```bash
python3 preprocess_csv.py
```