#!/bin/bash
set -e

SCRIPT_PATH=$(realpath "$(dirname "$0")")

# 1. Educational Attainment (No places_resolved.csv available)
echo "Processing Educational Attainment..."
python3 "$SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py" \
  --input_data="$SCRIPT_PATH/input_files/educational_attainment_by_age_range_and_gender.csv" \
  --pv_map="$SCRIPT_PATH/educational_attainment_by_age_range_and_gender_pvmap.csv" \
  --config_file="$SCRIPT_PATH/common_metadata.csv" \
  --output_path="$SCRIPT_PATH/output_files/educational_attainment_by_age_range_and_gender/educational_attainment_by_age_range_and_gender_output" \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf || { echo "Error: Processing educational_attainment failed!"; exit 1; }

# 2. Post Secondary Completions (Use specific places_resolved.csv)
echo "Processing Post Secondary Completions..."
python3 "$SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py" \
  --input_data="$SCRIPT_PATH/input_files/post_secondary_completions_total_awards_degrees.csv" \
  --pv_map="$SCRIPT_PATH/post_secondary_completions_total_awards_degrees_pvmap.csv" \
  --config_file="$SCRIPT_PATH/common_metadata.csv" \
  --output_path="$SCRIPT_PATH/output_files/post_secondary_completions_total_awards_degrees/post_secondary_completions_total_awards_degrees_output" \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --places_resolved_csv="$SCRIPT_PATH/post_secondary_completions_total_awards_degrees_places_resolved.csv" || { echo "Error: Processing post_secondary_completions failed!"; exit 1; }

# 3. Public School Enrollment (Use specific places_resolved.csv)
echo "Processing Public School Enrollment..."
python3 "$SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py" \
  --input_data="$SCRIPT_PATH/input_files/public_school_enrollment_by_county_grade_and_race.csv" \
  --pv_map="$SCRIPT_PATH/public_school_enrollment_by_county_grade_and_race_pvmap.csv" \
  --config_file="$SCRIPT_PATH/common_metadata.csv" \
  --output_path="$SCRIPT_PATH/output_files/public_school_enrollment_by_county_grade_and_race/public_school_enrollment_by_county_grade_and_race_output" \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --places_resolved_csv="$SCRIPT_PATH/public_school_enrollment_by_county_grade_and_race_places_resolved.csv" || { echo "Error: Processing public_school_enrollment failed!"; exit 1; }

# 4. Undergraduate STEM Enrollment (Use specific places_resolved.csv)
echo "Processing Undergraduate STEM Enrollment..."
python3 "$SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py" \
  --input_data="$SCRIPT_PATH/input_files/undergraduate_stem_enrollment.csv" \
  --pv_map="$SCRIPT_PATH/undergraduate_stem_enrollment_pvmap.csv" \
  --config_file="$SCRIPT_PATH/common_metadata.csv" \
  --output_path="$SCRIPT_PATH/output_files/undergraduate_stem_enrollment/undergraduate_stem_enrollment_output" \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --places_resolved_csv="$SCRIPT_PATH/undergraduate_stem_enrollment_places_resolved.csv" || { echo "Error: Processing undergraduate_stem_enrollment failed!"; exit 1; }

echo "All processing steps completed successfully."
exit 0
