# INPE_Fire_Event_Count

- source: https://terrabrasilis.dpi.inpe.br/queimadas/situacao-atual/estatisticas/estatisticas_estados/#anavigation, 

- how to download data: Download script (download.py).
    This script will create one main folder(inpe_data) and download 27 *.csv files for all states to be processed.The script will generate one input.csv file after merging data from all 27 files.

- type of place: Country (Brazil).

- years: 1998 to June 2025.

- Import Type: download.py is used to download the data.

- Source Data Availability: Monthly

- Release Frequency: P1M
  
#### Preprocessing 

download.py handles preprocessing. Merge the files from all states to generate a single file for processing.

#### Processing

If processing from current import folder :

`python3  download.py`../../tools/statvar_importer/stat_var_processor.py --input_data=<input_file>.csv --pv_map=<pv_map>.csv --config=<metadata>.csv --output_path=<filepath/filename>`



If processing from statvar_importer folder :

`python3 ../tools/statvar_importer/stat_var_processor.py --input_data=<input_files>.csv --pv_map=<pvmap>.csv --config_file=<metadata>.csv -output_path=<filepath/filename>`

#### Fully Autorefresh: 

Trigger `run_import.sh` manually for test/prod ingestion





