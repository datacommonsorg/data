# Importing USGS earthquake data

This directory containts the import scripts for [global earthquake events](https://www.usgs.gov/programs/earthquake-hazards/what-we-do-earthquake-hazards-program).

## Usage

Make sure you are in virtualenv and inside this directory.

### Step 1. Download source data

The source data is downloaded from the USGS [website](https://www.usgs.gov/programs/earthquake-hazards/earthquakes).

```sh
./download.sh
```

### Step 2. Generate preprocessed CSV file.

```sh
python preprocess.py
```

### Step 3. Create a PR for the updated place cache file (and any other changes).

## Things to note

- For the query params, the data you get is [starttime, endtime). For example, if `starttime=2011-03-11` and `endtime=2011-03-12`, the response contains all data that happens on 2011 March 11 exactly.
