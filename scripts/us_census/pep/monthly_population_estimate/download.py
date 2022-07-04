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
_URLS_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "file_urls.json")

_URLS_JSON = None
with open(_URLS_JSON_PATH, encoding="UTF-8") as file:
    _URLS_JSON = json.load(file)

# Flag names are globally defined!  So in general, we need to be
# careful to pick names that are unlikely to be used by other libraries.
# If there is a conflict, we'll get an error at import time.
flags.DEFINE_list("us_census_pep_monthly_pop_estimate_url", \
    _URLS_JSON["urls"], "Import Data URL's List")

_HEADER = 1
_SCALING_FACTOR_TXT_FILE = 1000


def _save_data(url: str, download_local_path: str) -> None:
    """
    This method loads the Data from url to pandas Dataframe.
    Writes the data to local path provided as one the parameter.

    Args:
        url (str): Url of the dataset
        download_local_path (str): LocalPath to save the datasets.

    Returns:
        None
    """
    df = None
    file_name = url.split("/")[-1]
    if ".xls" in url:
        df = pd.read_excel(url, header=_HEADER)
        df.to_excel(os.path.join(download_local_path, file_name),
                    index=False,
                    header=False,
                    engine='xlsxwriter')
    elif ".csv" in url:
        file_name = file_name.replace(".csv", ".xlsx")
        df = pd.read_csv(url, header=None)
        df = _clean_csv_file(df)
        df.to_excel(os.path.join(download_local_path, file_name),
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
        # Skipping 17 rows as the initial 17 rows contains the information about
        # the file being used, heading files spread accross multiple lines and
        # other irrelevant information like source/contact details.
        df = _clean_txt_file(df)
        # Multiplying the data with scaling factor 1000.
        for col in df.columns:
            if "year" not in col.lower():
                df[col] = df[col].apply(_mulitply_scaling_factor)
        df.to_excel(os.path.join(download_local_path, file_name),
                    index=False,
                    engine='xlsxwriter')


def _concat_cols(col: pd.Series) -> pd.Series:
    """
    This method concats two DataFrame column values
    with space in-between.

    Args:
        col[0] (Series) : DataFrame Column of dtype str
        col[1] (Series) : DataFrame Column of dtype str

    Returns:
        res (Series) : Concatenated DataFrame Columns
    """
    # Looking at the data whenever col[0] has year, col[1] is None
    # Thus concatinating Date with Month which is needed here
    res = col[0]
    if col[1] is None:
        return res
    res = col[0] + ' ' + col[1]
    return res


def _mulitply_scaling_factor(col: pd.Series) -> pd.Series:
    """
    This method multiply dataframe column with scaling factor.

    Args:
        col (Series): DataFrame Column of dtype int
        **kwargs (dict): Dict with key 'scaling_factor' and value type int

    Returns:
        res (Series): DataFrame column values mulitplied by scaling_factor.
    """
    res = col
    if col not in [None, np.NAN]:
        if col.isdigit():
            res = int(col) * _SCALING_FACTOR_TXT_FILE
    return res


def _clean_csv_file(df: pd.DataFrame) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a csv file format.
    Also, Performs transformations on the data.

    Args:
        df (DataFrame) : DataFrame of csv dataset

    Returns:
        df (DataFrame) : Transformed DataFrame for txt dataset.
    """
    # Removal of file description and headers in the initial lines of the input
    #
    # Input Data:
    # table with row headers in column A and column headers in rows 3 through 5 (leading dots indicate sub-parts)
    # Table 1. Monthly Population Estimates for the United States:  April 1, 2000 to December 1, 2010
    # Year and Month    Resident Population     Resident Population Plus Armed Forces Overseas   Civilian Population	Civilian Noninstitutionalized Population
    # 2000
    # .April 1	28,14,24,602	28,16,52,670	28,02,00,922	27,61,62,490
    # .May 1	28,16,46,806	28,18,76,634	28,04,28,534	27,63,89,920
    #
    # Output Data:
    # (Made Headers) Year and Month    Resident Population     Resident Population Plus Armed Forces Overseas   Civilian Population    Civilian Noninstitutionalized Population
    # 2000
    # .April 1	28,14,24,602	28,16,52,670	28,02,00,922	27,61,62,490
    # .May 1	28,16,46,806	28,18,76,634	28,04,28,534	27,63,89,920

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


def _clean_txt_file(df: pd.DataFrame) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a txt file format.
    Also, Performs transformations on the data.

    Args:
        df (DataFrame) : DataFrame of txt dataset
        scaling_factor_txt_file (int) : Scaling factor for text file

    Returns:
        df (DataFrame) : Transformed DataFrame for txt dataset.
    """
    # Month and Year are concatenated into a single column if they are not None
    df['Year and Month'] = df[['Year and Month', 'Date']]\
                                    .apply(_concat_cols, axis=1)
    df.drop(columns=['Date'], inplace=True)
    for col in df.columns:
        df[col] = df[col].str.replace(",", "")

    # The index numbers alotted as per where the columns are present to
    # move the columns left
    resident_population = 1
    resident_population_plus_armed_forces_overseas = 2
    civilian_population = 3
    civilian_noninstitutionalized_population = 4
    # Moving the row data left upto one index value.
    # As the text file has (census) mentioned in some rows and it makes the
    # other column's data shift by one place, we need to shift it back to the
    # original place.
    idx = df[df['Resident Population'] == "(census)"].index
    df.iloc[idx, resident_population] = df.iloc[idx][
        "Resident Population Plus Armed Forces Overseas"]
    df.iloc[idx, resident_population_plus_armed_forces_overseas] = df.iloc[idx][
        "Civilian Population"]
    df.iloc[idx, civilian_population] = df.iloc[idx][
        "Civilian NonInstitutionalized Population"]
    df.iloc[idx, civilian_noninstitutionalized_population] = np.NAN
    return df


def download(download_path: str, file_urls: list) -> None:
    """
    This method iterates on each url and calls the above defined
    functions to download and clean the data.

    Args:
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
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "input_data")
    download(path, file_urls)


if __name__ == "__main__":
    app.run(main)
