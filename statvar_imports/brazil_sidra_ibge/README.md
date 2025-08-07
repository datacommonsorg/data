1. import_name": "Brazil_SIDRA_IBGE"

2. Import Overview
Population Census on Economy Statistics for Brazil at country and state level.
Source URL: https://sidra.ibge.gov.br/home/pnadct/brazil
Import Type: Fully Autorefresh
Source Data Availability: 2020 to 2025
Release Frequency: P3M

3. Preprocessing Steps (Yes)
 Run 
 " brazil_download_script.py " 
 This script automatically downloads the raw input files from the source. It will create a main input_files directory and organize the downloaded files by segregating them into different subfolders within it

4. Autorefresh Type

Fully Autorefresh:"30 09 25 * * " (Runs at 9:30 AM on the 25th day of every month).

5. Script Execution Details

 " python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='../../statvar_imports/brazil_sidra_ibge/input_files/Average_Real_Income/*.xlsx' --pv_map='../../statvar_imports/brazil_sidra_ibge/config_files/average_real_income_pvmap.csv' --config_file='../../statvar_imports/brazil_sidra_ibge/config_files/brazil_sidra_metadata.csv' --output_path=../../statvar_imports/brazil_sidra_ibge/output/average_real_income_output "


" python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='../../statvar_imports/brazil_sidra_ibge/input_files/Mass_Income/*.xlsx' --pv_map='../../statvar_imports/brazil_sidra_ibge/config_files/mass_income_pvmap.csv' --config_file='../../statvar_imports/brazil_sidra_ibge/config_files/brazil_sidra_metadata.csv' --output_path=../../statvar_imports/brazil_sidra_ibge/output/mass_income_output "


" python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='../../statvar_imports/brazil_sidra_ibge/input_files/Population_Economic_sector/*.xlsx' --pv_map='../../statvar_imports/brazil_sidra_ibge/config_files/population_pvmap.csv' --config_file='../../statvar_imports/brazil_sidra_ibge/config_files/brazil_sidra_metadata.csv' --output_path=../../statvar_imports/brazil_sidra_ibge/output/population_economic_sector_output "


" python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='../../statvar_imports/brazil_sidra_ibge/input_files/Employment_And_Unemployment_Labor_Force/*.xlsx' --pv_map='../../statvar_imports/brazil_sidra_ibge/config_files/employment_and_unemployment_labor_force_pvmap.csv' --config_file='../../statvar_imports/brazil_sidra_ibge/config_files/brazil_sidra_metadata.csv' --output_path=../../statvar_imports/brazil_sidra_ibge/output/employment_and_unemployment_labor_force_output "

