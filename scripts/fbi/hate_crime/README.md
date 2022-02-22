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