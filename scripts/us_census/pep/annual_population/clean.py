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
import sys
import pandas as pd

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.join(_MODULE_DIR, '../../../../'))
# pylint: disable=wrong-import-position
# pylint: disable=import-error
import util.alpha2_to_dcid as alpha2todcid
# pylint: enable=wrong-import-position
# pylint: enable=import-error

_EXTRA_LOCATION_COL_IDX = 2
_PROPER_DATA_END_COL_IDX = 7


def clean_data_df(data_df: pd.DataFrame, file_format: str) -> pd.DataFrame:
    """
    This Methods cleans the CSV dataset using the Geographic Area as header.
    Arguments:
        data_df (DataFrame) : Dataframe contains CSV data
        file_format (str) : Sring value of either CSV, TXT
    Returns:
        data_df (DataFrame) : Cleaned Dataframe
    """
    if file_format.lower() == "csv":
        header = "Geographic Area"
        idx = data_df[data_df[0] == header].index
        idx = idx.values[0]
        data_df = data_df.iloc[idx:, :]
        data_df = data_df.reset_index().drop(columns=["index"])
    return data_df


def _get_fips_code(fips_code: str) -> str:
    """Returns geoID's for the Country, State and counties.

    Args:
        fips_code (str): FIPS Code

    Returns:
        str: geoId String
    """
    if str(fips_code) == "00000":
        return "country/USA"
    if str(fips_code)[-3:] == "000" and len(fips_code) == 5:
        return "geoId/" + fips_code[:2]
    return "geoId/" + fips_code


def find_file_format(path: str) -> str:
    return os.path.splitext(path)[-1]


def _move_data_to_right(data_df: pd.DataFrame, row_index: list) -> pd.DataFrame:
    """
    Moving data to right starting from 2nd index column to 7th index column.

    Args:
        data_df (pd.DataFrame): Input DataFrame
        row_index (list): row index value requires data shifting to right side

    Returns:
        pd.DataFrame: DataFrame
    """
    for row in row_index:
        for idx in range(_PROPER_DATA_END_COL_IDX, _EXTRA_LOCATION_COL_IDX, -1):
            data_df.iloc[row, idx] = data_df.iloc[row, idx - 1]
    return data_df


