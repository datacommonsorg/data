This import process handles data from Brazil's SIDRA IBGE platform.

1.Description: Population Census on Economy Statistics for Brazil at the country and state level.

2.Source URL: https://sidra.ibge.gov.br/home/pnadct/brazil

3.Import Type: Fully Autorefresh

4.Data Availability: 2020 to 2025

5.Release Frequency: P3M, which means every 3 months (quarterly).

6.Preprocessing and Data Acquisition

To get the raw input files, run the following script:

Bash

python3 brazil_download_script.py

This script automatically downloads the source data into a main input_files directory. It then organizes and segregates the files into separate subfolders based on their category.


7.Data Processing

After the files are downloaded, the data is processed in four separate stages using the stat_var_processor.py script. Each stage handles a specific data category. The script uses various command-line arguments to specify the input data, private-variable map, configuration file, and output path for each category.

1.Average Real Income

Bash

python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='../../statvar_imports/brazil_sidra_ibge/input_files/Average_Real_Income/*.xlsx' --pv_map='../../statvar_imports/brazil_sidra_ibge/config_files/average_real_income_pvmap.csv' --config_file='../../statvar_imports/brazil_sidra_ibge/config_files/brazil_sidra_metadata.csv' --output_path=../../statvar_imports/brazil_sidra_ibge/output/average_real_income_output

2.Mass Income

Bash

python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='../../statvar_imports/brazil_sidra_ibge/input_files/Mass_Income/*.xlsx' --pv_map='../../statvar_imports/brazil_sidra_ibge/config_files/mass_income_pvmap.csv' --config_file='../../statvar_imports/brazil_sidra_ibge/config_files/brazil_sidra_metadata.csv' --output_path=../../statvar_imports/brazil_sidra_ibge/output/mass_income_output

3.Population Economic Sector

Bash

python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='../../statvar_imports/brazil_sidra_ibge/input_files/Population_Economic_sector/*.xlsx' --pv_map='../../statvar_imports/brazil_sidra_ibge/config_files/population_pvmap.csv' --config_file='../../statvar_imports/brazil_sidra_ibge/config_files/brazil_sidra_metadata.csv' --output_path=../../statvar_imports/brazil_sidra_ibge/output/population_economic_sector_output

4.Employment and Unemployment

Bash

python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/script


8.Automation

This import pipeline is configured to run automatically on a monthly schedule.

9.Cron Expression: 30 09 25 * *

Schedule: The script runs at 9:30 AM on the 25th day of every month.
