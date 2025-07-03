India_RBIStateDomesticProduct
source: https://www.rbi.org.in/Scripts/AnnualPublications.aspx?head=Handbook%20of%20Statistics%20on%20Indian%20States

how to download data: Download script (rbi_sdp_download.py). To download the data, you'll need to use the provided download script,rbi_sdp_download.py. This script will automatically create an "input" folder where you should place the file to be processed. The script also requires a configuration file (config.ini) to function correctly.

type of place: State.

statvars: Demographics

years: 2004 to 2024.

place_resolution: Places resolved to wikidataId in metadata sheet itself.

How to run:
python3 stat_var_processor.py  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='../../statvar_imports/india_rbistatedomesticproduct/test_data/<filename>.xlsx' --pv_map=".../../statvar_imports/india_rbistatedomesticproduct/<filename>_pvmap.csv" --output_path='.../../statvar_imports/india_rbistatedomesticproduct/test_data/<filename>' --config=".../../statvar_imports/india_rbistatedomesticproduct/<filename>_metadata.csv"


Example
Download :
python3 rbi_sdp_download.py


python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='../../statvar_imports/india_rbistatedomesticproduct/test_data/state_domestic_input.xlsx' --pv_map="../../statvar_imports/india_rbistatedomesticproduct/state_domestic_product_pv_map.csv" --output_path='../../statvar_imports/india_rbistatedomesticproduct/test_data/sample_output' --config=".../../statvar_imports/india_rbistatedomesticproduct/state_domestic_product_metadata.csv"