# Importing U.S. Bureau of Labor Statistics Consumer Price Index

This directory contains data and scripts for importing
[U.S. Bureau of Labor Statistics Consumer Price Index
](https://www.bls.gov/cpi/data.htm) into Data Commons.

## Raw Data
1. [c_cpi_u_1999_2020.xlsx](c_cpi_u_1999_2020.xlsx) contains Chained CPI for
   All Urban Consumers (C-CPI-U) data from 1999 to 2020.
2. [cpi_u_1913_2020.xlsx](cpi_u_1913_2020.xlsx) contains CPI for All Urban
   Consumers (CPI-U) data from 1913 to 2020.
3. [cpi_w_1913_2020.xlsx](cpi_w_1913_2020.xlsx) contains CPI for Urban Wage
   Earners and Clerical Workers (CPI-W) data from 1913 to 2020.

In the xlsx files provided by BLS, header starts at Row 12 (counting from one).
Rows 1-11 are descriptions of the dataset. Column A is the index (year).
Columns B-M are the 12 columns that correspond to the 12 months in a year, so
each row represents a year and contains the CPIs for that year.

BLS does not have CPIs for the most recent months in the current year, so the
last several cells are empty and will be NaNs when read into a Pandas DataFrame.


## Cleaned Data
1. [c_cpi_u_1999_2020.csv](c_cpi_u_1999_2020.csv)
2. [cpi_u_1913_2020.csv](cpi_u_1913_2020.csv)
3. [cpi_w_1913_2020.csv](cpi_w_1913_2020.csv)

These are csv files converted from the xlsx files above using the script below.
Each of them has two columns: date and cpi. "date" is of the form "YYYY-MM" and
"cpi" is numeric.


## Script
1. [xlsx2csv.py](xlsx2csv.py) is a Python script for converting the xlsx files
   to csv files of two columns: date and cpi. "date" is of the form "YYYY-MM"
   and "cpi" is numeric.

## Instance MCFs
1. [c_cpi_u_1999_2020_StatisticalVariable.mcf
   ](c_cpi_u_1999_2020_StatisticalVariable.mcf)
2. [cpi_u_1913_2020_StatisticalVariable.mcf
   ](cpi_u_1913_2020_StatisticalVariable.mcf)
3. [cpi_w_1913_2020_StatisticalVariable.mcf
   ](cpi_w_1913_2020_StatisticalVariable.mcf)

They define the StatisticalVariables representing the CPIs in Data Commons in
MCF format.

## Template MCFs
1. [c_cpi_u_1999_2020.tmcf](c_cpi_u_1999_2020.tmcf)
2. [cpi_u_1913_2020.tmcf](cpi_u_1913_2020.tmcf)
3. [cpi_w_1913_2020.tmcf](cpi_w_1913_2020.tmcf)

They define the mappings from the cleaned csv files to the StatisticalVariables.