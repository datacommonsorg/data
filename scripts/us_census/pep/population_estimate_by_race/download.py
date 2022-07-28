# Copyright 2022 Google LLC
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
""" A Script to download USA Census PEP population data by Race
    from the URLS in provided json file.
"""

import os
import json
from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen
from absl import app
from absl import flags
import pandas as pd

_FLAGS = flags.FLAGS
_URLS_JSON_PATH = os.path.dirname(os.path.abspath(__file__)) \
                    + os.sep +"file_urls.json"
print(_URLS_JSON_PATH)
_URLS_JSON = None
with open(_URLS_JSON_PATH, encoding="UTF-8") as file:
    _URLS_JSON = json.load(file)

# Flag names are globally defined!  So in general, we need to be
# careful to pick names that are unlikely to be used by other libraries.
# If there is a conflict, we'll get an error at import time.
flags.DEFINE_list("_url", _URLS_JSON["urls"], "Import Data URL's List")


def _resolve_pe_11(file_name: str, _url: str) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a csv file format.

    Arguments:
        file_path (str) : File path of csv dataset

    Returns:
        df (DataFrame) : Transformed DataFrame for csv dataset.
    """
    year = file_name[-8:-4]
    if int(year) < 1960:
        cols = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
        df = pd.read_csv(_url, names=cols)
        df = df[df["0"].str.contains("All ages", na=False)]
        df['Year'] = year
        df['Geographic Area'] = "United States"
    else:
        cols = [
            "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"
        ]
        df = pd.read_csv(_url, names=cols, skiprows=2)
        df = df[df["0"].str.contains("All ages", na=False)]
        df['Year'] = year
        df['Geographic Area'] = "United States"
    return df


def _save_data(_url: str, download_local_path: str) -> None:
    """
    This method loads the Data from url to pandas Dataframe.
    Writes the data to local path provided as one the parameter.

    Arguments:
        _url (str): Url of the dataset
        download_local_path (str): LocalPath to save the datasets.

    Returns:
        None
    """
    file_name = _url.split("/")[-1]
    print(file_name)
    if ".csv" in _url:
        if "st-est" in _url or 'SC-EST' in _url:
            file_name = file_name.replace(".csv", ".xlsx")
            df = pd.read_csv(_url, on_bad_lines='skip', header=0)
            df.to_excel(download_local_path + os.sep + file_name\
                ,index=False,engine='xlsxwriter')
        elif "pe-11" in _url:
            df = _resolve_pe_11(file_name, _url)
            df.to_csv(download_local_path + os.sep + file_name, index=False)
        elif "pe-19" in _url:
            file_name = file_name.replace(".csv", ".xlsx")
            df = pd.read_csv(_url, skiprows=5, on_bad_lines='skip', header=0)
            df.to_excel(download_local_path + os.sep + file_name\
                ,index=False,engine='xlsxwriter')
        elif "co-asr-7079" in _url or "pe-02" in _url:
            file_name = file_name.replace(".csv", ".xlsx")
            cols=['Year','FIPS','Race/Sex',1,2,3,4,5,6,7,8,9,10,11,12,\
                13,14,15,16,17,18]
            if "pe-02" in _url:
                df = pd.read_csv(_url, skiprows=7, on_bad_lines='skip', \
                    names=cols)
            else:
                df = pd.read_csv(_url, on_bad_lines='skip', names=cols)
            df.to_excel(download_local_path + os.sep + file_name,\
                index=False,engine='xlsxwriter')
        elif "co-est00int-alldata" in _url or "CC-EST2020-ALLDATA" in _url:
            df = pd.read_csv(_url,
                             on_bad_lines='skip',
                             encoding='ISO-8859-1',
                             low_memory=False)
            df.to_csv(download_local_path + os.sep + file_name, index=False)

    elif ".txt" in _url and "srh" in _url:
        if "crh" in _url:
            file_name = file_name.replace("crh", "USCounty")
            df = pd.read_table(_url, index_col=False, engine='python')
            df.to_csv(download_local_path + os.sep + file_name, index=False)
        else:
            cols = ['Area', 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            df = pd.read_table(_url,index_col=False,delim_whitespace=True\
                ,engine='python',skiprows=14,names=cols)
            file_name = file_name.replace(".txt", ".csv")
            df.to_csv(download_local_path + os.sep + file_name, index=False)

    elif "xlsx" in _url:
        df = pd.read_excel(_url, skiprows=2, header=0)
        df.to_excel(download_local_path + os.sep + file_name\
            ,index=False,header=False,engine='xlsxwriter')


def _download(download_path: str, file_urls: list) -> None:
    """
    This method iterates on each url and calls the above defined
    functions to download and clean the data.

    Arguments:
        download_path (str) : Local Path to download datasets from URLS
        file_urls (list) : List of dataset URLS.

    Returns:
        df (DataFrame) : Transformed DataFrame for txt dataset.
    """
    if not os.path.exists(download_path):
        os.mkdir(download_path)
    for _url in file_urls:
        _save_data(_url, download_path)


def main(_):
    """
    Main Function to Start Execution of The Code
    """

    file_urls = _FLAGS._url
    path = os.path.dirname(os.path.abspath(__file__)) + os.sep + "input_data"
    _download(path, file_urls)


if __name__ == "__main__":
    app.run(main)
