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
    python3 ../../util/download_util_script.py --download_url="$url" --output_folder=input_files/
    
    echo "Renaming $temp_name to $final_name..."
    mv "input_files/$temp_name" "input_files/$final_name"
}

BASE_URL="https://www.insee.fr/en/statistiques/fichier/8333211"
declare -A files_to_download
files_to_download["Pop_annu_compo_evol_va.xlsx"]="annual_population_components.xlsx"
files_to_download["Pop1janv_age_va.xlsx"]="population_sex_detailed_age.xlsx"
files_to_download["Pop1janv_grages_va.xlsx"]="population_sex_age_groups.xlsx"
files_to_download["Pop_age_moyen_median_va.xlsx"]="average_median_age.xlsx"

for source_file in "${!files_to_download[@]}"; do
  url="${BASE_URL}/${source_file}"
  dest_file="${files_to_download[$source_file]}"
  download_and_rename "$url" "$dest_file"
done

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
    python3 "$STATVAR_PROCESSOR" \
        --input_data="input_files/$input" \
        --pv_map="$pvmap" \
        --config_file="$CONFIG" \
        --existing_statvar_mcf="$MCF_PATH" \
        --output_path="output/$out"
}

datasets=(
    "annual_population_components"
    "population_sex_detailed_age"
    "population_sex_age_groups"
    "average_median_age"
)

for dataset in "${datasets[@]}"; do
    run_processor "${dataset}.xlsx" "${dataset}_pvmap.csv" "${dataset}_output"
done

echo "Import completed successfully."
