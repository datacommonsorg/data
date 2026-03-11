#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting France Demographics Import..."

mkdir -p input_files
mkdir -p output

download_and_rename() {
    local url=$1
    local final_name=$2
    local temp_name=$(basename "$url")
    
    echo "Downloading $temp_name..."
    python ../../util/download_util_script.py --download_url="$url" --output_folder=input_files/
    
    echo "Renaming $temp_name to $final_name..."
    mv "input_files/$temp_name" "input_files/$final_name"
}

download_and_rename "https://www.insee.fr/en/statistiques/fichier/8333211/Pop_annu_compo_evol_va.xlsx" "annual_population_components.xlsx"
download_and_rename "https://www.insee.fr/en/statistiques/fichier/8333211/Pop1janv_age_va.xlsx" "population_sex_detailed_age.xlsx"
download_and_rename "https://www.insee.fr/en/statistiques/fichier/8333211/Pop1janv_grages_va.xlsx" "population_sex_age_groups.xlsx"
download_and_rename "https://www.insee.fr/en/statistiques/fichier/8333211/Pop_age_moyen_median_va.xlsx" "average_median_age.xlsx"

echo "Verifying downloaded files:"
ls -lh input_files/

MCF_PATH="gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
CONFIG="france_demographics_metadata.csv"
STATVAR_PROCESSOR="../../tools/statvar_importer/stat_var_processor.py"

run_processor() {
    local input=$1
    local pvmap=$2
    local out=$3
    
    echo "Processing $input..."
    python "$STATVAR_PROCESSOR" \
        --input_data="input_files/$input" \
        --pv_map="$pvmap" \
        --config_file="$CONFIG" \
        --existing_statvar_mcf="$MCF_PATH" \
        --output_path="output/$out"
}

run_processor "annual_population_components.xlsx" "annual_population_components_pvmap.csv" "annual_population_components_output"
run_processor "population_sex_detailed_age.xlsx" "population_sex_detailed_age_pvmap.csv" "population_sex_detailed_age_output"
run_processor "population_sex_age_groups.xlsx" "population_sex_age_groups_pvmap.csv" "population_sex_age_groups_output"
run_processor "average_median_age.xlsx" "average_median_age_pvmap.csv" "average_median_age_output"

echo "Import completed successfully."
