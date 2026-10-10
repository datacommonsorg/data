# NCES - HBCU Enrollment Import

- source: https://nces.ed.gov/programs/digest/d23/tables/dt23_313.30.asp 

- how to download data: Statvar processor downloads the xls file by using --data_url=https://nces.ed.gov/programs/digest/d23/tables/xls/tabn313.30.xlsx

- type of place: Country

- statvars: Education

- years: 1990 to 2022


### How to run:

`python3 stat_var_processor.py --data_url="https://nces.ed.gov/programs/digest/d23/tables/xls/tabn313.30.xlsx" --input_data=source_data/input.xls --pv_map=statvar_imports/nces/hbcu_enrollment/hbcu_pvmap.csv --config=statvar_imports/nces/hbcu_enrollment/hbcu_metadata.csv --output_path=--output_path=<filepath/filename>`

#### Example
`python3 stat_var_processor.py --data_url=https://nces.ed.gov/programs/digest/d23/tables/xls/tabn313.30.xlsx --input_data=/statvar_imports/nces/hbcu_enrollment/test_data/sample_input/input.xls --pv_map=/statvar_imports/nces/hbcu_enrollment/hbcu_pvmap.csv --config=/statvar_imports/nces/hbcu_enrollment/hbcu_metadata.csv --output_path=/statvar_imports/nces/hbcu_enrollment/test_data/sample_output/hbcu`
