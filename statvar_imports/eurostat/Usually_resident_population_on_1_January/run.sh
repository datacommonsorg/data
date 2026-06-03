#!/bin/bash
# Auto-generated commands
export GEMINI_API_KEY="..."
export DC_API_KEY="..."


# Step 3: Data Download
curl -L --retry 3 "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/DEMO_URESPOP/?format=SDMX-CSV&compressed=false" -o sdmx/Usually_resident_population_on_1_January/Usually_resident_population_on_1_January_data_raw.csv

# Step 4: Data Sampling
/usr/local/google/home/abhishekjaisw/.pyenv/versions/3.11.8/envs/dc_import_env/bin/python3 tools/statvar_importer/data_sampler.py "--sampler_input=sdmx/Usually_resident_population_on_1_January/Usually_resident_population_on_1_January_data_raw.csv" "--sampler_output=sdmx/Usually_resident_population_on_1_January/sample_data.csv" "--sampler_output_rows=200"

# Step 5: Generate PV Map
echo "y" | /usr/local/google/home/abhishekjaisw/.pyenv/versions/3.11.8/envs/dc_import_env/bin/python3 tools/agentic_import/pvmap_generator.py "--input_data=sdmx/Usually_resident_population_on_1_January/sample_data.csv" "--input_metadata=sdmx/Usually_resident_population_on_1_January/Usually_resident_population_on_1_January_metadata.json" "--output_path=sdmx/Usually_resident_population_on_1_January/sample_output/output" --sdmx_dataset

# Step 6: Full Data Processing
/usr/local/google/home/abhishekjaisw/.pyenv/versions/3.11.8/envs/dc_import_env/bin/python3 tools/statvar_importer/stat_var_processor.py "--input_data=sdmx/Usually_resident_population_on_1_January/Usually_resident_population_on_1_January_data_raw.csv" "--pv_map=sdmx/Usually_resident_population_on_1_January/sample_output/output_pvmap_cleaned.csv" "--config_file=sdmx/Usually_resident_population_on_1_January/sample_output/output_metadata.csv" "--generate_statvar_name=True" "--skip_constant_csv_columns=False" "--output_columns=observationDate,observationAbout,variableMeasured,value,observationPeriod,measurementMethod,unit,scalingFactor" "--output_path=sdmx/Usually_resident_population_on_1_January/final_output/output" "--places_resolved_csv=sdmx/places_resolved.csv" "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf" "--maps_api_key=AIzaSyBKu8mX6XZx0UDk_EKtXTtzQFmiZtXAB30"

# Step 7: Java Linting
java "-Ddcid.api_key=5FB5ESzcsKNd6M1hraeQpyF0sCGXKXTy8qx8NpbAE8BKFZ0a" -jar /usr/local/google/home/abhishekjaisw/Desktop/data_abhi/datacommons-import-tool-0.1-jar-with-dependencies.jar lint sdmx/Usually_resident_population_on_1_January/final_output/output.csv sdmx/Usually_resident_population_on_1_January/final_output/output.tmcf sdmx/Usually_resident_population_on_1_January/final_output/output_stat_vars.mcf "-o=sdmx/Usually_resident_population_on_1_January/final_output" "--num-threads=4" "--resolution=FULL"

# Step 6: Full Data Processing (Using Clean Local Map)
/usr/local/google/home/abhishekjaisw/.pyenv/versions/3.11.8/envs/dc_import_env/bin/python3 tools/statvar_importer/stat_var_processor.py "--input_data=sdmx/Usually_resident_population_on_1_January/Usually_resident_population_on_1_January_data_raw.csv" "--pv_map=sdmx/Usually_resident_population_on_1_January/sample_output/output_pvmap_cleaned.csv" "--config_file=sdmx/Usually_resident_population_on_1_January/sample_output/output_metadata.csv" "--generate_statvar_name=True" "--skip_constant_csv_columns=False" "--output_columns=observationDate,observationAbout,variableMeasured,value,observationPeriod,measurementMethod,unit,scalingFactor" "--output_path=sdmx/Usually_resident_population_on_1_January/final_output/output" "--places_resolved_csv=sdmx/places_resolved_runtime.csv" "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"

