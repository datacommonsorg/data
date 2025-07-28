# US EIA Open Data Import

## About the Dataset

### Download URL

Each dataset available as a Zip-file of JSONL content. See [here](https://www.eia.gov/opendata/bulkfiles.php) for more details.

### Data Exploration

To ease analysis of the datasets, see [`generate_jsonl_for_bq.py`](generate_jsonl_for_bq.py) for instructions to convert and import the data into BigQuery.

### EIA International Import (`--dataset=INTL`)

As part of the latest refresh, data quality for the EIA International import has been significantly enhanced. This includes unit standardization and the implementation of filtering mechanisms within `common.py` to resolve identified data discrepancies. A comprehensive explanation of these specific issues and their resolution is documented in the "EIA_combined_8_imports_doc_Data_Commons_Import" file, within the `EIA_International` tab.

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

The `process.py` script manages the download and processing of EIA datasets.

To perform only download:

```bash
python3 process.py --dataset=ELEC --mode=download

To perform only process:
(Running this command generates input files, CSV, MCF, TMCF, and SVG.MCF files.)

Bash

python3 process.py --dataset=ELEC --mode=process

To download and process the data together:

Bash

python3 process.py --dataset=ELEC

General Usage:

You can use the following general command, replacing the placeholders for other datasets and modes:

Bash

python3 process.py --dataset=<DATASET_NAME> --mode=<MODE>
Where:

<DATASET_NAME>: Replace this with the specific dataset you want.

Choose from: INTL, ELEC, COAL, PET, NG, SEDS, NUC_STATUS, or TOTAL.

<MODE>: This tells the script what action to perform.

--mode=download: Only downloads the raw data.

--mode=process: Only processes the data.

Skip --mode entirely: If you omit this parameter (as shown in the "Download and process together" example), the script will automatically download AND process the data for you.
