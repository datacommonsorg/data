# US Census PEP: National Population Count by Residential Status and Military Status

## About the Dataset
This dataset has Population Count Estimates for the United States from the year 1980 on a monthly basis till latest year.

The population is categorized by residential status (resident,InArmedForcesOverseas), military status(Civilian,InArmedForces) and a combination of the same. 

### Download URL
The data in txt/xls/xlsx formats are downloadable from within https://www2.census.gov/programs-surveys/popest/tables. The actual URLs are listed in input_url.json.

#### API Output
These are the attributes that we will use
| Attribute      					| Description                                                 				|
|-------------------------------------------------------|---------------------------------------------------------------------------------------|
| Year and Month   					| The Year and Month of the population estimates provided. 				|
| Resident Population   				| The total resident population in the US. 						|
| Resident Population Plus Armed Forces Overseas   	| Sum of the Resident Population and the Armed Forces Deployed Overseas in the US.  	|
| Civilian Population   				| Total Civilian Population in the US. 							|
| Civilian Noninstitutionalized Population   		| Part of Civilian Population that is noninstituitionalized in the US.  		|
| Household Population   				| Totol household population in the US. 						|


#### Cleaned Data
Cleaned data will be inside [Output/USA_Population_Count.csv] as a CSV file with the following columns.

- Date
- Location
- Count_Person_InUSArmedForcesOverseas
- Count_Person_USResident
- Count_Person_USResidentOrInUSArmedForcesOverseas
- Count_Person_Civilian
- Count_Person_Civilian_NonInstitutionalized
- Count_Person_ResidesInHouseholds


#### MCFs and Template MCFs
- [Output/USA_Population_Count.mcf]
- [Output/USA_Population_Count.tmcf]

### Running Tests

Run the test cases

```/bin/python3 scripts/us_census/pep/monthly_population_estimate/preprocess_test.py
```

### Import Procedure

[Updated the script on November 11, 2024]
Downloading input files is now integrated into preprocess.py, eliminating the need to run the separate download.sh script. 
All source file URLs, including future URLs adhering to the same structure, are centrally managed in the input_url.json file.
All input files required for processing should be stored within the designated "input_files" folder.

### Downloading and Processing Data

To perform "download and process", run the below command:
    python3 preprocess.py 
Running this command generates input_fles and csv, mcf, tmcf files

If you want to perform "only process", run the below command:
    python3 preprocess.py --mode=process
        
If you want to perform "only download", run the below command:
    python3 preprocess.py --mode=download
    

Note: 11-Feb-2025:
1. Code fix done the remove overlapping values from different files for year 2010 & 2020
2. dropping junk value rows from files for year < 2000.
3. Future years (e.g., 2030) should also be checked for overlapping data. Update the script accordingly.