# Unified District Information System for Education (UDISE) Geography

## About the Dataset
UDISE states match the revenue states. UDISE has its district and block hierarchy. There is a unique udiseCode for each state, district, and block. 

### Download URL
A backend API allows the master data to be queryable and responds with JSON data. The API endpoint is at
`http://pgi.seshagun.gov.in/BackEnd-master/api/report/getMasterData` to get the master data. The API takes JSON input with two attributes.

- extensionCall - Defines the master data type, one of GET_STATE, GET_DISTRICT or GET_BLOCK 
- condition - Filtering condition. An empty string will get everything.


#### Cleaned Data

- [UDISE_States.csv](UDISE_States.csv).
It has the following columns
1. state_name - the name of the state
2. udise_state_code - UDISE code of the state
3. isoCode - ISO Code of the state  

- [UDISE_Districts.csv](UDISE_Districts.csv).
It has the following columns
1. udise_state_code - UDISE state code
2. udise_district_code - UDISE district code
3. district_name - Name of the UDISE district


- [UDISE_Blocks.csv](UDISE_Blocks.csv).
It has the following columns
1. udise_dist_code - UDISE district code
2. udise_block_code - UDISE block code
3. block_name -  Name of UDISE Block 

#### Template MCFs
- [UDISE_States.tmcf](UDISE_States.tmcf).
- [UDISE_Districts.tmcf](UDISE_Districts.tmcf).
- [UDISE_Blocks.tmcf](UDISE_Blocks.tmcf).

#### Scripts
- [preprocess.py](preprocess.py): Clean up and import script.


### Running Tests

```bash
python3 -m unittest discover -v -s scripts/ -p *_test.py
```

### Import Procedure

The below script will generate csv files.

`python -m india_udise.udise_geography.preprocess`
