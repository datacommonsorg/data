# Lint as python3
"""Preprocess the ISTAT geo code to NUTS code for importing into Data Commons"""

import pandas as pd

FILE_PATH_it = "./Elenco-codici-statistici-e-denominazioni-al-01_01_2020_it.csv"
FILE_PATH_en = "./Elenco-codici-statistici-e-denominazioni-al-01_01_2020_en.csv"


def translate():
  # tranlate the column names to English based on Google translate
  data = pd.read_csv(FILE_PATH_it, sep = ';', encoding = 'cp1252')
  data.columns = ["Region Code", "Supra-municipal territorial unit code (valid for statistical purposes)", \
    "Province Code (Historic) (1)", "Municipality progress (2)","Common alphanumeric format code", \
    "Name (Italian and foreign)", "Name in Italian", "Name in other language", "Geographic breakdown code", \
    "Geographical breakdown", "Region name", "Name of the supra-municipal territorial unit (valid for statistical purposes)", \
    "Flag Municipality provincial capital / metropolitan city / free consortium", "Automotive abbreviation", \
    "Common Code numeric format", "Numeric Common Code with 110 provinces (from 2010 to 2016)", \
    "Numeric Common Code with 107 provinces (from 2006 to 2009)", "Numerical Common Code with 103 provinces (from 1995 to 2005)", \
    "Cadastral code of the municipality", "Legal population 2011 (09/10/2011)", "NUTS1", "NUTS2(3)", "NUTS3"]
  data.to_csv(FILE_PATH_en, encoding = 'utf-8', index = False)
  
def preprocess():
  data = pd.read_csv(FILE_PATH_en)
  print(data.head(5))
  
  
if __name__ == "__main__":
  preprocess()
