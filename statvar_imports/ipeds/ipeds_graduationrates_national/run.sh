mkdir -p output_files

gcloud storage cp -r gs://unresolved_mcf/IPEDS/graduation_rates_national/input_files ./

python ../../../tools/statvar_importer/stat_var_processor.py --input_data=./input_files/* --config_file=graduation_rates_ipeds_metadata.csv --pv_map=graduation_rates_ipeds_pvmap.csv --statvar_dcid_remap_csv=remap/graduation_rates_ipeds_remap.csv --output_path=output_files/graduation_rates_ipeds_output --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
