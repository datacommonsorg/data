# US Census SRH Import

## Overview

This import covers US Census Population estimate by SRH (Sex, Race and Hispanic / Origin).
Data is covered for 

    1990 - latest_data     County
    1980 - latest_data     State
    1980 - latest_data     National

"latest_data" refers to the most recent population estimates for counties, states, and the nation based on the US Census Bureau's ACS Redistricting Data Summary Files.
The provided URL points you to the source for downloading relevant data files "https://www2.census.gov/programs-surveys/popest/datasets/".


Properties Covered - 

GenderType
- Male
- Female

Race
- WhiteAlone
- BlackOrAfricanAmericanAlone
- AmericanIndianOrAlaskaNativeAlone
- AsianOrPacificIslander
- AsianAlone
- NativeHawaiianOrOtherPacificIslanderAlone
- TwoOrMoreRaces
- WhiteAloneOrInCombinationWithOneOrMoreOtherRaces
- BlackOrAfricanAmericanAloneOrInCombinationWithOneOrMoreOtherRaces
- AmericanIndianAndAlaskaNativeAloneOrInCombinationWithOneOrMoreOtherRaces
- AsianAloneOrInCombinationWithOneOrMoreOtherRaces
- NativeHawaiianAndOtherPacificIslanderAloneOrInCombinationWithOneOrMoreOtherRaces

Origin
- Hispanic
- Not Hispanic



## Scripts
```
process.py
```
Above scipt creates necessary folders required for processing files and download's US 
Census PEP files to folder input_files. And reads downloaded files from input_files folder, prepares consolidated 
(National, State, County) output files for as-is (population_estimate_by_srh.csv) and aggregated (population_estimate_by_srh_agg.csv) in output_files folder

### Additional Notes

We have modified the script for Automation setup, now it's not required to add the future URL's in input_url.jason file. Code will take care of future URL formation automatically.

### Import Procedure

The below command will run process.py and generate output csv, mcf and tmcf. 
`python3 script/us_census/pep/pep_by_srh/process.py`

Execute the 'process.py' script by using the following commands:

  - if you want to perform "download and process", run the below command:

        `python3 process.py`

  - if you want to perform "only process", run the below command:

        `python3 process.py --mode=process`
        
  - if you want to perform "only download", run the below command:

        `python3 process.py --mode=download`
    
```
generate_mcf.py
generate_tmcf.py
```
Generates mcf and tmcf files for both 'as-is' data processing and 'aggregated' data processing

### New Implentation:
- [Updated the script on October 30, 2024]
- Downloading input files is now integrated into process.py, eliminating the need to run the separate download.sh script. 
- All source file URLs, including future URLs adhering to the same structure, are centrally managed in the input_url.json file.
- All input files required for processing should be stored within the designated "input_files" folder.
