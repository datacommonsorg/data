# US Census PEP: National Population Count

## About the Dataset
This dataset has Annual Population Estimates from the year 1900 to 2021 for different geographic level such as National, State, County, and Cities.

The population is categorized by [Count_Person](https://datacommons.org/browser/Count_Person) StatVar in Datacommons.org

### Download URL
The data in txt/csv formats are downloadable from within https://www2.census.gov/programs-surveys/popest/tables and https://www2.census.gov/programs-surveys/popest/datasets. The actual URLs are listed in file_urls.txt.

#### API Output
These are the attributes that we will use
| Attribute      					| Description                                                 				|
|-------------------------------------------------------|---------------------------------------------------------------------------------------|
| Year and Month   					| The Year and Month of the population estimates provided. 				|
| Population Estimates  				| The total population estimates in the US/State/County/City.						|


#### Cleaned Data
Cleaned data will be inside [Output/USA_Annual_Population.csv] as a CSV file with the following columns.

- Year
- Location
- [Count_Person](https://datacommons.org/browser/Count_Person)


#### MCFs and Template MCFs
- [output_files/USA_Annual_Population.mcf]
- [output_files/USA_Annual_Population.tmcf]

### Running Tests

Run the test cases

`/bin/python3 -m unittest scripts/us_census/pep/annual_population_estimate/preprocess_test.py`

### Import Procedure

The below script will download the data, generate csv and mcf files.

`/usr/bin/python3 scripts/us_census/pep/annual_population_estimate/preprocess.py`

Execute the 'preprocess.py' script by using the following commands:

  - if you want to perform "download and process", run the below command:

        `python3 preprocess.py --mode=""`

  - if you want to perform "only process", run the below command:

        `python3 preprocess.py --mode="process"`
        
  - if you want to perform "only download", run the below command:

        `python3 preprocess.py --mode="download"`

### New Implentation:
- [Updated the script on October 29, 2024]
- Downloading input files is now integrated into preprocess.py, eliminating the need to run the separate download.sh script. 
- All source file URLs, including future URLs adhering to the same structure, are centrally managed in the input_url.json file.
- All input files required for processing should be stored within the designated "input_files" folder.


