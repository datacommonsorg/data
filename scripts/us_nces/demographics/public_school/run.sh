mkdir -p gcs_output/input_files
gsutil -m cp -r gs://unresolved_mcf/us_nces/demographics/public_school/semi_automation_input_files/* gcs_output/input_files/
