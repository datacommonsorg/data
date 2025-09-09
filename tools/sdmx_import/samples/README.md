# SDMX Utility Sample Scripts

This directory contains sample scripts demonstrating how to use the functions in the `tools.sdmx.dataflow` module to download data and metadata from different SDMX APIs.

## Scripts

### OECD

*   `fetch_oecd_gdp_metadata.py`: Downloads the complete metadata for the OECD's Quarterly GDP Growth dataset.
*   `fetch_oecd_gdp_data.py`: Fetches a specific slice of data from the same GDP dataset and saves it as a CSV.
*   `fetch_oecd_full_gdp_dataset.py`: A more complete example that combines both functions to download the metadata and then the full dataset.

### Eurostat

*   `fetch_eurostat_gdp_metadata.py`: Downloads the metadata for the annual GDP dataset from Eurostat.
*   `fetch_eurostat_gdp_data.py`: Downloads a slice of the annual GDP data for Germany, France, and Italy from Eurostat.

## Running the Samples

You can execute each script from the root of the repository, for example:

```bash
python3 tools/sdmx/samples/fetch_oecd_gdp_metadata.py
```

The scripts will download the requested data/metadata and save it as `.xml` or `.csv` files in the project's root directory.
