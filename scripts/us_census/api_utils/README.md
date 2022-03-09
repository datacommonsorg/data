# US Census API Wrappers

## API Overview

[Official User Guide for better context](https://www.census.gov/content/dam/Census/data/developers/api-user-guide/api-guide.pdf)

The data available in the US Census is divided into various datasets based on the type of data. 

Each dataset could be either a timeseries or have data within it divided by year. 

Each dataset has a number of variables within it. Each variable representing a particular statistic. Many datasets in turn have a collection of such variables grouped together into groups(or tables). These can be collectively fetched in single call. NOTE: Some variables could not be part of any group and might need to be fetched individually.

[Basic configuration of datasets](https://api.census.gov/data.json) acts as entry point for building a map of available data in the API.

API key to access the data can be [requested](https://api.census.gov/data/key_signup.html) very easily.

## census_api_data_downloader.py

This file is the top level module needed to be called to download the actual data.

```
python census_api_data_downloader.py --dataset=acs/acs5/subject --table_id=S0101 --start_year=2012 --end_year=2015 --summary_levels=010,030,040,050,060,140,160,310,500,860,950,960,970 --output_path=~/us_census --api_key=<YOUR API Key>
```

To download data for all available summary levels:
```
python census_api_data_downloader.py --dataset=acs/acs5/subject --table_id=S0101 --start_year=2012 --end_year=2015 --all_summaries --output_path=~/us_census --api_key=<YOUR API Key>
```

## census_api_config_fetcher.py

This script fetches the configrations of the API including:

- Available datasets
- Available years
- Available groups
- Available geography categories
- Available non group variables

In order to fetch the configuration, following command could be run:
```
python census_api_config_fetcher.py --force_fetch_config
```

This would create a `config_files` folder and store the data there. NOTE: Prefetched version of config can be downloaded from GCS.

## census_api_helpers.py

This file contains functions to get list of available options and some geo config builder tools that would be used by `url_list_compiler.py`.

Get list of available datasets
```
python census_api_helpers.py --available_datasets
```

Get list of available years for a given dataset
```
python census_api_helpers.py --available_years --dataset=acs/acs5/subject
```

Get list of available groups for a given dataset
```
python census_api_helpers.py --available_groups --dataset=acs/acs5/subject
```

Get list of available available summary levels for a given dataset
```
python census_api_helpers.py --available_summary_levels --dataset=acs/acs5/subject
```

## url_list_compiler.py

Functions useful for creating list of all URL calls required to be made to download data for a given configuration.

NOTE: Output path will have subdirectories for dataset and groups created within it for download. 

```
python url_list_compiler.py --dataset=acs/acs5/subject --table_id=S0101 --start_year=2012 --end_year=2015 --summary_levels=010,030,040,050,060,140,160,310,500,860,950,960,970 --output_path=~/us_census --api_key=<YOUR API Key>
```

To download data for all available summary levels:
```
python url_list_compiler.py --dataset=acs/acs5/subject --table_id=S0101 --start_year=2012 --end_year=2015 --all_summaries --output_path=~/us_census --api_key=<YOUR API Key>
```

NOTE: In case the script hangs due to heacy URL list sync, it might be helpful to delete `download_status.json` file in the destination folder to speed up the process.


# Download Utilities

## download_utils.py

Basic functions to make parallel URL requests using `aiohttp` package.

The functions accept a list of dict objects with relevant information. Each dict can have following keys:

- `url` (mandatory) - The URL destination for request.
- `store_path` (mandatory) - The path to store the response.
- `force_fetch` (optional) - Boolean value to force request even if the response file exists.
- `method` (optional) - Request method to be used. **NOTE: Only `get` is currently supported.**
- `status` - Status of the request. Can take any value from `['pending', 'ok', 'fail', 'fail_http']`. Generated based on the response.
- `http_code` - String version of the HTTP response code.
- `data` - Payload for `POST` request. **NOTE: Not supported currently.**

The availble methods accept callback functions to:

- Attach API key information to the URL.
- Process and store the response. **NOTE: The response needs to be stored in the callback function. By default the response is NOT stored. Simplest callback function would parse to required format and store it to the destination path.**

### Example code

```
from download_utils import download_url_list, async_save_resp_json

url_list = [{
            'url': 'https://httpbin.org/get?a=1',
            'store_path': './tmp/1.json',
            'status': 'pending'
        }, {
            'url': 'https://httpbin.org/get?b=2',
            'store_path': './tmp/2.json'
        }, {
            'url': 'https://httpbin.org/status/204',
            'store_path': './tmp/3.json'
        }, {
            'url': 'https://httpbin.org/status/404',
            'store_path': './tmp/4.json',
            'status': 'pending'
        }]

        fail_ctr = download_url_list(url_list, None, '', async_save_resp_json, {})
```

## status_file_utils.py

Utility functions to manage and update status of the download URL list passed to `download_utils.py`. Function to sync 2 differnt URL lists is also provided.
