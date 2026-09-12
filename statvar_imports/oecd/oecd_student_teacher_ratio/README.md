# OECD - Student Teacher Ratio

- source: https://stats.oecd.org/Index.aspx?datasetcode=EAG_PERS_RATIO

- how to download data: Manual download from source based on filter - `Student Teacher Ratio`.

- type of place: Country.

- statvars: Education

- years: 2005 to 2020

- place_resolution: Resolved manually.

### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=statvar_imports/oecd/oecd_student_teacher_ratio/pv_map/<filename>_pvmap.csv --places_resolved_csv=statvar_imports/oecd/oecd_student_teacher_ratio/Places_Resolved.csv --config=statvar_imports/oecd/oecd_student_teacher_ratio/metadata.csv --output_path=--output_path=<filepath/filename>`

#### Example
`python3 stat_var_processor.py --input_data=/statvar_imports/oecd/oecd_student_teacher_ratio/test_data/sample_input/oecd_student_teacher_ratio.csv --pv_map=/statvar_imports/oecd/oecd_student_teacher_ratio/pv_map.csv --places_resolved_csv=/statvar_imports/oecd/oecd_student_teacher_ratio/Places_Resolved.csv --config=/statvar_imports/oecd/oecd_student_teacher_ratio/metadata.csv --output_path=/statvar_imports/oecd/oecd_student_teacher_ratio/test_data/sample_output/oecd_student_teacher_ratio`
