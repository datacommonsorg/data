# UDISE Geography

## About the Dataset
UDISE states match the revenue states. UDISE has its district and block hierarchy. There is a unique udiseCode for each state, district, and block. 

### Download URL
Available for download using API.

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

#### MCF
- [UDISE_Places.mcf](UDISE_Places.mcf).

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
