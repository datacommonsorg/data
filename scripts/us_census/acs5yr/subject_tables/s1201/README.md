# Artefacts for US census ACS5YR S1201 (Marital Status) Subject Table import #

This import includes the population characteristics (such as gender, age, race and labor force participation) characterized by the marital status.

Years: 2010-2019
Geo : Country, State, County and Place

Important Notes :
1. Data for 2010-2014 contain ‘NATIVITY’ label. However, it is not present in data for 2015-2019. 
2. Duplicate column names were found in datasets for years 2010-2012.
3. Local import scripts s2409/process.py and s2409/generate_col_map.py are created to handle duplicate column names seperately while loading the dataset.
