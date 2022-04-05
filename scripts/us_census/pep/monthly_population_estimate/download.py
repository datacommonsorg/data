""" A Script to download USA Census PEP monthly population data
    from the URLS in provided json file.
    Typical usage:
    1. python3 download.py
    2. python3 download.py -f file_urls.json
    3. python3 download.py -f <<path_to_file>>
"""
import os
import json
import argparse
import pandas as pd
import numpy as np

HEADER = 1
SKIP_ROWS = 1


def save_data(url, download_local_path):
    """
    This method loads the Data from url to pandas Dataframe.
    Writes the data to local path provided as one the parameter.

    Parameters:
    url (str): Url of the dataset
    download_local_path (str): Path to save the datasets.

    Returns:
    None
    """
    df = ""
    file_name = url.split("/")[-1]
    if ".xls" in url:
        df = pd.read_excel(url, header=HEADER)
        df.to_excel(download_local_path + os.sep + file_name,
                    index=False,
                    header=False,
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
        df = clean_txt_file(df)
        df.to_excel(download_local_path + os.sep + file_name,
                    index=False,
                    engine='xlsxwriter')


def sum_cols(col):
    """
    This method adds Dataframe columns Year and Month, Date.
    Returns the column value in format yyyymmdd. Example: 2022March01
    """
    if col[1] is None:
        return col[0]
    return col[0] + ' ' + col[1]


def mulitply(col):
    """
    This method multiply dataframe column with scaling factor 1000.
    Returns New column value mulitplied by 1000.
    """
    res = col
    if col not in [None, np.NAN]:
        if col.isdigit():
            res = int(col) * 1000
    return res


def clean_txt_file(df):
    """
    This method cleans the dataframe loaded from a txt file format.
    Also, Performs transformations on the data.
    """

    df['Year and Month'] = df[['Year and Month', 'Date']]\
                                    .apply(sum_cols, axis=1)
    df.drop(columns=['Date'], inplace=True)
    for col in df.columns:
        df[col] = df[col].str.replace(",", "")
    idx = df[df['Resident Population'] == "(census)"].index

    resident_population = 1
    resident_population_plus_armed_forces_overseas = 2
    civilian_population = 3
    civilian_noninstitutionalized_population = 4

    #Moving the row data left upto one index value.
    df.iloc[idx, resident_population] = df.iloc[idx][
        "Resident Population Plus Armed Forces Overseas"]
    df.iloc[idx, resident_population_plus_armed_forces_overseas] = df.iloc[idx][
        "Civilian Population"]
    df.iloc[idx, civilian_population] = df.iloc[idx][
        "Civilian NonInstitutionalized Population"]
    df.iloc[idx, civilian_noninstitutionalized_population] = np.NAN

    #Multiplying the data with scaling factor 1000.
    scaling_factor = 1000
    for col in df.columns:
        if "year" not in col.lower():
            if scaling_factor != 1:
                df[col] = df[col].apply(mulitply)
    return df


def download():
    """
    This method iterates on each url and calls the above defined
    functions to download and clean the data.
    """

    download_path = os.path.dirname(
        os.path.abspath(__file__)) + os.sep + "input_data"
    if not os.path.exists(download_path):
        os.mkdir(download_path)
    for url in FILE_URLS:
        save_data(url, download_path)


if __name__ == "__main__":
    #Initialize parser
    parser = argparse.ArgumentParser()
    #Adding optional argument
    default_urls_file = os.path.dirname(os.path.abspath(__file__))\
                        + os.sep + "file_urls.json"
    parser.add_argument("-f",
                        "--file_urls",
                        default=default_urls_file,
                        help="Json file with Dataset URLS")

    # Read arguments from command line
    args = parser.parse_args()
    urls_file = args.file_urls

    #Loading urls config file
    urls = None
    with open(urls_file, encoding="UTF-8") as file:
        urls = file.read()

    #Loading json string and extracting urls.
    urls = json.loads(urls)
    FILE_URLS = urls['new_urls']

    download()
