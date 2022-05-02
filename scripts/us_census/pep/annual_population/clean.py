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
"""
This Python Script contains methods to clean the county, state datasets
"""
import os
import pandas as pd
from state_to_geoid import USSTATE_MAP
from fips_to_state import FIPSCODE


def clean_df(df: pd.DataFrame, file_format: str) -> pd.DataFrame:
    """
    This Methods cleans the CSV dataset using the key Geographic Area as header
    Arguments:
        df (DataFrame) : Dataframe contains CSV data
        file_format (str) : Sring value of either CSV, TXT
    Returns:
        df (DataFrame) : Cleaned Dataframe
    """
    if file_format.lower() == "csv":
        header = "Geographic Area"
        idx = df[df[0] == header].index
        idx = idx.values[0]
        df = df.iloc[idx:, :]
        df = df.reset_index().drop(columns=["index"])
    return df


def find_file_format(path: str) -> str:
    return path[path.rfind('.') + 1:]


def _move_data_to_right(df: pd.DataFrame, row_index: list) -> pd.DataFrame:

    for row in row_index:
        for idx in range(7, 2, -1):
            df.iloc[row, idx] = df.iloc[row, idx - 1]
    return df


def _get_nonna_index_for_tmp1(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["tmp1"].notnull()].index.values


def _move_data_to_left(df: pd.DataFrame,
                       row_values: list,
                       idx1: int = -7,
                       idx2: int = -2) -> pd.DataFrame:
    for row in row_values:
        for idx in range(idx1, idx2):  #-2:74, -3:73, -4:72, -5:71, -6:70
            df.iloc[row, idx] = df.iloc[row, idx + 1]
    return df


def _get_numeric_index(df: pd.DataFrame, column: str) -> pd.DataFrame:
    return df[df[column].apply(lambda row: row.isnumeric())].index.values


def _get_char_index_in_col(df: pd.DataFrame, col: str) -> pd.DataFrame:
    return df[df[col].str.replace(
        ".", "").apply(lambda row: row.isalpha())].index.values


def _merge_rows(df: pd.DataFrame, index_list: list, lr_idx: int, left_idx: int,
                right_idx: int) -> pd.DataFrame:

    for idx in index_list:
        if lr_idx == 0:
            df.iloc[idx - 1, -8:] = df.iloc[idx, left_idx:right_idx]
        else:
            df.iloc[idx - 1, -8:-1] = df.iloc[idx, left_idx:right_idx]
        #print(df.iloc[idx-2:idx+2,:])
    return df


def _clean_county_df(county_df: pd.DataFrame,
                     first_df_cols: list) -> pd.DataFrame:
    """

    Args:
        county_df (pd.DataFrame): County Dataframe
        first_df_cols (list): List of Dataset Columns

    Returns:
        county_df (pd.DataFrame): Returns Transformed County dataframe
    """
    if "1980" in first_df_cols:
        lr_idx, right_idx = 0, -1
    else:
        lr_idx, right_idx = -1, -2
    index_list = _get_char_index_in_col(county_df, "Fips_Code")
    county_df = _merge_rows(county_df, index_list, lr_idx, -9, right_idx)
    county_df = county_df.drop(index=index_list)
    county_df = county_df.reset_index().drop(columns=["index"])

    index_list = _get_numeric_index(county_df, "Tmp_Row")
    county_df = _move_data_to_right(county_df, index_list)
    county_df = county_df.reset_index().drop(columns=["index"])

    index_list = _get_nonna_index_for_tmp1(county_df)
    county_df = _move_data_to_left(county_df, index_list)
    county_df = county_df.reset_index().drop(columns=["index"])

    return county_df


