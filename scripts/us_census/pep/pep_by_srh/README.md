# US Census SRH Import

## Overview

This import covers US Census Population estimate by SRH (Sex, Race and Hispanic / Origin).
Data is covered for 

    1990 - 2023     County
    1980 - 2023     State
    1980 - 2023     National

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

### Import Procedure
The below command will run process.py and generate output csv, mcf and tmcf. 
`python3 script/us_census/pep/pep_by_srh/process.py`


```
generate_mcf.py
generate_tmcf.py
```
Generates mcf and tmcf files for both 'as-is' data processing and 'aggregated' data processing

### Additional Notes

We have modified the script for Automation setup, now it's not required to add the future URL's in input_url.jason file. Code will take care of future URL formation automatically.


