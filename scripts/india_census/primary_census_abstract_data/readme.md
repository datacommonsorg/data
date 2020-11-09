# Primary Census Abstract Data Tables (India, States/UTs - District Level) Overview


### Download URL
It's available at [censusindia.gov.in](http://censusindia.gov.in/pca/DDW_PCA0000_2011_Indiastatedist.xlsx). You can pre-download the dataset and place it in the `data` folder, or you can download it from the URL in real-time. 

### Overview

The first nine columns refer to the location for which the data is tabulated. The 9th column is called TRU; it stands for Total, Urban, or Rural. From Column 10-93, we have values tabulated. The column header is the census variable. For example, the 10th column header `No_HH`, which has the values for `Number of Households`. A list of all such variables and their definition can be found in the CSV  `india_census/common/primary_abstract_data_variables.csv`

 - State - Two digit state code
 - District - Three digit district code inside the specific state
 - Subdistt - Five digit sub-district code inside the specific state
 - Town/Village - Six digit town or village code
 - Ward - Four digit ward code
 - EB - Six digit Enumeration Block Number
 - Level - If the actual location is India (country), STATE, DISTRICT, SUB-DISTRICT, TOWN, VILLAGE or EB
 - Name - Official Name of the place
 - TRU - Stands for Total, Urban or Rural
 - 10-93 - Data value columns 


#### Raw Data Snippet

| State | District | Subdistt | Town/Village | Ward | EB     | Level | Name            | TRU   | No_HH     | TOT_P      | ... |
| ----- | -------- | -------- | ------------ | ---- | ------ | ----- | --------------- | ----- | --------- | ---------- | --- |
| 00    | 000      | 00000    | 000000       | 0000 | 000000 | India | India           | Total | 249501663 | 1210854977 | ... |
| 00    | 000      | 00000    | 000000       | 0000 | 000000 | India | India           | Rural | 168612897 | 833748852  | ... |
| 00    | 000      | 00000    | 000000       | 0000 | 000000 | India | India           | Urban | 80888766  | 377106125  | ... |
| 01    | 000      | 00000    | 000000       | 0000 | 000000 | STATE | JAMMU & KASHMIR | Total | 2119718   | 12541302   | ... |
| ....  |
| ....  |


#### Cleaned Data
As part of the cleaning process, we remove the unwanted columns and then convert the columns into rows. Then add the `StatisticalVariable` column corresponding to census variable and TRU.

Cleaned data [IndiaCensus2011_Primary_Abstract_Data.csv](IndiaCensus2011_Primary_Abstract_Data.csv) will have the following columns.

- census_location_id - Census location id
- TRU - TRU
- columnName - census variable name
- StatisticalVariable - statistical variable
- Value - Value for the attribute
- Year - Census year
- Region - dcid of the region

#### Cleaned Data Snippet

| census_location_id                      | TRU   | columnName | Value     | StatisticalVariable   | Year | Region                    |
| --------------------------------------- | ----- | ---------- | --------- | --------------------- | ---- | ------------------------- |
| COI2011-00-000-00000-000000-0000-000000 | Total | No_HH      | 249501663 | Count_Household       | 2011 | dcid:country/IND          |
| COI2011-00-000-00000-000000-0000-000000 | Rural | No_HH      | 168612897 | Count_Household_Rural | 2011 | dcid:country/IND          |
| COI2011-00-000-00000-000000-0000-000000 | Urban | No_HH      | 80888766  | Count_Household_Urban | 2011 | dcid:country/IND          |
| COI2011-01-000-00000-000000-0000-000000 | Total | No_HH      | 2119718   | Count_Household       | 2011 | dcid:wikidataId/Q66278313 |



#### MCFs and Template MCFs
- [IndiaCensus2011_Primary_Abstract_Data.mcf](IndiaCensus2011_Primary_Abstract_Data.mcf)
- [IndiaCensus2011_Primary_Abstract_Data.tmcf](IndiaCensus2011_Primary_Abstract_Data.tmcf)


### Import Procedure

Make sure to run scripts to get [DCIDs for Census Locations](./../) before you run the below script. The below script will generate; mcf, tmcf, and csv files.

`python -m india_census.primary_census_abstract_data.preprocess`