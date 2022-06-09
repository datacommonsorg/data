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
Cleaned data will be inside [Output/postprocess.csv] as a CSV file with the following columns.

- Year
- geo_ID
- Count_Person_Male
- Count_Person_Female
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
These files are genrated for the datasets which are processed as is.
- [preprocess/Sex_Race.mcf]
- [preprocess/Sex_Race.tmcf]

These files are genrated for the datasets which are having aggregated Statvar Count_Person_Male and Count_Person_Female.
- [preprocess/Sex_Race_aggregate.mcf]
- [preprocess/Sex_Race_aggregate.tmcf]

These files are genrated for the datasets which are aggregated from different geo granularity.
- [preprocess/Sex_Race_aggregate_state_2010_2020.mcf]
- [preprocess/Sex_Race_aggregate_state_20102_2020.tmcf]


### Running Tests
The below command will run preprocess_test.py `python3 -m unittest script/us_census/pep/population_estimate_by_sr/preprocess_test.py`

### Import Procedure
The below command will run preprocess.py and generate three output csv, mcf and tmcf.  `python script/us_census/pep/population_estimate_by_sr/preprocess.py`
