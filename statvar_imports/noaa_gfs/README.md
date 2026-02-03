# NOAA: Global Forecast System Dataset
## Overview
The NOAA-GFS 0.25 Atmos dataset provides high-resolution global atmospheric and land-surface data on a 0.25-degree (~28km) grid. It includes a wide range of meteorological variables, such as temperature, wind, humidity, precipitation, and soil moisture, generated four times daily with forecasts extending up to 16 days (384 hours).
The dataset provides a standardized global output on a 0.25-degree (~28km) equidistant cylindrical grid, covering the entire Earth's surface and up to 127 vertical atmospheric layers. It is distributed in GRIB2 (Gridded Binary Edition 2) format via the NOAA Operational Model Archive and Distribution System (NOMADS) and is categorized as a public domain product of the United States Government.

## Data Source
**Source URL:**
https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/

**Provenance Description:**
The NOAA Global Forecast System (GFS) 0.25 Atmos dataset is produced and maintained by the National Centers for Environmental Prediction (NCEP), a component of the National Oceanic and Atmospheric Administration (NOAA). The data is generated through the Global Data Assimilation System (GDAS), which integrates global observations from satellites, weather balloons, radar, and commercial aircraft into the Finite Volume Cubed-Sphere (FV3) dynamical core.

## How To Download Input Data
The source contains a huge number of data files. For the correct file:
- Go to the source
- Choose the date of observation.
- Select one of the 4 directories available. These directories represent the data collected 4 times a day.
- Select the atmos directory for atmospheric data.
- There are multiple files available in the directory, some holding vertical soundings, others files with raw, unstructured data for super computers, Surface flux files etc.
- For general mapping and analysis of the GFS data, the following format files are available:
gfs.t00z.pgrb2.0p25.f000
gfs.t00z.pgrb2.0p25.f001
and so on, till gfs.t00z.pgrb2.0p25.f384
- t00z represents the cycle of the day selected out of 4; 0p25 denoting the 0.25 degrees horizontal resolution and fXXX refers to the forecast hour.
- Till the 120th hour, i.e f000 to f120, the data is provided in 1-hour increments. After f120 (Day 5), the data switches to 3-hour increments.
- The .idx file has the metadata and the variables that are present in the main data file.
- The main file is a binary file and can be converted using the wgrib2 tool by NOAA.

The wgrib2 tool is available in Github from NOAA.
- Once the raw data file is downloaded, we use the wgrib2 tool provided by NOAA on github.
- Clone the repository and install the wgrib2 tool.
- Convert the binary file into the desired format (csv) using the command : wgrib2 input_file.grib2 -csv output.csv

**Inventory URL:**
https://www.nco.ncep.noaa.gov/pmb/products/gfs/gfs.t00z.pgrb2.0p25.anl.shtml
This is the URL to the description of the variables.
## Processing Instructions
The processing of data is done using custom script which:
- connects to Google Cloud Storage bucket and opens local CSV file containing raw NOAA GFS weather data
- references the parameter mapping to translate short meteorological codes (like TMP or UGRD) into formal descriptive terms (like Temperature_Place or WindSpeed) and assigns their corresponding scientific units
- runs a cleaning function to standardize "Levels." It converts human-readable strings like "2 m above ground" or "1000 mb" into structured IDs
- It combines the parameter and the level to create Data Commons Identifier (DCID). For example, temperature at the surface becomes dcid:Temperature_Place_SurfaceLevel. (DCID Construction)
- processes the data in batches of 1,000 rows, writing them to a memory buffer before "streaming" that chunk directly to the Google Cloud bucket.

After processing the input csv to the structured output csv, the output.csv is stored in the bucket.
