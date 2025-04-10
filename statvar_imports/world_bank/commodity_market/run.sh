#run the download script to download the input files
python3 download.py

#process the Monthy Price sheet
python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data="input/monthly_prices_data.csv" --pv_map="commodity_monthly_price_pvmap.csv" --config_file="commodity_monthly_price_metadata.csv" -output_path="output/commodity_monthly_price"


#process the Annual Price sheet (real)
python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data="input/annual_prices_real_data.csv" --pv_map="commodity_annual_price_pvmap_real.csv" --config_file="commodity_annual_price_metadata.csv" --output_path="output/commodity_annual_real_price"


#process the Annual Price sheet (nominal)
python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data="input/annual_prices_nominal_data.csv" --pv_map="commodity_annual_price_pvmap_nominal.csv" --config_file="commodity_annual_price_metadata.csv" --output_path="output/commodity_annual_nominal_price"



#process the Monthy Indices sheet
python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data="input/monthly_indices_data.csv" --pv_map="commodity_monthly_indices_pvmap.csv" --config_file="commodity_monthly_indices_metadata.csv" --output_path="output/commodity_monthly_indices"



#process the Annual Indices sheet (Nominal)
python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data="input/annual_indices_nominal_data.csv" --pv_map="commodity_annual_indices_pvmap_nominal.csv" --config_file="commodity_annual_indices_metadata.csv" --output_path="output/commodity_annual_nominal_indices"



#process the Annual Indices sheet (Real)
python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data="input/annual_indices_real_data.csv" --pv_map="commodity_annual_indices_pvmap_real.csv" --config_file="commodity_annual_indices_metadata.csv" --output_path="output/commodity_annual_real_indices"



