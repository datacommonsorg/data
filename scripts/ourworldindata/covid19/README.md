# Importing OurWorldInData Covid19 Data

<<<<<<< HEAD
This directory contains artifacts required for importing [OurWorldInData Covid19 Data](https://github.com/owid/covid-19-data/tree/master/public/data)
into Data Commons, along with scripts used to generate these artifacts.

## Artifacts:

- [OurWorldInData_Covid19.csv](OurWorldInData_Covid19.csv): the cleaned CSV.
- [OurWorldInData_Covid19.tmcf](OurWorldInData_Covid19.tmcf): the mapping file (Template MCF).
- [OurWorldInData_Covid19_StatisticalVariables.mcf](OurWorldInData_Covid19_StatisticalVariables.mcf):
  the new StatisticalVariables defined for this dataset.
=======
This directory imports [OurWorldInData Covid19 Data](https://github.com/owid/covid-19-data/tree/master/public/data)
into Data Commons. 

The script generates:
- OurWorldInData_Covid19.csv
- OurWorldInData_Covid19.tmcf

and it relies on these statistic variables:
- dcs:CumulativeCount_Vaccine_COVID_19_Administered
- dcs:IncrementalCount_Vaccine_COVID_19_Administered
- dcs:CumulativeCount_MedicalConditionIncident_COVID_19_ConfirmedCase
- dcs:IncrementalCount_MedicalConditionIncident_COVID_19_ConfirmedCase
- dcs:CumulativeCount_MedicalConditionIncident_COVID_19_PatientDeceased
- dcs:IncrementalCount_MedicalConditionIncident_COVID_19_PatientDeceased
- dcs:Count_MedicalConditionIncident_COVID_19_PatientInICU
- dcs:Count_MedicalConditionIncident_COVID_19_PatientHospitalized
- dcs:CumulativeCount_MedicalTest_ConditionCOVID_19
- dcs:IncrementalCount_MedicalTest_ConditionCOVID_19
>>>>>>> 05fceb34ee8a5f0e6074e089b8ac300eab73b1da

## Generating Artifacts:

`OurWorldInData_Covid19_StatisticalVariable.mcf` was handwritten.

To generate `OurWorldInData_Covid19.tmcf` and `OurWorldInData_Covid19.csv`, run:

```bash
python3 preprocess_csv.py
```
