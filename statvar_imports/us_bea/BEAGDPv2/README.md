# GDP by County, Metro, and Other Areas

The data set contains GDP by  county, Metro, and Other Areas

Download:

Data download URL : https://apps.bea.gov/regional/zip/CAGDP9.zip
Select the CAGDP9: Real GDP in chaied dollars by County & MSA


Processing: 
Earlier code : https://source.corp.google.com/piper///depot/google3/datacommons/mcf/bea/v2/ ( 2001-2021 data)
Current execution : Using statvarProcessor ( 2001-2023 data).

File paths in gcs:

input file : gs://unresolved_mcf/us_bea/gdp_chained_dollar_county_msa/20241217/input_files/CAGDP9__ALL_AREAS_2001_2023.csv
pv_map: gs://unresolved_mcf/us_bea/gdp_chained_dollar_county_msa/20241217/configs/pv_map.py
place mappings : gs://unresolved_mcf/us_bea/gdp_chained_dollar_county_msa/20241217/configs/place_mapping.json
config file: gs://unresolved_mcf/us_bea/gdp_chained_dollar_county_msa/20241217/configs/config.py
output files: gs://unresolved_mcf/us_bea/gdp_chained_dollar_county_msa/20241217/output_files/


Check for any addiitonal NAICS to be mapped from source and update the pv_map.py
Also any new place mappings has to be updated in the place_mappings.json with corresponding dcid
Used the statvar_remap to map the dcid generated in the format of existing dcid ( The existing statvar has measurement qualifier in the end of statvar whereas the script generates dcid has it in the beginning) 

Execution step :

python3 {$SCRIPT_PATH}/stat_var_processor.py --pv_map={$INPUT_PATH}/pv_map.py,observationAbout:{$INPUT_PATH}/place_mapping.json --config={$INPUT_PATH}/config.py --input_data={$INPUT_PATH}/CAGDP9__ALL_AREAS_2017_2022.csv --output_path={$OUTPUT_PATH}/cagdp9  2>&1 | tee gdp.log

