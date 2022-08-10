# US Census PEP: National Population Count by Residential Status and Military Status

## About the Dataset
This dataset has Population Count Estimates for the United States from the year 1980 to 2022 on a monthly basis.

The population is categorized by residential status (resident,InArmedForcesOverseas), military status(Civilian,InArmedForces) and a combination of the same. 

### Download URL
The data in txt/xls/xlsx formats are downloadable from within https://www2.census.gov/programs-surveys/popest/tables. The actual URLs are listed in file_urls.json.

#### API Output
These are the attributes that we will use
| Attribute      					| Description                                                 				|
|-------------------------------------------------------|---------------------------------------------------------------------------------------|
| Year and Month   					| The Year and Month of the population estimates provided. 				|
| Resident Population   				| The total resident population in the US. 						|
| Resident Population Plus Armed Forces Overseas   	| Sum of the Resident Population and the Armed Forces Deployed Overseas in the US.  	|
| Civilian Population   				| Total Civilian Population in the US. 							|
| Civilian Noninstitutionalized Population   		| Part of Civilian Population that is noninstituitionalized in the US.  		|
| Household Population   				| Totol household population in the US. 						|


#### Cleaned Data
Cleaned data will be inside [Output/USA_Population_Count.csv] as a CSV file with the following columns.

- Date
- Location
- Count_Person_InUSArmedForcesOverseas
- Count_Person_USResident
- Count_Person_USResidentOrInUSArmedForcesOverseas
- Count_Person_Civilian
- Count_Person_Civilian_NonInstitutionalized
- Count_Person_ResidesInHouseholds


#### MCFs and Template MCFs
- [Output/USA_Population_Count.mcf]
- [Output/USA_Population_Count.tmcf]

### Running Tests

Run the test cases

```/bin/python3 scripts/us_census/pep/monthly_population_estimate/preprocess_test.py
```



### Import Procedure

The below script make a new folder named as input_data (if not already present) where the download.py script is present and will download the data into this folder.
`/bin/python3 scripts/us_census/pep/monthly_population_estimate/download.py`

The below script will generate csv and mcf files.
`/bin/python3 scripts/us_census/pep/monthly_population_estimate/preprocess.py`
