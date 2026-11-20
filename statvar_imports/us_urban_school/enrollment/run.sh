#!/bin/bash
set -euo pipefail

SCRIPT_PATH=$(realpath "$(dirname "$0")")

mkdir -p "$SCRIPT_PATH/output_files" "$SCRIPT_PATH/counters"

# --- 1. Process 2010, 2012, and 2014 Files (Comma-separated XLSX format) ---
for file in \
  "$SCRIPT_PATH/input_files/2010_Enrollment.xlsx" \
  "$SCRIPT_PATH/input_files/2012_Enrollment.xlsx" \
  "$SCRIPT_PATH/input_files/2014_Enrollment.xlsx"; do
  if [[ ! -s "$file" ]]; then
    echo "Error: Required input file $file is missing or empty!"
    exit 1
  fi
done
LEGACY_XLSX_FILES="$SCRIPT_PATH/input_files/2010_Enrollment.xlsx,$SCRIPT_PATH/input_files/2012_Enrollment.xlsx,$SCRIPT_PATH/input_files/2014_Enrollment.xlsx"

# Race and Sex (2010-2014)
python3 "$SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py" \
--input_data="$LEGACY_XLSX_FILES" \
--pv_map="$SCRIPT_PATH/race_and_sex_pvmap.csv" \
--config_file="$SCRIPT_PATH/metadata.csv" \
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
--output_path="$SCRIPT_PATH/output_files/enrollment_by_race_and_sex_2010_2014_output" \
--output_counters="$SCRIPT_PATH/counters/enrollment_by_race_and_sex_2010_2014_counters.csv" \
--recon_property=variableMeasured \
--log_level=-2 \
--log_every_n=1000 || \
{ echo "Error: Processing race_and_sex files for the year 2010 to 2014 failed!"; exit 1; }

# Disability and Sex (2010-2014)
python3 "$SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py" \
--input_data="$LEGACY_XLSX_FILES" \
--pv_map="$SCRIPT_PATH/disability_and_sex_pvmap.csv" \
--config_file="$SCRIPT_PATH/metadata.csv" \
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
--output_path="$SCRIPT_PATH/output_files/enrollment_by_disability_and_sex_2010_2014_output" \
--output_counters="$SCRIPT_PATH/counters/enrollment_by_disability_and_sex_2010_2014_counters.csv" \
--recon_property=variableMeasured \
--log_level=-2 \
--log_every_n=1000 || \
{ echo "Error: Processing disability_and_sex for the year 2010 to 2014 failed!"; exit 1; }

# LEP and Sex (2010-2014)
python3 "$SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py" \
--input_data="$LEGACY_XLSX_FILES" \
--pv_map="$SCRIPT_PATH/lep_and_sex_pvmap.csv" \
--config_file="$SCRIPT_PATH/metadata.csv" \
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
--output_path="$SCRIPT_PATH/output_files/enrollment_by_lep_and_sex_2010_2014_output" \
--output_counters="$SCRIPT_PATH/counters/enrollment_by_lep_and_sex_2010_2014_counters.csv" \
--recon_property=variableMeasured \
--log_level=-2 \
--log_every_n=1000 || \
{ echo "Error: Processing lep_and_sex for the year 2010 to 2014 failed!"; exit 1; }

# --- 2. Process 2016 File (Separate CSV) ---
SINGLE_2016_FILE="$SCRIPT_PATH/input_files/2016_Enrollment.csv"
if [[ ! -s "$SINGLE_2016_FILE" ]]; then
  echo "Error: Required input file $SINGLE_2016_FILE is missing or empty!"
  exit 1
fi

# Race and Sex (2016)
python3 "$SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py" \
--input_data="$SINGLE_2016_FILE" \
--pv_map="$SCRIPT_PATH/race_and_sex_pvmap.csv" \
--config_file="$SCRIPT_PATH/metadata.csv" \
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
--output_path="$SCRIPT_PATH/output_files/enrollment_by_race_and_sex_2016_output" \
--output_counters="$SCRIPT_PATH/counters/enrollment_by_race_and_sex_2016_counters.csv" \
--recon_property=variableMeasured \
--log_level=-2 \
--log_every_n=1000 || \
{ echo "Error: Processing race_and_sex for the year 2016 failed!"; exit 1; }

