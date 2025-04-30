
# OpenAFRICA Data Downlaod script

**About OpenAFRICA:**

OpenAFRICA is a platform providing access to a diverse collection of open data from across the African continent. Our goal is to make this data easily discoverable and usable for research, development, civic engagement, and more. To ensure interoperability and consistency, the platform utilizes the SDMX (Statistical Data and Metadata eXchange) standard data format.

URL: "https://{COUNTRY_NAME}.opendataforafrica.org/api/1.0/sdmx" 


**Data Download:**

This is a commom script to data download from OpenAFRICA for all countries.

**Dependencies:**

Before running the scripts, ensure the following dependencies are installed:

1.  **Python Packages:** Install the required Python libraries listed in `requirements.txt` using pip:
    ```bash
    pip install -r import-automation/executor/requirements.txt
    ```
    This typically includes `xmltodict`.

2.  **jq:** Install the `jq` command-line JSON processor if it's not already installed on your system:
    ```bash
    sudo apt-get install jq
    ```

### Running the `download.sh` Script:

The `download.sh` script automates the download of XML data for specified African countries. It accepts the following parameters:

1.  `country_name` (mandatory): The name of the African country for which to download data (e.g., 'egypt', 'kenya').
2.  `dataset_ids` (optional): A comma-separated list of specific dataset IDs to download for the specified country (e.g., 'qdanpdb,sfulpbb'). If omitted, all available datasets for the country will be downloaded.
3.  `output_csv_path` (optional): The path to the directory where the final CSV files will be saved. If omitted, the default is a newly created `input_files` directory in the current working directory.

**Usage Examples:**

* Download all datasets for Egypt:
    ```bash
    bash download.sh 'egypt'
    ```

* Download specific datasets ('qdanpdb' and 'sfulpbb') for Kenya:
    ```bash
    bash download.sh 'kenya' 'qdanpdb,sfulpbb'
    ```

* Download specific datasets ('qdanpdb' and 'sfulpbb') for Côte d'Ivoire and save the CSV files to `/output_csv_path`:
    ```bash
    bash download.sh 'cotedivoire' 'qdanpdb,sfulpbb' '/output_csv_path'
    ```


