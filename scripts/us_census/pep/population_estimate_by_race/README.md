# US Census PEP: Population Estimate by Race

## About the Dataset
This import includes the Population Count Estimates by Race for the United States from the year 1900 to 2020 on a yearly basis.

The population is categorized by Race:
AmericanIndianAndAlaskaNativeAlone,AsianAlone,BlackOrAfricanAmericanAlone,WhiteAlone,NativeHawaiianAndOtherPacificIslanderAlone
 

### Download URL
The data in txt/csv formats are downloadable from within "https://www2.census.gov/programs-surveys/popest/tables" and "https://www2.census.gov/programs-surveys/popest/datasets". The actual URLs are listed in file_urls.json and file_url.txt(County data from 2020).

#### API Output
These are the attributes that we will use
| Attribute      					| Description                                                 				|
|-------------------------------------------------------|---------------------------------------------------------------------------------------|
| Geographic Area  					| The Year and Month ofpopulation estimates provided. 					|
| Total  				          	| The total estimate  population by race in the US. 					|
| white                                       		| The Total EstimatIon of Population by White alone  in the US				|
| Black Or African American    				| Total Estimation of Population by Black Or African American  in the US. 		|
| American Indian and Alaska Native  		   	| Total Population Estimate by American Indian And Alaska Native in the US.  		|
| Asian                         			| Totol population estimation by Asian Alone in the US. 		        	|
| Native Hawailan and Other Pacific Islander    	| Total Population Estimation by Native Hawailan and Other Pacific Islander		|
| Two or More Races                             	| Population Estimation By Two or More Races						|
#### Cleaned Data
Cleaned data will be inside [Output/USA_Population_Count_by_Race.csv] as a CSV file with the following columns.

- Year
- geo_ID
- Count_Person_USAllRaces
- Count_Person_WhiteAlone
- Count_Person_BlackOrAfricanAmericanAlone
- Count_Person_AmericanIndianOrAlaskaNativeAlone
- Count_Person_AsianAlone
- Count_Person_NativeHawaiianAndOtherPacificIslanderAlone
- Count_Person_White
- Count_Person_Black
- Count_Person_AsianOrPacificIslander
- Count_Person_AmericanIndianOrAlaskaNative
- Count_Person_TwoOrMoreRace
- Count_Person_NonWhite

#### MCFs and Template MCFs
- [Output/USA_Population_Count_by_Race.mcf]
- [Output/USA_Population_Count_by_Race.tmcf]

### Running Tests

Run the test cases

```/bin/python3 scripts/us_census/pep/population_estimate_by_race/preprocess_test.py```

### Import Procedure

The below scripts will download the data
`/bin/python3 scripts/us_census/pep/population_estimate_by_race/download.py`
`sh scripts/us_census/pep/population_estimate_by_race/download1.sh`

The below script will generate csv and mcf files.
`/bin/python3 scripts/us_census/pep/population_estimate_by_race/preprocess.py`
