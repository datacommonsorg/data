# NCES - Number and percentage distribution of science, technology, engineering, and mathematics (STEM)

- source: hhttps://nces.ed.gov/programs/digest/d22/tables/dt22_318.45.asp

- how to download data: Statvar processor downloads the xls file by using --data_url=https://nces.ed.gov/programs/digest/d23/tables/xls/tabn318.45.xlsx

- type of place: Country

- statvars: Education

- years: 1990 to 2022


### How to run:

`python3 stat_var_processor.py --data_url="https://nces.ed.gov/programs/digest/d23/tables/xls/tabn318.45.xlsx" --input_data=source_data/input.xls --pv_map=statvar_imports/nces/stem_degrees/stem_pv_map.csv --config=statvar_imports/nces/stem_Degrees/stem_metadata.csv --output_path=--output_path=<filepath/filename>`

#### Example
`python3 stat_var_processor.py --data_url=https://nces.ed.gov/programs/digest/d23/tables/xls/tabn313.30.xlsx --input_data=/statvar_imports/nces/stem_degrees/test_data/sample_input/input.xls --pv_map=/statvar_imports/nces/stem_degrees/pv_map/stem_pv_map.csv --config=/statvar_imports/nces/stem_degrees/s_metadata.csv --output_path=/statvar_imports/nces/stem_degrees/test_data/sample_output/nces_stem`

