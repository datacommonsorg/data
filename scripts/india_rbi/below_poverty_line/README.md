# Number and Percentage of Population Below Poverty Line


## About the Dataset
Number and Percentage of Population Below Poverty Line published by Reserve Bank of India/Planning Commission.


### Download URL

* Available for downlod as [XLSX](https://rbidocs.rbi.org.in/rdocs/Publications/DOCs/154T_HB15092019609736EE47614B23BFD377A47FFC1A5D.XLSX)


### Overview
Poverty data is per state and by year. There are three sets of data, for the years 2004-05, 2009-10, 2011-12. The dataset contains the following columns.

1. Year  
2. State/Union Territory
3. No. of Persons (Thousands), Rural  
4. % of Persons, Rural
5. Poverty line (₹), Rural  
6. No. of Persons (Thousands), Urban  
7. % of Persons, Urban
8. Poverty line (₹), Urban  
9. No. of Persons (Thousands), Combined
10. % of Persons, Combined


**Notes from the RBI/Planning Commission data page :** 
1. Population as on 1st March 2012 has been used for estimating number of persons below poverty line. (2011 Census population extrapolated)
2. Poverty line of Tamil Nadu has been used for Andaman and Nicobar Island.
3. Urban Poverty Line of Punjab has been used for both rural and urban areas of Chandigarh.
4. Poverty Line of Maharashtra has been used for Dadra & Nagar Haveli.
5. Poverty line of Goa has been used for Daman & Diu.
6. Poverty Line of Kerala has been used for Lakshadweep.
7. Computed as per Tendulkar method on Mixed Reference Period (MRP)



#### Cleaned Data
- [BelowPovertyLine_India.csv](BelowPovertyLine_India.csv).

It has the following columns
1. year - Ending Year  
2. territory - isoCode of the territory
3. count_person_rural - No. of Persons, Rural  
4. percentage_person_rural - % of Persons, Rural
5. poverty_line_rural - Poverty line (₹), Rural  
6. count_person_urban - No. of Persons, Urban  
7. percentage_person_urban - % of Persons, Urban
8. poverty_line_urban - Poverty line (₹), Urban  
9. count_person_combined - No. of Persons, Combined
10. percentage_person_combined - Combined - % of Persons


#### MCF
- [BelowPovertyLine_India_StatisticalVariables.mcf](BelowPovertyLine_India_StatisticalVariables.mcf).

#### Template MCFs
- [BelowPovertyLine_india.tmcf](BelowPovertyLine_india.tmcf).

#### Scripts
- [preprocess.py](preprocess.py): Clean up and import script.


### Running Tests

```bash
python3 -m unittest preprocess_test
```

### Import Procedure

To import data, run the following command:

```
python3 preprocess.py
```
