# Importing The COVID Tracking Project's Historic US Data

This directory contains artifacts required for importing
The COVID Tracking Project's Historic US Data
into Data Commons, along with scripts used to generate these artifacts.

To generate `COVIDTracking_US.tmcf` and `COVIDTracking_US.csv`, run:

```bash
python3 preprocess_csv.py
```

#### Note:

`COVIDTracking_US.mcf` is actually the same with `COVIDTracking_States.mcf`, so we don't need to actually check it.

Also, will have a future version to combine US level and states level data together. Coming soon.