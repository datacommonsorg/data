mkdir -p gcs_folder/input_files
gsutil -m cp -r gs://unresolved_mcf/us_nces/demographics/school_district/semi_automation_input_files/* gcs_folder/input_files/
