
# Importing DeepSolar model results

This directory imports results from Stanford's [DeepSolar model](http://web.stanford.edu/group/deepsolar/home) - a deep learning framework that analyzes satellite imagery to identify the GPS locations and sizes of solar photovoltaic (PV) panels in the contiguous US. These scripts generate the following files:

`deepsolar.csv`  
`deepsolar.tmcf`

which include the following StatisticalVariables:
  
- `Count_SolarInstallation_Residential`  
- `Count_SolarInstallation_Commercial`  
- `Count_SolarInstallation_UtilityScale`  
- `Count_SolarThermalInstallation_NonUtility`  
- `Count_SolarInstallation`  
- `Mean_CoverageArea_SolarInstallation_Residential`  
- `Mean_CoverageArea_SolarInstallation_Commercial`  
- `Mean_CoverageArea_SolarInstallation_UtilityScale`  
- `Mean_CoverageArea_SolarThermalInstallation_NonUtility`

## Usage

A copy of the raw DeepSolar results must be located in the working directory. To generate `deepsolar.csv` and `deepsolar.tmcf` run the following:  

    python3 deepsolar.py

As of August, 2021 this includes solar installation data for 2017.

### Unit Tests

To run unit tests:

    python3 deepsolar_test.py

## Data Download
Check for data to download at http://web.stanford.edu/group/deepsolar/home or contact Stanford's Magic Lab (Prof. Arun Majumdar)
