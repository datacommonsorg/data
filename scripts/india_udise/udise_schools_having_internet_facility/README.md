# UDISE+ - Number of Schools having Internet Facility by School Category and Management 

## About the Dataset
This dataset gives the number of schools that have Internet Facility. This dataset (Report Id:3106) has count of schools by school level and school management.

Data is available at State, District, and Block levels. Currently, we are importing State and District level data.

### Download URL
A backend API allows the data to be queryable and responds with JSON data. The API endpoint is at `https://dashboard.udiseplus.gov.in/BackEnd-master/api/report/getTabularData`. The API takes JSON input with two main attributes.

- dependencyValue - JSON value of query elements like year, state, dist, block
- mapid - 79 - ID for the report

#### API Output
These are the attributes that we will use
| Attribute       | Description                                                  |
|--------|--------------------------------------------------------------|
| cat1   | PS (I-V) - Primary only with grades 1 to 5                   |
| cat2   | UPS (I-VIII) - Upper Primary with grades 1 to 8               |
| cat3   |  HSS (I-XII) - HigherSecondary with grades 1 to 12           |
| cat4   | UPS (VI-VIII) - Upper Primary only with grades 6 to 8        |
| cat5   | HSS (VI-XII)    - Higher Secondary with grades 6 to 12       |
| cat6   | SS (I-X) - Secondary/Sr. Sec.with grades 1 to 10             |
| cat7   | SS (VI-X) - Secondary/Sr. Sec.with grades 6 to 10            |
| cat8   | SS (IX-X) - Secondary/Sr. Sec.only with grades 9 & 10        |
| cat10  | HSS (IX-XII) - Higher Secondary with grades 9 to 12          |
| cat11  | HSS (XI-XII) - Hr.Sec. /Jr. College only with grades 11 & 12 |
| total  | Total across all the school levels |
| sch_mgmt_name  | School Management Type |


#### Cleaned Data
Cleaned data will be inside [UDISEIndia_Schools_Having_Internet_Facility.zip](UDISEIndia_Schools_Having_Internet_Facility.zip) as a CSV file with the following columns.

- Period - Education year
- UDISECode  - UDISE Location Code
- LocationType  - State, District, Block
- StatisticalVariable - Name of the stat var
- Value - Actual value of the stat var

#### MCFs and Template MCFs
- [UDISEIndia_Schools_Having_Internet_Facility.mcf](UDISEIndia_Schools_Having_Internet_Facility.mcf)
- [UDISEIndia_Schools_Having_Internet_Facility.tmcf](UDISEIndia_Schools_Having_Internet_Facility.tmcf)

### Running Tests

Run all the test cases

```bash
python3 -m unittest discover -v -s scripts/ -p *_test.py
```

Run only the test cases related to this import

```bash
python3 -m unittest india_udise.udise_schools_having_internet_facility.preprocess_test.TestPreprocess
```

### Import Procedure

The below script will download the data
`python -m india_udise.udise_schools_having_internet_facility.preprocess download`

The below script will generate csv and mcf files.
`python -m india_udise.udise_schools_having_internet_facility.preprocess process`
