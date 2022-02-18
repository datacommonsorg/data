# Birth Control Data - 2008 to 2020
        
## About the dataset
Birth Control Data for the years 2008 to 2020. Available in National Health Mission data portal.

Source: Health Information Management System (HIMS), Ministry of Health and Family Welfare

### Download URL
Available for download as xls and zip files.

[Performance of Key Indicators in HIMS (District level)](https://nrhm-mis.nic.in/hmisreports/frmstandard_reports.aspx)

### Overview
Birth Control Data is available for financial year starting from 2008. The xls files are under 'data/' folder.
The dataset contains key performance indicators of Birth Control Data for the particular financial year. 

#### Cleaned data
- [NHM_BirthControl.csv](NHM_BirthControl.csv)

The cleaned csv has the following columns:

- District: District
- lgdCode: lgdCode
- Date: Date
- Count_BirthControlEvent_Vasectomy: Number of Vasectomies Conducted (Public and Private Institutions)
- Count_BirthControlEvent_Vasectomy: Number of Vasectomies Conducted (Public and Private Institutions)
- Count_BirthControlEvent_Tubectomy: Number of Tubectomies Conducted (Public and Private Institutions)
- Count_BirthControlEvent_Tubectomy: Number of Tubectomies Conducted (Public and Private Institutions)
- Count_BirthControlEvent_Sterilization: Total Sterilisation Conducted
- Count_BirthControlEvent_Vasectomy_AsFractionOf_Count_BirthControlEvent_Sterlization: Percent of Male Sterlisation (Vasectomies) to Total sterilisation
- Count_Death_BirthControlSterilization: Total cases of deaths following Sterilisation (Male and Female)
- Count_BirthControlEvent_IUCDInsertion: Total IUCD Insertions done
- Count_BirthControlEvent_IUCDInsertion: Total IUCD Insertions done
- Count_BirthControlEvent_IUCDInsertion_AsFractionOf_Count_BirthControlEvent: Percent of IUCD insertions to all family planning methods
- Count_BirthControlEvent_IUCDInsertion_AsFractionOf_Count_BirthControlEvent: Percent of IUCD insertions to all family planning methods
- Count_ContraceptiveDistribution_OralPill: Oral Pills distributed
- Count_ContraceptiveDistribution_OralPill: Combined Oral Pills distributed
- Count_ContraceptiveDistribution_Condom: Condom pieces distributed

#### TMCF
- [NHM_BirthControl.tmcf](NHM_BirthControl.tmcf)

#### Scripts
- [preprocess.py](preprocess.py): Clean up data and generate TMCF file
        