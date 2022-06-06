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
""" A Script to download, perform some basic transformations to
    USA Census PEP monthly population data from the URLS in
    provided json file and save it as an xlsx file.
"""

import os
import json
import pandas as pd
import numpy as np
from absl import app
from absl import flags

_FLAGS = flags.FLAGS
_URLS_JSON_PATH = os.path.dirname(os.path.abspath(__file__)) \
                    + os.sep +"file_urls.json"

_URLS_JSON = None
with open(_URLS_JSON_PATH, encoding="UTF-8") as file:
    _URLS_JSON = json.load(file)

# Flag names are globally defined!  So in general, we need to be
# careful to pick names that are unlikely to be used by other libraries.
# If there is a conflict, we'll get an error at import time.
flags.DEFINE_list("us_census_pep_monthly_pop_estimate_url", \
    _URLS_JSON["urls"], "Import Data URL's List")

_HEADER = 1
SKIP_ROWS = 1
_SCALING_FACTOR_TXT_FILE = 1000


def _save_data(url: str, download_local_path: str) -> None:
    """
    This method loads the Data from url to pandas Dataframe.
    Writes the data to local path provided as one the parameter.

    Arguments:
        url (str): Url of the dataset
        download_local_path (str): LocalPath to save the datasets.

    Returns:
        None
    """
    df = None
    file_name = url.split("/")[-1]
    if ".xls" in url:
        df = pd.read_excel(url, header=_HEADER)
        df.to_excel(download_local_path + os.sep + file_name,
                    index=False,
                    header=False,
                    engine='xlsxwriter')
    elif ".csv" in url:
        file_name = file_name.replace(".csv", ".xlsx")
        df = pd.read_csv(url, header=None)
        df = _clean_csv_file(df)
        df.to_excel(download_local_path + os.sep + file_name,
                    index=False,
                    engine='xlsxwriter')
    elif ".txt" in url:
        file_name = file_name.replace(".txt", ".xlsx")
        cols = [
            "Year and Month", "Date", "Resident Population",
            "Resident Population Plus Armed Forces Overseas",
            "Civilian Population", "Civilian NonInstitutionalized Population"
        ]
        df = pd.read_table(url,
                           index_col=False,
                           delim_whitespace=True,
                           engine='python',
                           skiprows=17,
                           names=cols)
        df = _clean_txt_file(df, _SCALING_FACTOR_TXT_FILE)
        df.to_excel(download_local_path + os.sep + file_name,
                    index=False,
                    engine='xlsxwriter')


def _sum_cols(col: pd.Series) -> pd.Series:
    """
    This method concats two DataFrame column values
    with space in-between.

    Arguments:
        col[0] (Series) : DataFrame Column of dtype str
        col[1] (Series) : DataFrame Column of dtype str

    Returns:
        res (Series) : Concatenated DataFrame Columns
    """
    print(type(col))
    res = col[0]
    if col[1] is None:
        return res
    res = col[0] + ' ' + col[1]
    return res


def _mulitply_scaling_factor(col: pd.Series, **kwargs: dict) -> pd.Series:
    """
    This method multiply dataframe column with scaling factor.

    Arguments:
        col (Series): DataFrame Column of dtype int
        **kwargs (dict): Dict with key 'scaling_factor' and value type int

    Returns:
        res (Series): DataFrame column values mulitplied by scaling_factor.
    """
    res = col
    if col not in [None, np.NAN]:
        if col.isdigit():
            res = int(col) * kwargs["scaling_factor"]
    return res


def _clean_csv_file(df: pd.DataFrame) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a csv file format.
    Also, Performs transformations on the data.

    Arguments:
        df (DataFrame) : DataFrame of csv dataset

    Returns:
        df (DataFrame) : Transformed DataFrame for txt dataset.
    """
    # Removal of file description and headers in the initial lines of the input
    idx = df[df[0] == "Year and Month"].index
    df = df.iloc[idx.values[0] + 1:][:]
    df = df.dropna(axis=1, how='all')
    cols = [
        "Year and Month", "Resident Population",
        "Resident Population Plus Armed Forces Overseas", "Civilian Population",
        "Civilian NonInstitutionalized Population"
    ]
    df.columns = cols
    for col in df.columns:
        df[col] = df[col].str.replace(",", "")
    return df


def _clean_txt_file(df: pd.DataFrame,
                    scaling_factor_txt_file: int) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a txt file format.
    Also, Performs transformations on the data.

    Arguments:
        df (DataFrame) : DataFrame of txt dataset
        scaling_factor_txt_file (int) : Scaling factor for text file

    Returns:
        df (DataFrame) : Transformed DataFrame for txt dataset.
    """
    # Month and Year are concatenated into a single column if they are not None
    df['Year and Month'] = df[['Year and Month', 'Date']]\
                                    .apply(_sum_cols, axis=1)
    df.drop(columns=['Date'], inplace=True)
    for col in df.columns:
        df[col] = df[col].str.replace(",", "")
    idx = df[df['Resident Population'] == "(census)"].index

    resident_population = 1
    resident_population_plus_armed_forces_overseas = 2
    civilian_population = 3
    civilian_noninstitutionalized_population = 4

    # Moving the row data left upto one index value.
    df.iloc[idx, resident_population] = df.iloc[idx][
        "Resident Population Plus Armed Forces Overseas"]
    df.iloc[idx, resident_population_plus_armed_forces_overseas] = df.iloc[idx][
        "Civilian Population"]
    df.iloc[idx, civilian_population] = df.iloc[idx][
        "Civilian NonInstitutionalized Population"]
    df.iloc[idx, civilian_noninstitutionalized_population] = np.NAN

    # Multiplying the data with scaling factor 1000.
    for col in df.columns:
        if "year" not in col.lower():
            if scaling_factor_txt_file != 1:
                df[col] = df[col].apply(_mulitply_scaling_factor,
                                        scaling_factor=scaling_factor_txt_file)
    return df


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
    for url in file_urls:
        _save_data(url, download_path)


def main(_):
    file_urls = _FLAGS.us_census_pep_monthly_pop_estimate_url
    path = os.path.dirname(os.path.abspath(__file__)) + os.sep + "input_data"
    _download(path, file_urls)


if __name__ == "__main__":
    app.run(main)
