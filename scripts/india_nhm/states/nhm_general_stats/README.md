# General Health Statistics Data - 2008 to 2020
        
## About the dataset
General Health Statistics Data for the years 2008 to 2020. Available in National Health Mission data portal.

Source: Health Information Management System (HIMS), Ministry of Health and Family Welfare

### Download URL
Available for download as xls and zip files.

[Performance of Key Indicators in HIMS (State level)](https://nrhm-mis.nic.in/hmisreports/frmstandard_reports.aspx)

### Overview
General Health Statistics Data is available for financial year starting from 2008. The xls files are under 'data/' folder.
The dataset contains key performance indicators of General Health Statistics Data for the particular financial year. 

#### Cleaned data
- [NHM_GeneralStats.csv](NHM_GeneralStats.csv)

The cleaned csv has the following columns:

- State: State
- isoCode: isoCode
- Date: Date
- Count_InPatient: Number of In-patients
- Count_OutPatient: Number of Out-patients
- Count_OutPatient: Number of Out-patients (Allopathic)
- Count_SurgicalProcedure_Major: Number of Major Operations
- Count_SurgicalProcedure_Minor: Number of Minor Operations
- Count_InPatient_Deceased_AsFractionOf_Count_InPatient: Percent of Inpatient Deaths to Total Inpatients
- Count_OutPatient_Ayush: Number of AYUSH outpatients

#### TMCF
- [NHM_GeneralStats.tmcf](NHM_GeneralStats.tmcf)

#### Scripts
- [preprocess.py](preprocess.py): Clean up data and generate TMCF file
        