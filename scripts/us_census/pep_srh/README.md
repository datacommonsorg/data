# US Census SRH Import

## Overview

This import covers US Census Population estimate by SRH (Sex, Race and Hispanic / Origin).
Data is covered for 

    1990 - 2020     County
    1980 - 2020     State
    1980 - 2020     National

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
download.sh
```
Above scipt creates necessary folders required for processing files and download's US 
Census PEP files to folder download_files.


```
process.py
```
Reads downloaded files from download_files folder, prepares consolidated 
(National, State, County) output files for as-is (population_estimate_by_srh.csv) and aggregated (population_estimate_by_srh_agg.csv) in output_files folder


```
generate_mcf.py
generate_tmcf.py
```
Generates mcf and tmcf files for both 'as-is' data processing and 'aggregated' data processing
