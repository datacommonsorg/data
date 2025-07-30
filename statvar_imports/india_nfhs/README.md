# India_NFHS

- source: https://ndap.niti.gov.in/dataset, 

- how to download data: 
    Download script (download.py). This script automates the download, preprocessing, and storage of data from the NDAP API. It fetches data for three specified datasets, handles API pagination to ensure all available records are retrieved, and then performs specific data transformations like generating YearCode and DistrictName columns. The processed data is saved as CSV files (NFHS_Survey4.csv, NFHS_Survey5.csv, NFHS_state.csv) in the gcs_output directory.
  
- type of place: Country (India).


- years: 2019.

- Import Type:  Fully Automated

- Source Data Availability: 

- Release Frequency: Yearly




#### Processing

If processing from current import folder :

"download.py","../../tools/statvar_importer/stat_var_processor.py --input_data=gcs_output/NFHS_state.csv --pv_map=NFHS-Statepvmap.csv --config_file=metadata.csv --places_resolved_csv=NFHS-Stateplace_resolver.csv --output_path=output/NFHS_output"



Fully Autorefresh:

Trigger `data/import-automation/executor/run_import.sh` manually for test/prod ingestion 




