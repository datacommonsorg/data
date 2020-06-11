# Importing Federal Reserve Treasury Constant Maturity Rates into Data Commons

## Raw Data
1. [FRB_H15.csv](FRB_H15.csv) contains annual interest rates for Treasury
   securities traded in secondary markets at various constant maturities such
   as 1-year and 10-year.

## Cleaned Data
1. [treasury_constant_maturity_rates.csv](treasury_constant_maturity_rates.csv)
   contains the data portion of [FRB_H15.csv](FRB_H15.csv). It has the same
   number of columns as the number of constant maturities provided and an extra
   column for dates. "date" column is of the form "YYYY-MM-DD". The other
   interest rate columns are numeric.

## StatisticalVariable Instance MCFs
1. [treasury_constant_maturity_rates.mcf](treasury_constant_maturity_rates.mcf)

## Template MCFs
1. [treasury_constant_maturity_rates.tmcf
   ](treasury_constant_maturity_rates.tmcf)

## Scripts
1. [extract.py](extract.py) extracts the data out of the raw csv and stores it
   in "treasury_constant_maturity_rates.csv". The output table has the same
   number of columns as the number of constant maturities provided and an extra
   column for dates. "date" column is of the form "YYYY-MM-DD". The other
   interest rate columns are numeric.
2. [generate_mcf.py](generate_mcf.py) writes out the instance and template MCFs.
3. [maturity.py](maturity.py) lists the maturities included in the dataset. 
