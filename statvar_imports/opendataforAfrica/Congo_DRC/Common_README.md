###  Congo DRC - Demographics, Economy, Education And Health

- import_name: "congo_drc_demographics"
               "congo_drc_economy"
               "congo_education"
               "congo_health"

- source:`https://drcongo.opendataforafrica.org/data/#topic=Demographics`
          https://drcongo.opendataforafrica.org/data/#topic=Economy
          https://drcongo.opendataforafrica.org/data/#topic=Education
          https://drcongo.opendataforafrica.org/data/#topic=Health

- how to download data: Manual download from source based on filter - #topic=Demographics, Economy, Education, Health
    Demographics:
    1. Visit this link: https://drcongo.opendataforafrica.org/data/#topic=Demographics

    2. Navigate to "Democratic Republic of the Congo" > "Regional Statistics" > "2017".

    3. Click "Select Dataset."

    4. Choose all regions and indicators related to demographics and covering the timeframe 2006 to 2017.

    5. Select the corresponding table and download the data.
    
    Economy:
    1. Visit this link: https://drcongo.opendataforafrica.org/data/#topic=Economy

    2. Navigate to "Democratic Republic of the Congo" > "Regional Statistics" > "2017".

    3. Click "Select Dataset."

    4. Choose all regions and indicators related to economy and covering the timeframe 2006 to 2017.

    5. Select the corresponding table and download the data.
                    
    Education:
    1. Visit this link: https://drcongo.opendataforafrica.org/data/#topic=Education

    2. Navigate to "Democratic Republic of the Congo" > "Regional Statistics" > "2017".

    3. Click "Select Dataset."

    4. Choose all regions and indicators related to education and covering the timeframe 2006 to 2017.

    5. Select the corresponding table and download the data.
    
    Health:
    1. Visit this link: https://drcongo.opendataforafrica.org/data/#topic=Health

    2. Navigate to "Democratic Republic of the Congo" > "Regional Statistics" > "2017".

    3. Click "Select Dataset."

    4. Choose all regions and indicators related to health and covering the timeframe 2006 to 2017.

    5. Select the corresponding table and download the data.

- place_resolution: Regions (place names) and their corresponding Wikipedia IDs in the Democratic Republic of the Congo .

- statvars: Regions of Congo DRC.
  
- years: 2006 to 2017

- type of place: AA1, City, Country, Place.

### How to run:

`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data=<input_file>.csv --pv_map=<filepath>/pv_map.csv --places_resolved_csv=<filepath>/Congo_DRC_places_resolved.csv --config=<filepath/filename>metadata.csv --output_path=<filepath/filename>`

 ###  Example to run:
`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data=<input_file>Congo_DRC_Demographics.csv --pv_map=<filepath>/pv_map.csv --places_resolved_csv=<filepath>/Congo_DRC_places_resolved.csv --config=<filepath>/Congo_DRC_Demographics_metadata.csv --output_path=<filepath/filename>`

