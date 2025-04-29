# NigeriaStatistics

- source: https://nigeria.opendataforafrica.org, 

- how to download data: Manual download from source based on filter

- type of place: Country.

- statvars: Education, Health, Economy 

- years: 1960 to 2023.

- place_resolution:Places are resolved based on region ID.

### How to run:

`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='/data/statvar_imports/opendataforafrica/nigeria_census/testdata/jgngifg_input.csv' --pv_map='/data/statvar_imports/opendataforafrica/nigeria_census/jgngifg_pvmap.csv' --config='/data/statvar_imports/opendataforafrica/nigeria_census/jgngifg_metadata.csv' --output_path=/data/statvar_imports/opendataforafrica/nigeria_census/testdata/jgngifg_output`

`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='/data/statvar_imports/opendataforafrica/nigeria_census/testdata/uopetnd_input.csv' --pv_map='/data/statvar_imports/opendataforafrica/nigeria_census/uopetnd_pvmap.csv' --config='/data/statvar_imports/opendataforafrica/nigeria_census/uopetnd_metadata.csv' --output_path=/data/statvar_imports/opendataforafrica/nigeria_census/testdata/uopetnd_output`

-- Add inputfile.csv and pvmap and metadata accordingly and run like above.

## If place resolution is involved,use:
` --places_resolved_csv=data/statvar_imports/opendataforafrica/nigeria_census/places_resolved_csv.csv` along with the remaining command.


#### Processing
`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='data/statvar_imports/opendataforafrica/nigeria_census/testdata/ngnbsncpir2017_input.csv' --pv_map='data/statvar_imports/opendataforafrica/nigeria_census/ngnbsncpir2017_pvmap.csv' --places_resolved_csv='data/statvar_imports/opendataforafrica/nigeria_census/places_resolved_csv.csv' --config='data/statvar_imports/opendataforafrica/nigeria_census/ngnbsncpir2017_metadata.csv' --output_path=data/statvar_imports/opendataforafrica/nigeria_census/output/ngnbsncpir2017_output`


