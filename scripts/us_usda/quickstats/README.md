The `process.py` script generates statvars based on the 
USDA agriculture survey (and census data very soon) data 
using the USDA quickstats [API][api].

## Source URL:
[api]: https://quickstats.nass.usda.gov/api/

## Historical and Latest Data
Historical Data: Covers the period from 2000 to 2023.
Latest Data: The 2024 & 2025 data will be updated annually.

## Source Data Availability: P1Y 

## Autorefresh Type: Fully-Autorefresh 

### Script Execution Details

### Automation Refresh: The process.py has a parameter 'mode' with values 'download' and 'process'

when the file 'process.py' is run with the flag --mode=download, it will  download and place it in the 'input/parts' & 'input/response' directory. i.e. python3 process.py --mode=download

when the file 'process.py' is ran with the flag --mode=process, it will process the downloaded files and place it in the 'output' directory. i.e. python3 process.py --mode=process

when the file 'process.py' is ran without any flag, it will download and process the files and keep it in the respective directories as mentioned above. i.e. python3 process.py

The output will be `output/ag-2023.csv`.

To run unit tests:
    python3 process_test.py

The latest StatisticalVariable mappings are in `sv.csv`. The CSV fields are as follows: 

* `name`: The "Data Item" in the USDA/NASS QuickStats tool 
* `sv`: The corresponding StatisticalVariable dcid
* `unit`: The unit dcid, if it exists 

TODO: Add additional mappings for other StatisticalVariables.

