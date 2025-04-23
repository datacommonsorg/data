# BEAGDPv2

The data set contains GDP by  county, Metro, and Other Areas

Download:
Data download URL : `https://apps.bea.gov/regional/zip/CAGDP9.zip`
Select the CAGDP9: Real GDP in chaied dollars by County & MSA


Processing: 
Earlier code : https://source.corp.google.com/piper///depot/google3/datacommons/mcf/bea/v2/ ( 2001-2021 data)
Current execution : Using statvarProcessor ( 2001-2023 data).

###File paths in gcs:

input file: gs://unresolved_mcf/us_bea/gdp_chained_dollar_county_msa/latest/input_files/CAGDP9__ALL_AREAS_2001_2023.csv
pv_map: gs://unresolved_mcf/us_bea/gdp_chained_dollar_county_msa/latest/input_files/pv_map.py
place mappings : gs://unresolved_mcf/us_bea/gdp_chained_dollar_county_msa/latest/input_files/place_mapping.csv
config file: gs://unresolved_mcf/us_bea/gdp_chained_dollar_county_msa/latest/input_files/bea_metadata.py
output files: gs://unresolved_mcf/us_bea/gdp_chained_dollar_county_msa/latest/


Check for any addiitonal NAICS to be mapped from source and update the pv_map.py
Also any new place mappings has to be updated in the place_mappings.json with corresponding dcid
Used the statvar_remap to map the dcid generated in the format of existing dcid ( The existing statvar has measurement qualifier in the end of statvar whereas the script generates dcid has it in the beginning) 

###Execution steps :

To Download, run:

`python3 bea_download.py`
Note : The downloaded file will be saved in "input_files/CAGDP9__ALL_AREAS_2001_2023.csv"

To divide the input file into smaller files, Run:

`sh preprocess.sh`
Note: the input file will be divided into multiple files. These files will be named following the pattern "bea_gdp_input_*.csv", where the asterisk will be replaced by a sequential number to distinguish each part.

To Process the files, Run:

`python3 {$SCRIPT_PATH}/stat_var_processor.py --pv_map={$INPUT_PATH}/pv_map.py,observationAbout:{$INPUT_PATH}/place_mapping.json --config={$INPUT_PATH}/config.py --input_data={$INPUT_PATH}/CAGDP9__ALL_AREAS_2017_2022.csv --output_path={$OUTPUT_PATH}/cagdp9  2>&1 | tee gdp.log`

eg:
python3 stat_var_processor.py --input_data=/data/statvar_imports/gdp_by_county_metro_and_other_areas/beagdpv2/input_files/bea_gdp_input_*.csv --pv_map=/data/statvar_imports/gdp_by_county_metro_and_other_areas/beagdpv2/pv_map.py --places_resolved_csv=/data/statvar_imports/gdp_by_county_metro_and_other_areas/beagdpv2/place_mapping.csv --config_file=/data/statvar_imports/gdp_by_county_metro_and_other_areas/beagdpv2/bea_metadata.py --statvar_dcid_remap_csv=/data/statvar_imports/gdp_by_county_metro_and_other_areas/beagdpv2/bea_statvar_remap.csv --existing_statvar_mcf=stat_vars.mcf --output_path=/data/statvar_imports/gdp_by_county_metro_and_other_areas/beagdpv2/output_files/bea_gdp_output