def clean_1970_1989_county_txt(df: pd.DataFrame, first_df_cols: list,
                               second_df_cols: list) -> pd.DataFrame:
    """

    Args:
        df (pd.DataFrame): Dataframe contains county data from 1970 to 1989
        first_df_cols (list): Columns List from 1970 to 1974 or 1980 to 1984
        second_df_cols (list): Columns List from 1975 to 1979 or 1985 to 1989

    Returns:
        final_df (pd.DataFrame): Returns Transformed County dataframe
    """
    idx = df[df[0] == "FIPS"].index.values
    next_idx = 0
    final_df = None
    for first_idx, second_idx in zip(idx[::2], idx[1::2]):
        next_idx += 2
        if next_idx >= len(idx):
            end_idx = len(df)
        else:
            end_idx = idx[next_idx]
        initial_df = df.iloc[first_idx + 2:second_idx, :]
        next_df = df.iloc[second_idx + 2:end_idx, :]
        initial_df.reset_index().drop(columns=["index"])

        initial_df.columns, next_df.columns = first_df_cols, second_df_cols
        initial_df = initial_df.reset_index().drop(columns=["index"])
        next_df = next_df.reset_index().drop(columns=["index"])

        initial_df = _clean_county_df(initial_df, first_df_cols)
        next_df = _clean_county_df(next_df, first_df_cols)
        if "1985" in second_df_cols:
            index_list = _get_char_index_in_col(next_df, "1985")
            next_df = _move_data_to_left(next_df, index_list, -8, -2)
        if "1980" in first_df_cols:
            index_list = _get_char_index_in_col(initial_df, "1980")
            if len(index_list) > 0:
                initial_df = _move_data_to_left(initial_df, index_list, -8, -1)
                if initial_df.loc[index_list[0], "tmp2"] is not None:
                    initial_df = _move_data_to_left(initial_df, index_list, -3,
                                                    -1)
        if "1970" in first_df_cols:
            index_list = _get_char_index_in_col(initial_df, "1970")
            if len(index_list) > 0:
                initial_df = _move_data_to_left(initial_df, index_list, -7, -1)
                if initial_df.loc[index_list[0], "tmp2"] is not None:
                    initial_df = _move_data_to_left(initial_df, index_list, -3,
                                                    -1)
        if "1975" in second_df_cols:
            index_list = _get_char_index_in_col(next_df, "1975")
            if len(index_list) > 0:
                next_df = _move_data_to_left(next_df, index_list, -7, -1)
                if next_df.loc[index_list[0], "tmp2"] is not None:
                    next_df = _move_data_to_left(next_df, index_list, -3, -1)
        next_df = initial_df.merge(next_df,
                                   how="inner",
                                   on="Fips_Code",
                                   suffixes=("", "_right"))
        next_df["Location"] = next_df["Fips_Code"].apply(
            lambda row: FIPSCODE.get(row, "geoId/" + row))
        if final_df is None:
            final_df = next_df
        else:
            final_df = pd.concat([final_df, next_df], axis=0)
    final_cols = ["Location"] + first_df_cols[3:8] + second_df_cols[3:8]

    return final_df[final_cols]


def _create_final_file(op_tmp_file: str, search_string: str,
                       op_file: str) -> None:
    """

    Args:
        op_tmp_file (str): Output temp File path
        search_string (str): Search String in File
        op_file (str): Output File
    """
    states = []
    with open(op_tmp_file + ".csv", encoding='utf-8') as file:
        for line in file.readlines():
            if line.strip() == '':
                continue
            if line.strip().find(search_string) != -1:
                header = ['Location']
                header[1:] = (" ".join(line.strip('\n').split()).split())
            elif len(" ".join(line.strip('\n').split()).split()[0]) == 2:
                states.append(" ".join(line.strip('\n').split()).split())
    with open(op_file + ".csv", 'a', encoding='utf-8') as op:
        for state in states:
            items = dict(zip(header, state))
            # state_name = items['Location']
            state_name = USSTATE_MAP.get(items['Location'], items['Location'])
            for k, v in items.items():
                if k not in ['Location', '(census)', '1970']:
                    op.write("\n" + k + "," + state_name + "," +
                             v.replace(",", ""))


def _create_intermediate_file(ip_file: str, temp_file1: str, temp_file2: str,
                              search_string1: str, search_string2: str) -> None:
    """

    Args:
        ip_file (str): Input File Path
        temp_file1 (str): Temporary File Path
        temp_file2 (str): Temporary File Path
        search_string1 (str): Search String in Input File
        search_string2 (str): Search String in Input File
    """

    flag1 = 0
    flag2 = 0

    with open(temp_file1 + ".csv", 'w', encoding='utf-8') as temp_file_1:
        with open(temp_file2 + ".csv", 'w', encoding='utf-8') as temp_file_2:
            with open(ip_file, encoding='utf-8') as file:
                for line in file.readlines():
                    if line.strip() == search_string1:
                        flag1 = 1
                        flag2 = 0
                    elif line.strip() == search_string2:
                        flag1 = 0
                        flag2 = 1

                    if flag1:
                        temp_file_1.write(line)
                    elif flag2:
                        temp_file_2.write(line)


