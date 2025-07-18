# US: National Center for Education Statistics
## Import Overview:
This dataset has Population Estimates for the National Center for Education Statistics in US for 
- Private School - 1997-2019
- School District - 2010-2023
- Public Schools - 2010-2023

## Source URL:
  https://nces.ed.gov/ccd/elsi/tableGenerator.aspx 

## Import Type:
   Using a Selenium script to download data.

## Source Data Availability: P1Y 
  
## Autorefresh Type: Semi-Autorefresh 
  - `/bin/python3 download.py --import_name={"PrivateSchool"(or)"District"(or)"PublicSchool"} --years_to_download= "{select the available years       mentioned under each school type}"`

   For Example:  `/bin/python3 download.py --import_name="PublicSchool" --years_to_download="2023"`.
    - The input_files folder containing all the files will be present in: 
    `scripts/us_nces/demographics/public_school/input_files`

 Note: Give one year at a time for District and Public Schools as there are large number of column values.
 
### upload the files manually to GCP bucket for processing using gsutil command.
    Ex private :
        gsutil cp -r /scripts/us_nces/demographics/private_school/input_files gs://unresolved_mcf/us_nces/demographics/private_school/semi_automation_input_files/
    Ex public :
        gsutil cp -r /scripts/us_nces/demographics/private_school/input_files gs://unresolved_mcf/us_nces/demographics/public_school/semi_automation_input_files/
    Ex district:
        gsutil cp -r /scripts/us_nces/demographics/school_district/input_files gs://unresolved_mcf/us_nces/demographics/school_district/semi_automation_input_files/

### Note:
    The manual part of this process is downloading and uploading the input files to the GCP bucket. Once uploaded, a processing script automatically handles and processes the data directly from the bucket.

### Script Execution Details
    public    :  python3 private_school/process.py
    private   :  python3 public_school/process.py
    district  :  python3 school_district/process.py


#### Cleaned Data
    import_name consists of the school name being used 
    - "private_school"
    - "school_district"
    - "public_school"

Cleaned data will be saved as a CSV file within the following paths.
- private_school -> [private_school/output_files/us_nces_demographics_private_school.csv]
- district_school -> [school_district/output_files/us_nces_demographics_district_school.csv]
- public_school -> [public_school/output_files/us_nces_demographics_public_school.csv]

The Columns for the csv files are as follows
- school_state_code 
- year
- sv_name
- observation
- scaling_factor
- unit

## The NCES import script operates as follows:
If it's the beginning of a new year:
-The script downloads the latest data using Selenium.
Otherwise:
-The script retrieves school IDs for Private, Public, and District schools from a local JSON file located at gs://unresolved_mcf/us_nces/demographics/school_id_list.json.

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

    1. `County Number`
    2. `School Name`
    3. `School ID - NCES Assigned`
    4. `Lowest Grade Offered`
    5. `Highest Grade Offered`
    6. `Phone Number`
    7. `ANSI/FIPS State Code`
    8. `Location Address 1`
    9. `Location City`
    10. `Location ZIP`
    11. `Magnet School`
    12. `Charter School`
    13. `School Type`
    14. `Title I School Status`
    15. `National School Lunch Program`
    16. `School Level (SY 2017-18 onward)`
    17. `State School ID`
    18. `State Agency ID`
    19. `State Abbr`
    20. `Agency Name`
    21. `Location ZIP4`
    22. `Agency ID - NCES Assigned`
    23. `School Level`
    24. `State Name`
        

### Download URL
The data in .csv formats are downloadable from https://nces.ed.gov/ccd/elsi/tableGenerator.aspx -> 	.


#### API Output
The attributes used for the import are as follows
| Attribute      					| Description                                               |
|-------------------------------------------------------|------------------------------------------------------------------------------------------------|
| time       					| The Year of the population estimates provided. 				|
| geo       					| The Area of the population estimates provided. 				|
| Race  		        		| The Number of Students categorised under race. 				|
| Gender                      	| The Number of Students categorised under Gender.              |
| School Grade  	        	| The Number of Students categorised under School Grade. 		|
| Full-Time Equivalent 			| The Count of Teachers Available.						        |

### Import Procedure

#### Downloading the input files using scripts.
    - There are 3 scripts created to download the input files.
    - fetch_ncid.py
    - download_config.py
    - download_file_details.py
    - download.py

    #### fetch_ncid.py script
     - The code is a Python function that retrieves National Center for Education Statistics (NCES) IDs for a given school and year. It automates interacting with a webpage using Selenium to select options and then extracts the corresponding IDs.

    ##### download_config.py script  
     - The download_config.py script has all the configurations required to download the file.
     - It has filter, download url, maximum tries etc. The values are same under all cases.

    ##### download_config.py script
     - The download_file_details.py script has values for "default column", "columns to be downloaded" and "key coulmns".
     - Every input file can only accommodate 60 columns. In Public Schools multiple input files will be downloaded. All these input files will have a common column called as "Key Column" which acts as primary key.
     - In the "Public columns to be downloaded" create a list of columns.
        -ex: PUBLIC_COLUMNS = ["State Name [Public School]", "State Abbr [Public School]", "School Name [Public School]"]
     - Steps to add columns to the list.
        - Under "Select Table Columns" 
        - select the "Information" tab 
        - expand the hit area "BasicInformation" 
        - right click on the desired column checkbox and choose inspect 
        - from the elements on the right hand side, check the number assigned to "value" and add confirm the column under that list which corresponds to value.

    ##### download.py script
     - The download.py script is the main script. It considers the import_name and year to be downloaded. It downloads, extracts and places the input csv in "input_files" folder under the desired school directory.

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

If there are Duplicate School IDs present in School Place, they will be saved inside the same output path as that of csv and tmcf file.
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

