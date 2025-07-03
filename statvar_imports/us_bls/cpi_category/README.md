# BLS_CPI_Category Import

- source: https://www.bls.gov/cpi/tables/supplemental-files/

- How to download data: We have the download script cpi_category_download.py to download the data from source website and keep csv files inside the input_data folder.
### How to run download script:
`python3 cpi_category_download.py`

- type of place: Country.

- statvars: Economy

- years: 2011 till latest available data


### How to run:
To process from current import folder

`../../../tools/statvar_importer/stat_var_processor.py --input_data='input_data/filename' --pv_map=<pvmap_file> --config_file=<metadata_file> --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path=<file_path/filename>`


#### Example

To process from current import folder

`../../../tools/statvar_importer/stat_var_processor.py --input_data='input_data/cpi-w/*' --pv_map='cpi_w_pvmap.csv' --config_file='cpi_w_metadata.csv' --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path='output/cpi_w/cpi_w'`

In the same way please change the input folder and the pvmap, config files which are available in the cpi_category folder to generate output for cpi_u and c_cpi_u.

#### Download
Running from current import folder
`python3 cpi_category_download.py`

