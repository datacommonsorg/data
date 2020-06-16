# Importing The COVID Tracking Project's Historic State Data

This directory contains artifacts required for importing
The COVID Tracking Project's Historic State Data
into Data Commons, along with scripts used to generate these artifacts.

## Artifacts:

- [COVIDTracking_States.csv](COVIDTracking_States.csv): the cleaned CSV.
- [COVIDTracking_States.mcf](COVIDTracking_States.mcf): the mapping file (Template MCF).
- [COVIDTracking_States_StatisticalVariables.mcf](COVIDTracking_States_StatisticalVariables.mcf):
  the new StatisticalVariables defined for this dataset.

## Generating Artifacts:

`COVIDTracking_States_StatisticalVariable.mcf` was handwritten.

To generate `COVIDTracking_States.tmcf` and `COVIDTracking_States.csv`, run:

```bash
python3 preprocess_csv.py
```

To run the test file `preprocess_csv_test.py`, run:

```bash
python3 -m unittest preprocess_csv_test
```
