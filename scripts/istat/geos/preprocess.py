# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Preprocess the ISTAT geo code to NUTS code for importing into Data Commons"""

import zipfile
import io
import os
import requests
import pandas as pd

URL = "https://www.istat.it/storage/codici-unita-amministrative/"+\
    "Elenco-codici-statistici-e-denominazioni-delle-unita-territoriali.zip"

def download(url):
    """download and extract the csv file to ./raw/xx"""
    response = requests.get(url)
    file_zip = zipfile.ZipFile(io.BytesIO(response.content))
    file_zip.extractall("./raw/temp")
    folder_name = os.listdir("./raw/temp")[0]
    folder = os.path.join("./raw/temp", folder_name)
    files = [file for file in os.listdir(folder) if file[-4:] == ".csv"]
    if len(files) != 1:
        raise Exception("0 or more than 1 files found")
    file_name = files[0]
    os.rename(os.path.join(folder, file_name), "./raw/"+file_name[:-4]+"_it.csv")
    os.system("rm -rf ./raw/temp")
    return "./raw/"+file_name[:-4]+"_it.csv"

def translate(file_path):
    """tranlate the column names to English based on Google translate"""
    data = pd.read_csv(file_path, sep=';', encoding='cp1252')
    data.columns = ["Region Code", "Supra-municipal territorial unit"+\
        "code (valid for statistical purposes)", "Province Code (Historic) (1)",  \
        "Municipality progress (2)", "Common alphanumeric format code", \
        "Name (Italian and foreign)", "Name in Italian", "Name in other language",\
         "Geographic breakdown code", "Geographical breakdown", "Region name", \
         "Name of the supra-municipal territorial unit (valid for statistical purposes)", \
        "Flag Municipality provincial capital / metropolitan city / free consortium", \
        "Automotive abbreviation", "Common Code numeric format", \
        "Numeric Common Code with 110 provinces (from 2010 to 2016)", \
        "Numeric Common Code with 107 provinces (from 2006 to 2009)", \
        "Numerical Common Code with 103 provinces (from 1995 to 2005)", \
        "Cadastral code of the municipality", \
        "Legal population 2011 (09/10/2011)", "NUTS1", "NUTS2(3)", "NUTS3"]
    file_path_en = file_path.replace('_it.csv', '_en.csv')
    data.to_csv(file_path_en, encoding='utf-8', index=False)
    return file_path_en

def preprocess(file_path):
    """"preprocess the csv file for importing into Data Commons"""
    data = pd.read_csv(file_path)
    columns_rename = {"Province Code (Historic) (1)": "Province Code",\
        "Name of the supra-municipal territorial unit (valid for statistical purposes)":\
        "Province name", "Automotive abbreviation":"Province Abbreviation",\
        "NUTS2(3)":"NUTS2", "Common Code numeric format":"Municipal Code", \
        "Name in Italian":"Municipal Name"}
    data = data.rename(columns=columns_rename)

    # correct some of the mismatch of NUTS code and names
    reorg = [("ITG2A", 91, "OG", "Ogliastra"), ("ITG28", 95, "OR", "Oristano"),\
            ("ITG27", 92, "CA", "Cargliari"), ("ITG29", 90, "OT", "Olbia-Tempio")]
    for (nuts3, province_code, province_abbrev, province_name) in reorg:
        data.loc[data[data["NUTS3"] == nuts3].index, "Province Code"] = province_code
        data.loc[data[data["NUTS3"] == nuts3].index, "Province Abbreviation"] = province_abbrev
        data.loc[data[data["NUTS3"] == nuts3].index, "Province name"] = province_name
    data.loc[data[data["Province name"] == "Napoli"].index, "Province Abbreviation"] = "NA"

    region_data = data[["Region Code", "NUTS2", "Region name"]].drop_duplicates()
    region_data["NUTS2"] = "nuts/" + region_data["NUTS2"]
    region_data["Region Code"] = region_data["Region Code"].astype(str).str.zfill(2)
    region_data.loc[region_data[region_data["NUTS2"] == "nuts/ITH1"].index, "Region name"] = \
        "Provincia Autonoma di Bolzano/Bozen"
    region_data.loc[region_data[region_data["NUTS2"] == "nuts/ITH2"].index, "Region name"]\
        = "Provincia Autonoma di Trento"
    region_data.to_csv("ISTAT_region.csv", index=False)

    province_data = data[["Province Code", "NUTS3", "Province name", \
        "Province Abbreviation"]].drop_duplicates()
    province_data["NUTS3"] = "nuts/" + province_data["NUTS3"]
    province_data["Province Code"] = province_data["Province Code"].astype(str).str.zfill(3)
    province_data.to_csv("ISTAT_province.csv", index=False)

    municipal_data = data[["Municipal Code", "Municipal Name", "NUTS3"]].drop_duplicates()
    municipal_data["NUTS3"] = "dcid:nuts/" + municipal_data["NUTS3"]
    municipal_data["Municipal Code"] = municipal_data["Municipal Code"].astype(str).str.zfill(6)
    municipal_data.to_csv("ISTAT_municipal.csv", index=False)

if __name__ == "__main__":
    FILE_PATH_IT = download(URL)
    FILE_PATH_EN = translate(FILE_PATH_IT)
    preprocess(FILE_PATH_EN)
