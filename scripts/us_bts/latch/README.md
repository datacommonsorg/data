# US Latch: Transportation Statictics for Household

## About the Dataset
This dataset has US Tract Transportation Statistics for Household for years 2009,2017.

The population is categorized by various set of combinations as below:
        
        1. PersonMiles, PersonTrips, VehicleMiles, VehicleTrips
        2. PersonMiles with Houshold combination
        3. PersonTrips with Houshold combination
        4. VehicleMiles with Houshold combination
        5. VehicleTrips with Houshold combination

### Download URL
The data in csv, zip formats are downloadable from https://www.bts.dot.gov/latch/latch-data -> 	By Census Tract (CSV) for 2017 year, By Census Tract (CSV) for 2009 year.

The actual URLs are listed in download_input_files.py.


#### API Output
These are the attributes that we will use
| Attribute      					| Description                                                 				|
|-------------------------------------------------------|---------------------------------------------------------------------------------------|
| geo code, geoid      					| The Area of the population estimates provided. 				|
| est_pmiles2007_11, est_pmiles                         | Miles traveled by a Person.
| est_ptrp2007_11, est_ptrp   	| Trips made by a Person.  |
| est_vmiles2007_11, est_vmiles 				| Miles traveled by a Vehicle.					|
| est_vtrp2007_11, est_vtrp 				| Trips made by a Vehicle. 							|
| pmiles_(p)mem_(v)veh   				|  Miles traveled by a 'p' Persons in 'v' Vehicles.					|
| ptrp_(p)mem_(v)veh   				|  Trips made by a 'p' Persons in 'v' Vehicles.					|
| vmiles_(p)mem_(v)veh   				|  Miles traveled in 'v' Vehicles of 'p' Persons.							|
| vtrp_(p)mem_(v)veh   				|  Trips made in 'v' Vehicles of 'p' Persons.				|



#### Cleaned Data
Cleaned data will be inside [output_files/us_transportation_household.csv] as a CSV file with the following columns.

- year
- location
- sv
- measurement_method
- observation



#### MCFs and Template MCFs
- [output_files/us_transportation_household.mcf]
- [output_files/us_transportation_household.tmcf]

### Running Tests

Run the test cases

`sh run_tests.sh -p /scripts/us_bts/latch`




### Import Procedure

The below script will download the data and saves to local folder **input_files**.

`python3 scripts/us_bts/latch/download_input_files.py`

The below script will clean the data, Also generate final csv, mcf and tmcf files.

`python3 sscripts/us_bts/latch/process.py`