###  Congo DRC - Demographics, Economy, Education & Health

- import_name: "congo_drc_demographics"
               "congo_drc_economy"
               "congo_education"
               "congo_health"

- source: https://drcongo.opendataforafrica.org/data/#topic=Demographics
          https://drcongo.opendataforafrica.org/data/#topic=Economy
          https://drcongo.opendataforafrica.org/data/#topic=Education
          https://drcongo.opendataforafrica.org/data/#topic=Health

- how to download data: Manual download from source based on filter - #topic=Demographics, Economy, Education, Health

- place_resolution: Regions (place names) and their corresponding Wikipedia IDs in the Democratic Republic of the Congo .

- statvars: Regions of Congo DRC.
  
- years: 2006 to 2017

- type of place: AA1, City, Country, Place.

### How to run:

`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data=<input_file>.csv --pv_map=statvar_imports/opendataforAfrica/<filepath>/pv_map.csv --places_resolved_csv=statvar_imports/<input_file>.csv --config=<filepath/filename>.csv --output_path=<filepath/filename>`


   

