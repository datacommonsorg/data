# CMIP6 Sea Level Projections (from NASA)

This dataset has been downloaded from the [NASA
PO.DAAC](https://podaac.jpl.nasa.gov/announcements/2021-08-09-Sea-level-projections-from-the-IPCC-6th-Assessment-Report)
website.  It includes all the data for Global and Regional Sea Level projections
reported in the [CMIP6
Report](https://www.ipcc.ch/report/ar6/wg1/downloads/report/IPCC_AR6_WGI_Chapter_09.pdf),
expressed in two ways:
* Sea-level change since CMIP6 reference period (1995-2014), in meters
* Rate of sea-level change, in mm/year

The data is broken down by 5 SSP pathways.  There are a few other custom
scenarios (like “1.5 decC in year 2100 temperature target”), which we will skip
in this poss.

## Download

Download the Global and Regional tar.gz files from
https://podaac-tools.jpl.nasa.gov/drive/files/misc/web/misc/IPCC.  These require
creating an account with PO.DAAC.

## Run

The NetCDF4 file contains two types of geos: Tide Gauge Stations and 1x1 global
grids.

The script has 3 modes of operation to generate: 1. just the places; 2. just the
StatVars, 3. just the StatVarObs.

There is a wrapper shell script that runs all the modes together.

To run it, first extract tar.gz files to a `scratch/` in this directory, and
then just run it as:

`$ ./run.sh`
