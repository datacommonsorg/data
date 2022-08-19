# US Census PEP: Populations Estimates By Sex And Race

## About the Dataset
This dataset has Population Estimates By Sex And Race from the year 1900 to 2020 for different geographic level such as National, State and County.

The population is categorized by Sex and Race.

### Download URL
The data in txt/csv formats are downloadable from within "https://www2.census.gov/programs-surveys/popest/tables" and "https://www2.census.gov/programs-surveys/popest/datasets". The actual URLs are listed in 
individual .json files.


#### API Output
These are the attributes that we will use

| Attribute				| Description														|
|———————————————————————————————————————————-————————————————	|
| Year					| The Year of population estimates provided.						                               	|
| Sex					| Gender either Male or Female.											|
| Race					| Races off the population in the US.										|

#### Cleaned Data
Cleaned data will be inside four CSVs file with the following columns.

- Year
- geo_ID
- Count_Person_Male_WhiteAlone
- Count_Person_Male_BlackOrAfricanAmericanAlone
- Count_Person_Male_AsianAlone
- Count_Person_Male_AmericanIndianAndAlaskaNativeAlone
- Count_Person_Male_NativeHawaiianAndOtherPacificIslanderAlone
- Count_Person_Male_TwoOrMoreRaces
- Count_Person_Female_WhiteAlone
- Count_Person_Female_BlackOrAfricanAmericanAlone
- Count_Person_Female_AsianAlone
- Count_Person_Female_AmericanIndianAndAlaskaNativeAlone
- Count_Person_Female_NativeHawaiianAndOtherPacificIslanderAlone
- Count_Person_Female_TwoOrMoreRaces
- Count_Person_Male_AsianAndPacificIslander
- Count_Person_Female_AsianAndPacificIslander
- Count_Person_Male_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces
- Count_Person_Female_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces
- Count_Person_Male_AmericanIndianAndAlaskaNativeAloneOrInCombinationWithOneOrMoreOtherRaces
- Count_Person_Female_AmericanIndianAndAlaskaNativeAloneOrInCombinationWithOneOrMoreOtherRaces
- Count_Person_Male_AsianAloneOrInCombinationWithOneOrMoreOtherRaces
- Count_Person_Female_AsianAloneOrInCombinationWithOneOrMoreOtherRaces
- Count_Person_Male_BlackOrAfricanAmericanAloneOrInCombinationWithOneOrMoreOtherRaces
- Count_Person_Female_BlackOrAfricanAmericanAloneOrInCombinationWithOneOrMoreOtherRaces
- Count_Person_Male_NativeHawaiianAndOtherPacificIslanderAloneOrInCombinationWithOneOrMoreOtherRaces
- Count_Person_Male_NativeHawaiianAndOtherPacificIslanderAloneOrInCombinationWithOneOrMoreOtherRaces
- Count_Person_Male_NonWhite
- Count_Person_Female_NonWhite

#### MCFs and Template MCFs
These files contain data for national level before the year 2000.
- [national_before_2000.mcf]
- [national_before_2000.tmcf]

These files contain data for national level after the year 2000.
- [national_after_2000.mcf]
- [national_after_2000.tmcf]

These files contain data for state and county level before the year 2000.
- [state_county_before_2000.mcf]
- [state_county_before_2000.tmcf]

These files contain data for state and county level after the year 2000.
- [state_county_after_2000.mcf]
- [state_county_after_2000.tmcf]


### Running Tests
The below command will run preprocess_test.py `python3 -m unittest script/us_census/pep/population_estimate_by_sr/preprocess_test.py`

### Import Procedure
The below command will run preprocess.py and generate three output csv, mcf and tmcf.  `python3 script/us_census/pep/population_estimate_by_sr/preprocess.py`

### Additional Notes
This import has seperate .py script for different year ranges. They are as follow:

1. county_1970_1979.py 
- This script process as is data for county from year 1970 to 1979.

2. county_1980_1989.py 
- This script process as is data for county from year 1980 to 1989.

3. county_1990_2000.py 
- This script process as is data for county from year 1990 to 2000.

4. county_2000_2009.py 
- This script process as is data for county from year 2000 to 2009.

5. county_2010_2020.py 
- This script process as is data for county from year 2010 to 2020.

6. state_1970_1979.py 
- This script process as is data for state from year 1970 to 1979.

7. state_1980_1990.py 
- This script process as is data for state from year 1980 to 1990.

8. state_1990_2000.py 
- This script process as is data for state from year 1990 to 2000.

9. state_2000_2010.py 
- This script process as is data for state from year 2000 to 2010.

10. state_2010_2020.py 
- This script aggregates data from county level to state level from year 2010 to 2020.

11. national_1900_1970.py 
- This script process as is data for national from year 1900 to 1970.

12. national_1980_1990.py 
- This script aggregates data from state level to national level from year 1980 to 1990.

13. national_1990_2000.py 
- This script aggregates data from state level to national level from year 1990 to 2000.

14. national_2000_2010.py 
- This script process as is data for national from year 2000 to 2010.

15. national_2010_2020.py 
- This script aggregates data from state level to national level from year 2010 to 2020.

All these scripts are processed by running preprocess.py script.