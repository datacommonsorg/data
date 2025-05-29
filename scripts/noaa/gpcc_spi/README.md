# GPCC SPI Import

## Overview
These script cover two imports which are:
1. NOAA_GPCC_StandardardizedPrecipitationIndex
2. NOAA_GPCC_StandardardizedPrecipitationIndex_AggPlace


## Scripts
```
download.py
```
Above script creates necessary input files with .nc extention required for processing files and store it in a tmp directory. (/tmp/gpcc_spi/)


```
preprocess_gpcc_spi.py
```
Reads downloaded files from tmp directory and create output csv files in tmp directory itself inside 'out' folder.(/tmp/gpcc_spi/out/)
This script generate output for 'NOAA_GPCC_StandardardizedPrecipitationIndex' Import.
Tmcf for this can be taken from 'scripts/noaa/gpcc_spi/gpcc_spi.tmcf'


```
gpcc_spi_aggregation.py
```
Reads the files generated from 'preprocess_gpcc_spi.py' script from tmp directory, aggragte data based on place and create output csv files in tmp directory itself inside 'agg' folder.(/tmp/gpcc_spi/agg/)
This script generate output for 'NOAA_GPCC_StandardardizedPrecipitationIndex_AggPlace' Import.
Tmcf for this can be taken from 'scripts/noaa/gpcc_spi/gpcc_spi_aggregation.tmcf'

## To run test

```
python3 -m unittest preprocess_gpcc_spi.py
```

```
python3 -m unittest gpcc_spi_aggregation_test.py
```
