The `process.py` script generates statvars based on the 
USDA agriculture survey (and census data very soon) data 
using the USDA quickstats [API][api].

[api]: https://quickstats.nass.usda.gov/api/

To generate CSV:
```
python3 process.py
```

The output will be `output/ag-2023.csv`.

The latest StatisticalVariable mappings are in `sv.csv`. The CSV fields are as follows: 

* `name`: The "Data Item" in the USDA/NASS QuickStats tool 
* `sv`: The corresponding StatisticalVariable dcid
* `unit`: The unit dcid, if it exists 

TODO: Add additional mappings for other StatisticalVariables.

touching this file