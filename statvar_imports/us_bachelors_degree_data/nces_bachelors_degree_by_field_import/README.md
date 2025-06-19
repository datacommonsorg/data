# NCES_Bachelors_Degree_By_Field_Import

Bachelor's degrees conferred to (fe)males by post secondary institutions, by race/ethnicity and field of study.

- source:  `https://nces.ed.gov/programs/digest/d23/tables/dt23_322.50.asp`

- how to download data: Download script (download_data.py).
    To download the data, you'll need to run the provided download script, `download_data.py`. This script will automatically create an "input_files" folder where you should place the file to be processed.
We need to run `preprocess.py` 

#### Download the data: 

For download the source data, run:

`python3 download_data.py`

Notes: All the files will be downloaded inside "input_files" folder after executing the download script.

To preprocess data, run:
`python3 preprocess.py`

###Note:
The latest year data file will be moved from the `input_files` folder to `input_files_latest` folder. 
This is because of the way we are handling the input data.
For example, if an input file contains data for both 2010-11 and 2011-12, we are currently ignoring the 2011-12 data from that same file during processing to avoid duplicate value issues.
However, the problem is that the latest file should include all years without ignoring any columns.
So, we are keeping the latest year input file in a separate folder and processing it with different metadata file (`metadata_latest.csv`).

#### Processing the data:
Execute the script inside the folder `/data/tools/statvar_importer/`

```
python3 stat_var_processor.py 
--input_data=../../statvar_imports/us_bachelors_degree_data/nces_bachelors_degree_by_field_import/input_files/table_50_*.xlsx 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf 
--pv_map=../../statvar_imports/us_bachelors_degree_data/nces_bachelors_degree_by_field_import/table50_female_pvmap.csv 
--config_file=../../statvar_imports/us_bachelors_degree_data/nces_bachelors_degree_by_field_import/metadata.csv 
--output_path=../../statvar_imports/us_bachelors_degree_data/nces_bachelors_degree_by_field_import/output_files/nces_female_output
```

```
python3 stat_var_processor.py 
--input_data=../../statvar_imports/us_bachelors_degree_data/nces_bachelors_degree_by_field_import/input_files/table_40_*.xlsx 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf 
--pv_map=../../statvar_imports/us_bachelors_degree_data/nces_bachelors_degree_by_field_import/table40_male_pvmap.csv 
--config_file=../../statvar_imports/us_bachelors_degree_data/nces_bachelors_degree_by_field_import/metadata.csv 
--output_path=../../statvar_imports/us_bachelors_degree_data/nces_bachelors_degree_by_field_import/output_files/nces_male_output
```

```
python3 stat_var_processor.py 
--input_data=../../statvar_imports/us_bachelors_degree_data/nces_bachelors_degree_by_field_import/input_files_latest/table_50_*.xlsx 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf 
--pv_map=../../statvar_imports/us_bachelors_degree_data/nces_bachelors_degree_by_field_import/table50_female_pvmap.csv 
--config_file=../../statvar_imports/us_bachelors_degree_data/nces_bachelors_degree_by_field_import/metadata_latest.csv 
--output_path=../../statvar_imports/us_bachelors_degree_data/nces_bachelors_degree_by_field_import/output_files/nces_female_output_latest
```

```
python3 stat_var_processor.py 
--input_data=../../statvar_imports/us_bachelors_degree_data/nces_bachelors_degree_by_field_import/input_files_latest/table_40_*.xlsx 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf 
--pv_map=../../statvar_imports/us_bachelors_degree_data/nces_bachelors_degree_by_field_import/table40_male_pvmap.csv 
--config_file=../../statvar_imports/us_bachelors_degree_data/nces_bachelors_degree_by_field_import/metadata_latest.csv 
--output_path=../../statvar_imports/us_bachelors_degree_data/nces_bachelors_degree_by_field_import/output_files/nces_male_output_latest
```

