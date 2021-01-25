

# Periodic Labour Force Survey (PLFS) - Average wage/salary earnings


## About the Dataset
Average wage/salary earnings (Rs. 0.00) during the preceding calendar month from regular wage/salaried employment among the regular wage/ salaried employees in CWS for each State/ UT.


### Download URL

* For July 2018 - June 2019 [XLSX](http://mospi.nic.in/sites/default/files/reports_and_publication/PLFS_2018_19_Anual/Table_42.xlsx)


### Overview

Average wage/salary earnings is per state and by quarter. There are three sets of data, for the years 2018-19. The dataset contains the following columns.

1. State \ UT  
2. State/Union Territory
3. rural, male
4. rural, female
5. rural, person
6. urban, male
7. urban, female
8. urban, person
9. rural+urban, male
10. rural+urban, female
11. rural+urban, total


**Notes from the data page :** 
1. Reported earnings from regular wage/salaried employment



#### Cleaned Data
- [PLFSWageData_India_Table_42_07_09_2018.csv](PLFSWageData_India_Table_42_07_09_2018.csv)
- [PLFSWageData_India_Table_42_10_12_2018.csv](PLFSWageData_India_Table_42_10_12_2018.csv)
- [BelowPovertyLine_India.csv](PLFSWageData_India_Table_42_01_03_2019.csv)
- [BelowPovertyLine_India.csv](PLFSWageData_India_Table_42_04_06_2019.csv)

It has the following columns

1. period
2. territory
3. wage_rural_male
4. wage_rural_female
5. wage_rural_person
6. wage_urban_male
7. wage_urban_female
8. wage_urban_person
9. wage_total_male
10. wage_total_female
11. wage_total_person

#### MCF
- [PLFSWageData_India_StatisticalVariables.mcf](PLFSWageData_India_StatisticalVariables.mcf).

#### Template MCFs
- [PLFSWageData_India.tmcf](PLFSWageData_India.tmcf).

### Running Tests

```bash
python3 -m unittest discover -v -s scripts/ -p *_test.py
```

### Import Procedure

The below script will generate; mcf, tmcf and csv files.

`python -m india_plfs.wage_data.preprocess`
