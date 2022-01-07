Importing World Bank Population Data into Data Commons
Author: aarushitiwari@

About the Dataset
The world bank HNP dataset contains information about population, nutrition and health statistics of all countries, updated annually from all countries and marked special regions 
The dataset from 1960 onwards is available online. For this import, the series selected are all population statistics – male and female, age 00 to 25.

Size: 5447kb
Format: Json (access is directly from browser)
Time period: Annual, from 1960
Granularity: Country level
Variables: 
Age: 26
Gender:2

Population
265 per age per gender

The data set can be downloaded from  with the following API:
An example of series would be “SP.POP.AG19.FE.IN” or “SP.POP.AG19.MA.IN”


https://api.worldbank.org/v2/country/{country}/indicator/{series}?format=JSON


Data downloaded from API using pandas.json_normalize then stored in a dataframe, using the country codes and series ID of the required series. This particular import only contains the population and gender of people aged 0 to 25 of all countries of the world.
Schema Design
StatisticalVariable

The StatVars mcf will be generated as part of the program. There are 52 StatVars for different combinations of age and gender. They would be of the following types:

## StatVar template for energy value per country annual
Node: Count_Persons_5Years_Female
typeOf: dcs:StatisticalVariable
description: "Age population, age 05, female, interpolated"
populationType: dcs:Person
measuredProperty: dcs:count
gender: dcs:Female
statType: dcs:measuredValue
age: [Years 5]
##age and gender will be replaced as needed

StatVarObservation
The import process output will be a CSV with the following columns:

Country
Year
Gender
Age
StatVar
Population

The following tMCF will be used with the csv output:

Node: E: WorldBankPopulation ->E0
typeOf: dcs:StatVarObservation
variableMeasured: C: WorldBankPopulation ->StatVar
observationAbout: C:WorldBankPopulation ->Country
observationDate: C:WorldBankPopulation->Year
value: C: WorldBankPopulation ->Population

License
https://datacatalog.worldbank.org/public-licenses 
