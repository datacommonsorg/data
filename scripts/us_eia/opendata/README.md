# US EIA Open Data Import

## About the Dataset

### Download URL

Each dataset available as a Zip-file of JSONL content. See [here](https://www.eia.gov/opendata/bulkfiles.php) for more details.

### Data Exploration

To ease analysis of the datasets, see [`generate_jsonl_for_bq.py`](generate_jsonl_for_bq.py) for instructions to convert and import the data into BigQuery.

### EIA International Import (`--dataset=INTL`)

As part of the latest refresh, data quality for the EIA International import has been significantly enhanced. This includes unit standardization and the implementation of filtering mechanisms within `common.py` to resolve identified data discrepancies. A comprehensive explanation of these specific issues and their resolution is documented in the **"EIA_combined_8_imports_doc_Data_Commons_Import"** file (found under 'Import Docs and Schemas' in Drive), within the `EIA_International` tab.

### License

This dataset is available for public use, license is available at https://www.eia.gov/about/copyrights_reuse.php


- Run the [processor](process/README.md)

## Autorefresh Type - Fully Autorefresh
    EIA_Coal: "0 14 5,20 * *" (Runs at 2:00 PM on the 5th and 20th day of every month)

    EIA_Electricity: "0 7 5,20 * *" (Runs at 7:00 AM on the 5th and 20th day of every month)

    EIA_NaturalGas: "0 8 5,20 * *" (Runs at 8:00 AM on the 5th and 20th day of every month)

    EIA_NuclearOutages: "0 9 5,20 * *" (Runs at 9:00 AM on the 5th and 20th day of every month)

    EIA_Petroleum: "0 10 5,20 * *" (Runs at 10:00 AM on the 5th and 20th day of every month)

    EIA_International: "0 11 5,20 * *" (Runs at 11:00 AM on the 5th and 20th day of every month)

    EIA_SEDS: "0 12 5,20 * *" (Runs at 12:00 PM on the 5th and 20th day of every month)

    EIA_TotalEnergy: "0 13 5,20 * *" (Runs at 1:00 PM on the 5th and 20th day of every month)

### Downloading and Processing Data


    If you want to perform "only download", run the below command:

        python3 process.py --dataset=INTL --mode=download
        python3 process.py --dataset=ELEC --mode=download
        python3 process.py --dataset=COAL --mode=download
        python3 process.py --dataset=PET --mode=download
        python3 process.py --dataset=NG --mode=download
        python3 process.py --dataset=SEDS --mode=download
        python3 process.py --dataset=NUC_STATUS --mode=download
        python3 process.py --dataset=TOTAL --mode=download



   If you want to perform "only process", run the below command:

   Running this command generates input_fles and csv, mcf, tmcf, svg.mcf files.

        python3 process.py --dataset=INTL --mode=process
        python3 process.py --dataset=ELEC --mode=process
        python3 process.py --dataset=COAL --mode=process
        python3 process.py --dataset=PET --mode=process
        python3 process.py --dataset=NG --mode=process
        python3 process.py --dataset=SEDS --mode=process
        python3 process.py --dataset=NUC_STATUS --mode=process
        python3 process.py --dataset=TOTAL --mode=process
        
    To Download and process the data together, run the below command:
    ```bash
    python3 process.py --dataset=TOTAL
    python3 process.py --dataset=INTL
    python3 process.py --dataset=ELEC
    python3 process.py --dataset=COAL
    python3 process.py --dataset=NG
    python3 process.py --dataset=PET
    python3 process.py --dataset=SEDS
    python3 process.py --dataset=NUC_STATUS

    ```
