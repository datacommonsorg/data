# Periodic Labour Force Survey (PLFS) -  Average daily wage earnings


## About the Dataset
Average wage earnings (Rs. 0.00) per day from casual labour work other than public works in CWS for each State/ UT.

### Download Data

#### PLES July 2019 - Jun 2020
Wage data from PLES July 2019 - Jun 2020 is available as embedded tables inside the  [PDF](http://mospi.nic.in/sites/default/files/publication_reports/Annual_Report_PLFS_2019_20.pdf). Table format is the same.

* Page 384 has the data for July-Sep 2019 
* Page 385 has the data for Oct-Dec 2019
* Page 386 has the data for Jan-Mar 2020
* Page 387 has the data for Apr-Jun 2020

Extracted as XLSX using [tabula](https://github.com/tabulapdf/tabula) by running the command

```
java -jar tabula-java.jar --lattice -a 24.731,106.819,519.359,637.228 -p 385 Annual_Report_PLFS_2019_20.pdf  -o Table_43_07_09_2019.csv
java -jar tabula-java.jar --lattice  -a 24.731,106.819,519.359,637.228 -p 386 Annual_Report_PLFS_2019_20.pdf   -o Table_43_10_12_2019.csv
java -jar tabula-java.jar --lattice -a 24.731,106.819,519.359,637.228 -p 387 Annual_Report_PLFS_2019_20.pdf   -o Table_43_01_03_2020.csv
java -jar tabula-java.jar --lattice -a 24.731,106.819,519.359,637.228 -p 388 Annual_Report_PLFS_2019_20.pdf   -o Table_43_04_06_2020.csv
```

#### PLES July 2018 - June 2019
Wage data from PLES July 2018 - June 2019 is available as [XLSX](http://mospi.nic.in/sites/default/files/reports_and_publication/PLFS_2018_19_Anual/Table_43.xlsx).

#### PLES July 2017 - June 2018
Wage data from PLES July 2017 - June 2018 is available as embedded tables inside the  [PDF](http://mospi.nic.in/sites/default/files/publication_reports/Annual%20Report%2C%20PLFS%202017-18_31052019.pdf). Table format is the same. 

* Page 404 has the data for July-Sept 2017 
* Page 405 has the data for Oct-Dec 2017      
* Page 406 has the data for Jan-Mar 2018
* Page 407 has the data for Apr-June 2018

Extracted as XLSX using [tabula](https://github.com/tabulapdf/tabula) by running the command

```
java -jar tabula-java.jar  -a 40.506,97.049,521.453,782.161 -p 404 "$1" 
java -jar tabula-java.jar  -a 40.506,97.049,521.453,782.161 -p 405 "$1" 
java -jar tabula-java.jar  -a 40.506,97.049,521.453,782.161 -p 406 "$1" 
java -jar tabula-java.jar  -a 40.506,97.049,521.453,782.161 -p 407 "$1" 
```

    
### Overview

Average wage/salary earnings are per state and by quarter. There are three sets of data for the years 2018-19. The dataset contains the following columns.

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
1. The Current Weekly Status (CWS) approach to measuring uses seven days preceding the date of survey as the reference period. 


#### Cleaned Data
- [PLFSDailyWageData_India.csv](PLFSDailyWageData_India.csv)

It has the following columns.

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
- [PLFSDailyWageData_India_StatisticalVariables.mcf](PLFSDailyWageData_India_StatisticalVariables.mcf).

#### Template MCFs
- [PLFSDailyWageData_India.tmcf](PLFSDailyWageData_India.tmcf).

### Running Tests

```bash
python3 -m unittest discover -v -s scripts/ -p *_test.py
```

### Import Procedure

The below script will generate; mcf, tmcf and csv files.

`python -m india_plfs.daily_wage_data.preprocess`
