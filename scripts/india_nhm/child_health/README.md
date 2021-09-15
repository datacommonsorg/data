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

- Count_ChildBirthEvent_Live: Total Number of reported live births
- Count_ChildBirthEvent_Still: Total Number of reported Still Births
- Count_ChildBirthEvent_Live_AsFractionOf_Count_ChildDeliveryEvent: % Live Births to Total Deliveries
- Count_ChildVaccinationEvent_BCG: Number of Infants given BCG
- Count_ChildVaccinationEvent_OPV: Number of Infants given OPV 0 (Birth Dose)
- Count_ChildVaccinationEvent_DPT_FirstDose: Number of Infants given DPT1
- Count_ChildVaccinationEvent_DPT_SecondDose: Number of Infants given DPT2
- Count_ChildVaccinationEvent_DPT_ThirdDose: Number of Infants given DPT3
- Count_ChildVaccinationEvent_Measles: Number of Infants given Measles
- Count_ChildVaccinationEvent_AdverseEvents_Death: Adverse Events Following Immunisation
- Count_ChildDeathEvent: Total Number of Infant Deaths reported

#### TMCF
- [NHM_ChildHealth.tmcf](NHM_ChildHealth.tmcf)

#### Scripts
- [preprocess.py](preprocess.py): Clean up data and generate TMCF file
        