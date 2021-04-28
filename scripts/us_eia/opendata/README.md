# US EIA Open Data Import

## About the Dataset

### Download URL

Each dataset available as a Zip-file of JSONL content. See [here](https://www.eia.gov/opendata/bulkfiles.php) for more details.

To download the latest versions of ALL datasets available, run the following command. Files will be downloaded and extracted to a tmp_raw_data folder.

```bash
python3 download_bulk.py
```

### Data Exploration

To ease analysis of the datasets, see [`generate_jsonl_for_bq.py`](generate_jsonl_for_bq.py) for instructions to convert and import the data into BigQuery.

### License

This dataset is available for public use, license is available at https://www.eia.gov/about/copyrights_reuse.php

### Import procedure

- Download data 
    ```bash
    python3 download_bulk.py
    ```

- Run the [processor](process/README.md)