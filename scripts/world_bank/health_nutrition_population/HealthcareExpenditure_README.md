Importing World Bank Healthcare Expenditure Data into Data Commons
Author: aarushitiwari@

About the Dataset
The world bank HNP dataset contains information about population, nutrition and health statistics of all countries, updated annually from all countries and marked special regions 
The dataset from 1960 onwards is available online. For this import, the series selected are all population statistics – male and female, age 00 to 25.


Size
?

Format: Json (access is directly from browser)

Time period: Annual, from 1960

Granularity: Country level
Variables

Importing World Bank Healthcare Expenditure Data into Data Commons
Author: aarushitiwari@

About the Dataset

https://databank.worldbank.org/source/health-nutrition-and-population-statistics# 
The world bank HNP dataset contains information about population, nutrition and health statistics of all countries, updated annually from all countries and marked special regions 
The dataset from 1960 onwards is available online. This import focusses on expenditure on healthcare.


Size
?

Format
Json (access is directly from browser)

Time period
Annual, from 1960

Granularity
Country level
Variables






2







The data set can be downloaded from  with the following API:
An example of a series would be 'SH.SGR.CRSK.ZS', containing information about the % of people at risk of catastrophic expenditure on surgery.

SH.SGR.CRSK.ZS  :  Risk of catastrophic expenditure for surgical care (% of people at risk)
SH.UHC.NOP1.CG  :  Increase in poverty gap at $1.90 ($ 2011 PPP) poverty line due to out-of-pocket health care expenditure (USD)
SH.UHC.NOP1.TO  :  Number of people pushed below the $1.90 ($ 2011 PPP) poverty line by out-of-pocket health care expenditure
SH.UHC.NOP1.ZG  :  Increase in poverty gap at $1.90 ($ 2011 PPP) poverty line due to out-of-pocket health care expenditure (% of poverty line)
SH.UHC.NOP1.ZS  :  Proportion of population pushed below the $1.90 ($ 2011 PPP) poverty line by out-of-pocket health care expenditure (%)
SH.UHC.NOP2.CG  :  Increase in poverty gap at $3.20 ($ 2011 PPP) poverty line due to out-of-pocket health care expenditure (USD)
SH.UHC.NOP2.TO  :  Number of people pushed below the $3.20 ($ 2011 PPP) poverty line by out-of-pocket health care expenditure
SH.UHC.NOP2.ZG  :  Increase in poverty gap at $3.20 ($ 2011 PPP) poverty line due to out-of-pocket health care expenditure (% of poverty line)
SH.UHC.NOP2.ZS  :  Proportion of population pushed below the $3.20 ($ 2011 PPP) poverty line by out-of-pocket health care expenditure (%)
SH.UHC.OOPC.10.TO  :  Number of people spending more than 10% of household consumption or income on out-of-pocket health care expenditure
SH.UHC.OOPC.10.ZS  :  Proportion of population spending more than 10% of household consumption or income on out-of-pocket health care expenditure (%)
SH.UHC.OOPC.25.TO  :  Number of people spending more than 25% of household consumption or income on out-of-pocket health care expenditure
SH.UHC.OOPC.25.ZS  :  Proportion of population spending more than 25% of household consumption or income on out-of-pocket health care expenditure (%)


https://api.worldbank.org/v2/country/all/indicator/{series}?format=JSON&per_page=17000


Data downloaded from API using pandas.json_normalize then stored in a dataframe, using the country codes and series ID of the required series. Schema Design
StatisticalVariable

The StatVars mcf will be generated as part of the program. There are 33 StatVars for different ways of measuring relative and absolute expenditure on healthcare

## StatVar template 
Node: Count_Person_SpendingMoreThan10PercentOfIncomeOnHealthcare
name: Count_Person_SpendingMoreThan10PercentOfIncomeOnHealthcare
typeOf: dcs:StatisticalVariable
description: "Number of people spending more than 10% of household consumption or income on out-of-pocket health care expenditure"
populationType: dcs:Person
constraintProperties: dcs:expenditureType, dcs:activityType
measuredProperty: dcs:count
statType: dcs:measuredValue
expenditureType: OutOfPocketHealthCareExpenditure
expenditure: [10 - PercentOfIncome]
​​



## StatVar template 
dcid:OutOfPocketHealthCareExpenditure
dcs:expenditureType
typeOf: dcs:Property, dcs:expenditureType
domainIncludes: dcs:EconomicActivity
Name: dcs:expenditureType
rangeIncludes: dcs:ExpenditureTypeEnum
 
####
dcid: Amount_EconomicActivity_ExpenditureActivity_HealthcareExpenditure_person
typeOf: dcs:StatisticalVariable
activitySource: dcs:ExpenditureActivity
constraintProperties: dcs:remunerator, dcs:expenditureType, dcs:activitySource
 
description	: “The amount of personal expenditure on healthcare”
expenditureType: dcs:HealthcareExpenditure
measuredProperty:	dcs:amount
memberOf	:Economic Activity With Activity Source = Expenditure Activity, Expenditure Type = Education Expenditure, Remunerator = Government
name	: Amount of Expenditure Activity, Healthcare Expenditure, Government
populationType: dcs:EconomicActivity
remunerator	: dcs:Person
statType: dcs:measuredValue


StatVarObservation
The import process output will be a CSV with the following columns:

Country
Date
Statvar
statvarobservation










The following tMCF will be used with the csv output:

Node: E: WorldBankPopulation ->E0
typeOf: dcs:StatVarObservation
variableMeasured: C: WorldBankPopulation ->StatVar
observationAbout: C:WorldBankPopulation ->Country
observationDate: C:WorldBankPopulation->Year
value: C: WorldBankPopulation ->Population




License
https://datacatalog.worldbank.org/public-licenses 



The data set can be downloaded from  with the following API:
An example of series would be “'SH.SGR.CRSK.ZS', containing information about the % of people at risk of catastrophic expenditure on surgery.



https://api.worldbank.org/v2/country/all/indicator/{series}?format=JSON&per_page=17000


Data downloaded from API using pandas.json_normalize then stored in a dataframe, using the country codes and series ID of the required series. This particular import only contains the population and gender of people aged 0 to 25 of all countries of the world.
Schema Design
StatisticalVariable

The StatVars mcf will be generated as part of the program. There are 52 StatVars for different combinations of age and gender. They would be of the following types:

## StatVar template for energy value per country annual
Node: Count_Person_SpendingMoreThan10PercentOfIncomeOnHealthcare
name: Count_Person_SpendingMoreThan10PercentOfIncomeOnHealthcare
typeOf: dcs:StatisticalVariable
description: "Number of people spending more than 10% of household consumption or income on out-of-pocket health care expenditure"
populationType: dcs:Person
measuredProperty: dcs:count
statType: dcs:measuredValue









StatVarObservation
The import process output will be a CSV with the following columns:

Country
Date
Statvar
statvarobservation










The following tMCF will be used with the csv output:

Node: E: WorldBankPopulation ->E0
typeOf: dcs:StatVarObservation
variableMeasured: C: WorldBankPopulation ->StatVar
observationAbout: C:WorldBankPopulation ->Country
observationDate: C:WorldBankPopulation->Year
value: C: WorldBankPopulation ->Population




License
https://datacatalog.worldbank.org/public-licenses 


