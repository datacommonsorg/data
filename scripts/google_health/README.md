# Importing The Google Health Covid19 US Data

This directory contains artifacts required for importing
The Covid19 data collected by Google Health into Data Commons.

## About the Dataset

### Overview

Google Health collected, reconciled, and uniformed the COVID data from [The COVID Tracking Project](https://github.com/COVID19Tracking/covid-tracking-data), [Johns Hopkins University](https://github.com/CSSEGISandData/COVID-19), [California Health and Human Services](https://data.chhs.ca.gov/dataset/healthcare-facility-bed-types-and-counts) for research and prediction use.

### Coverage

The US dataset contains data points from 51 states (including one special: D.C) and 3143 counties and cities, coded using common Data Commons dcids; the dates range from 2020-1-22 to latest day.

### Variables

The dataset contains observations for the following variables:
- dcs:CumulativeCount_MedicalTest_COVID_19
- dcs:CumulativeCount_MedicalTest_COVID_19_Positive
- dcs:CumulativeCount_MedicalTest_COVID_19_Negative
- dcs:CumulativeCount_MedicalConditionIncident_COVID_19_PatientRecovered
- dcs:CumulativeCount_MedicalConditionIncident_COVID_19_PatientDeceased
- dcs:Count_MedicalConditionIncident_COVID_19_PatientHospitalized
- dcs:CumulativeCount_MedicalConditionIncident_COVID_19_PatientHospitalized
- dcs:Count_MedicalConditionIncident_COVID_19_PatientInICU
- dcs:CumulativeCount_MedicalConditionIncident_COVID_19_PatientInICU
- dcs:Count_MedicalConditionIncident_COVID_19_PatientOnVentilator
- dcs:CumulativeCount_MedicalConditionIncident_COVID_19_PatientOnVentilator

## Artifacts:

- [Google_Health_COVID19_US.csv](Google_Health_COVID19_US.csv): the cleaned CSV generated from Google Health pipeline.
- [Google_Health_COVID19_US.tmcf](Google_Health_COVID19_US.tmcf): the mapping file (Template MCF).

