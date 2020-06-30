# Importing Italy Department of Civil Protection Covid-19 Data into Data Commons

This directory contains artifacts required for importing Italy Department of Civil Protection Covid-19 data into Data Commons, along with scripts used to generate these artifacts.

## Artifacts:
### Cleaned CSV files:
- [dpc-covid19-ita-national-trend.csv](dpc-covid19-ita-national-trend.csv): national trend data
- [dpc-covid19-ita-regional.csv](dpc-covid19-ita-regional.csv): data at regions level
- [dpc-covid19-ita-province.csv](dpc-covid19-ita-province.csv): cumulative positive cases at province level

### Template MCFs:
- [dpc-covid19-ita-national-trend.tmcf](dpc-covid19-ita-national-trend.tmcf): national level
- [dpc-covid19-ita-regional.tmcf](dpc-covid19-ita-regional.tmcf): regions level
- [dpc-covid19-ita-province.tmcf](dpc-covid19-ita-province.tmcf): provinces level

### MCF of statistical variable:
- [dpc-covid19-ita_StatisticalVariable.mcf](dpc-covid19-ita_StatisticalVariable.mcf)

## Scripts:
- [preprocess.py](preprocess.py): generate the Cleaned CSV files and template MCFs
- [generate_statvar.py](generate_statvar.py): generate the mcf of statistical variables
- [test_template_mcf_names.py](test_template_mcf_names.py): 
    - test if the statistical variables in the template MCF can be found in the mcf of StatVars.
    - test if the columns specified in the template MCF can be found in the csv files.
    
## Note:
Starting from 2020/06/25, different sources of total positive cases are reported:
- positive cases from clinic activity  
- positive cases from surveys and tests 
These two variables haven't been imported into Data Commons yet.  

