#!/bin/bash
set -e

SCRIPT_PATH=$(realpath "$(dirname "$0")")

# --- 1. Process 2010 and 2012 Files (Older XLSX format) ---
python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py \
--input_data="$SCRIPT_PATH/input_files/*.xlsx" \
--pv_map=$SCRIPT_PATH/maths_and_science_pvmap.csv \
--config_file=$SCRIPT_PATH/metadata.csv \
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
--output_path=$SCRIPT_PATH/output_files/maths_and_science_2010_2012_output \
--log_level=-2 \
--log_every_n=1000 || \
{ echo "Error: Processing maths_and_science files for the year 2010 to 2012 failed!"; exit 1; }

# --- 2. Process 2016 File (Separate CSV) ---
python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py \
--input_data="$SCRIPT_PATH/input_files/2016_School_data.csv" \
--pv_map=$SCRIPT_PATH/maths_and_science_pvmap.csv \
--config_file=$SCRIPT_PATH/metadata.csv \
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
--output_path=$SCRIPT_PATH/output_files/maths_and_science_2016_output \
--log_level=-2 \
--log_every_n=1000 || \
{ echo "Error: Processing maths_and_science files for the year 2016 failed!"; exit 1; }

# --- 3. Process 2018 onwards Files (Combined CSVs for each course) ---
# This is dynamic and will include 2018, 2021, 2022, and any future files.

# Advanced mathematics (2018 onwards)
python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py \
--input_data="$SCRIPT_PATH/input_files/*_Advanced_Mathematics.csv" \
--pv_map=$SCRIPT_PATH/maths_and_science_pvmap.csv \
--config_file=$SCRIPT_PATH/metadata.csv \
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
--output_path=$SCRIPT_PATH/output_files/advanced_mathematics_2018_onwards_output \
--log_level=-2 \
--log_every_n=1000 || \
{ echo "Error: Processing Advanced mathematics files for the year 2018 onwards failed!"; exit 1; }

# Algebra II (2018 onwards)
python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py \
--input_data="$SCRIPT_PATH/input_files/*_Algebra_II.csv" \
--pv_map=$SCRIPT_PATH/maths_and_science_pvmap.csv \
--config_file=$SCRIPT_PATH/metadata.csv \
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
--output_path=$SCRIPT_PATH/output_files/algebra2_2018_onwards_output \
--log_level=-2 \
--log_every_n=1000 || \
{ echo "Error: Processing Algebra II files for the year 2018 onwards failed!"; exit 1; }

# Biology (2018 onwards)
python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py \
--input_data="$SCRIPT_PATH/input_files/*_Biology.csv" \
--pv_map=$SCRIPT_PATH/maths_and_science_pvmap.csv \
--config_file=$SCRIPT_PATH/metadata.csv \
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
--output_path=$SCRIPT_PATH/output_files/biology_2018_onwards_output \
--log_level=-2 \
--log_every_n=1000 || \
{ echo "Error: Processing Biology files for the year 2018 onwards failed!"; exit 1; }

# Calculus (2018 onwards)
python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py \
--input_data="$SCRIPT_PATH/input_files/*_Calculus.csv" \
--pv_map=$SCRIPT_PATH/maths_and_science_pvmap.csv \
--config_file=$SCRIPT_PATH/metadata.csv \
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
--output_path=$SCRIPT_PATH/output_files/calculus_2018_onwards_output \
--log_level=-2 \
--log_every_n=1000 || \
{ echo "Error: Processing Calculus files for the year 2018 onwards failed!"; exit 1; }

# Chemistry (2018 onwards)
python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py \
--input_data="$SCRIPT_PATH/input_files/*_Chemistry.csv" \
--pv_map=$SCRIPT_PATH/maths_and_science_pvmap.csv \
--config_file=$SCRIPT_PATH/metadata.csv \
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
--output_path=$SCRIPT_PATH/output_files/chemistry_2018_onwards_output \
--log_level=-2 \
--log_every_n=1000 || \
{ echo "Error: Processing Chemistry files for the year 2018 onwards failed!"; exit 1; }

# Geometry (2018 onwards)
python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py \
--input_data="$SCRIPT_PATH/input_files/*_Geometry.csv" \
--pv_map=$SCRIPT_PATH/maths_and_science_pvmap.csv \
--config_file=$SCRIPT_PATH/metadata.csv \
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
--output_path=$SCRIPT_PATH/output_files/geometry_2018_onwards_output \
--log_level=-2 \
--log_every_n=1000 || \
{ echo "Error: Processing Geometry files for the year 2018 onwards failed!"; exit 1; }

# Physics (2018 onwards)
python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py \
--input_data="$SCRIPT_PATH/input_files/*_Physics.csv" \
--pv_map=$SCRIPT_PATH/maths_and_science_pvmap.csv \
--config_file=$SCRIPT_PATH/metadata.csv \
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
--output_path=$SCRIPT_PATH/output_files/physics_2018_onwards_output \
--log_level=-2 \
--log_every_n=1000 || \
{ echo "Error: Processing Physics files for the year 2018 onwards failed!"; exit 1; }

echo "All processing steps completed successfully."
exit 0



