India_RBIStateDomesticProduct
source: https://www.rbi.org.in/Scripts/AnnualPublications.aspx?head=Handbook%20of%20Statistics%20on%20Indian%20States

how to download data: Download script (download_script/rbi_sdp_download.py). To download the data, you'll need to use the provided download script, download_script/rbi_sdp_download.py. This script will automatically create an "input" folder where you should place the file to be processed. The script also requires a configuration file (config.ini) to function correctly.

type of place: State.

statvars: Demographics

years: 2004 to 2024.

place_resolution: Places resolved to wikidataId in metadata sheet itself.

How to run:
python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='<input_file>.xlsx' --pv_map='statvar_imports/uae_Population/UAE_Population/<filename>_pvmap.csv,observationAbout:statvar_imports/uae_Population/UAE_Population/UAEPopulation_places_resolved_csv.csv' --config='statvar_imports/uae_Population/UAE_Population/UAEPopulationByEmiratesNationality_metadata.csv' --output_path=<filepath/filename>

Example
Download :
python3 rbi_sdp_download.py

Processing
python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='data/statvar_imports/uae_population/test_data/uae_population_input.xlsx' --pv_map='data/statvar_imports/uae_population/uae_popolation_pvmap.csv' --config='data/statvar_imports/uae_population/uae_popolation_metadata.csv' --output_path=data/statvar_imports/uae_population/test_data/output