# Disability and Sex (2016)
python3 "$SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py" \
--input_data="$SINGLE_2016_FILE" \
--pv_map="$SCRIPT_PATH/disability_and_sex_pvmap.csv" \
--config_file="$SCRIPT_PATH/metadata.csv" \
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
--output_path="$SCRIPT_PATH/output_files/enrollment_by_disability_and_sex_2016_output" \
--output_counters="$SCRIPT_PATH/counters/enrollment_by_disability_and_sex_2016_counters.csv" \
--recon_property=variableMeasured \
--log_level=-2 \
--log_every_n=1000 || \
{ echo "Error: Processing disability_and_sex for the year 2016 failed!"; exit 1; }

# LEP and Sex (2016)
python3 "$SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py" \
--input_data="$SINGLE_2016_FILE" \
--pv_map="$SCRIPT_PATH/lep_and_sex_pvmap.csv" \
--config_file="$SCRIPT_PATH/metadata.csv" \
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
--output_path="$SCRIPT_PATH/output_files/enrollment_by_lep_and_sex_2016_output" \
--output_counters="$SCRIPT_PATH/counters/enrollment_by_lep_and_sex_2016_counters.csv" \
--recon_property=variableMeasured \
--log_level=-2 \
--log_every_n=1000 || \
{ echo "Error: Processing lep_and_sex for the year 2016 failed!"; exit 1; }

# --- 3. Process 2018 onwards Files (Comma-separated CSVs, excluding 2016) ---
# Inputs: All *.csv files in input_files except 2016_Enrollment.csv
# This is dynamic and will include 2018, 2021, 2022, 2024, and any future files.
CSV_FILES_2018_ONWARD=$(find "$SCRIPT_PATH/input_files" -maxdepth 1 -name "*.csv" ! -name "2016_Enrollment.csv" | sort | paste -sd, -)

if [ -z "$CSV_FILES_2018_ONWARD" ]; then
  echo "Error: No CSV files found for 2018 onward in $SCRIPT_PATH/input_files!"
  exit 1
fi

# Race and Sex (2018 onwards)
python3 "$SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py" \
--input_data="$CSV_FILES_2018_ONWARD" \
--pv_map="$SCRIPT_PATH/race_and_sex_pvmap.csv" \
--config_file="$SCRIPT_PATH/metadata.csv" \
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
--output_path="$SCRIPT_PATH/output_files/enrollment_by_race_and_sex_2018Onwards_output" \
--output_counters="$SCRIPT_PATH/counters/enrollment_by_race_and_sex_2018Onwards_counters.csv" \
--recon_property=variableMeasured \
--log_level=-2 \
--log_every_n=1000 || \
{ echo "Error: Processing race_and_sex for the year 2018Onwards failed!"; exit 1; }

# Disability and Sex (2018 onwards)
python3 "$SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py" \
--input_data="$CSV_FILES_2018_ONWARD" \
--pv_map="$SCRIPT_PATH/disability_and_sex_pvmap.csv" \
--config_file="$SCRIPT_PATH/metadata.csv" \
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
--output_path="$SCRIPT_PATH/output_files/enrollment_by_disability_and_sex_2018Onwards_output" \
--output_counters="$SCRIPT_PATH/counters/enrollment_by_disability_and_sex_2018Onwards_counters.csv" \
--recon_property=variableMeasured \
--log_level=-2 \
--log_every_n=1000 || \
{ echo "Error: Processing disability_and_sex for the year 2018Onwards failed!"; exit 1; }

# LEP and Sex (2018 onwards)
python3 "$SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py" \
--input_data="$CSV_FILES_2018_ONWARD" \
--pv_map="$SCRIPT_PATH/lep_and_sex_pvmap.csv" \
--config_file="$SCRIPT_PATH/metadata.csv" \
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
--output_path="$SCRIPT_PATH/output_files/enrollment_by_lep_and_sex_2018Onwards_output" \
--output_counters="$SCRIPT_PATH/counters/enrollment_by_lep_and_sex_2018Onwards_counters.csv" \
--recon_property=variableMeasured \
--log_level=-2 \
--log_every_n=1000 || \
{ echo "Error: Processing lep_and_sex for the year 2018Onwards failed!"; exit 1; }

echo "All processing steps completed successfully."
exit 0
