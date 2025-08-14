### This import process handles data from Brazil's SIDRA IBGE platform.

- Description: Population Census on Economy Statistics for Brazil at the country and state level.

- Source URL: https://sidra.ibge.gov.br/home/pnadct/brazil

- Import Type: Fully Autorefresh

- Data Availability: 2022 to 2025

- Release Frequency: P3M, which means every 3 months (quarterly).

### Preprocessing and Data Acquisition

To get the raw input files, run the following script:

Bash

    python3 brazil_download_script.py

This script automatically downloads the source data into a main input_files directory. It then organizes and segregates the files into separate subfolders based on their category.


### Data Processing

After the files are downloaded, the data is processed in four separate stages using the stat_var_processor.py script. Each stage handles a specific data category. The script uses various command-line arguments to specify the input data, pvmap, configuration file, and output path for each category.

 * Average Real Income

Bash

    python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='../../statvar_imports/brazil_sidra_ibge/input_files/Average_Real_Income/*.xlsx' --pv_map='../../statvar_imports/brazil_sidra_ibge/config_files/average_real_income_pvmap.csv' --config_file='../../statvar_imports/brazil_sidra_ibge/config_files/brazil_sidra_metadata.csv' --output_path=../../statvar_imports/brazil_sidra_ibge/output/average_real_income_output

 * Mass Income

Bash

    python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='../../statvar_imports/brazil_sidra_ibge/input_files/Mass_Income/*.xlsx' --pv_map='../../statvar_imports/brazil_sidra_ibge/config_files/mass_income_pvmap.csv' --config_file='../../statvar_imports/brazil_sidra_ibge/config_files/brazil_sidra_metadata.csv' --output_path=../../statvar_imports/brazil_sidra_ibge/output/mass_income_output

 * Population Economic Sector

Bash

    python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='../../statvar_imports/brazil_sidra_ibge/input_files/Population_Economic_sector/*.xlsx' --pv_map='../../statvar_imports/brazil_sidra_ibge/config_files/population_pvmap.csv' --config_file='../../statvar_imports/brazil_sidra_ibge/config_files/brazil_sidra_metadata.csv' --output_path=../../statvar_imports/brazil_sidra_ibge/output/population_economic_sector_output

 * Employment and Unemployment

Bash

    python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='../../statvar_imports/brazil_sidra_ibge/input_files/Employment_And_Unemployment_Labor_Force/*.xlsx' --pv_map='../../statvar_imports/brazil_sidra_ibge/config_files/employment_and_unemployment_labor_force_pvmap.csv' --config_file='../../statvar_imports/brazil_sidra_ibge/config_files/brazil_sidra_metadata.csv' --output_path=../../statvar_imports/brazil_sidra_ibge/output/employment_and_unemployment_labor_force_output


### Automation

This import pipeline is configured to run automatically on a monthly schedule.

- Cron Expression: 30 09 25 * *

Schedule: The script runs at 9:30 AM on the 25th day of every month.
