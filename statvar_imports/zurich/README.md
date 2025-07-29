1. import_name": "Zurich_Population_Number_Of_Company_Workplace_Employees"

2. Import Overview
Zurich population data at Province and City Level.
Source URL: [Zurich country website](https://www.stadt-zuerich.ch/content/dam/web/de/politik-verwaltung/statistik-und-daten/linked-open-data/datacommons/wir_2552_wiki.csv)
Import Type: Fully Autorefresh
Source Data Availability: 2011 to 2022
Release Frequency: P1Y

3. Preprocessing Steps (No)

4. Autorefresh Type

Fully Autorefresh:"0 2 29 * * " (Runs at 2:00 AM on the 29th day of every month).

5. Script Execution Details

" python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='../../statvar_imports/zurich/wir_2552_wiki/test_data/wir_2552_wiki_input.csv' --pv_map='../../statvar_imports/zurich/wir_2552_wiki/wir_2552_wiki_pvmap.csv' --config_file='../../statvar_imports/zurich/wir_2552_wiki/wir_2552_wiki_metadata.csv' --output_path=../../statvar_imports/zurich/wir_2552_wiki/output/zurich_population_wir_2552_wiki_output  "

#####


1. import_name": "Zurich_Population_By_Age"

2. Import Overview
Zurich population data at Province and City Level.
Source URL: [Zurich country website](https://www.stadt-zuerich.ch/content/dam/web/de/politik-verwaltung/statistik-und-daten/linked-open-data/datacommons/bev_3903_age10_wiki.csv)
Import Type: Fully Autorefresh
Source Data Availability: 1993 to 2023
Release Frequency: P1Y

3. Preprocessing Steps (No)

4. Autorefresh Type

Fully Autorefresh:" 0 6 29 * * " (Runs at 6:00 AM on the 29th of every month).

5. Script Execution Details

" python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='../../statvar_imports/zurich/bev_3903_age10_wiki/test_data/bev_3903_age10_wiki_input.csv' --pv_map='../../statvar_imports/zurich/bev_3903_age10_wiki/bev_3903_age10_wiki_pvmap.csv' --config_file='../../statvar_imports/zurich/bev_3903_age10_wiki/bev_3903_age10_wiki_metadata.csv' --output_path=../../statvar_imports/zurich/bev_3903_age10_wiki/output/zurich_population_bev_3903_age10_wiki_output "

#####


1. import_name": "Zurich_Population"

2. Import Overview
Zurich population data at Province and City Level.
Source URL: [Zurich country website](https://www.stadt-zuerich.ch/content/dam/web/de/politik-verwaltung/statistik-und-daten/linked-open-data/datacommons/bev_3240_wiki.csv)
Import Type: Fully Autorefresh
Source Data Availability: 1941 to 2023
Release Frequency: P1Y

3. Preprocessing Steps (No)

4. Autorefresh Type

Fully Autorefresh:" 30 11 29 * * " (Runs at 11:30 AM on the 29th of every month).

5. Script Execution Details

" python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='../../statvar_imports/zurich/bev_3240_wiki/test_data/bev_3240_wiki_input.csv' --pv_map='../../statvar_imports/zurich/bev_3240_wiki/bev_3240_wiki_pvmap.csv' --config_file='../../statvar_imports/zurich/bev_3240_wiki/bev_3240_wiki_metadata.csv' --output_path=../../statvar_imports/zurich/bev_3240_wiki/output/zurich_population_bev_3240_wiki.csv_output "

#####


1. import_name": "Zurich_Population_Number_Of_Birth_By_Origin"

2. Import Overview
Zurich population data at Province and City Level.
Source URL: [Zurich country website](https://www.stadt-zuerich.ch/content/dam/web/de/politik-verwaltung/statistik-und-daten/linked-open-data/datacommons/bev_4031_hel_wiki.csv)
Import Type: Fully Autorefresh
Source Data Availability: 1998 to 2023
Release Frequency: P1Y

3. Preprocessing Steps (No)

4. Autorefresh Type

Fully Autorefresh:" 45 15 29 * * " (Runs at 3:45 PM on the 29th of every month).

5. Script Execution Details

"python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='../../statvar_imports/zurich/bev_4031_hel_wiki/test_data/bev_4031_hel_wiki_input.csv' --pv_map='../../statvar_imports/zurich/bev_4031_hel_wiki/bev_4031_hel_wiki_pvmap.csv' --config_file='../../statvar_imports/zurich/bev_4031_hel_wiki/bev_4031_hel_wiki_metadata.csv' --output_path=../../statvar_imports/zurich/bev_4031_hel_wiki/output/zurich_bev_4031_hel_wiki_output"

#####


1. import_name": "Zurich_Population_Number_Of_Birth"

2. Import Overview
Zurich population data at Province and City Level.
Source URL: [Zurich country website](https://www.stadt-zuerich.ch/content/dam/web/de/politik-verwaltung/statistik-und-daten/linked-open-data/datacommons/bev_4031_wiki.csv)
Import Type: Fully Autorefresh
Source Data Availability: 1998 to 2023
Release Frequency: P1Y

3. Preprocessing Steps (No)

4. Autorefresh Type

Fully Autorefresh:" 0 20 29 * * " (Runs at 8:00 PM on the 29th of every month).

5. Script Execution Details

"python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='../../statvar_imports/zurich/bev_4031_wiki/test_data/bev_4031_wiki_input.csv' --pv_map='../../statvar_imports/zurich/bev_4031_wiki/bev_4031_wiki_pvmap.csv' --config_file='../../statvar_imports/zurich/bev_4031_wiki/bev_4031_wiki_metadata.csv' --output_path=../../statvar_imports/zurich/bev_4031_wiki/output/zurich_bev_4031_wiki_output"

#####


1. import_name": "Zurich_Population_By_Origin"

2. Import Overview
Zurich population data at Province and City Level.
Source URL: [Zurich country website](https://www.stadt-zuerich.ch/content/dam/web/de/politik-verwaltung/statistik-und-daten/linked-open-data/datacommons/bev_3903_hel_wiki.csv)
Import Type: Fully Autorefresh
Source Data Availability: 1993 to 2023
Release Frequency: P1Y

3. Preprocessing Steps (Yes) There's an encoding issue with the source input file. To resolve the special characters, please run the following command
    python3 convert_to_utf8.py --input_csv_path= <input.csv file>
    example: python3 convert_to_utf8.py --input_csv_path=bev_3903_hel_wiki.csv
4. Autorefresh Type

Fully Autorefresh:" 15 1 29 * * " (Runs at 1:15 AM on the 29th of every month).

5. Script Execution Details

"python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='../../statvar_imports/zurich/bev_3903_hel_wiki/test_data/bev_3903_hel_wiki_utf8_input.csv' --pv_map='../../statvar_imports/zurich/bev_3903_hel_wiki/bev_3903_hel_wiki_pvmap.csv' --config_file='../../statvar_imports/zurich/bev_3903_hel_wiki/bev_3903_hel_wiki_metadata.csv' --output_path=../../statvar_imports/zurich/bev_3903_hel_wiki/output/zurich_population_bev_3903_hel_wiki_output"

#####


1. import_name": "Zurich_Population_Number_Of_Birth_By_Sex"

2. Import Overview
Zurich population data at Province and City Level.
Source URL: [Zurich country website](https://www.stadt-zuerich.ch/content/dam/web/de/politik-verwaltung/statistik-und-daten/linked-open-data/datacommons/bev_4031_sex_wiki.csv)
Import Type: Fully Autorefresh
Source Data Availability: 1993 to 2023
Release Frequency: P1Y

3. Preprocessing Steps (No)

4. Autorefresh Type

Fully Autorefresh:" 07 19 29 * * " (Runs at 7:07 PM on the 29th of every month).

5. Script Execution Details

"python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='../../statvar_imports/zurich/bev_4031_sex_wiki/test_data/bev_4031_sex_wiki_input.csv' --pv_map='../../statvar_imports/zurich/bev_4031_sex_wiki/bev_4031_sex_wiki_pvmap.csv' --config_file='../../statvar_imports/zurich/bev_4031_sex_wiki/bev_4031_sex_wiki_metadata.csv' --output_path=../../statvar_imports/zurich/bev_4031_sex_wiki/output/zurich_bev_4031_sex_wiki_output"

#####


1. import_name": "Zurich_Population_By_Sex"

2. Import Overview
Zurich population data at Province and City Level.
Source URL: [Zurich country website](https://www.stadt-zuerich.ch/content/dam/web/de/politik-verwaltung/statistik-und-daten/linked-open-data/datacommons/bev_3903_sex_wiki.csv)
Import Type: Fully Autorefresh
Source Data Availability: 1993 to 2023
Release Frequency: P1Y

3. Preprocessing Steps (No)
    

4. Autorefresh Type

Fully Autorefresh:" 55 10 29 * * " (Runs at 10:55 AM on the 29th of every month).

5. Script Execution Details

"python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='../../statvar_imports/zurich/bev_3903_sex_wiki/test_data/bev_3903_sex_wiki_input.csv' --pv_map='../../statvar_imports/zurich/bev_3903_sex_wiki/bev_3903_sex_wiki_pvmap.csv' --config_file='../../statvar_imports/zurich/bev_3903_sex_wiki/bev_3903_sex_wiki_metadata.csv' --output_path=../../statvar_imports/zurich/bev_3903_sex_wiki/output/zurich_population_bev_3903_sex_wiki_output"

#####
