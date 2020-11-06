# Census of India - Imports

This directory stores all scripts used to import datasets from Census of India into Data Commons.


## Getting DCIDs for Census Locations

Every census file has the following columns to refer the specific geography

 - State - Two digit state code
 - District - Three digit district code inside the specific state
 - Subdistt - Five digit sub-district code inside the specific state
 - Town/Village - Six digit town or village code
 - Ward - Four digit ward code
 - EB - Six digit Enumeration Block Number
 - Level - If the actual location is India (country), STATE, DISTRICT, SUB-DISTRICT, TOWN, VILLAGE or EB
 - Name - Official Name of the place
 
 We create a column called census_location_id which is of the format `COI{year}-{state}-{district}-{subdistt}-{town_or_village}-{ward}-{eb}` to refer the geography. We also use the above columns to get the dcid using `place_name_resolver`

 ### Steps to get dcids 

1. Download any census file that has this information, one can use [Primary Census Abstract Data Tables (India & States/UTs - Town/Village/Ward Level)](http://censusindia.gov.in/pca/pcadata/pca.html) to get details up Ward/Village. One can use [Primary Census Abstract Data Tables (India & States/UTs - District Level)](http://censusindia.gov.in/pca/DDW_PCA0000_2011_Indiastatedist.xlsx) for upto district level.

2. Currently it loads files from `india_census/geo/data` for the year `2011`. To change edit the file `india_census/geo/clean_census_location_code_generator.py`

2. Clean the CSV: `python -m india_census.geo.clean_census_location_code_generator`

4. It produces a CSV called `india_census_2011_geo_cleaned.csv`

4. Use the `place_name_resolver` tool to add a `dcid` column to the CSV:

```
go run ../../../tools/place_name_resolver/resolver.go --in_csv_path=india_census_2011_geo_cleaned.csv --out_csv_path=india_census_2011_geo_resolved.csv --maps_api_key=YOUR_API_KEY
```

5. Clean the resolved CSV: `python india_census/geo/convert_census_location_to_json.py`

6. It produces a CSV called `india_census_2011_geo_cleaned.json`. It's a simple key value json. Snippet of it looks like this
```
{
    "COI2011-00-000-00000-000000-0000-000000": "dcid:country/IND",
    "COI2011-01-000-00000-000000-0000-000000": "dcid:wikidataId/Q66278313"
}
```



## Primary Census Abstract Data Tables (India, States/UTs - District Level) Overview
- Make sure to run scripts to get dcid for Census Locations first
- Refer the read me inside [primary_census_abstract_data](./primary_census_abstract_data/eadme.md) folder.