
# Importing Italy Department of Civil Protection Covid-19 Data Into Data Commons

Author: qlj-lijuan

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [Import Artifacts](#import-artifacts)
1. [Generating Artifacts](#generating-artifacts)

## About the Dataset

### Download URL

CSV files are available for download from https://github.com/pcm-dpc/COVID-19. 

### Overview
  This dataset contains daily updated information on Covid-19 in Italy from the Head of Department of Civil Protection starting from 2020/02/24. 
  
  The dataset is broken up into three Geo levels: 
  1. National level
  2. Regions level
  3. Provinces level

  The naional level and regions level datasets are  broken into 12 statistical variables.
  
   1. Hospitalized with symptoms: hospitalized positive cases with symptoms
   2. Intensive care: hospitalized positive cases in intensive case
   3. Hospitalized: hospitalized positive cases
   4. People in home isolation: positive cases in home isolation
   5. Active case: currently positive cases
   6. Incremental active case: change in active cases, i.e. (active cases today - active cases of previous day)
   7. Recovered: cumulative recovered cases
   8. Death: cumulative death
   9. Positive case: cumulative positive cases
  10. Incremental positive case: new postive cases, i.e. (total positive cases today - total positive cases of previous day)
  11. Tests performed: total number of tests performed
  12. Tested people: total number of people tested

The province level dataset reports:
1. Positive case: cumulative positive cases


### Notes and Caveats

- This dataset contains occasional decrease in cumulative counts due to recalculation of cases across different locations.

### License

This dataset is under Creative Commons Attribution 4.0 International License ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)). It grants users the right to copy and redistribute the material in any medium or format; remix, transform, and build upon the material for any purpose, even commercially.

The license is available online at https://github.com/pcm-dpc/COVID-19/blob/master/LICENSE.

### Dataset Documentation and Relevant Links 

- Documentation: [COVID-19 Italy performance data](https://github.com/pcm-dpc/COVID-19/blob/master/dati-andamento-covid19-italia.md)
- Data Visualization UI: [interactive geographical dashboard](http://opendatadpc.maps.arcgis.com/apps/opsdashboard/index.html#/b0c68bce2cce478eaac82fe38d4138b1)

## Import Artifacts

### Raw Data
- [dpc-covid19-ita-national-trend.csv](https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-andamento-nazionale/dpc-covid19-ita-andamento-nazionale.csv): national level
- [dpc-covid19-ita-regioni.csv](https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-regioni/dpc-covid19-ita-regioni.csv): regions level
- [dpc-covid19-ita-province.csv](https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-province/dpc-covid19-ita-province.csv): provinces level 

### Cleaned Data
- [dpc-covid19-ita-national-trend.csv](dpc-covid19-ita-national-trend.csv): national level
- [dpc-covid19-ita-regional.csv](dpc-covid19-ita-regional.csv): regions level
- [dpc-covid19-ita-province.csv](dpc-covid19-ita-province.csv): provinces level

### Template MCFs
- [dpc-covid19-ita-national-trend.tmcf](dpc-covid19-ita-national-trend.tmcf): national level
- [dpc-covid19-ita-regional.tmcf](dpc-covid19-ita-regional.tmcf): regions level
- [dpc-covid19-ita-province.tmcf](dpc-covid19-ita-province.tmcf): provinces level

### StatisticalVariable Instance MCF
- [dpc-covid19-ita_StatisticalVariable.mcf](dpc-covid19-ita_StatisticalVariable.mcf)

### Scripts
- [generate_statvar.py](generate_statvar.py): generate the statistical variables
- [preprocess.py](preprocess.py): generate the cleaned CSV files and template MCFs
- [test_template_mcf_names.py](test_template_mcf_names.py): test the following
    - if the column names in template mcf can be found in the cleaned csv files
    - if the statistical variables specified in template mcf can be found in the mcf of statistical variables.

### Notes

Starting 2020-06-25, two new columns were added:

- positive cases from clinic activity  
- positive cases from surveys and tests

These two variables have not been integrated into the import yet.

## Generating Artifacts

To generate `template_filename.tmcf` and `data_filename.csv`, run: 

    python3 preprocess.py 

To generate the `dpc-covid19-ita_StatisticalVariable.mcf,`, run:

    python3 generate_statvar.py

To run the test file `test_template_mcf_names.py`, run:

    python3 test_template_mcf_names.py
