# Sub-national Demographic data - Worldbank Population

## About the Dataset
This dataset has Population Estimates for the Sub-national Demographic data - Worldbank Population for Country and States from 2000 to 2016.  

The population has only one attribute Count of Person.

### Download URL
The data in .csv formats are downloadable from [source](https://databank.worldbank.org/source/subnational-population).


#### API Output
The attributes used for the import are as follows
| Attribute      					| Description                                                 				|
|-------------------------------------------------------|---------------------------------------------------------------------------------------|
| time       					| The Year of the population estimates provided. 				|
| geo       					| The Area of the population estimates provided. 				|



#### Cleaned Data
Cleaned data will be saved as a CSV file within the following paths.
- [scripts/world_bank/subnational_population/output_files/subnational.csv]

The Columns for the csv files are as follows
- observationDate
- observationAbout
- value 


#### MCFs and Template MCFs
-  [scripts/world_bank/subnational_population/output_files/subnational.mcf]
-  [scripts/world_bank/subnational_population/output_files/subnational.tmcf]


### Running Tests

Run the test cases

- `/bin/python3 scripts/world_bank/subnational_population/process_test.py`

### Import Procedure

The below script will download the data and extract it.
There is only one input file for this import and it is done manually.
In the above mentioned link slect the following give:
- Under 'Database' -> 'Subnational Population'
- Under 'Country' -> Check in the country name and there is check box to select all the places.
- Check the adjacent box as well to include all the places with respect to that country.
- Under 'Series' -> 'Population, total'
- Under 'Time' -> Select all the years available.

- After selecting the required data, there is a download drop down option to download the file as required. Select excel as an option(There might be some data loss if downloaded as csv). After downloading the input file as excel, convert the file into csv manually using google sheets to avoid unreadable characters.


The below script will clean the data, Also generate final csv, mcf and tmcf files.
- `/bin/python3 scripts/world_bank/subnational_population/process.py 2>&1 | tee subnational.log`
