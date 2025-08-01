python3 download.py --download_data_dir=input_data/un_energy
cat input_data/un_energy*/*.csv > input_data/un_energy_all.csv
python3 process.py --csv_data_files=input_data/un_energy_all.csv --output_path=output_data/un_energy_output