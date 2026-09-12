# Resolving place IDs for Sub-national Demographic data - Worldbank Population

## About the Dataset
This dataset has Population Estimates for the Sub-national Demographic data - Worldbank Population for Country and States from 2000 to 2016. 

### Resolving Place IDs
The following steps resolve place and create mapping dcids for place.

  #### Resolving Place for the input source
   - The source has a column "Country Name" whose values are unresolved place.
   - The column "Country Name" is renamed as "name" and a new column "administrative_area" is added to it
        whose value is "AdministrativeArea1". 
   - The file is saved in and as `scripts/world_bank/subnational_population/dcid_resolve/place_input.csv`
   - This file is passed into place_resolver.py script.
   - The Place Resolver script generates dcids from DataCommons based on Place Name.
   - The file is saved in and as `scripts/world_bank/subnational_population/dcid_resolve/place_dcid.csv`

  #### Using APIs to get property values
   - The dcids generated from the place resolver are converted to a list and passed throug APIs to 
   get "typeOf" and "alternateName".
   - The "typeOf" and "alternateName" generated are added back to the file as columns.

  #### Extracting all the available AdministrativeArea1 dcids from DataCommons 
   - The "build_geo_mapping.py" script generates all "AdministrativeArea1" dcids from DataCommons along with place.
   - It takes "country_dcid.csv" as reference to generate the dcids.
   - The "country_dcid.csv" is present in `scripts/world_bank/subnational_population/reference_files`
   - It saves the generated output in the following path
    `scripts/world_bank/subnational_population/output_files/tmp_country_level1_map.csv`
    
  #### Normalising and mapping Place names
   - Now two generated files are considered ->  "place_dcid.csv" and "tmp_country_level1_map.csv".
   - The Place columns in both the files are separated into "country_name" and "place_name".
   - Both the columns are normalised which means the prefixes in place_name is removed and both the columns are converted to lower case.
   - This is done to match the names of country column generated from input file and country column generated from DataCommons.
   - The same matching is done with place name column as well.

  #### Creating mapping dcid file
   - Now in the end there are two files "place_dcid.csv" and "tmp_country_level1_map.csv".
   - Merge both the files based on lower order country name and lower order place name.
   - Write the merged dataframe to a csv file.
   - For the rows that are mapped, create a json dictonary file named as "countrystatecode.json" with the following path `scripts/world_bank/subnational_population/countrystatecode.json`
     - Example: {
        "Afghanistan": "dcid:country/AFG",
        "Afghanistan, Badakhshan": "dcid:wikidataId/Q165376",
        "Afghanistan, Badghis": "dcid:wikidataId/Q172052",
        "Afghanistan, Baghlan": "dcid:wikidataId/Q170309"
        }
   - There are certain places that are not mapped. For the unmapped places, search the wiki id in wikipedia and verify the dcid shown in wikipedia with DataCommons. Give it as `browser/wikidataId/{dcid}` in DataCommons.

### Import Procedure

The below script will run the preprocess script and generate mapped places.
Give the api key and run the code.

`/bin/python3 scripts/world_bank/subnational_population/preprocess.py --maps_key=''`