def _get_nonna_index_for_extra_data_col_1(
        data_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns Non-NA index values from extra_data_col_1 column
    extra_data_col_1 column can contains actual data
    because of extra delimiters for some rows.
    Args:
        data_df (pd.DataFrame): Input Raw DataFrame

    Returns:
        pd.DataFrame: DataFrame
    """
    return data_df[data_df["extra_data_col_1"].notnull()].index.values


def _move_data_to_left(data_df: pd.DataFrame,
                       row_values: list,
                       idx1: int = -7,
                       idx2: int = -2) -> pd.DataFrame:
    """
    Moving data to left starting from idx1 index column to idx2 index column

    Example Row that requires left shift using _move_data_to_left method.
    DataFrame:
    Fips_Code Location extra_Location 1970   1971   1972   1973 \
        01115      St.          Clair  Co.  27956  29500  31300 \
            1974    extra_data_col_1 extra_data_col_2
            32200              33700             None
    Because of extra delimiters Location column, the data is shifted right by 1
    index and will be to shifted left by 1 index value

    Args:
        data_df (pd.DataFrame): Input DataFrame
        row_index (list): row index value requires data shifting to left side

    Returns:
        pd.DataFrame: DataFrame
    """
    for row in row_values:
        for idx in range(idx1, idx2):
            data_df.iloc[row, idx] = data_df.iloc[row, idx + 1]
    return data_df


def _get_numeric_index(data_df: pd.DataFrame, column: str) -> pd.DataFrame:
    return data_df[data_df[column].apply(
        lambda row: row.isnumeric())].index.values


def _get_char_index_in_col(data_df: pd.DataFrame, col: str) -> pd.DataFrame:
    return data_df[data_df[col].str.replace(
        ".", "", regex=False).apply(lambda row: row.isalpha())].index.values


def _merge_rows(data_df: pd.DataFrame, index_list: list, f_idx: int,
                left_idx: int, right_idx: int) -> pd.DataFrame:
    """
    Merge two rows from index list and from columns left_idx to right_idx

    Some rows in DataFrame is merged as they were splitted into two rows
       Fips_Code Location extra_Location   1970  1971   1972  1973 \
           51097     King            and  Queen  None   None  None \
              Co.    5491           5500   5500  5700   5800  None \
                1974 extra_data_col_1 extra_data_col_2
                None             None             None
                None             None             None

    The above two rows will be merged and formed as below in single row
    DataFrame:
    Fips_Code Location extra_Location  1970  1971  1972  1973 \
        51097     King            and  5491  5500  5500  5700 \
                1974 extra_data_col_1 extra_data_col_2
                5800             None             None

    Args:
        data_df (pd.DataFrame): Input DataFrame
        index_list (list): Row index list
        f_idx (int): Final Column Index
        left_idx (int): Left Column Index
        right_idx (int): Right Column Index

    Returns:
        pd.DataFrame: DataFrame
    """
    for idx in index_list:
        if f_idx == 0:
            # Merging two Dataframe rows starting from -8th index
            data_df.iloc[idx - 1, -8:] = data_df.iloc[idx, left_idx:right_idx]
        else:
            data_df.iloc[idx - 1, -8:-1] = data_df.iloc[idx, left_idx:right_idx]
    return data_df


def _clean_county_data_df(county_data_df: pd.DataFrame,
                          first_data_df_cols: list) -> pd.DataFrame:
    """
    Transforms the county DataFrame by data shifting left/right by one column.

    Example Row that requires right shift using _move_data_to_right method.
    DataFrame:
    Fips_Code Location extra_Location     1970     1971     1972     1973 \
        49000     Utah        1059273  1101000  1135000  1169000  1199000 \
            1974 extra_data_col_1 extra_data_col_2
            None             None             None
    1970 column data is shifted by 1 places to left and it will be right
    shifted by 1 place
    Args:
        county_data_df (pd.DataFrame): County Dataframe
        first_data_df_cols (list): List of Dataset Columns

    Some rows in DataFrame is merged as they were splitted into two rows
       Fips_Code Location extra_Location   1970  1971   1972  1973 \
           51097     King            and  Queen  None   None  None \
              Co.    5491           5500   5500  5700   5800  None \
                1974 extra_data_col_1 extra_data_col_2
                None             None             None
                None             None             None

    The above two rows will be merged and formed as below in single row
    DataFrame:
    Fips_Code Location extra_Location  1970  1971  1972  1973 \
        51097     King            and  5491  5500  5500  5700 \
                1974 extra_data_col_1 extra_data_col_2
                5800             None             None
    Returns:
        county_data_df (pd.DataFrame): Returns Transformed County dataframe
    """
    # Below idx values helps to merge two rows in DataFrame
    # depends on the dataset either 1980-89 or 1970-79
    if "1980" in first_data_df_cols:
        lr_idx, right_idx = 0, -1
    elif "1970" in first_data_df_cols:
        lr_idx, right_idx = -1, -2
    index_list = _get_char_index_in_col(county_data_df, "Fips_Code")
    county_data_df = _merge_rows(county_data_df, index_list, lr_idx, -9,
                                 right_idx)
    county_data_df = county_data_df.drop(index=index_list)
    county_data_df = county_data_df.reset_index().drop(columns=["index"])
    index_list = _get_numeric_index(county_data_df, "extra_Location")
    county_data_df = _move_data_to_right(county_data_df, index_list)
    county_data_df = county_data_df.reset_index().drop(columns=["index"])
    index_list = _get_nonna_index_for_extra_data_col_1(county_data_df)
    county_data_df = _move_data_to_left(county_data_df, index_list)
    county_data_df = county_data_df.reset_index().drop(columns=["index"])
    return county_data_df


def clean_1970_1989_county_txt(data_df: pd.DataFrame, first_data_df_cols: list,
                               second_data_df_cols: list) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists county data from 1970 to 1989

    Example Row that requires left shift using _move_data_to_left method.
    DataFrame:
    Fips_Code Location extra_Location 1970   1971   1972   1973 \
        01115      St.          Clair  Co.  27956  29500  31300 \
            1974    extra_data_col_1 extra_data_col_2
            32200              33700             None
    Because of extra delimiters Location column, the data is shifted right by 1
    index and will be to shifted left by 1 index value

    Below Example requires double left shift using _move_data_to_left func.
    DataFrame:
    Fips_Code Location extra_Location   1970   1971   1972   1973 \
        51093     Isle             of  Wight     Co  18285  19300 \
            1974   extra_data_col_1 extra_data_col_2
            19500             19800            20000
    Locaion Value is shifted by 2 places to right and so it will be left
    shifted twice

    Args:
        data_df (pd.DataFrame): Dataframe contains county data from 1970 to 1989
        first_data_df_cols (list): Columns List from 1970 to 1974 or
                                   1980 to 1984
        second_data_df_cols (list): Columns List from 1975 to 1979 or
                                    1985 to 1989

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """

    idx = data_df[data_df[0] == "FIPS"].index.values
    next_idx = 0
    final_data_df = None
    for first_idx, second_idx in zip(idx[::2], idx[1::2]):
        next_idx += 2
        if next_idx >= len(idx):
            end_idx = len(data_df)
        else:
            end_idx = idx[next_idx]
        initial_data_df = data_df.iloc[first_idx + 2:second_idx, :]
        next_data_df = data_df.iloc[second_idx + 2:end_idx, :]
        initial_data_df.reset_index().drop(columns=["index"])

        initial_data_df.columns = first_data_df_cols
        next_data_df.columns = second_data_df_cols
        initial_data_df = initial_data_df.reset_index().drop(columns=["index"])
        next_data_df = next_data_df.reset_index().drop(columns=["index"])
        initial_data_df = _clean_county_data_df(initial_data_df,
                                                first_data_df_cols)
        next_data_df = _clean_county_data_df(next_data_df, first_data_df_cols)
        if "1985" in second_data_df_cols:
            index_list = _get_char_index_in_col(next_data_df, "1985")
            # Shifting data to left starting from column at -2 index to -8
            next_data_df = _move_data_to_left(next_data_df, index_list, -8, -2)
        if "1980" in first_data_df_cols:
            index_list = _get_char_index_in_col(initial_data_df, "1980")
            if len(index_list) > 0:
                # Shifting data to left starting from column at -1 index to -8
                initial_data_df = _move_data_to_left(initial_data_df,
                                                     index_list, -8, -1)
                if initial_data_df.loc[index_list[0],
                                       "extra_data_col_2"] is not None:
                    # Shifting data to left starting
                    # from column at -1 index to -3
                    initial_data_df = _move_data_to_left(
                        initial_data_df, index_list, -3, -1)
        if "1970" in first_data_df_cols:
            index_list = _get_char_index_in_col(initial_data_df, "1970")
            if len(index_list) > 0:
                # Shifting data to left starting from column at -1 index to -7
                initial_data_df = _move_data_to_left(initial_data_df,
                                                     index_list, -7, -1)
                if initial_data_df.loc[index_list[0],
                                       "extra_data_col_2"] is not None:
                    # Shifting data to left starting from column at -3
                    #  index to -1
                    initial_data_df = _move_data_to_left(
                        initial_data_df, index_list, -3, -1)
        if "1975" in second_data_df_cols:
            index_list = _get_char_index_in_col(next_data_df, "1975")
            if len(index_list) > 0:
                # Shifting data to left starting from column at -1 index to -7
                next_data_df = _move_data_to_left(next_data_df, index_list, -7,
                                                  -1)
                if next_data_df.loc[index_list[0],
                                    "extra_data_col_2"] is not None:
                    # Shifting data to left starting from
                    # column at -1 index to -1
                    next_data_df = _move_data_to_left(next_data_df, index_list,
                                                      -3, -1)
        next_data_df = initial_data_df.merge(next_data_df,
                                             how="inner",
                                             on="Fips_Code",
                                             suffixes=("", "_right"))
        next_data_df["Location"] = next_data_df["Fips_Code"].apply(
            _get_fips_code)
        if final_data_df is None:
            final_data_df = next_data_df
        else:
            final_data_df = pd.concat([final_data_df, next_data_df], axis=0)
    final_cols = ["Location"
                 ] + first_data_df_cols[3:8] + second_data_df_cols[3:8]
    return final_data_df[final_cols]


def _create_final_file(op_tmp_file: str, search_string: str,
                       op_file: str) -> None:
    """
    Creates Final CSV File using files created
    thru _create_intermediate_file method
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
            state_name = alpha2todcid.USSTATE_MAP\
                            .get(items['Location'], items['Location'])
            for k, v in items.items():
                if k not in ['Location', '(census)', '1970']:
                    op.write("\n" + k + "," + state_name + "," +
                             v.replace(",", ""))


def _create_intermediate_file(ip_file: str, temp_file1: str, temp_file2: str,
                              search_string1: str, search_string2: str) -> None:
    """
    Reads txt file and creates Intermediate files
    which are further processed to create final CSV file
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


def process_states_1970_1979(file_path: str) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists states data from 1970 to 1989
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
        data_df = pd.read_csv("out.csv", header=0)
        os.remove("out.csv")
        return data_df


def process_states_1980_1989(file_path: str) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists
    States data from 1980 to 1989
    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
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

                    for year, val in dict(zip(cols, data)).items():
                        outfile.write(f"{year},{loc},{val}\n")
        data_df = pd.read_csv("out.csv", header=0)
        os.remove("out.csv")
        return data_df


def process_states_1990_1999(file_path: str) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists states data from 1990 to 1999
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
                # Skipping unwanted Lines
                if len(line.strip()) == 0:
                    continue
                # Skipping unwanted Lines
                if line.startswith("------"):
                    flag = True
                    continue
                # Skipping unwanted Lines
                if line.startswith("Documentation Notes"):
                    flag = False
                    continue
                # Skipping unwanted Lines
                if search_str1 in line.strip():
                    flag = True
                    cols = ["1999", "1998", "1997", "1996", "1995", "1994"]
                    continue
                # Skipping unwanted Lines
                if search_str2 in line.strip():
                    flag = True
                    cols = ["1993", "1992", "1991", "1990"]
                    continue
                # Processing the actual data rows
                if flag:
                    data = line.split(" ")
                    data = [val.strip() for val in data if val != '']
                    for idx, val in enumerate(data):
                        if val.isnumeric():
                            continue
                        if idx > 1:
                            data[1] = data[1] + val
                            data[idx] = ''
                    # Skiping extra empty spaces
                    data = [val.strip() for val in data if val != '']
                    loc = data[1]
                    if loc == "Alabama":
                        start = True
                    if start:
                        for year, val in dict(zip(cols, data[2:])).items():
                            outfile.write(f"{year},{loc},{val}\n")
                    if data[1] == "Wyoming":
                        start = False
        data_df = pd.read_csv("out.csv", header=0)
        os.remove("out.csv")
        return data_df


def process_states_1900_1969(states_config: dict, file_path: str,
                             file_name: str,
                             scaling_factor: int) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists states data from 1990 to 1999
    Args:
        states_config (dict): dict of states file config
        file_path (str): Input File Path
        file_name (str): Input File Name
        scaling_factor (int): Scaling factor to be multiplied

    Returns:
        data_df (DataFrame): Cleaned States Dataframe
    """
    conf = states_config[file_name]
    temp_file1 = conf['temp_file1']
    temp_file2 = conf['temp_file2']
    s1 = conf['search_string_1']
    s2 = conf['search_string_2']
    op_file_name = conf['op_file_name']
    final_file_path = op_file_name + ".csv"
    # Creating intermediates Files
    _create_intermediate_file(file_path, temp_file1, temp_file2, s1, s2)
    _create_final_file(temp_file1, s1, op_file_name)
    _create_final_file(temp_file2, s2, op_file_name)
    data_df = pd.read_csv(final_file_path, header=None)
    data_df.columns = ["Year", "Location", "Count_Person"]
    data_df["Count_Person"] = data_df["Count_Person"].multiply(scaling_factor)
    os.remove(temp_file1 + ".csv")
    os.remove(temp_file2 + ".csv")
    os.remove(final_file_path)
    return data_df
