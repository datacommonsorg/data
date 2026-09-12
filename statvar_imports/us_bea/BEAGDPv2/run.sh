#Set the local paths

import dateutil
export SCRIPT_PATH="/statvar_imports/us_bea/BEAGDPv2" 
export CONFIG_PATH="/statvar_imports/us_bea/BEAGDPv2"
export INPUT_PATH="/statvar_imports/us_bea/BEAGDPv2/test_data/sample_input" 
export OUTPUT_PATH="/statvar_imports/us_bea/BEAGDPv2/test_data/sample_output"

#Execute the script
python3 stat_var_processor.py --pv_map=/statvar_imports/us_bea/BEAGDPv2/pvmap/pv_map.py,observationAbout:/statvar_imports/us_bea/BEAGDPv2/place_mapping.json --config=/statvar_imports/us_bea/BEAGDPv2/config.py --input_data=/statvar_imports/us_bea/BEAGDPv2/test_data/sample_input/CAGDP9__ALL_AREAS_2017_2022.csv --existing_statvar_mcf=stat_vars.mcf --output_path=/statvar_imports/us_bea/BEAGDPv2/test_data/sample_output/cagdp9  2>&1 | tee gdp.log
