# Maternal Health Data - 2008 to 2020
        
## About the dataset
Maternal Health Data for the years 2008 to 2020. Available in National Health Mission data portal.

Source: Health Information Management System (HIMS), Ministry of Health and Family Welfare

### Download URL
Available for download as xls and zip files.

[Performance of Key Indicators in HIMS (State level)](https://nrhm-mis.nic.in/hmisreports/frmstandard_reports.aspx)

### Overview
Maternal Health Data is available for financial year starting from 2008. The xls files are under 'data/' folder.
The dataset contains key performance indicators of Maternal Health Data for the particular financial year. 

#### Cleaned data
- [NHM_MaternalHealth.csv](NHM_MaternalHealth.csv)

The cleaned csv has the following columns:

- State: State
- isoCode: isoCode
- Date: Date
- Count_PregnancyEvent: Estimated Number of Annual Pregnancies #
- Count_PregnantWomen_RegisteredForAntenatalCare: Total number of pregnant women Registered for ANC
- Count_PregnantWomen_RegisteredForAntenatalCareWithinFirstTrimester: Number of Pregnant women registered within first trimester
- Count_ChildDeliveryEvent: Total reported deliveries
- Count_ChildDeliveryEvent_InAnInstitution: Institutional deliveries (Public Insts.+Pvt. Insts.)
- Count_ChildDeliveryEvent_InPublicInstitution: Deliveries Conducted at Public Institutions
- Count_ChildDeliveryEvent_AtHome: Number of Home deliveries
- Count_ChildDeliveryEvent_AtHome_WithStandByAssist: Number of home deliveries attended by SBA trained (Doctor/Nurse/ANM)
- Count_DeliveryEvent_Safe_AsFractionOf_Count_DeliveryEvent: % Safe deliveries to Total Reported Deliveries

#### TMCF
- [NHM_MaternalHealth.tmcf](NHM_MaternalHealth.tmcf)

#### Scripts
- [preprocess.py](preprocess.py): Clean up data and generate TMCF file
        