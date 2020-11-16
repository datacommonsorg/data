# Primary Census Abstract Data for Scheduled Castes (SC) (India & States/UTs - District Level) Overview


### Download URL
It's available at [censusindia.gov.in](http://censusindia.gov.in/2011census/SC-ST/pca_state_distt_sc.xls). You can pre-download the dataset and place it in the `data` folder, or you can download it from the URL in real-time. 

### Overview
The first 4 columns refer to the location for which the data is tabulated. The 5th column is called TRU; it stands for Total, Urban, or Rural. From Column 6 - 85, we have values tabulated. The column header is the variable. For example, the 6th column header is `No_HH_Head`, which has the values for `Number of Household Heads`. A list of all such variables and their definition can be found in the CSV  `india_census/common/primary_abstract_data_variables.csv`

 - State - Two-digit state code
 - District - Three-digit district code inside the specific state
 - Level - If the actual location is India (country), STATE, DISTRICT, SUB-DISTRICT, TOWN, VILLAGE or EB
 - Name - Official Name of the place
 - TRU - Stands for Total, Urban or Rural
 - 6-84 - Data value columns 

 #### Raw Data Snippet

| State |  District | Level  |  Name            | TRU    |  No_HH_Head | TOT_P     | .... |
| ----- | --------- | ------ | ---------------- | ------ | ----------- | --------- | ---- |
| 00    | 000       |  India |  India           |  Total |  41694863   | 201378372 |      |
| 00    | 000       |  India |  India           |  Rural |  31803775   | 153850848 |      |
| 00    | 000       |  India |  India           |  Urban |  9891088    |  47527524 |      |
| 01    | 000       |  State |  JAMMU & KASHMIR |  Total |  183020     | 924991    |      |
| 01    | 000       |  State |  JAMMU & KASHMIR |  Rural |  149536     | 751026    |      |
| ....  |


#### Cleaned Data
As part of the cleaning process, we remove the unwanted columns and then convert the columns into rows. Then add the `StatisticalVariable` column corresponding to census variable and TRU.

Cleaned data [IndiaCensus2011_Primary_Abstract_ScheduleCaste.csv](IndiaCensus2011_Primary_Abstract_ScheduleCaste.csv) will have the following columns.

- census_location_id - Census location id
- TRU - TRU
- columnName - census variable name
- StatisticalVariable - statistical variable
- Value - Value for the attribute
- Year - Census year

#### Cleaned Data Snippet

|census_location_id                     |TRU  |columnName|Value   |StatisticalVariable                |Year|
|---------------------------------------|-----|----------|--------|-----------------------------------|----|
|COI2011-00-000-00000-000000-0000-000000|Total|No_HH_Head|41694863|Count_Household_ScheduleCaste      |2011|
|COI2011-00-000-00000-000000-0000-000000|Rural|No_HH_Head|31803775|Count_Household_ScheduleCaste_Rural|2011|
|COI2011-00-000-00000-000000-0000-000000|Urban|No_HH_Head|9891088 |Count_Household_ScheduleCaste_Urban|2011|
|COI2011-01-000-00000-000000-0000-000000|Total|No_HH_Head|183020  |Count_Household_ScheduleCaste      |2011|
|COI2011-01-000-00000-000000-0000-000000|Rural|No_HH_Head|149536  |Count_Household_ScheduleCaste_Rural|2011|


#### MCFs and Template MCFs

- [IndiaCensus2011_Primary_Abstract_ScheduleCaste.mcf](IndiaCensus2011_Primary_Abstract_ScheduleCaste.mcf)
- [IndiaCensus2011_Primary_Abstract_ScheduleCaste.tmcf](IndiaCensus2011_Primary_Abstract_ScheduleCaste.tmcf)

### Import Procedure

The below script will generate; mcf, tmcf and csv files.

`python -m india_census.primary_census_abstract_scheduled_caste.preprocess`