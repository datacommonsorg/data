mkdir -p gcs_folder/input_files
gcloud storage cp --recursive gs://unresolved_mcf/us_nces/demographics/private_school/semi_automation_input_files/* gcs_folder/input_files/
