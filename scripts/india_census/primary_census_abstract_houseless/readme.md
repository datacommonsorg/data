# Primary Census Abstract Data for Houseless Population Overview


### Download URL
It's available at [censusindia.gov.in](https://censusindia.gov.in/2011-Documents/PCA_HL_2011_Release.xls). You can pre-download the dataset and place it in the `data` folder, or you can download it from the URL in real-time. 

### Overview
The first 4 columns refer to the location for which the data is tabulated. The 5th column is called TRU; it stands for Total, Urban, or Rural. From Column 6 - 85, we have values tabulated. The column header is the variable. For example, the 6th column header is `No_HH_Head,` which has the values for `Number of Household Heads`. A list of all such variables and their definition can be found in the CSV  `india_census/common/primary_abstract_data_variables.csv`

 - State - Two-digit state code
 - District - Three-digit district code inside the specific state
 - Level - If the actual location is India (country), STATE, DISTRICT, SUB-DISTRICT, TOWN, VILLAGE or EB
 - Name - Official Name of the place
 - TRU - Stands for Total, Urban or Rural
 - 6-84 - Data value columns 

 #### Raw Data Snippet

|State|District|Level   |Name           |TRU  |No_HH |TOT_HL_P|    |
|-----|--------|--------|---------------|-----|------|--------|----|
|00   |000     |India   |India          |Total|449787|1773040 |    | 
|00   |000     |India   |India          |Rural|192891|834692  |    |
|00   |000     |India   |India          |Urban|256896|938348  |    |
|01   |000     |STATE   |JAMMU & KASHMIR|Total|3064  |19047   |    |
|01   |000     |STATE   |JAMMU & KASHMIR|Rural|1441  |8199    |    |
|01   |000     |STATE   |JAMMU & KASHMIR|Urban|1623  |10848   |    |
|01   |001     |DISTRICT|Kupwara        |Total|75    |495     |    |
| ... |


#### Cleaned Data
As part of the cleaning process, we remove the unwanted columns and then convert the columns into rows. Then add the `StatisticalVariable` column corresponding to census variable and TRU.

Cleaned data [IndiaCensus2011_Primary_Abstract_Houseless.csv](IndiaCensus2011_Primary_Abstract_Houseless.csv) will have the following columns.

- census_location_id - Census location id
- TRU - TRU
- columnName - census variable name
- StatisticalVariable - statistical variable
- Value - Value for the attribute
- Year - Census year


#### Cleaned Data Snippet

|census_location_id                     |TRU  |columnName|Value |StatisticalVariable            |Year|
|---------------------------------------|-----|----------|------|-------------------------------|----|
|COI2011-00-000-00000-000000-0000-000000|Total|No_HH     |449787|Count_Household_Houseless      |2011|
|COI2011-00-000-00000-000000-0000-000000|Rural|No_HH     |192891|Count_Household_Houseless_Rural|2011|
|COI2011-00-000-00000-000000-0000-000000|Urban|No_HH     |256896|Count_Household_Houseless_Urban|2011|
|COI2011-01-000-00000-000000-0000-000000|Total|No_HH     |3064  |Count_Household_Houseless      |2011|
|COI2011-01-000-00000-000000-0000-000000|Rural|No_HH     |1441  |Count_Household_Houseless_Rural|2011|
|COI2011-01-000-00000-000000-0000-000000|Urban|No_HH     |1623  |Count_Household_Houseless_Urban|2011|


#### MCFs and Template MCFs

- [IndiaCensus2011_Primary_Abstract_Houseless.mcf](IndiaCensus2011_Primary_Abstract_Houseless.mcf)
- [IndiaCensus2011_Primary_Abstract_Houseless.tmcf](IndiaCensus2011_Primary_Abstract_Houseless.tmcf)

### Import Procedure

The below script will generate; mcf, tmcf, and csv files.

`python -m india_census.primary_census_abstract_houseless.preprocess`