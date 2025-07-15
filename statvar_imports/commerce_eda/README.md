# Commerce_EDA

- source: https://www.eda.gov/performance/data-disclaimer, 

- how to download data: Download script (download.py).
    This Python script automates the download of specific Excel (.xlsx) files from the U.S. Economic Development Administration (EDA) website, extracts designated sheets from these Excel  files,create a folder for that downloaded_eda_data  and saves them as individual CSV files in folder input_file.
  
- type of place: Country (U.S).


- years: 1990 to June 2021.

- Import Type: download.py is used to download the data.

- Source Data Availability: 

- Release Frequency:


###Pre Processing
The script process.py reads an input CSV file (input_file/Investment.csv), identifies US state names in the first column, and then restructures the data. For rows identified as state headers, it assigns the state name to a new 'Place' column and "Total" to a new 'Category' column. For subsequent rows under a state (which are assumed to be categories), it assigns the most recently detected state to the 'Place' column and the original first column's content to the 'Category' column. It then cleans numerical values (removes trailing .0) and handles missing data, finally saving the processed data to a new CSV file (input_file/Investment1.csv).


#### Processing

If processing from current import folder :

"download.py","process.py","../../tools/statvar_importer/stat_var_processor.py --input_data=input_file/Investment1.csv --pv_map=Investmentpvmap.csv --config_file=Investmentmetadata.csv --output_path=output/Investment_output"`



Fully Autorefresh:
Trigger `data/import-automation/executor/run_import.sh` manually for test/prod ingestion 




