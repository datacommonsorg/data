# Child Health Data - 2008 to 2020
        
## About the dataset
Child Health Data for the years 2008 to 2020. Available in National Health Mission data portal.

Source: Health Information Management System (HIMS), Ministry of Health and Family Welfare

### Download URL
Available for download as xls and zip files.

[Performance of Key Indicators in HIMS (State level)](https://nrhm-mis.nic.in/hmisreports/frmstandard_reports.aspx)

### Overview
Child Health Data is available for financial year starting from 2008. The xls files are under 'data/' folder.
The dataset contains key performance indicators of Child Health Data for the particular financial year. 

#### Cleaned data
- [NHM_ChildHealth.csv](NHM_ChildHealth.csv)

The cleaned csv has the following columns:

- State: State
- isoCode: isoCode
- Date: Date
- Count_BirthEvent_LiveBirth: Total Number of reported live births
- Count_BirthEvent_StillBirth: Total Number of reported Still Births
- Count_BirthEvent_LiveBirth_AsFractionOf_Count_ChildDeliveryEvent: % Total Reported Live Births to Total Deliveries
- Count_Infant_VaccineAdministered_BCG: Number of Infants given BCG
- Count_Infant_VaccineAdministered_OPV: Number of Infants given OPV 0 (Birth Dose)
- Count_Infant_VaccineAdministered_DPTDose1: Number of Infants given DPT1
- Count_Infant_VaccineAdministered_DPTDose2: Number of Infants given DPT2
- Count_Infant_VaccineAdministered_DPTDose3: Number of Infants given DPT3
- Count_ChildVaccinationEvent_MMR: Number of Infants given Measles
- Count_Infant_VaccineSideEffect_Adverse_Deaths: Adverse Events Following Imunisation (Deaths)
- Count_Infant_VaccineSideEffect_Adverse_Others: Adverse Events Following Imunisation (Others)
- Count_Death_Infant: Total Number of Infant Deaths reported

#### TMCF
- [NHM_ChildHealth.tmcf](NHM_ChildHealth.tmcf)

#### Scripts
- [preprocess.py](preprocess.py): Clean up data and generate TMCF file
        