# NCSES - NCSES_Demographics_SEH_Import

- source: https://ncses.nsf.gov/surveys/graduate-students-postdoctorates-s-e/2022#data

- how to download data: Statvar processor downloads the xls file by using --data_url=https://nces.ed.gov/programs/digest/d23/tables/xls/tabn318.45.xlsx

- type of place: Country

- statvars: Education

- years: 2017 to 2022


### How to run:

`python3 stat_var_processor.py --data_url="download url" --input_data=test_data/sample_input/input*.xls --pv_map=statvar_imports/ncses/demographics_seh/seh_pv_map.csv --config=statvar_imports/ncses/demographics_seh/seh_metadata.csv --output_path=<filepath/filename>`


#### Example

'python3 stat_var_processor.py --data_url="https://wayback.archive-it.org/5902/20240828214053/https://ncsesdata.nsf.gov/gradpostdoc/2017/excel/gss17-dt-tab002-1.xlsx" --input_data='/statvar_imports/ncses/demographics_seh/test_data/sample_input/input1.xls' --output_path=/statvar_imports/ncses/demographics_seh/test_data/sample_output/ncses_stem --pv_map=/statvar_imports/ncses/demographics_seh/seh_pv_map.csv --config=/statvar_imports/ncses/demographics_seh/seh_metadata.csv'
