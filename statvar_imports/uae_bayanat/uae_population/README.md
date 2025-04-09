# UAE_Population

- source: https://admin.bayanat.ae/Dataset/DownloadDatasetResource?fileId=26585eaf-9a9c-486d-b773-fc51ef0204c9&resourceID=11243, 

- how to download data: Download script (download_script/UAE_Download.py).
    To download the data, you'll need to use the provided download script, download_script/UAE_Download.py. This script will automatically create an "input" folder where you should place the file to be processed. The script also requires a configuration file (config.ini) to function correctly.

- type of place: Country.

- statvars: Demographics

- years: 1975 to 2005.

- place_resolution: Places resolved to wikidataId in metadata sheet itself.

### How to run:

`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='<input_file>.xlsx' --pv_map='statvar_imports/uae_Population/UAE_Population/<filename>_pvmap.csv,observationAbout:statvar_imports/uae_Population/UAE_Population/UAEPopulation_places_resolved_csv.csv' --config='statvar_imports/uae_Population/UAE_Population/UAEPopulationByEmiratesNationality_metadata.csv' --output_path=<filepath/filename>`

#### Example
#### Download : 
`python3 uae_download.py`

'After running the script python3 uae_download.py, it successfully creates an "input" folder and downloaded the source file named uaepopulationbyemiratesnationalityandgender.xlsx into it.'

#### Processing
`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='/data/statvar_imports/uae_bayanat/uae_population/input/UAEPopulationByEmiratesNationalityandgender.xlsx' --pv_map='data/statvar_imports/uae_bayanat/uae_population/uae_population_pvmap.csv' --places_resolved_csv='data/statvar_imports/uae_bayanat/uae_population/uae_population_places_resolved_csv.csv' --config='data/statvar_imports/uae_bayanat/uae_population/uae_population_metadata.csv' --output_path=data/statvar_imports/uae_bayanat/uae_population/output/uaepopulation_output`


