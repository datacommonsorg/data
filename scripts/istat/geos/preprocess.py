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
  
def find_duplicates(df):
  duplicated = pd.DataFrame(columns = df.columns)
  for col in df.columns:
    dup_vals = df[df[col].duplicated()][col].unique()
    for val in dup_vals:
      duplicated = pd.concat([duplicated, df[df[col]==val]], ignore_index = True)
  duplicated = duplicated.drop_duplicates()
  #print(duplicated)
  return duplicated
      
def preprocess():
  data = pd.read_csv(FILE_PATH_en)
  province_data = data[["Province Code (Historic) (1)", "NUTS3","Name of the supra-municipal territorial unit (valid for statistical purposes)", "Automotive abbreviation"]].rename(\
    columns = {"Province Code (Historic) (1)": "Province Code","Name of the supra-municipal territorial unit (valid for statistical purposes)":"Province name", "Automotive abbreviation":"Province Abbreviation"}).drop_duplicates()
  region_data = data[["Region Code", "NUTS2(3)", "Region name"]].rename(columns= {"NUTS2(3)":"NUTS2"}).drop_duplicates()
  province_data.to_csv("ISTAT_ProvinceCode_NUTS3.csv", index = False)
  region_data.to_csv("ISTAT_RegionCode_NUTS2.csv", index = False)
  #find the regions/provinces that does not make one-to-one map from ISTAT to NUTS
  except_region = find_duplicates(region_data)
  except_province = find_duplicates(province_data)
  pd.concat([except_province,except_region], axis = 1, ignore_index = False).to_csv("ISTAT_exceptions.csv", index = False)
  
if __name__ == "__main__":
  preprocess()
