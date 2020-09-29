# COVID-19 Cases Counts as reported by Ministry of Health and Family Welfare (MoHFW)


## About the Dataset

### Download URL
You can download the parsed [JSON file](https://github.com/datameet/covid19/blob/master/data/mohfw.json) and refer to [daily reports here](https://github.com/datameet/covid19/tree/master/downloads/mohfw-backup).



### Overview
[MoHFW](https://www.mohfw.gov.in/) publishes cumulative confirmed, cured, death due to COVID-19 counts, everyday. It's published for every State and Union Territory. Sometimes it's published more than once a day. It's scraped by the [DataMeet](https://github.com/datameet/covid19). It's available under Attribution 4.0 International (CC BY 4.0).


Each record is a JSON document

```
{
  "id": "2020-08-30T08:00:00.00+05:30|mh",
  "key": "2020-08-30T08:00:00.00+05:30|mh",
  "value": {
    "_id": "2020-08-30T08:00:00.00+05:30|mh",
    "_rev": "1-6471d8fcff410d90a7d5898c5d81b9c3",
    "state": "mh",
    "report_time": "2020-08-30T08:00:00.00+05:30",
    "cured": 554711,
    "death": 24103,
    "confirmed": 764281,
    "source": "mohfw",
    "type": "cases"
  }
}
```

### Notes
- Published by the central agency for each state and Union Territory
- MoHFW publishes a single number for "Cured/Discharged/Migrated"
- MoHFW sometimes publishes the "unassigned" numbers where the cases are not assigned to any state or UT. We are ignoring it.
- Sometimes reports are published more than once. Hence observationDate is DateTime

#### Cleaned Data
- [COVID19_cases_indian_states.csv](COVID19_cases_indian_states.csv).

#### Template MCFs
- [COVID19_cases_indian_states.tmcf](COVID19_cases_indian_states.tmcf).


#### Scripts
- [preprocess.py](preprocess.py): COVID-19 India cases count import script.


### Running Tests

```bash
python3 -m unittest preprocess_test
```


### Import Procedure

To import data, run the following command:

```
python3 preprocess.py
```