Research Doctorate Recipients Import

### Import Overview

- source: https://ncses.nsf.gov/pubs/nsf23300/data-tables

- type of place: Country

- statvars: Demographics, Education

- years: 2011 to 2021

Source Data Availability: Yearly

Release Frequency:P1Y

### Preprocessing Steps
It is handled by download_and_process.py, when it is run by default

### Autorefresh Type
- Fully Autorefresh

### Script Execution Details
the manifest.json triggers the below commands

`python3 download_and_process.py`
this will create 2 csv files for male and female with proper data format and create temp_downloads folder with xls source files

`python3 stat_var_processor.py --input_data=ncses_employed_female_data.csv --pv_map=ncses_employed_female_pvmap.csv --config_file=ncses_employed_common_metadata.csv --output_path=output_files/female_output --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"`

`stat_var_processor.py --input_data=ncses_employed_male_data.csv --pv_map=ncses_employed_male_pvmap.csv --config_file=ncses_employed_common_metadata.csv --output_path=output_files/male_output --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf`

The above two commands generate's necessary output data within out_files/ folder