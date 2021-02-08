# State-wise Unemployment Rate: Usual Status (Adjusted)

## About the Dataset
State-wise Unemployment Rate: Usual Status (Adjusted) Urban and Rural. Available from RBI's Handbook of Statistics on the Indian States.

Source: NSSO Employment & Unemployment Survey Reports, NITI Aayog, and Periodic Labour Force Survey (PLFS), NSO.

### Download URL
Available for download as xlsx. 

* [State-wise Unemployment Rate: Usual Status (Adjusted) Urban](https://www.rbi.org.in/scripts/PublicationsView.aspx?id=20002), [XLSX](https://rbidocs.rbi.org.in/rdocs/Publications/DOCs/T_13091EFB2ADFEA47CAA069BEE53BD82F14.XLSX)
* [State-wise Unemployment Rate: Usual Status (Adjusted) Rural](https://www.rbi.org.in/scripts/PublicationsView.aspx?id=20001), [XLSX](https://rbidocs.rbi.org.in/rdocs/Publications/DOCs/T_123C6CE499AEFB461E8242E14098242CA5.XLSX)


### Overview
Poverty data is per state and by financial year. There are three sets (sheet) of data in each XLSX Workbook, Male, Female and Overall.

The dataset contains the following columns.
State/Union Territory   


1. State/Union Territory
2. 1993-94 - The unemployment rate for the year, per thousand 
3. 1999-00 - The unemployment rate for the year, per thousand 
4. 2004-05 - The unemployment rate for the year, per thousand 
5. 2009-10 - The unemployment rate for the year, per thousand 
6. 2011-12 - The unemployment rate for the year, per thousand 
7. 2017-18 - The unemployment rate for the year, per thousand 
8. 2018-19 - The unemployment rate for the year, per thousand

Notes: Employment figures are the sum of principal status and subsidiary status.

#### Cleaned Data
- [UnemploymentRate_India.csv](UnemploymentRate_India.csv).

It has the following columns
1. territory - isoCode of the territory
2. value - The unemployment rate for the year, per hundred
3. period - Ending Year  
4. statisticalVariable


#### MCF
- [UnemploymentRate_India_StatisticalVariables.mcf](UnemploymentRate_India_StatisticalVariables.mcf).

#### Template MCFs
- [UnemploymentRate_India_StatisticalVariables.tmcf](UnemploymentRate_India_StatisticalVariables.tmcf).

#### Scripts
- [preprocess.py](preprocess.py): Clean up and import script.


### Running Tests

```bash
python3 -m unittest discover -v -s scripts/ -p *_test.py
```

### Import Procedure

The below script will generate csv file.

`python -m india_rbi.unemployment_rate_india.preprocess`
