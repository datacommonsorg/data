# India_NFHS

- source: https://ndap.niti.gov.in/dataset, It comprises of three dataset 
            NFHS_state: Data on key indicators of NFHS-5 at state level. The National Family Health Survey (NFHS) provides information on population, health, and other many important indicators.
            NFHS_Survey4: The National Family Health Survey (NFHS) provides information on population, health, and other many important indicators. NFHS-4  is the fourth in the NFHS series.
            NFHS_Survey5:The National Family Health Survey (NFHS) provides information on population, health, and other many important indicators. NFHS-5  is the fifth survey in the NFHS series.

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





