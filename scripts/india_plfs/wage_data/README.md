# Periodic Labour Force Survey (PLFS) - Average wage/salary earnings


## About the Dataset
Average wage/salary earnings (Rs. 0.00) during the preceding calendar month from regular wage/salaried employment among the regular wage/ salaried employees in CWS for each State/ UT.


### Download Data

#### PLFS July 2020 - Jun 2021
Wage data from PLES July 2020 - Jun 2021 is available as embedded tables inside the [PDF](https://dge.gov.in/dge/sites/default/files/Anual%20report/Annual%20Report%20PLFS%202020-21.pdf). Standard table format.

```
wget https://dge.gov.in/dge/sites/default/files/Anual%20report/Annual%20Report%20PLFS%202020-21.pdf -O Annual_Report_PLFS_2020-21.pdf
```

* Page 387 has the data for July-Sep 2020
* Page 388 has the data for Oct-Dec 2020
* Page 389 has the data for Jan-Mar2021
* Page 390 has the data for Apr-Jun 2021

Extracted as XLSX using [tabula](https://github.com/tabulapdf/tabula) by running the command

```
java -jar tabula-java.jar --lattice -a 14.207,102.083,567.77,693.532 -p 387 Annual_Report_PLFS_2020-21.pdf -o Table_42_07_09_2020.csv
java -jar tabula-java.jar --lattice  -a 14.207,102.083,567.77,693.532 -p 388 Annual_Report_PLFS_2020-21.pdf -o Table_42_10_12_2020.csv
java -jar tabula-java.jar --lattice -a 14.207,102.083,567.77,693.532 -p 389 Annual_Report_PLFS_2020-21.pdf -o Table_42_01_03_2021.csv
java -jar tabula-java.jar --lattice -a 14.207,102.083,567.77,693.532 -p 390 Annual_Report_PLFS_2020-21.pdf -o Table_42_04_06_2021.csv
```

#### PLES July 2019 - Jun 2020
Wage data from PLES July 2019 - Jun 2020 is available as embedded tables inside the  [PDF](http://mospi.nic.in/sites/default/files/publication_reports/Annual_Report_PLFS_2019_20.pdf). Standard table format.

* Page 381 has the data for July-Sep 2019 
* Page 382 has the data for Oct-Dec 2019
* Page 383 has the data for Jan-Mar 2020
* Page 384 has the data for Apr-Jun 2020

Extracted as CSV using [tabula](https://github.com/tabulapdf/tabula) by running the command

```
java -jar tabula-java.jar --lattice -a 26.836,136.812,514.097,628.283 -p 381 Annual_Report_PLFS_2019_20.pdf  -o Table_42_07_09_2019.csv
java -jar tabula-java.jar --lattice  -a 26.836,136.812,514.097,628.283 -p 382 Annual_Report_PLFS_2019_20.pdf   -o Table_42_10_12_2019.csv
java -jar tabula-java.jar --lattice -a 26.836,136.812,514.097,628.283 -p 383 Annual_Report_PLFS_2019_20.pdf   -o Table_42_01_03_2020.csv
java -jar tabula-java.jar --lattice -a 26.836,136.812,514.097,628.283 -p 384 Annual_Report_PLFS_2019_20.pdf   -o Table_42_04_06_2020.csv
```

#### PLES July 2018 - June 2019
Wage data from PLES July 2018 - June 2019 is available as [XLSX](http://mospi.nic.in/sites/default/files/reports_and_publication/PLFS_2018_19_Anual/Table_42.xlsx).

#### PLES July 2017 - June 2018
Wage data from PLES July 2017 - June 2018 is available as embedded tables inside the  [PDF](http://mospi.nic.in/sites/default/files/publication_reports/Annual%20Report%2C%20PLFS%202017-18_31052019.pdf). Table format is the same. Extracted as XLSX using [tabula](https://github.com/tabulapdf/tabula) by running the command

```
java -jar tabula-java.jar  -a 52.094,85.771,549.879,760.359 -p 400 "$1" 
java -jar tabula-java.jar  -a 52.094,85.771,549.879,760.359 -p 401 "$1" 
java -jar tabula-java.jar  -a 52.094,85.771,549.879,760.359 -p 402 "$1" 
java -jar tabula-java.jar  -a 52.094,85.771,549.879,760.359 -p 403 "$1" 
```

* Page 400 has the data for July-Sept 2017 
* Page 401 has the data for Oct-Dec 2017      
* Page 402 has the data for Jan-Mar 2018
* Page 403 has the data for Apr-June 2018




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


**Notes from the data page:** 
1. Reported earnings from regular wage/salaried employment
2. The Current Weekly Status (CWS) approach to measuring uses seven days preceding the date of survey as the reference period. 
3. Cell value zero(0) indicates no sample observation in the respective category



#### Cleaned Data
- [PLFSWageData_India.csv](PLFSWageData_India.csv)

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
