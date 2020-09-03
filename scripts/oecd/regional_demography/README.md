# OECD Regional Demography Statistics Imports

## Getting DCIDs for OECD geos

1. Download the List of regions and typologies xls file.

The xls file can be found in the info sidebar of the regional
demographics dataset
[page](https://stats.oecd.org/index.aspx?DataSetCode=REGION_DEMOGR)

2. Export the "List of regions"  sheet to CSV and save it in this directory.

3. Clean the CSV: `python3 clean_geos_csv.py`

4. Use the `place_name_resolver` tool to add a `dcid` colum to the CSV:

```
go run ../../../tools/place_name_resolver/resolver.go --in_csv_path=geos_cleaned.csv --out_csv_path=geos_resolved.csv --maps_api_key=YOUR_API_KEY
```

5. Clean the resolved CSV: `python3 clean_geos_resolved_to_dict.py`

## OECD Dataset Import Overview

### Download csv files

This is the overall link for regional demographics [dataset](https://stats.oecd.org/index.aspx?DataSetCode=REGION_DEMOGR). You can click on export menu and get .csv files for the specific dataset.

### Directories

We have five subdirectories for now, there are:
* deaths (Deaths by 5-year age groups,small regions TL3)
* life_expectancy_and_mortality (Life Expectancy and Mortality, large TL2 and small TL3 regions)
* pop_density (Population density and area, large TL2 and small TL3 regions)
* population_tl2 (Population by 5-year age groups, large regions TL2)
* population_tl3 (Population by 5-year age groups, small regions TL3)

## Import Artifacts

### Raw Data
Note in each subdirectory, all the source csv files are name by `REGION_DEMPGR_{subdirectory name}.csv`.

### Cleaned Data
All the cleaned data are named by `OECD_{subdirectory name}_cleaned.csv`.

### StatisticalVariables(MCF) files
All the MCF files are named by `OECD_{subdirectory name}_stat_vars.mcf`. Except population TL2 and TL3, these two datasets have the same MCF files.

### Template MCFs
All the template MCF files are named by `OECD_{subdirectory name}.tmcf`.

### Script
The script file `preprocess_csv.py` is used to generate cleaned csv files and template MCFs.

## Generating Artifacts
To generate the cleaned csv and template MCF files, run
```bash
python3 preprocess_csv.py
```

## Geo Resolution Tracking

Run `python3 gen_place_mapping_stats.py > stats.txt` to regenerate the
geo resolution statistics. The diffs in stats.txt will help track
geo resolution changes.

