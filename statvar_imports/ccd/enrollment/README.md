# US CCD Enrollment

- source: https://nces.ed.gov/programs/digest/d24/tables/dt24_203.65.asp

- how to download data: Download script (download.py)
    
    The data is downloaded based in xls format.
    This script will do some cleaning on the xls format and save it as a csv file.

- type of place: Country

- statvars: Education

- years: 2013 to 2023

- place_resolution: Manually resolved.

- NOTE: The data has not been updated since 2023. Added future years in pvmap just incase the data gets updated.

### How to run:

- To download the input file

    `python3 download.py`

- To process the data

    `python3 stat_var_processor.py --input_data=../../statvar_imports/ccd/enrollment/input_files/ccd_input.csv --pv_map=../../statvar_imports/ccd/enrollment/CCD_Enrollment_pvmap.csv --config_file=../../statvar_imports/ccd/enrollment/CCD_Enrollment_metadata.csv --output_path=../../statvar_imports/ccd/enrollment/output/CCD_Enrollment_output --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf`