# Step 7: Java Linting (Online Structural Validation)
java "-Ddcid.api_key=JmbDhCZMj6oZDrjjLhKlBpGHiwF5XlKTBVEHWBDq0BaWjjRK" -jar /usr/local/google/home/abhishekjaisw/Desktop/data_abhi/datacommons-import-tool-0.1-jar-with-dependencies.jar lint sdmx/Usually_resident_population_on_1_January/final_output/output.csv sdmx/Usually_resident_population_on_1_January/final_output/output.tmcf sdmx/Usually_resident_population_on_1_January/final_output/output_stat_vars.mcf sdmx/provisional_places.mcf sdmx/stat_vars_schema.mcf "-o=sdmx/Usually_resident_population_on_1_January/final_output" "--num-threads=4" "--resolution=FULL"

# Step 6: Full Data Processing (Using Clean Local Map)
/usr/local/google/home/abhishekjaisw/.pyenv/versions/3.11.8/envs/dc_import_env/bin/python3 tools/statvar_importer/stat_var_processor.py "--input_data=sdmx/Usually_resident_population_on_1_January/Usually_resident_population_on_1_January_data_raw.csv" "--pv_map=sdmx/Usually_resident_population_on_1_January/sample_output/output_pvmap_cleaned.csv" "--config_file=sdmx/Usually_resident_population_on_1_January/sample_output/output_metadata.csv" "--generate_statvar_name=True" "--skip_constant_csv_columns=False" "--output_columns=observationDate,observationAbout,variableMeasured,value,observationPeriod,measurementMethod,unit" "--output_path=sdmx/Usually_resident_population_on_1_January/final_output/output" "--places_resolved_csv=sdmx/places_resolved_runtime.csv" "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"

# Step 7: Java Linting (Online Structural Validation)
java "-Ddcid.api_key=JmbDhCZMj6oZDrjjLhKlBpGHiwF5XlKTBVEHWBDq0BaWjjRK" -jar /usr/local/google/home/abhishekjaisw/Desktop/data_abhi/datacommons-import-tool-0.1-jar-with-dependencies.jar lint sdmx/Usually_resident_population_on_1_January/final_output/output.csv sdmx/Usually_resident_population_on_1_January/final_output/output.tmcf sdmx/Usually_resident_population_on_1_January/final_output/output_stat_vars.mcf sdmx/provisional_places.mcf sdmx/stat_vars_schema.mcf "-o=sdmx/Usually_resident_population_on_1_January/final_output" "--num-threads=4" "--resolution=FULL"

# Step 6: Full Data Processing (Using Clean Local Map)
/usr/local/google/home/abhishekjaisw/.pyenv/versions/3.11.8/envs/dc_import_env/bin/python3 tools/statvar_importer/stat_var_processor.py "--input_data=sdmx/Usually_resident_population_on_1_January/Usually_resident_population_on_1_January_data_raw.csv" "--pv_map=sdmx/Usually_resident_population_on_1_January/sample_output/output_pvmap_cleaned.csv" "--config_file=sdmx/Usually_resident_population_on_1_January/sample_output/output_metadata.csv" "--generate_statvar_name=True" "--skip_constant_csv_columns=False" "--output_columns=observationDate,observationAbout,variableMeasured,value,observationPeriod,measurementMethod,unit" "--output_path=sdmx/Usually_resident_population_on_1_January/final_output/output" "--places_resolved_csv=sdmx/places_resolved_runtime.csv" "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"

# Step 7: Java Linting (Online Structural Validation)
java "-Ddcid.api_key=JmbDhCZMj6oZDrjjLhKlBpGHiwF5XlKTBVEHWBDq0BaWjjRK" -jar /usr/local/google/home/abhishekjaisw/Desktop/data_abhi/datacommons-import-tool-0.1-jar-with-dependencies.jar lint sdmx/Usually_resident_population_on_1_January/final_output/output.csv sdmx/Usually_resident_population_on_1_January/final_output/output.tmcf sdmx/Usually_resident_population_on_1_January/final_output/output_stat_vars.mcf sdmx/provisional_places.mcf sdmx/stat_vars_schema.mcf "-o=sdmx/Usually_resident_population_on_1_January/final_output" "--num-threads=4" "--resolution=FULL"
