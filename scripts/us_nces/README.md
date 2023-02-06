# US: National Center for Education Statistics

## About the Dataset
This dataset has Population Estimates for the National Center for Education Statistics in US for 
- Private School - 1997-2019
- School District - 2010-2020
- Public Schools - 2010-2020

The population is categorized on various attributes and their combinations:
        
        1. Count of Students categorised based on Race.
        2. Count of Students categorised based on School Grade from Pre Kindergarten to Grade 13.
        3. Count of Students categorised based on Pupil/Teacher Ratio.
        4. Count of Full-Time Equivalent (FTE) Teachers. 
        5. Count of Students with a combination of Race and School Grade. 
        6. Count of Students with a combination of Race and Gender.
        7. Count of Students with a combination of School Grade and Gender.
        8. Count of Students with a combination of Race, School Grade and Gender.
        9. Count of Students under Ungraded Classes, Ungraded Students and Adult Education Students.

The Place properties of Schools are given as below:
    (All the properties are available based on the type of School)

    1. School ID - NCES Assigned
    2. School Type
    3. Lowest Grade Offered
    4. Highest Grade Offered
    5. Phone Number
    6. ANSI/FIPS State Code
    7. Location City
    8. Location ZIP
    9. Location ZIP4
    10. School Level
    11. Agency ID - NCES Assigned
    12. State Agency ID
    13. National School Lunch Program
    14. Title I School Status
    13. State School ID
    14. Magnet School
    15. Charter School
    16. County Number
    17. County Name
        

### Download URL
The data in .csv formats are downloadable from https://nces.ed.gov/ccd/elsi/tableGenerator.aspx -> 	.


#### API Output
The attributes used for the import are as follows
| Attribute      					| Description                                                 				|
|-------------------------------------------------------|---------------------------------------------------------------------------------------|
| time       					| The Year of the population estimates provided. 				|
| geo       					| The Area of the population estimates provided. 				|
| Race  				| The Number of Students categorised under race. 						|
| Gender   	| The Number of Students categorised under Gender.  |
| School Grade  	        	| The Number of Students categorised under School Grade. 		|
| Full-Time Equivalent 				| The Count of Teachers Available.						|



#### Cleaned Data
import_name consists of the school name being used 
- "private_school"
- "district_school"
- "public_school"

Cleaned data will be saved as a CSV file within the following paths.
- private_school -> [private_school/output_files/us_nces_demographics_private_school.csv]
- district_school -> [school_district/output_files/us_nces_demographics_district_school.csv]
- public_school -> [public_school/output_files/us_nces_demographics_public_school.csv]

The Columns for the csv files are as 
- time
- geo
- SV
- Measurement_Method
- observation
- scaling_factor
- unit



#### MCFs and Template MCFs
- private_school -> [private_school/output_files/us_nces_demographics_private_school.mcf]
                    [private_school/output_files/us_nces_demographics_private_school.tmcf]


- district_school -> [school_district/output_files/us_nces_demographics_district_school.mcf],
                     [school_district/output_files/us_nces_demographics_district_school.tmcf]


- public_school ->  [public_school/output_files/us_nces_demographics_public_school.mcf],
                    [public_school/output_files/us_nces_demographics_public_school.tmcf]


#### Cleaned Place
"import_name" consists the type of school being executed. 
- "private_school"
- "district_school"
- "public_school"

Cleaned data will be inside as a CSV file with the following paths.
- private_school:
[private_school/output_place/us_nces_demographics_private_place.csv]
- district_school:
[school_district/output_place/us_nces_demographics_district_place.csv]
- public_school:
[public_school/output_place/us_nces_demographics_public_place.csv]

If there are Duplicate School IDs present in place, they would we inside the same output folder
- [scripts/us_nces/demographics/private_school/output_place/dulicate_id_us_nces_demographics_private_place.csv]
- [scripts/us_nces/demographics/school_district/output_place/dulicate_id_us_nces_demographics_district_place.csv]
- [scripts/us_nces/demographics/public_school/output_place/dulicate_id_us_nces_demographics_public_place.csv]


#### Template MCFs Place
- private_school:
[private_school/output_place/us_nces_demographics_private_place.tmcf]
- district_school:
[school_district/output_place/us_nces_demographics_district_place.tmcf]
- public_school:
[public_school/output_place/us_nces_demographics_public_place.tmcf]

### Running Tests

Run the test cases

- `/bin/python3 -m unittest scripts/us_nces/demographics/private_school/process_test.py`
- `/bin/python3 -m unittest scripts/us_nces/demographics/school_district/process_test.py`
- `/bin/python3 -m unittest scripts/us_nces/demographics/public_school/process_test.py`




### Import Procedure

The below script will download the data and extract it.

`/bin/python3 scripts/us_nces/demographics/download.py --import_name={"PrivateSchool"(or)"District"(or)"PublicSchool"} --years_to_download= "{select the available years mentioned under each school type}"`

- The input files would download under its respective year. Keep all one type of school input files under one folder named "input_files". Place the input_files under its respective import name folder.
- For example, after downlading input file for Private School, keep only the files in input_files folder and place it in `scripts/us_nces/demographics/private_school/`.

The below script will clean the data, Also generate final csv, mcf and tmcf files.
- for Private Schools:
`/bin/python3 scripts/us_nces/demographics/private_school/process.py`
- for School Districts:
`/bin/python3 scripts/us_nces/demographics/school_district/process.py`
- for Public Schools:
`/bin/python3 scripts/us_nces/demographics/public_school/process.py`