def get_state_file_config() -> dict:
    """
    This Method create a dict of states config file.
    Returns:
        states_config (dict): dict of states file config
    """
    states_config = {
        "st0009ts.txt": {
            "temp_file1":
                "st0005ts_tmp",
            "temp_file2":
                "st0509ts_tmp",
            "search_string_1":
                "1900     1901     1902     1903     1904    1905",
            "search_string_2":
                "1906     1907     1908     1909",
            "op_file_name":
                "st0069ts"
        },
        "st1019ts.txt": {
            "temp_file1":
                "st1015ts_tmp",
            "temp_file2":
                "st1519ts_tmp",
            "search_string_1":
                "1910     1911     1912     1913     1914    1915",
            "search_string_2":
                "1916     1917     1918     1919",
            "op_file_name":
                "st0069ts"
        },
        "st2029ts.txt": {
            "temp_file1":
                "st2025ts_tmp",
            "temp_file2":
                "st2529ts_tmp",
            "search_string_1":
                "1920     1921     1922     1923     1924    1925",
            "search_string_2":
                "1926     1927     1928     1929",
            "op_file_name":
                "st0069ts"
        },
        "st3039ts.txt": {
            "temp_file1":
                "st3035ts_tmp",
            "temp_file2":
                "st3539ts_tmp",
            "search_string_1":
                "1930     1931     1932     1933     1934    1935",
            "search_string_2":
                "1936     1937     1938     1939",
            "op_file_name":
                "st0069ts"
        },
        "st4049ts.txt": {
            "temp_file1":
                "st4045ts_tmp",
            "temp_file2":
                "st4549ts_tmp",
            "search_string_1":
                "1940     1941     1942     1943     1944    1945",
            "search_string_2":
                "1946     1947     1948     1949",
            "op_file_name":
                "st0069ts"
        },
        "st5060ts.txt": {
            "temp_file1":
                "st5054ts_tmp",
            "temp_file2":
                "st5559ts_tmp",
            "search_string_1":
                "(census)    1950     1951     1952    1953     1954",
            "search_string_2":
                "1955    1956     1957     1958    1959 (census)",
            "op_file_name":
                "st0069ts"
        },
        "st6070ts.txt": {
            "temp_file1":
                "st6064ts_tmp",
            "temp_file2":
                "st6569ts_tmp",
            "search_string_1":
                "1960     1960     1961     1962     1963     1964",
            "search_string_2":
                "1965     1966     1967     1968     1969     1970",
            "op_file_name":
                "st0069ts"
        }
    }
    return states_config


def process_states_1970_1979(file_path: str) -> pd.DataFrame:
    """

    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: DataFrame with Processed States Data
                      from 1970 to 1979
    """
    with open(file_path, "r", encoding="UTF-8") as file:
        search_str1 = "4/1/70      7/71      7/72      7/73      7/74      7/75"
        search_str2 = "7/76      7/77      7/78      7/79    4/1/80"
        with open("out.csv", "w", encoding="UTF-8") as outfile:
            outfile.write("Year,Location,Count_Person\n")
            cols = None
            flag = None
            for line in file.readlines():
                if len(line.strip()) == 0:
                    continue
                if line.startswith("    US"):
                    flag = False
                    continue
                if search_str1 in line.strip():
                    flag = True
                    cols = ["1970", "1971", "1972", "1973", "1974", "1975"]
                    continue
                if search_str2 in line.strip():
                    flag = True
                    cols = ["1976", "1977", "1978", "1979"]
                    continue
                if flag:
                    #print(line)
                    data = line.split(" ")
                    data = [
                        val.strip()
                        for val in data
                        if val != '' and val.strip().isnumeric()
                    ]
                    if not data[1].isnumeric():
                        continue
                    loc = "geoId/" + f"{int(data[0]):02d}"
                    for year, val in dict(zip(cols, data[1:])).items():
                        outfile.write(f"{year},{loc},{val}\n")
        df = pd.read_csv("out.csv", header=0)
        os.remove("out.csv")
        return df


