#!/bin/bash
set -e

# ----------------------------------------------------------------------------------------------------------------------------------------------------
# This Bash script automates the full data processing pipeline for the Teachers and Staff dataset by strategically grouping input files. 
# First, it combines all older XLSX files (2010, 2012, and 2014) for processing into a single legacy output file. 
# Next, it isolates the 2016 CSV file to generate a separate output for that specific year. 
# Finally, it locates and processes all remaining CSV files (2018 onwards) together to create one combined, up-to-date output file, 
# ensuring the processing tool runs successfully for each major historical format and grouping while providing clear error messages if any step fails.
# ----------------------------------------------------------------------------------------------------------------------------------------------------

SCRIPT_PATH=$(realpath "$(dirname "$0")")

# --- 1. Process 2010 and 2014 Files (Older XLSX format) ---
LEGACY_XLSX_FILES="$SCRIPT_PATH/input_files/*2010_Teachers.xlsx $SCRIPT_PATH/input_files/*2012_Teachers.xlsx $SCRIPT_PATH/input_files/*2014_Teachers.xlsx"

# teachers_and_staff (2010-2014)
python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py \
--input_data=$LEGACY_XLSX_FILES \
--pv_map=$SCRIPT_PATH/teachers_and_staff_pvmap.csv \
--config_file=$SCRIPT_PATH/metadata.csv \
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
--output_path=$SCRIPT_PATH/output_files/teachers_and_staff_2010_2014_output \
--log_level=-2 \
--log_every_n=1000 || \
{ echo "Error: Processing teachers_and_staff files for the year 2010 to 2014 failed!"; exit 1; }

# --- 2. Process 2016 File (Separate CSV) ---
SINGLE_2016_FILE="$SCRIPT_PATH/input_files/2016_Teachers.csv"

python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py \
--input_data=$SINGLE_2016_FILE \
--pv_map=$SCRIPT_PATH/teachers_and_staff_pvmap.csv \
--config_file=$SCRIPT_PATH/metadata.csv \
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
--output_path=$SCRIPT_PATH/output_files/teachers_and_staff_2016_output \
--log_level=-2 \
--log_every_n=1000 || \
{ echo "Error: Processing teachers_and_staff files for the year 2016 failed!"; exit 1; }

# --- 3. Process 2018 onwards Files (Combined CSVs, excluding 2016) ---
# This is dynamic and will include 2018, 2021, 2022, and any future files.
CSV_FILES_2018_ONWARD=$(find $SCRIPT_PATH/input_files -maxdepth 1 -name "*.csv" | grep -v "2016_Teachers.csv" | xargs)

# Teachers and Staff (2018 onwards)
python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py \
--input_data=$CSV_FILES_2018_ONWARD \
--pv_map=$SCRIPT_PATH/teachers_and_staff_pvmap.csv \
--config_file=$SCRIPT_PATH/metadata.csv \
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
--output_path=$SCRIPT_PATH/output_files/teachers_and_staff_2018_2022_output \
--log_level=-2 \
--log_every_n=1000 || \
{ echo "Error: Processing teachers_and_staff files for the year 2018 to 2022 failed!"; exit 1; }

echo "All processing steps completed successfully."
exit 0


