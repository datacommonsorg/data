# UDISE - School Dropout Rate: By Gender, Level of School Education and Social Category

## About the Dataset
The “dropout rate” is the percentage of students in a particular set who are no longer enrolled. This dataset (Report Id:4014) has dropout rates by Gender, Social Category at various school levels.


### Download URL
A backend API allows the data to be queryable and responds with JSON data. The API endpoint is at
`http://pgi.seshagun.gov.in/BackEnd-master/api/report/getTabularData`. The API takes JSON input with two main attributes.

- dependencyValue - JSON value of query elements like year, state, dist, block
- mapid - 117 - ID for the report

#### API Output
These are the attributes that we will use

- rpt_type = One of "S", "D", "B"
- location_code = Actual UDISE location code
- location_name = Actual UDISE location name
- item_name = One of "General", "SC", "ST", "OBC", "Overall"
- pri_girl_c1_c5_dropout_rate
- pri_boy_c1_c5_dropout_rate
- pri_c1_c5_dropout_rate
- secondary_girl_c9_c10_dropout_rate
- secondary_boy_c9_c10_dropout_rate
- secondary_c9_c10_dropout_rate
- upper_pri_c6_c8_dropout_rate
- upper_pri_boy_c6_c8_dropout_rate
- upper_pri_girl_c6_c8_dropout_rate

#### Cleaned Data
Cleaned data will be inside [UDISEIndia_School_Dropout_Rate.zip](UDISEIndia_School_Dropout_Rate.zip) as a CSV file with the following columns.

- Period - Education year
- LocationCode  - UDISE Location Code
- LocationType  - State, District, Block
- SocialCategory - GeneralCategory, ScheduledCaste, ScheduledTribe, OtherBackwardClass
- Gender - Male, Female
- SchoolLevel - PrimarySchool, MiddleSchool, SecondarySchool
- ColumnName - Column name from which the value comes from
- StatisticalVariable - Name of the stat var
- Value - Actual value of the stat var

#### MCFs and Template MCFs
- [UDISEIndia_School_Dropout_Rate.mcf](UDISEIndia_School_Dropout_Rate.mcf)
- [UDISEIndia_School_Dropout_Rate.tmcf](UDISEIndia_School_Dropout_Rate.tmcf)

#### Scripts
- [preprocess.py](preprocess.py): Download and process data script.


### Running Tests

```bash
python3 -m unittest discover -v -s scripts/ -p *_test.py
```

### Import Procedure

The below script will download the data
`python -m india_udise.udise_school_dropout_rate.preprocess download`

The below script will generate csv and mcf files.
`python -m india_udise.udise_school_dropout_rate.preprocess process`
