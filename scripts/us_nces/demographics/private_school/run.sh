mkdir -p gcs_folder/input_files
gsutil -m cp -r gs://unresolved_mcf/us_nces/demographics/private_school/semi_automation_input_files/* gcs_folder/input_files/
