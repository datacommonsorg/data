- import_name: "Indonesia_Census"

- source: https://www.bps.go.id/en/statistics-table?subject=526

- how to download data: Manual download from source 
  `To download the data` visit the website and select the desired year. Then, click on the download button to save the file to your computer."
  
  `https://www.bps.go.id/en/statistics-table/2/MTAxIzI=/number-of-crime-according-to-police-territorial-jurisdiction.html`

- type of place:  country , AA1. 

- statvars: Crime

- years: 2000 to 2022

- place_resolution:  places are resolved based on name.

### How to run:

python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data=<input_file>.xlsx --pv_map=statvar_imports/indonesia_bps_statistics/indonesia_census/indsonesia_crime/pv_map/<filename>_pvmap.csv --places_resolved_csv=statvar_imports/indonesia_bps_statistics/indonesia_census/indonesia_place_resolved.csv --config= statvar_imports/indonesia_bps_statistics/indonesia_census/indsonesia_crime/metadata/<filename>_metadata.csv --output_path=<filepath/filename>

