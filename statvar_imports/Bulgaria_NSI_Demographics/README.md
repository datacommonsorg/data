
# Bulgaria Demographics Dataset
## Overview
This dataset contains demographic information from Bulgaria sourced directly from the National Statistical Institute (NSI) datasets for foundational demographic and socio-economic statistics for Bulgaria.

## Data Source
**Source URL:** 
 https://www.nsi.bg/en/statistical-data/206/649
The data comes from Bulgaria's official statistical authority and includes comprehensive demographic variables such as population counts, age distributions, and other census-related metrics.

## Caveats
This is a manual refresh, as data cannot be downloaded directly from the source API due to the NSI Firewall blocking Google Cloud IP addresses. Once the data is manually downloaded, we can run the existing pvmap to generate the output. Remember to download the population data disaggregated by districts, age, place of residence, and sex.

## Processing Instructions
To process the Bulgaria Census data and generate statistical variables, use the following command from the "data" directory:

python3 tools/statvar_importer/stat_var_processor.py \
    --input_data='statvar_imports/Bulgaria_NSI_Demographics/test_data/BulgariaNSI_Demographics_input.csv' \
    --pv_map='statvar_imports/Bulgaria_NSI_Demographics/BulgariaNSI_Demographics_pvmap.csv' \
    --output_path='statvar_imports/Bulgaria_NSI_Demographics/test_data/BulgariaNSI_Demographics_output' \
    --config_file='statvar_imports/Bulgaria_NSI_Demographics/BulgariaNSI_Demographics_metadata.csv' \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

