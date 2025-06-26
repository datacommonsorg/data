# OECD Regional Education

- source: https://stats.oecd.org/Index.aspx?DataSetCode=REGION_EDUCAT, 

- how to download data: Download script (download_script.py).
    This script will create two main folders (input and output).The file to be processed will be inside input. The processed output will be stored in output folder.

- type of place: Country (USA).

- statvars: Economy

- years: 1998 to latest (Note: Every Month data is also there for each year and also for latest year and month)


### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=<pv_map>.csv --config=<metadata>.csv --output_path=<filepath/filename>`

#### Example
#### Download : 

`python3 download.py`

#### Processing

If processing from current import folder :

`python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=input/oecd_regional_education_data.csv --pv_map=oecd_regional_education_pvmap.csv --config_file=oecd_regional_education_metadata.csv --output_path=output/oecd_regional_education`


If processing from statvar_importer folder :

`python3 stat_var_processor.py --input_data=input/oecd_regional_education_data.csv --pv_map=oecd_regional_education_pvmap.csv --config_file=oecd_regional_education_metadata.csv --output_path=output/oecd_regional_education`
