# OECD Regional Statistics Imports

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

