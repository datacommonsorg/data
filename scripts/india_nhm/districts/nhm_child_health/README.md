# Child Health Data - 2008 to 2020
        
## About the dataset
Child Health Data for the years 2008 to 2020. Available in National Health Mission data portal.

Source: Health Information Management System (HIMS), Ministry of Health and Family Welfare

### Download URL
Available for download as xls and zip files.

[Performance of Key Indicators in HIMS (District level)](https://nrhm-mis.nic.in/hmisreports/frmstandard_reports.aspx)

### Overview
Child Health Data is available for financial year starting from 2008. The xls files are under 'data/' folder.
The dataset contains key performance indicators of Child Health Data for the particular financial year. 

#### Cleaned data
- [NHM_ChildHealth.csv](NHM_ChildHealth.csv)

The cleaned csv has the following columns:

- District: District
- lgdCode: lgdCode
- Date: Date
- Count_BirthEvent_LiveBirth: Total number of reported live births
- Count_BirthEvent_StillBirth: Total number of reported still births
- Count_BirthEvent_LiveBirth_AsFractionOf_Count_ChildDeliveryEvent: Percent of total reported live births to total deliveries
- Count_Infant_VaccineAdministered_BCG: Number of infants given BCG vaccine
- Count_Infant_VaccineAdministered_OPV: Number of infants given OPV 0 Vaccine (Birth Dose)
- Count_Infant_VaccineAdministered_DPTDose1: Number of infants given DPT Vaccine Dose 1
- Count_Infant_VaccineAdministered_DPTDose2: Number of infants given DPT Vaccine Dose 2
- Count_Infant_VaccineAdministered_DPTDose3: Number of infants given DPT Vaccine Dose 3
- Count_ChildVaccinationEvent_MMR: Number of infants given MMR Vaccine
- Count_Infant_VaccineSideEffect_Adverse_Deaths: Adverse events following immunization (Deaths)
- Count_Infant_VaccineSideEffect_Adverse_Others: Adverse events following immunization (Others)
- Count_Death_Infant: Total number of infant deaths reported

#### TMCF
- [NHM_ChildHealth.tmcf](NHM_ChildHealth.tmcf)

#### Scripts
- [preprocess.py](preprocess.py): Clean up data and generate TMCF file
        