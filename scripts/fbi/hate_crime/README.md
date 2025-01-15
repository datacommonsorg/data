# Importing FBI Hate Crime Data

This directory imports [FBI Hate Crime Data](https://ucr.fbi.gov/hate-crime) into Data Commons. It includes data at US, state and city level.

## Generating Artifacts:
To generate `cleaned.csv`, `output.mcf` for a publication. run:

```bash
cd table<publication number>
python3 preprocess.py
```

### Data Caveats:
- New Jersey is missing data for year 2012 in publications 11 and 12
- Data for a few locations of crime (publication 10) are missing for certain years
- The output MCF generated from these files is not used due to the change in populationType from 'CriminalIncidents' to 'HateCrimeIncidents' and removal of the 'isHateCrime' property in the statvar definitions. The definitions for the statvars come from the hate crime aggregation scripts.

## Download Publication Tables
The source has changed to https://cde.ucr.cjis.gov/LATEST/webapp/#/pages/home which wont allow to download the data through script, so we have to manually download the source data.
Steps to download latest publications data: 
1) Go to https://cde.ucr.cjis.gov/LATEST/webapp/#/pages/explorer/crime/hate-crime
2) From the left panel go to "Documents & Downloads"
3) Go to "Hate Crime Statistics Annual Reports" and here select the year from drop down and click on "Download"

### Notes
### Aggregation : 
The new source website dont have the historical hate crime publications data, so for refreshing the data downloaded the latest files (2020,2021,2022 and 2023) and downloaded the historical data (2004 to 2019) from BigQuery database.
Also now the aggregation script reads the configs and input csv from GCS bucket. Download and upload the data from source to "gs://unresolved_mcf/fbi/hate_crime/20250107/". If the input data is in a different path pass the path using --input

### Examples
python3 preprocess_aggregation.py --input=gs://unresolved_mcf/fbi/hate_crime/20250107/hate_crime.csv --config=gs://unresolved_mcf/fbi/hate_crime/20250107/config.json

### Publication Table :
Each table has respective processing script in the corresponding folders. The script is expecting the input data in a GCS buckt. Download and upload the data and upload to respective folders in "unresolved_mcf/fbi/hate_crime/20250107/". There is a config file which contains the links to the input data and expected columns.

### Examples
python3 preprocess.py --config_file=gs://unresolved_mcf/fbi/hate_crime/20250107/table_config.json


## Aggregations from master file

`preprocess_aggregations.py` creates aggregations from master file with each individual incident recorded. The script outputs individual files for each type of aggregation to ease debugging and a combined `aggregation.csv` file under `aggregations` folder with all the final observations.

To create aggregations
```bash
python preprocess_aggregations_test.py
```


### Changes required for final mcf file

The output mcf file is produced such that the DCIDs are present. In order to get the final version of the stat vars following changes need to be made:
- drop `isHateCrime` property
- change `populationType` to be `HateCrimeIncidents`
- `biasMotivation: dcs:TransgenderOrGenderNonConforming` to `biasMotivation: dcs:gender` and `targetedGender: dcs:TransgenderOrGenderNonConforming`
- add `offenderType` property with value from `KnownOffender`, `KnownOffenderRace`, `KnownOffenderEthnicity`, `KnownOffenderAge` where applicable.
