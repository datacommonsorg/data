# COVID-19 Cases Counts as reported by Ministry of Health and Family Welfare (MoHFW)


## About the Dataset

### Download URL
You can download the raw csv with district-wise daily case counts data for India from [covid19india api](https://api.covid19india.org/csv/latest/districts.csv)



### Overview
[MoHFW](https://www.mohfw.gov.in/) publishes daily confirmed, cured, death due to COVID-19 counts, everyday. It's published for every district in India. This code scrapes the data from [covid19india](https://covid19india.org), which compiles the data from MoHFW and provides it through an API.


#### Cleaned Data
- [COVID19_cases_indian_districts.csv](COVID19_cases_indian_districts.csv).

#### Template MCFs
- [COVID19_cases_indian_districts.tmcf](COVID19_cases_indian_districts.tmcf).


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