# Importing U.S. Bureau of Labor Statistics Consumer Price Index

This directory contains data and scripts for importing
[U.S. Bureau of Labor Statistics Consumer Price Index
](https://www.bls.gov/cpi/data.htm) into Data Commons.


## Cleaned Data
1. [c_cpi_u_1999_2020.csv](c_cpi_u_1999_2020.csv) contains
   seasonally unadjusted Chained CPI for All Urban Consumers (C-CPI-U) data
   from 1999 to 2020.
   Series ID is "SUUR0000SA0".
2. [cpi_u_1913_2020.csv](cpi_u_1913_2020.csv) contains
   seasonally unadjusted CPI for All Urban Consumers (CPI-U) data from
   1913 to 2020.
   Series ID is "CUUR0000SA0".
3. [cpi_w_1913_2020.csv](cpi_w_1913_2020.csv) contains
   seasonally unadjusted CPI for Urban Wage Earners and Clerical Workers
   (CPI-W) data from 1913 to 2020.
   Series ID is "CWUR0000SA0".

Each has two columns: "date" and "cpi". "date" is of the form "YYYY-MM" and
"cpi" is numeric.


## Script
1. [generate_csv.py](generate_csv.py) downloads and converts BLS CPI raw csv
   files to csv files of two columns: "date" and "cpi", where "date" is of the
   form "YYYY-MM" and "cpi" is numeric.


## StatisticalVariable instance MCFs
1. [c_cpi_u_1999_2020_StatisticalVariable.mcf
   ](c_cpi_u_1999_2020_StatisticalVariable.mcf)
2. [cpi_u_1913_2020_StatisticalVariable.mcf
   ](cpi_u_1913_2020_StatisticalVariable.mcf)
3. [cpi_w_1913_2020_StatisticalVariable.mcf
   ](cpi_w_1913_2020_StatisticalVariable.mcf)


## Template MCFs
1. [c_cpi_u_1999_2020.tmcf](c_cpi_u_1999_2020.tmcf)
2. [cpi_u_1913_2020.tmcf](cpi_u_1913_2020.tmcf)
3. [cpi_w_1913_2020.tmcf](cpi_w_1913_2020.tmcf)
