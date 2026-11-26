# US census ACS5YR S2405 Subject Table import

This b table provides data on the rent expense on US country based on number of bedrooms from 0 to 5 or more bedrooms.

Years: 2010-2021  
Geo : Country, State, County and Place

# Below column names found in input files.
Estimate!!Median gross rent --!!Total:
Margin of Error!!Median gross rent --!!Total:
Estimate!!Median gross rent --!!Total:!!No bedroom
Margin of Error!!Median gross rent --!!Total:!!No bedroom
Estimate!!Median gross rent --!!Total:!!1 bedroom
Margin of Error!!Median gross rent --!!Total:!!1 bedroom
Estimate!!Median gross rent --!!Total:!!2 bedrooms
Margin of Error!!Median gross rent --!!Total:!!2 bedrooms
Estimate!!Median gross rent --!!Total:!!3 bedrooms
Margin of Error!!Median gross rent --!!Total:!!3 bedrooms
Estimate!!Median gross rent --!!Total:!!4 bedrooms
Margin of Error!!Median gross rent --!!Total:!!4 bedrooms
Estimate!!Median gross rent --!!Total:!!5 or more bedrooms
Margin of Error!!Median gross rent --!!Total:!!5 or more bedrooms

#Populations type and Unit of measure took from below link.

https://autopush.datacommons.org/browser/Median_GrossRent_HousingUnit_WithCashRent_OccupiedHousingUnit_RenterOccupied
https://autopush.datacommons.org/browser/Rooms2To3

#Below configuration changes have to make.

File has to modify: scripts/us_census/acs5yr/subject_tables/common/generate_col_map.py

from
=====
year = filename.split(f'ACSST5Y')[1][:4]

to
===
year = filename.split(f'ACSDT5Y')[1][:4]

from
====

File name to be modify "data_loader.py"
year = filename.split(f'ACSST{self.estimate_period}Y')[1][:4]

to
===
year = filename.split(f'ACSDT{self.estimate_period}Y')[1][:4]

#Below query has to execute sequentially

1.

python3 /usr/local/google/home/shamimansari/datarefresh/data/scripts/us_census/acs5yr/subject_tables/process.py --has_percent='false' --input_path=/usr/local/google/home/shamimansari/datarefresh/data/scripts/us_census/acs5yr/input_file_b25031/productDownload_2023-09-12T052816.zip --output_dir=/usr/local/google/home/shamimansari/datarefresh/data/scripts/us_census/acs5yr/output_files_b25031/b25031/ --spec_path=/usr/local/google/home/shamimansari/datarefresh/data/scripts/us_census/acs5yr/subject_tables/b25031/B25031_spec.json --table_prefix=B25031 --option=colmap

2.

python3 /usr/local/google/home/shamimansari/datarefresh/data/scripts/us_census/acs5yr/subject_tables/process.py --has_percent='false' --input_path=/usr/local/google/home/shamimansari/datarefresh/data/scripts/us_census/acs5yr/input_file_b25031/productDownload_2023-09-12T052816.zip --output_dir=/usr/local/google/home/shamimansari/datarefresh/data/scripts/us_census/acs5yr/output_files_b25031/b25031/ --spec_path=/usr/local/google/home/shamimansari/datarefresh/data/scripts/us_census/acs5yr/subject_tables/b25031/B25031_spec.json --table_prefix=B25031

3. 



