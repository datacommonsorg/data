# COVID-19 Medical Test Counts by ICMR


## About the Dataset

### Download URL
You can download the parsed [JSON file](https://github.com/datameet/covid19/blob/master/data/icmr_testing_status.json) and refer to [PDF reports here](https://github.com/datameet/covid19/tree/master/downloads/icmr-backup).



### Overview
[ICMR](https://www.icmr.gov.in/) publishes daily cumulative tests count. It's scraped by the [DataMeet](https://github.com/datameet/covid19). It's available under Attribution 4.0 International (CC BY 4.0).


Each record is a JSON document and there is one record per day.

```
{
  "id": "2020-08-16T09:00:00.00+05:30|tests",
  "key": "2020-08-16T09:00:00.00+05:30|tests",
  "value": {
    "_id": "2020-08-16T09:00:00.00+05:30|tests",
    "_rev": "1-7b4fee2c24987134a740f188fb5dec42",
    "report_time": "2020-08-16T09:00:00.00+05:30",
    "samples": 29309703,
    "individuals": null,
    "confirmed_positive": null,
    "source": "icmr",
    "type": "tests"
  }
}
```

### Notes
- Published by the central agency once per day at the country level

#### Cleaned Data
- [COVID19_tests_india.csv](COVID19_tests_india.csv).

#### Template MCFs
- [COVID19_tests_india.tmcf](COVID19_tests_india.tmcf).

#### Scripts
- [preprocess.py](preprocess.py): Medical tests count import script.


### Runnint Tests

```bash
python3 -m unittest preprocess_test
```

### Import Procedure

To import data, run the following command:

```
python3 preprocess.py
```