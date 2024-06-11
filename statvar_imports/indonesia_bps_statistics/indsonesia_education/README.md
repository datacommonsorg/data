- import_name: "Indonesia_Census"

- source: https://www.bps.go.id/en/statistics-table?subject=519 

- how to download data: Manual download from source  

- type of place:  country , AA1. 

- statvars: Education

- years: 2016 to 2023

- place_resolution:  places are resolved based on name.

### How to run:

python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data=<input_file>.xlsx --pv_map=statvar_imports/indonesia_bps_statistics/indonesia_census/indsonesia_education/pv_map/<filename>_pvmap.csv --places_resolved_csv=statvar_imports/indonesia_bps_statistics/indonesia_census/indonesia_place_resolved.csv --config= statvar_imports/indonesia_bps_statistics/indonesia_census/indsonesia_education/metadata/<filename>_metadata.csv --output_path=<filepath/filename>

