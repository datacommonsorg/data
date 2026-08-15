# UAE_Population

- source: https://bayanat.ae/api/DatasetResources/DownloadSingle?resourceID=FT1CGOdcLYt6KdUJnFHWwOdTWpeao-LX539QkMLeAKA&fileName=UAE%20Population%20By%20Emirates%20Nationality%20and%20gender,

- how to download data: Download script (uae_download.py).
    To download the data, you'll need to use the provided download script, download_script/uae_download.py. This script will download a file to be processed. The script also requires a configuration file (config.ini) to function correctly.

- type of place: Country.

- statvars: Demographics

- years: 1975 to 2005.

#### Example
#### Download : 
`python3 uae_download.py`

'After running the script python3 uae_download.py, it successfully downloaded the source file named uae_populationbyemiratesnationalityandgender.xlsx into input folder.'

#### How to run:

`python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data=../../statvar_imports/uae_bayanat/uae_population/input/uae_populationbyemiratesnationalityandgender.xlsx --pv_map=../../statvar_imports/uae_bayanat/uae_population/uae_population_pvmap.csv --places_resolved_csv=../../statvar_imports/uae_bayanat/uae_population/uae_population_places_resolved_csv.csv --config_file=../../statvar_imports/uae_bayanat/uae_population/uae_population_metadata.csv --output_path=../../statvar_imports/uae_bayanat/uae_population/output/uae_population_output`



