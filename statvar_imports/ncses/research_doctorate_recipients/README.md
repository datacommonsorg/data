# NCSES Research Doctorate Recipients Import Autorefresh

- source: https://ncses.nsf.gov/pubs/nsf23300/data-tables

- how to download data: Download script (download_and_process.py)
    
    The data is downloaded based on urls and it is processed to give header to the data according to the source.
    This script will automatically create an "input" folder where you should place the file to be processed.

- type of place: Country

- statvars: Education

- years: 2011 to 2021

- place_resolution:Places are resolved based on name.

- NOTE: The data has not been updated since 2021. Added future years in pvmap just incase the data gets updated.

### How to run:

- To download the input file

    `python3 download_and_process.py`

- For Male

    `python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=input_files/nsf23300-tab001-009.xlsx --pv_map=config/research_doctorate_male_pvmap.csv --config_file=common_metadata.csv --output_path=output_path/research_doctorate_male --statvar_dcid_remap_csv=config/statvar_remap.csv"`

- For Female

    `python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=input_files/nsf23300-tab001-010.xlsx --pv_map=config/research_doctorate_female_pvmap.csv --config_file=common_metadata.csv --output_path=output_path/research_doctorate_female --statvar_dcid_remap_csv=config/statvar_remap.csv`


## If statvar remap is involved,use:
` --statvar_dcid_remap_csv=data/statvar_imports/ncses/research_doctorate_recipients/config/statvar_remap.csv` along with the remaining command for that particular file.