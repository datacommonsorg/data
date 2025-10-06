#!/bin/bash
set -e

SCRIPT_PATH=$(realpath "$(dirname "$0")")
PROCESSOR_SCRIPT="$SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py"
INPUT_BASE_PATH="gs://unresolved_mcf/country/brazil/VISDATA/Benefits_RuralDevelopmentProgram/latest/input_files"
CONFIG_FILE="$SCRIPT_PATH/brazil_metadata.csv"
EXISTING_MCF="gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
PLACES_RESOLVER="$SCRIPT_PATH/brazil_places_resolver.csv"

process_file() {
    local basename="$1"
    local places_resolver_arg=""
    if [[ "$2" == "with_resolver" ]]; then
        places_resolver_arg="--places_resolved_csv=$PLACES_RESOLVER"
    fi

    echo "Processing ${basename}.csv..."
    python3 "$PROCESSOR_SCRIPT" \
        --input_data="$INPUT_BASE_PATH/${basename}.csv" \
        --pv_map="$SCRIPT_PATH/${basename}_pvmap.csv" \
        --config_file="$CONFIG_FILE" \
        --output_path="$SCRIPT_PATH/output_files/${basename}_output" \
        --existing_statvar_mcf="$EXISTING_MCF" \
        $places_resolver_arg || { echo "Error: Processing ${basename}.csv failed!"; exit 1; }
}

files_no_resolver=(
    "Families_RuralDevelopmentProgram_Gender_Brazil"
    "Families_RuralDevelopmentProgram_SpecificPopulation_Brazil"
    "FinancialResources_Beneficiary_RuralDevelopmentProgram_brazil"
    "FinancialResources_Beneficiary_RuralDevelopmentProgram_brazil_yearly"
    "TotalFamilies_Rural_Development_Program_Brazil"
)

files_with_resolver=(
    "Families_RuralDevelopmentProgram_Gender_Municipality"
    "Families_RuralDevelopmentProgram_Gender_State"
    "Families_RuralDevelopmentProgram_SpecificPopulation_Municipality"
    "Families_RuralDevelopmentProgram_SpecificPopulation_State"
    "FinancialResources_Beneficiary_RuralDevelopmentProgram_latest_Municipality"
    "FinancialResources_Beneficiary_RuralDevelopmentProgram_latest_State"
    "FinancialResources_Beneficiary_RuralDevelopmentProgram_State"
    "FinancialResources_Beneficiary_RuralDevelopmentProgram_yearly_Municipality"
    "TotalFamilies_Rural_Development_Program_Municipality"
    "TotalFamilies_Rural_Development_Program_State"
)

for basename in "${files_no_resolver[@]}"; do
    process_file "$basename"
done

for basename in "${files_with_resolver[@]}"; do
    process_file "$basename" "with_resolver"
done

echo "All processing steps completed successfully."
exit 0

