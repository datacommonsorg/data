- import_name: "Indonesia_Census"

- source: https://www.bps.go.id/en/statistics-table?subject=520

- how to download data: Manual download from source 
  `To download the data` visit the website and select the desired year. Then, click on the download button to save the file to your computer."
  
  `https://docs.google.com/spreadsheets/d/1TyXaudsPr_jwcV6cjjpzIQCbvVbX4Uc5MoO660Ep13k/edit#gid=970127267`
  
  `https://www.bps.go.id/en/statistics-table/2/MTE2OCMy/percentage-of-formal-labor-by-province--percent-.html`

- type of place:  labour force sheet having lower-level places : AA2 & AA3

- statvars: Labour

- years: 2018 to 2022

- place_resolution:  places are resolved based on name.

### How to run:

python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data=<input_file>.xlsx --pv_map=statvar_imports/indonesia_bps_statistics/indonesia_census/indsonesia_labour/pv_map/<filename>_pvmap.csv --places_resolved_csv=statvar_imports/indonesia_bps_statistics/indonesia_census/indonesia_place_resolved.csv --config= statvar_imports/indonesia_bps_statistics/indonesia_census/indsonesia_labour/metadata/<filename>_metadata.csv --output_path=<filepath/filename>

