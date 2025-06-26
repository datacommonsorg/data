# Importing EPH Heat and Heat-related Illness data

This directory imports [Heat and Heat-related Illness](https://ephtracking.cdc.gov/qrlist/35) from EPH Tracking into Data Commons. It includes data at a state level.

## Cleaning source data
The source data is available from the EPH [website](https://ephtracking.cdc.gov/qrlist/35). Currently, this import brings in data related to [Heat-related Emergency Department Visits](https://ephtracking.cdc.gov/qrd/438), [Heat-Related Mortality](https://ephtracking.cdc.gov/qrd/370), and [Heat-related Hospitalizations](https://ephtracking.cdc.gov/qrd/431).

To download and clean the source data, run:

`python clean_data.py`

This clean_data.py script is used to download the html files from source url and then converts them into csv files. These multiple csv files are then combined into one csv file specific to different categories such as hospitalizations, hospitalizations_age, hospitalizations_gender, hospitalizations_age_by_gender, edVisits, edVisits_age, edVisits_gender, edVisits_age_by_gender and deaths.
Final csv input files are available in `source_data/combined_csv_files/` directory.

## Generating artifacts at a State level & Aggregating at a Country level:
The artifacts can be generated from the cleaned data and At a country level, aggregation is performed by summing over the state level `cleaned.csv` and country level data is generated as `state/country_output.csv`.

To generate `cleaned.csv`, `output.mcf`, `output.tmcf` and `country_output.csv`run:

```bash
python preprocess.py
```

## Data Caveats:
- Suppressed data points are skipped.
- Data for heat related deaths is heavily suppressed.
- State level data is aggregated to get the country level data.
