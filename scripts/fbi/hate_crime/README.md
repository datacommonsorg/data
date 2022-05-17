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
The `download_publication_data.py` script helps download xls files from the [UCR base url for hate crime](https://ucr.fbi.gov/hate-crime). 

The script works using `requests` and `BeautifulSoup` to find the download links.

### Notes
- Currently the script is not able to download data for 2004 and Table 13, 14 for 2005
- By default the extension of saved file is `.xls`. This might cause a problem is extenstions are changed in future
- The script tries to find a link to `Access Tables` at one stage. The first instance of it is used if multiple links are found
- Data for 2020 can be downloaded from the [crime data explorer](https://crime-data-explorer.app.cloud.gov/pages/downloads) website
- The scripts expect the data to be in hate_crime/source_data directory.

### Examples
To download data from 2005 to 2019
```bash
python3 download_publication_data.py
```

To download data for subset of years
```bash
python3 download_publication_data.py --start_year=2010 --end_year=2015
```

To download data from 2005 to 2019 at a different location and force download rather than using `cache`
```bash
python3 download_publication_data.py --store_path=./publications --force_fetch
```

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


## Download Publication Tables

The `download_publication_data.py` script helps download xls files from the [UCR base url for hate crime](https://ucr.fbi.gov/hate-crime). 

The script works using `requests` and `BeautifulSoup` to find the download links.

### Notes

- Currently the script is not able to download data for 2004 and Table 13, 14 for 2005
- By default the extension of saved file is `.xls`. This might cause a problem is extenstions are changed in future.
- The script tries to find a link to `Access Tables` at one stage. The first instance of it is used if multiple links are found.
- It is a good idea to check the size or content type(pandas load) of data for a sanity check. If some error was encountered, HTML data might be stored in the file making it unusable with xls applications.

## Examples

To download data from 2005 to 2019
```bash
python3 download_publication_data.py
```

To download data for subset of years
```bash
python3 download_publication_data.py --start_year=2010 --end_year=2015
```

To download data from 2005 to 2019 at a different location and force download rather than using `cache`
```bash
python3 download_publication_data.py --store_path=./publications --force_fetch
```
