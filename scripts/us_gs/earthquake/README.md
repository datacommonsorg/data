# Importing USGS earthquake data

This directory containts the import scripts for [global earthquake events](https://www.usgs.gov/programs/earthquake-hazards/what-we-do-earthquake-hazards-program). The source data is downloaded from the USGS [website](https://www.usgs.gov/programs/earthquake-hazards/earthquakes).

## Usage

Make sure you are in virtualenv.

```sh
python scripts/us_gs/earthquake/preprocess.py
```

## Notes

- For the query params, the data you get is [starttime, endtime). For example, if `starttime=2011-03-11` and `endtime=2011-03-12`, the response contains all data that happens on 2011 March 11 exactly.

- Currently `download.sh` will downlaod all earthquake events from 2022 Oct 7 to the date when the script is run. Since USGS earthquake data is updated at source frequently, running the script at a later time in the day should result in more data.
