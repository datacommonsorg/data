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
  #find not one-to-one mapping from ISTAT to NUTS
  duplicated = pd.DataFrame(columns = df.columns)
  for col in df.columns:
    dup_vals = df[df[col].duplicated()][col].unique()
    for val in dup_vals:
      duplicated = pd.concat([duplicated, df[df[col]==val]], ignore_index = True)
  duplicated = duplicated.drop_duplicates()
  print(duplicated)
  return duplicated
      
def preprocess():

  data = pd.read_csv(FILE_PATH_en)
  columns_rename = {"Province Code (Historic) (1)": "Province Code","Name of the supra-municipal territorial unit (valid for statistical purposes)":"Province name", "Automotive abbreviation":"Province Abbreviation", "NUTS2(3)":"NUTS2","Common Code numeric format":"Municipal Code", "Name in Italian":"Municipal Name"}
  data = data.rename(columns = columns_rename)
  
  #correct some of the mismatch of NUTS code and names
  reorg = [("ITG2A", 91, "OG", "Ogliastra"), ("ITG28", 95, "OR", "Oristano"), ("ITG27", 92, "CA","Cargliari"),
       ("ITG29", 90, "OT", "Olbia-Tempio")]
  for (nuts3, province_code, province_abbrev, province_name) in reorg:
    data.loc[data[data["NUTS3"] == nuts3].index, "Province Code"] = province_code
    data.loc[data[data["NUTS3"] == nuts3].index, "Province Abbreviation"] = province_abbrev
    data.loc[data[data["NUTS3"] == nuts3].index, "Province name"] = province_name
  data.loc[data[data["Province name"] == "Napoli"].index, "Province Abbreviation"] = "NA"
  
  region_data = data[["Region Code", "NUTS2", "Region name"]].drop_duplicates()
  region_data["NUTS2"] = "nuts/" + region_data["NUTS2"]
  region_data["Region Code"] = region_data["Region Code"].astype(str).str.zfill(2)
  region_data.loc[region_data[region_data["NUTS2"] == "nuts/ITH1"].index, "Region name"] = "Provincia Autonoma di Bolzano/Bozen"
  region_data.loc[region_data[region_data["NUTS2"] == "nuts/ITH2"].index, "Region name"] = "Provincia Autonoma di Trento"
  region_data.to_csv("ISTAT_region.csv", index = False)
  
  province_data = data[["Province Code", "NUTS3","Province name", "Province Abbreviation"]].drop_duplicates()
  province_data["NUTS3"] = "nuts/" + province_data["NUTS3"]
  province_data["Province Code"] = province_data["Province Code"].astype(str).str.zfill(3)
  province_data.to_csv("ISTAT_province.csv", index = False)
  
  municipal_data = data[["Municipal Code", "Municipal Name", "NUTS3"]].drop_duplicates()
  municipal_data["NUTS3"] = "dcid:nuts/" + municipal_data["NUTS3"]
  municipal_data["Municipal Code"] = municipal_data["Municipal Code"].astype(str).str.zfill(6)
  municipal_data.to_csv("ISTAT_municipal.csv", index = False)

def generate_tmcf():
  region_TEMPLATE = "Node: E:ISTAT->E0\n" +\
                 "typeOf: dcs:EurostatNUTS2\n" +\
                 "dcid: C:ISTAT->NUTS2\n" +\
                 "name: C:ISTAT->Region name\n" +\
                 "istatId: C:ISTAT->Region Code\n\n"
                 
  province_TEMPLATE = "Node: E:ISTAT->E0\n" +\
                      "typeOf: dcs:EurostatNUTS3\n" +\
                      "dcid: C:ISTAT->NUTS3\n" +\
                      "name: C:ISTAT->Province name\n" +\
                      "istatId: C:ISTAT->Province Code\n" +\
                      "abbreviation: C:ISTAT->Province Abbreviation\n\n"
                      
  municipal_TEMPLATE = "Node: E:ISTAT->E0\n" +\
                       "typeOf: dcs:AdministrativeArea3\n" +\
                       "istatId: C:ISTAT->Municipal Code\n" +\
                       "name: C:ISTAT->Municipal Name\n" +\
                       "containedInPlace: C:ISTAT->NUTS3\n\n"
                      
  with open("./ISTAT_region.tmcf", 'w') as f_out:
    f_out.write(region_TEMPLATE)
  with open("./ISTAT_province.tmcf", 'w') as f_out:
    f_out.write(province_TEMPLATE)
  with open("./ISTAT_municipal.tmcf", 'w') as f_out:
    f_out.write(municipal_TEMPLATE)
    
if __name__ == "__main__":
  preprocess()
  generate_tmcf()
  
