# OECD Regional Demography Statistics Imports

## OECD Dataset Import Overview

### Download csv files

This is the overall link for regional demographics [dataset](https://stats.oecd.org/index.aspx?DataSetCode=REGION_DEMOGR). You can click on export menu and get .csv files for the specific dataset.

### Directories

We have five subdirectories for now, there are:

- [deaths](deaths) (Deaths by 5-year age groups,small regions TL3)
- [life_expectancy_and_mortality](life_expectancy_and_mortality) (Life Expectancy and Mortality, large TL2 and small TL3 regions)
- [pop_density](pop_density) (Population density and area, large TL2 and small TL3 regions)
- [population_tl2](population_tl2) (Population by 5-year age groups, large regions TL2)
- [population_tl3](population_tl3) (Population by 5-year age groups, small regions TL3)

## Import Artifacts

### OECD ID to DCID mapping

[regid2dcid.json](regid2dcid.json): the mapping from OECD IDs to DCIDs. See the section "Getting/Imrpoving DCIDs for OECD geos" for updating the mapping.

### Raw Data

Note: in each subdirectory, the source csv files are named like `REGION_DEMOGR_{subdirectory name}.csv`.

### Cleaned Data

All the cleaned CSVs are saved in each subdirectory, named as `OECD_{subdirectory name}_cleaned.csv`.

### StatisticalVariables MCF files

The MCF files are in each subdirectory, named by `OECD_{subdirectory name}_stat_vars.mcf`. Note that [population_tl3/OECD_population_stat_vars.mcf](population_tl3/OECD_population_stat_vars.mcf) is a symlink to [population_tl2/OECD_population_stat_vars.mcf](population_tl2/OECD_population_stat_vars.mcf).

### StatVarObservation Template MCF files

The template MCF files are in each subdirectory, named by `OECD_{subdirectory name}.tmcf`.

### Script

The script file `preprocess_csv.py` in each subdirectory is used to generate cleaned CSV and template MCF files.

## Generating Artifacts

To generate the cleaned csv and template MCF files, run

```bash
python3 preprocess_csv.py
```

## Getting/Improving DCIDs mappings for OECD geos

To update [regid2dcid.json](regid2dcid.json):

1. Download the List of regions and typologies xls file.

NOTE: this is already done and saved as [geos.csv](geos.csv). Only do this step if for some reason you feel that file needs updating.

The xls file can be found in the info sidebar of the regional
demographics dataset
[page](https://stats.oecd.org/index.aspx?DataSetCode=REGION_DEMOGR)

Export the "List of regions" sheet to CSV and save it in this directory.

1. Clean the CSV: `python3 clean_geos_csv.py`

- This is where we append a place type to the place name,
  such as "AdministrativeArea1", as a hint to the place name resolver.
- This is also where we remove regions that are statistical
  regions, non official regions, etc. Essentially, we only
  keep places that are real administrative areas.
  - Whether places are statistical, administrative, or
    other regions are determined based on the
    [OECD Regions at a Glance Documentation](https://www.oecd-ilibrary.org/sites/reg_glance-2016-en/1/3/1/index.html?itemId=/content/publication/reg_glance-2016-en&_csp_=c935435269a6598b27c5166da7d1ad21&itemIGO=oecd&itemContentType=book#ID1d8692e3-637b-4fdc-9097-245b08f9948a) and further Googling.

Note: After further investigation/improved understanding of the regions,
update the special casing logic in this file.
E.g. when we realize that Japan TL2 is actually not an AdminArea,
but TL3 is, we should add a special case to append "AdministrativeArea1"
to the place names of TL3 regions, not the TL2 regions.

1. Use the `place_name_resolver` tool to add a `dcid` column to the CSV:

```
go run ../../../tools/place_name_resolver/resolver.go --in_csv_path=geos_cleaned.csv --out_csv_path=geos_resolved.csv --maps_api_key=YOUR_API_KEY
```

1. Clean the resolved CSV: `python3 clean_geos_resolved_to_dict.py`

- This is where we take the CSV result of the `place_name_resolver` tool
  and create [regid2dcid.json](regid2dcid.json).
- Here, we discard certain `dcid` column results from `place_name_resolver`,
  when we know we can derive the DCIDs from OECD IDs.
  - For countries, we directly use `"country/" + OECDId`.
  - For NUTS regions (those present in [region_nuts_codes.json](region_nuts_codes.json)), we directly use `"nuts/" + OECDId`.
  - For US states, we directly use `"geoId/" + OECDId_without_the_US_prefix`.
- Furthermore, if the `place_name_resolver` tool assigned the same DCID to multiple regions,
  we remove the later occurrences so that there is no conflict.

Note: After further investigation/improved understanding of the regions,
update the special casing logic in this file.
E.g. when we realized that USA TL2 OECD IDs are based on FIPS codes,
we added a special case to discard the resolver output in favor of
creating DCIDs based on the OECD ID.

## Geo Resolution Tracking

Run `python3 gen_place_mapping_stats.py > stats.txt` to regenerate the
geo resolution statistics. The diffs in [stats.txt](stats.txt) will help track
geo resolution changes. If the file is open in an IDE, remember to save
the edits from running the script.

To track changes to the final OECD region ID to DCID map (which uses the geo
resolution results but overwrites countries, NUTS, USA states, and other special
cases as specified in
[clean_geos_resolved_to_dict.py](clean_geos_resolved_to_dict.py)) just look at diffs in
[regid2dcid.json](regid2dcid.json).
