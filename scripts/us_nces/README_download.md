# Downloading input files for US: National Center for Education Statistics

## Dataset Source
- The dataset is extracted from source: https://nces.ed.gov/ccd/elsi/tableGenerator.aspx

### Process to download the input files

  ####  Downloading the input files manually.
  - Select the following from each drop down
    - Select A Table Row -> Select the type of School to download ("Private" or "District" or "Public")
    - Select Years -> Select the available years
    - Select Table Columns -> The school properties are catogerised into different tabs. Select the required           properties under each tab.
    - Select Filter -> Select "All 50 States + DC"
    - Click on "Create Table" and it shows all the columns selected.
    - Click om the "CSV" button and download the file.
    - A zip file will be downloaded which has to be extracted.

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

    
### Command to Download input file
  - `/bin/python3 scripts/us_nces/demographics/download.py --import_name={"PrivateSchool"(or)"District"(or)"PublicSchool"} --years_to_download= "{select the available years mentioned under each school type}"`

    For Example:  `/bin/python3 scripts/us_nces/demographics/download.py --import_name="PublicSchool" --years_to_download="2023"`.
    - The input_files folder containing all the files will be present in: 
    `scripts/us_nces/demographics/public_school/input_files`
 - Note: Give one year at a time for District and Public Schools as there are large number of column values.
     