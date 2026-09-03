1. import_name": "Zurich_Population_Number_Of_Company_Workplace_Employees"

2. Import Overview
Number of companies, workplaces and employees in Zurich city at Province and City Level.
Source URL: [BFS WIR STATENT Data](https://data.stadt-zuerich.ch/dataset/bfs_wir_statent_ast_beschaeftigte_vza_rechtsform_betrgr_jahr_od2552)
Import Type: Fully Autorefresh
Source Data Availability: 2011 to 2022
Release Frequency: P1Y

3. Preprocessing Steps (Yes)
Generate rollups from the downloaded dataset:
python3 wir_2552_wiki/generate_rollups.py

4. Autorefresh Type

Fully Autorefresh:"0 2 29 * * " (Runs at 2:00 AM on the 29th day of every month).

5. Script Execution Details

" python3 ../../util/download_util_script.py --download_url=https://data.stadt-zuerich.ch/dataset/bfs_wir_statent_ast_beschaeftigte_vza_rechtsform_betrgr_jahr_od2552/download/WIR255OD2552.csv --output_folder=wir_2552_wiki/input_files && python3 wir_2552_wiki/generate_rollups.py && python3 ../../tools/statvar_importer/stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data=wir_2552_wiki/input_files/WIR255OD2552_rollups.csv --pv_map=wir_2552_wiki/wir_2552_wiki_pvmap.csv --config_file=wir_2552_wiki/wir_2552_wiki_metadata.csv --output_columns=observationAbout,observationDate,value,variableMeasured --output_path=wir_2552_wiki/output/zurich_population_wir_2552_wiki --output_counters=wir_2552_wiki/counters/zurich_population_wir_2552_wiki_counters.csv "

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
Total population of Zurich city by quarter and year at Province and City Level.
Source URL: [BEV324OD3240 Dataset](https://data.stadt-zuerich.ch/dataset/bev_bestand_jahr_quartier_od3240)
Import Type: Fully Autorefresh
Source Data Availability: 1941 to 2023
Release Frequency: P1Y

3. Preprocessing Steps (No)

4. Autorefresh Type

Fully Autorefresh:" 30 11 29 * * " (Runs at 11:30 AM on the 29th of every month).

5. Script Execution Details

" python3 ../../util/download_util_script.py --download_url=https://data.stadt-zuerich.ch/dataset/bev_bestand_jahr_quartier_od3240/download/BEV324OD3240.csv --output_folder=bev_3240_wiki/input_files && python3 ../../tools/statvar_importer/stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data=bev_3240_wiki/input_files/BEV324OD3240.csv --pv_map=bev_3240_wiki/bev_3240_wiki_pvmap.csv --config_file=bev_3240_wiki/bev_3240_wiki_metadata.csv --output_columns=observationAbout,observationDate,value,variableMeasured --output_path=bev_3240_wiki/output/zurich_population_bev_3240_wiki --output_counters=bev_3240_wiki/counters/zurich_population_bev_3240_wiki_counters.csv "

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
