# Commerce_EDA

- source: https://www.eda.gov/performance/data-disclaimer, 

- how to download data: Download script (download.py).
    Manually downloaded an XLSX file from the source. From that, extract the specific sheet containing the data as a CSV. This CSV was then uploaded to our GCS bucket.
  
- type of place: Country (U.S).


- years: 1990 to June 2021.

- Import Type:  Manual file-based import (CSV)

- Source Data Availability: 

- Release Frequency: Yearly


###Pre Processing
The script process.py download files from gcp bucket to gcs_folder. Also for Investment.cvs, identifies US state names in the first column, and then restructures the data. For rows identified as state headers, it assigns the state name to a new 'Place' column and "Total" to a new 'Category' column. For subsequent rows under a state (which are assumed to be categories), it assigns the most recently detected state to the 'Place' column and the original first column's content to the 'Category' column. It then cleans numerical values (removes trailing .0) and handles missing data, finally saving the processed data to a new CSV file (input_file/Investment1.csv).


#### Processing

If processing from current import folder :

"process.py","../../tools/statvar_importer/stat_var_processor.py --input_data=input_file/Investment1.csv --pv_map=Investmentpvmap.csv --config_file=Investmentmetadata.csv --output_path=output/Investment_output"`



Semi Autorefresh:
Upload final files to:

     * `gs://unresolved_mcf/us_eda/latest/`
Trigger `data/import-automation/executor/run_import.sh` manually for test/prod ingestion 




