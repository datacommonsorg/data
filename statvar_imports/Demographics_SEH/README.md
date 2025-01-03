# NCSES - NCSES_Demographics_SEH_Import

- source: https://ncses.nsf.gov/surveys/graduate-students-postdoctorates-s-e/2022#data

- how to download data: Statvar processor downloads the xls file by using --data_url=https://nces.ed.gov/programs/digest/d23/tables/xls/tabn318.45.xlsx

- type of place: Country

- statvars: Education

- years: 2017 to 2022


### How to run:

`python3 stat_var_processor.py --input_data=test_data/sample_input/*.xls --pv_map=statvar_imports/NCSES/Demographics_SEH/pv_map/seh_pv_map.csv --config=statvar_imports/NCSES/Demographics_SEH/seh_metadata.csv --output_path=--output_path=<filepath/filename>`

#### Example
`python3 stat_var_processor.py --input_data=/statvar_imports/NCSES/Demographics_SEH/test_data/sample_input/*.xls --pv_map=/statvar_imports/NCSES/Demographics_SEH/pv_map/seh_pv_map.csv --config=/statvar_imports/NSCES/Demographics_SEH/seh_metadata.csv --output_path=/statvar_imports/NCSES/Demographics_SEH/test_data/sample_output/ncses_stem`