def process_states_1980_1989(file_path: str) -> pd.DataFrame:
    """

    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: DataFrame with Processed States Data
                      from 1980 to 1989
    """
    with open(file_path, "r", encoding="UTF-8") as file:
        search_str1 = "4/80cen     7/81      7/82      7/83      7/84"
        search_str2 = "7/85      7/86      7/87      7/88      7/89   4/90cen"
        with open("out.csv", "w", encoding="UTF-8") as outfile:
            outfile.write("Year,Location,Count_Person\n")
            cols = None
            flag = None
            for line in file.readlines():
                if len(line.strip()) == 0:
                    continue
                if line.startswith("Intercensal") or line.startswith(
                        "All data") or line.startswith("Table 2"):
                    flag = False
                    continue
                if search_str1 in line.strip():
                    flag = True
                    cols = ["1980", "1981", "1982", "1983", "1984"]
                    continue
                if search_str2 in line.strip():
                    flag = True
                    cols = ["1985", "1986", "1987", "1988", "1989"]
                    continue
                if flag:
                    #print(line)
                    data = line.split(" ")
                    loc = data[0]
                    if loc == "US":
                        continue
                    data = [
                        val.strip()
                        for val in data
                        if val != '' and val.strip().isnumeric()
                    ]
                    if not data[1].isnumeric():
                        continue

                    #loc = "geoId/" + f"{int(data[0]):02d}"
                    for year, val in dict(zip(cols, data)).items():
                        #print(f"{year},{loc},{val}")
                        outfile.write(f"{year},{loc},{val}\n")
        df = pd.read_csv("out.csv", header=0)
        os.remove("out.csv")
        return df


def process_states_1990_1999(file_path: str) -> pd.DataFrame:
    """

    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: DataFrame with Processed States Data
                      from 1990 to 1999
    """
    with open(file_path, "r", encoding="UTF-8") as file:
        search_str1 = "(Estimate)  (Estimate)  (Estimate)  (Estimate)" +\
                      "  (Estimate)  (Estimate)"
        search_str2 = "(Estimate)  (Estimate)  (Estimate)  (Estimate) "+\
                      "   (Census)"
        with open("out.csv", "w", encoding="UTF-8") as outfile:
            outfile.write("Year,Location,Count_Person\n")
            cols = None
            flag = None
            start = False
            for line in file.readlines():
                if len(line.strip()) == 0:
                    continue
                if line.startswith(
                        "------"
                ):
                    flag = True
                    continue
                if line.startswith("Documentation Notes"):
                    flag = False
                    continue
                if search_str1 in line.strip():
                    flag = True
                    cols = ["1999", "1998", "1997", "1996", "1995", "1994"]
                    continue
                if search_str2 in line.strip():
                    flag = True
                    cols = ["1993", "1992", "1991", "1990"]
                    continue
                if flag:
                    data = line.split(" ")

                    data = [val.strip() for val in data if val != '']
                    #print(data)
                    for idx, val in enumerate(data):
                        if val.isnumeric():
                            continue
                        if idx > 1:
                            data[1] = data[1] + val
                            data[idx] = ''
                    data = [val.strip() for val in data if val != '']
                    loc = data[1]
                    if loc == "Alabama":
                        start = True
                    if start:
                        for year, val in dict(zip(cols, data[2:])).items():
                            outfile.write(f"{year},{loc},{val}\n")
                    if data[1] == "Wyoming":
                        start = False
        df = pd.read_csv("out.csv", header=0)
        os.remove("out.csv")
        return df


def process_states_1900_1969(states_config: dict, file_path: str,
                             file_name: str,
                             scaling_factor: int) -> pd.DataFrame:
    """

    Args:
        states_config (dict): dict of states file config
        file_path (str): Input File Path
        file_name (str): Input File Name
        scaling_factor (int): Scaling factor to be multiplied

    Returns:
        df (DataFrame): Cleaned States Dataframe
    """
    conf = states_config[file_name]
    temp_file1 = conf['temp_file1']
    temp_file2 = conf['temp_file2']
    s1 = conf['search_string_1']
    s2 = conf['search_string_2']
    op_file_name = conf['op_file_name']
    final_file_path = op_file_name + ".csv"

    _create_intermediate_file(file_path, temp_file1, temp_file2, s1, s2)
    _create_final_file(temp_file1, s1, op_file_name)
    _create_final_file(temp_file2, s2, op_file_name)
    df = pd.read_csv(final_file_path, header=None)
    df.columns = ["Year", "Location", "Count_Person"]
    df["Count_Person"] = df["Count_Person"].multiply(scaling_factor)
    os.remove(temp_file1 + ".csv")
    os.remove(temp_file2 + ".csv")
    os.remove(final_file_path)
    return df
