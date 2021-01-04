# Religion PCA (India & States/UTs - District Level) Overview


### Download URL
It's available at [censusindia.gov.in](https://censusindia.gov.in/2011census/Religion_PCA.html). You can pre-download the dataset and place it in the `data` folder, or you can download it from the URL in real-time. 

### Overview
The first 4 columns refer to the location for which the data is tabulated. The 5th column is called TRU; it stands for Total, Urban, or Rural. 6th column is the name of the location.

The 7th column is `Religion`, for which the values are defined. The religion column has one of the following values.

- Total
- Hindu
- Muslim
- Christian
- Sikh
- Buddhist
- Jain
- Other religions and persuasions
- Religion not stated



From Column 8 - N, we have values tabulated. The column header is the variable. For example, the 6th column header is `TOT_P`, which has the values for `Total Population`. A list of all such variables and their definition can be found in the CSV  `india_census/common/primary_abstract_data_variables.csv`

 - State - Two-digit state code
 - District - Three-digit district code inside the specific state
 - Subdistt -
 - Town/Village
 - TRU - Stands for Total, Urban or Rural
 - Name - Official Name of the place
 - Religion - Religion for which data is defined
 - 8- N - Data value columns 

 #### Raw Data Snippet

| State | District | Subdistt | Town/Village | TRU   | Name  | Religion  | TOT_P      | TOT_M     | TOT_F     | P_06      | M_06     | F_06     | 
|-------|----------|----------|--------------|-------|-------|-----------|------------|-----------|-----------|-----------|----------|----------| 
| 00    | 000      | 00000    | 000000       | Total | INDIA | Total     | 1210854977 | 623270258 | 587584719 | 164515253 | 85752254 | 78762999 | 
| 00    | 000      | 00000    | 000000       | Total | INDIA | Hindu     | 966257353  | 498306968 | 467950385 | 127509717 | 66638103 | 60871614 | 
| 00    | 000      | 00000    | 000000       | Total | INDIA | Muslim    | 172245158  | 88273945  | 83971213  | 28299593  | 14564936 | 13734657 | 
| 00    | 000      | 00000    | 000000       | Total | INDIA | Christian | 27819588   | 13751031  | 14068557  | 3353497   | 1712933  | 1640564  | 


#### Cleaned Data
As part of the cleaning process, we remove the unwanted columns and then convert the columns into rows. Then add the `StatisticalVariable` column corresponding to census variable and TRU.

Cleaned data for India level data is in the CSV [IndiaCensus2011_Primary_Abstract_Religion.csv](IndiaCensus2011_Primary_Abstract_Religion.csv). It will have the following columns.

- census_location_id - indianCensusAreaCode2011
- TRU - TRU
- columnName - census variable name
- StatisticalVariable - statistical variable
- Value - Value for the attribute
- Year - Census year


Cleaned data for each state is in a separate CSV. They have the following name format.

`IndiaCensus2011_Primary_Abstract_Religion_<state_data_file.xlsx>.csv`

Each state has a file.



#### Cleaned Data Snippet

| census_location_id | TRU   | columnName | Value      | StatisticalVariable                                      | Year | 
|--------------------|-------|------------|------------|----------------------------------------------------------|------| 
| 0                  | Total | TOT_P      | 1210854977 | Count_Person_Religion_Total                              | 2011 | 
| 0                  | Total | TOT_P      | 966257353  | Count_Person_Religion_Hindu                              | 2011 | 
| 0                  | Total | TOT_P      | 172245158  | Count_Person_Religion_Muslim                             | 2011 | 
| 0                  | Urban | TOT_P      | 282163402  | Count_Person_Religion_Hindu_Urban                        | 2011 | 
| 0                  | Urban | TOT_P      | 68740419   | Count_Person_Religion_Muslim_Urban                       | 2011 | 
| 0                  | Urban | TOT_P      | 11162523   | Count_Person_Religion_Christian_Urban                    | 2011 | 
| 0                  | Urban | TOT_P      | 5902324    | Count_Person_Religion_Sikh_Urban                         | 2011 | 
| 0                  | Urban | TOT_P      | 3628123    | Count_Person_Religion_Buddhist_Urban                     | 2011 | 
| 0                  | Urban | TOT_P      | 3546944    | Count_Person_Religion_Jain_Urban                         | 2011 | 
| 0                  | Urban | TOT_P      | 738727     | Count_Person_Religion_OtherReligionsAndPersuasions_Urban | 2011 | 
| 0                  | Urban | TOT_P      | 1223663    | Count_Person_Religion_ReligionNotStated_Urban            | 2011 | 
| 01                 | Total | TOT_P      | 12541302   | Count_Person_Religion_Total                              | 2011 | 
| 01                 | Total | TOT_P      | 3566674    | Count_Person_Religion_Hindu                              | 2011 | 
| 0                  | Total | TOT_M      | 623270258  | Count_Person_Religion_Total_Male                         | 2011 | 
| 0                  | Total | TOT_M      | 498306968  | Count_Person_Religion_Hindu_Male                         | 2011 | 
| 0                  | Total | TOT_F      | 587584719  | Count_Person_Religion_Total_Female                       | 2011 | 
| 0                  | Total | TOT_F      | 467950385  | Count_Person_Religion_Hindu_Female                       | 2011 | 



#### MCFs and Template MCFs

- [IndiaCensus2011_Primary_Abstract_Religion.mcf](IndiaCensus2011_Primary_Abstract_Religion.mcf)
- [IndiaCensus2011_Primary_Abstract_Religion.tmcf](IndiaCensus2011_Primary_Abstract_Religion.tmcf)

### Import Procedure

The below script will generate; mcf, tmcf and csv files.

`python -m india_census.primary_religion_data.preprocess`

This will generate MCF, TMCF and Multiple cleaned data CSV files.