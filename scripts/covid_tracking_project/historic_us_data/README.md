# Importing The COVID Tracking Project's Historic US Data

This directory contains artifacts required for importing
The COVID Tracking Project's Historic US Data
into Data Commons, along with scripts used to generate these artifacts.

To generate `COVIDTracking_US.tmcf` and `COVIDTracking_US.csv`, run:

```bash
python3 preprocess_csv.py
```

#### Note:

`COVIDTracking_US_StatisticalVariables.mcf` is actually the same as `COVIDTracking_States_StatisticalVariables.mcf` in /historic_state_data/ folder, so we don't need to check it here.

Also, will have a future version to combine US level and states level data together. Coming soon.