# Importing Census ACS5Year Subject Tables

This folder contains a general-purpose script for importing ACS subject tables. It is based off the import for the S2201 table, so might need some tweaks to support additional tables. Please feel free to update the script!

Note: the script currently only supports dcids with the `geoId/` prefix (states, counties, places, etc.).

The script expects the following flags:

* `output`: This is the path to the folder where the TMCF and CSV files will be generated.
* `download_id`: This is a param that is used to fetch the source data from `https://www.census.gov/acs/www/data/data-tables-and-tools/subject-tables/`. To find the `download_id`, select the desired Geos and Years for the table, then click the "Download" button. If you Inspect Network, there should be a request of the form `https://data.census.gov/api/access/table/download?status&download_id=[DOWNLOAD_ID]`.
* `features`: This is the path to a JSON which contains custom mappings used to generate the Statistical Variables for the table and other info for the TMCF. These must be manually curated for each table and are based on the descriptive column names in the source data. Each descriptive column name has various features which are separated by `!!`. (For example, the descriptive column name `Estimate!!Total!!Households` includes the features `Estimate`, `Total`, and `Households`.) The JSON include the following optional maps:
  * `base`: This maps a feature to a "base Statistical Variable" that typically includes the `measuredProperty` and `populationType` and does not include any property values. (For example, the feature `Median income (dollars)` is mapped to the base `Median_Income_Household`, and the Statistical Variable `Count_Household_WithFoodStampsInThePast12Months` has a base of `Count_Household`.) This map should also have a `_DEFAULT` key option, which will be used if no other base is found.
  * `properties`: This maps a feature to a property value. (For example, the feature `Households receiving food stamps` is mapped to the property value `WithFoodStampsInThePast12Months`.)
  * `implied_properties`: This maps a feature to a list of features that imply it. We only use the most specific feature to generate the Statistical Variable. (For example, the feature `Male householder, no spouse present`, which is mapped to the property value `SingleFatherFamilyHousehold`, is only measured for the feature `Other family`, which is mapped to the property value `OtherFamilyHousehold`. However, both values are in the range of the property `householdType`, so we only include the most specific one.)
  * `inferred_properties`: This maps a feature to a feature that is inferred by it, but not explictly listed in the descriptive column name. We add the inferred property value to the Statistical Variable. (For example, the feature `No workers in past 12 months`, which is mapped to the property value `NoWorkersInThePast12Months`, is only measured for the feature `Families`, which is mapped to the property value `FamilyHousehold`, even though `Families` is not part of the descriptive column name. However, these values are in the ranges of different properties, so we should include both.)
  * `units`: This maps a Stastical Variable to a unit, which will be added to the TMCF. (For example, the Statistical Variable `Median_Income_Household_WithFoodStampsInThePast12Months` is mapped to the unit `USDollar`.)
* `stat_vars`: This is the path to a file that contains a list of supported Statistical Variables. When generating new Statiscal Variables from descriptive column names, variables not in this list will be skipped.

See the `s2201` folder for an example of these files.

To run the script, from the parent directory (`subject_tables`), run:

```
python3 common/process.py --output=[OUTPUT] --download_id=[DOWNLOAD_ID] --features=[FEATURES] --stat_vars=[STAT_VARS]
```

This will generate the files `output.tmcf` and `output.csv` in the path specified by the `output` flag.
