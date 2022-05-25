# Importing EPH Heat and Heat-related Illness data

This directory imports [Heat and Heat-related Illness](https://ephtracking.cdc.gov/qrlist/35) from EPH Tracking into Data Commons. It includes data at a state level.

## Cleaning source data
The source data is downloaded manually from the EPH [website](https://ephtracking.cdc.gov/qrlist/35). Currently, this import brings in data related to [Heat-related Emergency Department Visits](https://ephtracking.cdc.gov/qrd/438), [Heat-Related Mortality](https://ephtracking.cdc.gov/qrd/370), and [Heat-related Hospitalizations](https://ephtracking.cdc.gov/qrd/431).
To clean the source data, run:

```bash
python clean_data.py --input_path=source_data/ --output_path=<output_path>
```

## Generating artifacts at a State level:
The artifacts can be generated from the cleaned data.
To generate `cleaned.csv`, `output.mcf` run:

```bash
python preprocess.py --input_path=<directory path to cleaned data> --config_path=<path to config> --output_path=<directory path to write csv and mcf>
```

## Aggregating at a Country level
At a country level, aggregation is performed by summing over the state level `cleaned.csv`.
To aggregate run:

```bash
python aggregate.py --input_path=<path to state level csv> --output_path=<output csv path>
```

## Data Caveats:
- Suppressed data points are skipped.
- Data for heat related deaths is heavily suppressed.
- State level data is aggregated to get the country level data.
