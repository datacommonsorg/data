NCSES_Median_Annual_Salary_Import

- source: https://ncses.nsf.gov/surveys/national-survey-college-graduates/2023#data

- type of place: Country

- statvars: Demographics, Education

- years: 2023

### How to run:

`python3 stat_var_processor.py --input_data=nsf25322-tab004-001-data.csv --pv_map=nsf25322-tab004-001-pvmap.csv --config_file=nsf25322-tab004-001-metadata.csv --output_path=output_files/nsf25322_output_4_1 --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf`

`python3 stat_var_processor.py --input_data=nsf25322-tab004-002-data.csv --pv_map=nsf25322-tab004-002-pvmap.csv --config_file=nsf25322-tab004-002-metadata.csv --output_path=output_files/nsf25322_output_4_2 --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf`

The above two commands generate's necessary output data within output_files/ folder