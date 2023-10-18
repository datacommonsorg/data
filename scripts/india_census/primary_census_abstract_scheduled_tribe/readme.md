# Primary Census Abstract Data for Scheduled Tribes (SC) (India & States/UTs - District Level) Overview


### Download URL
It's available at [censusindia.gov.in](http://censusindia.gov.in/2011census/SC-ST/pca_state_distt_st.xls). You can pre-download the dataset and place it in the `data` folder, or you can download it from the URL in real-time. 

### Overview
The first 4 columns refer to the location for which the data is tabulated. The 5th column is called TRU; it stands for Total, Urban, or Rural. From Column 6 - 85, we have values tabulated. The column header is the variable. For example, the 6th column header is `No_HH_Head`, which has the values for `Number of Household Heads`. A list of all such variables and their definition can be found in the CSV  `india_census/common/primary_abstract_data_variables.csv`

 - State - Two-digit state code
 - District - Three-digit district code inside the specific state
 - Level - If the actual location is India (country), STATE, DISTRICT, SUB-DISTRICT, TOWN, VILLAGE or EB
 - Name - Official Name of the place
 - TRU - Stands for Total, Urban or Rural
 - 6-84 - Data value columns 

 #### Raw Data Snippet

|State|District|Level|Name |TRU  |No_HH_Head|   |
|-----|--------|-----|-----|-----|----------|---|
|00   |000     |India|India|Total|21511528  |   |
|00   |000     |India|India|Rural|19302332  |   |
|00   |000     |India|India|Urban|2209196   |   |
| ... |


#### Cleaned Data
As part of the cleaning process, we remove the unwanted columns and then convert the columns into rows. Then add the `StatisticalVariable` column corresponding to census variable and TRU.

Cleaned data [IndiaCensus2011_Primary_Abstract_ScheduleTribe.csv](IndiaCensus2011_Primary_Abstract_ScheduleTribe.csv) will have the following columns.

- census_location_id - indianCensusAreaCode2011
- TRU - TRU
- columnName - census variable name
- StatisticalVariable - statistical variable
- Value - Value for the attribute
- Year - Census year

#### Cleaned Data Snippet

|census_location_id|TRU|columnName|Value|StatisticalVariable|Year    |
|------------------|---|----------|-----|-------------------|--------|
|0                 |Total|No_HH_Head|21511528|Count_Household_ScheduledTribe|2011    |
|0                 |Rural|No_HH_Head|19302332|Count_Household_ScheduledTribe_Rural|2011    |
|0                 |Urban|No_HH_Head|2209196|Count_Household_ScheduledTribe_Urban|2011    |
|01                |Total|No_HH_Head|260401|Count_Household_ScheduledTribe|2011    |
|01                |Rural|No_HH_Head|245038|Count_Household_ScheduledTribe_Rural|2011    |
|01                |Urban|No_HH_Head|15363|Count_Household_ScheduledTribe_Urban|2011    |
|001               |Total|No_HH_Head|10498|Count_Household_ScheduledTribe|2011    |
|001               |Rural|No_HH_Head|10267|Count_Household_ScheduledTribe_Rural|2011    |
|001               |Urban|No_HH_Head|231  |Count_Household_ScheduledTribe_Urban|2011    |
|002               |Total|No_HH_Head|3240 |Count_Household_ScheduledTribe|2011    |

#### MCFs and Template MCFs

- [IndiaCensus2011_Primary_Abstract_ScheduledTribe.mcf](IndiaCensus2011_Primary_Abstract_ScheduledTribe.mcf)
- [IndiaCensus2011_Primary_Abstract_ScheduledTribe.tmcf](IndiaCensus2011_Primary_Abstract_ScheduledTribe.tmcf)

### Import Procedure

The below script will generate; mcf, tmcf and csv files.

`python -m india_census.primary_census_abstract_scheduled_tribe.preprocess`