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
This Python Script Load the datasets, cleans it
and generates cleaned csv, MCF, TMCF file
"""
import os

from copy import deepcopy
import pandas as pd

from absl import app
from absl import flags
from cols_map import (get_cols_dict, _get_nationals_1980_1999,
                      _get_nationals_2000_2009, _nationals_2010_2021,
                      _state_1980_1989, _state_1990_1999, _get_state_2010_2020,
                      _county_2000_2009, _county_2010_2020, _county_1900_1999)

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

FLAGS = flags.FLAGS
default_input_path = os.path.dirname(
    os.path.abspath(__file__)) + os.sep + "input_data"
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")


def _get_age_grp(age_grp: int) -> str:
    """
    Returns Age Groups using age_grp index as below
    0: ""
    1: 0To4
    2: 5To9
    3: 10To14
    ...
    ...
    85: 85
    Args:
        age_grp (int): Age Group Bucket Index

    Returns:
        str: Age Bucket Value
    """
    if age_grp == 0:
        return ""
    if age_grp == 85:
        return "85"
    start = 5 * (age_grp - 1)
    end = 5 * (age_grp) - 1
    return f"{start}To{end}"


def _get_age_grp2(age_grp: int) -> str:
    """
    Returns Age Groups using age_grp index as below
    0: "0"
    1: 1To4
    2: 5To9
    3: 10To14
    ...
    ...
    85: 85To89
    Args:
        age_grp (int): Age Group Bucket Index

    Returns:
        str: Age Bucket Value
    """
    if age_grp == 0:
        return "0"
    if age_grp == 1:
        return "1To4"
    start = 5 * (age_grp - 1)
    end = 5 * (age_grp) - 1
    return f"{start}To{end}"


def _add_measurement_method(df: pd.DataFrame, src_col: str,
                            tgt_col: str) -> pd.DataFrame:
    """Adds Measurement Method either CensusPEPSurvey or
    dcAggregate/CensusPEPSurvey to tgt_col column.
    Args:
        df (pd.DataFrame): Input DataFrame
        src_col (str): SV Column Name
        tgt_col (str): Measurement Method Column

    Returns:
        pd.DataFrame: DataFrame with New Columns
    """
    df[tgt_col] = df[src_col].str.split("_").str[-1]
    df[tgt_col] = df[tgt_col].str.replace(r"^(?!computed).*",
                                          "dcs:CensusPEPSurvey",
                                          regex=True)
    df[tgt_col] = df[tgt_col].str.replace('computed',
                                          "dcs:dcAggregate/CensusPEPSurvey",
                                          regex=False)
    df[src_col] = df[src_col].str.replace("_computed", "")
    return df


def _load_df(path: str,
             file_format: str,
             header: str = None,
             skip_rows: int = None,
             encoding: str = "UTF-8") -> pd.DataFrame:
    """
    Returns the DataFrame using input path and config
    Args:
        path (str): Input File Path
        file_format (str): Input File Format
        header (str, optional): Input File Header Index. Defaults to None.
        skip_rows (int, optional): Skip Rows Value. Defaults to None.
        encoding (str, optional): Input File Encoding. Defaults to None.

    Returns:
        df (pd.DataFrame): Dataframe of input file
    """
    df = None
    if file_format.lower() == "csv":
        df = pd.read_csv(path, header=header, encoding=encoding)
    elif file_format.lower() == "txt":
        df = pd.read_table(path,
                           index_col=False,
                           delim_whitespace=True,
                           engine='python',
                           header=header,
                           skiprows=skip_rows,
                           encoding=encoding)
    elif file_format.lower() in ["xls", "xlsx"]:
        df = pd.read_excel(path, header=header)
    return df


def _merge_df(df_1: pd.DataFrame, df_2: pd.DataFrame) -> pd.DataFrame:
    if df_1 is None:
        return df_2
    return pd.concat([df_1, df_2], axis=0)


def _transpose_df(df: pd.DataFrame,
                  common_col: list,
                  data_cols: list,
                  default_col="SV") -> pd.DataFrame:
    """
    Transpose the data_cols into single column named as default_col
    and concatinates the default_col with common_cols
    Args:
        df (pd.DataFrame): Dataframe with cleaned data
        common_col (list): Dataframe Column list
        data_cols (list): Dataframe Column list

    Returns:
        pd.DataFrame: Dataframe
    """
    res_df = pd.DataFrame()
    for col in data_cols:
        cols = common_col + [col]
        tmp_df = df[cols]
        tmp_df.columns = common_col + ["Count_Person"]
        tmp_df[default_col] = col
        res_df = pd.concat([res_df, tmp_df])
    return res_df


def _create_sv(desc: str, age: str) -> str:
    if age == 100:
        return f"Count_Person_{age}OrMoreYears_{desc}"
    if age == 85:
        return f"Count_Person_{age}OrMoreYears_{desc}"
    return f"Count_Person_{age}Years_{desc}"


def _process_nationals_1980_1989(file_path: str) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists
    national data for the year 1980-1989

    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    df = _load_df(file_path, "txt", header=None, skip_rows=1)
    # Extracting Year from the file name and adding '7'
    # to match the dataframe values
    yr = '7' + os.path.basename(file_path)[1:3]
    yr_100 = yr + '100'
    yr, yr_100 = int(yr), int(yr_100)
    yr_100_df = df[df[1] == yr_100].iloc[:, 1:].reset_index(drop=True)
    df = df[df[1] == yr].iloc[:, 1:].reset_index(drop=True)
    cols = [
        "Year", "Age", "Total_Population", "Total_Male_Population",
        "Total_Female_Population", "White_Male_Population",
        "White_Female_Population", "Black_Male_Population",
        "Black_Female_Population", "Male_AmericanIndianAndAlaskaNativeAlone",
        "Female_AmericanIndianAndAlaskaNativeAlone",
        "Male_AsianOrPacificIslander", "Female_AsianOrPacificIslander",
        "Male_HispanicOrLatino", "Female_HispanicOrLatino",
        "Male_WhiteAloneNotHispanicOrLatino",
        "Female_WhiteAloneNotHispanicOrLatino",
        "Male_NotHispanicOrLatino_Black", "Female_NotHispanicOrLatino_Black",
        "Male_NotHispanicOrLatino_AmericanIndianAndAlaskaNativeAlone",
        "Female_NotHispanicOrLatino_AmericanIndianAndAlaskaNativeAlone",
        "Male_NotHispanicOrLatino_AsianOrPacificIslander",
        "Female_NotHispanicOrLatino_AsianOrPacificIslander"
    ]
    hispanic_cols = _get_nationals_1980_1999("hispanic")
    derived_cols = _get_nationals_1980_1999("derived")
    df.columns = cols
    if yr_100_df.shape[0] > 0:
        yr_100_df.insert(0, 0, yr)
        yr_100_df[1] = 100
        yr_100_df = yr_100_df.drop(columns=[23])
        yr_100_df.columns = cols
        df = pd.concat([df, yr_100_df]).reset_index(drop=True)
    # Type casting dataframe values to int.
    for col in df.columns:
        df[col] = df[col].astype('int')
    # Creating Year Column
    df["Year"] = "19" + df["Year"].astype('str').str[-2:]
    # Deriving Columns for HispanicOrLatino Origin
    for dsv, sv in hispanic_cols.items():
        df[sv[1:]] = -df[sv[1:]]
        df[dsv] = df.loc[:, sv].sum(axis=1)
        df[sv[1:]] = -df[sv[1:]]
        cols.append(dsv)
    # Deriving New Columns
    for dsv, sv in derived_cols.items():
        df[dsv] = df.loc[:, sv].sum(axis=1)
        cols.append(dsv)
    f_cols = [val for val in cols if "Hispanic" in val]
    df = _transpose_df(df, ["Year", "Age"], f_cols)
    # Creating SV's name using SV, Age Column
    df["SV"] = df.apply(lambda row: _create_sv(row.SV, row.Age), axis=1)
    df["Location"] = "country/USA"
    final_cols = [
        "Year", "Location", "SV", "Measurement_Method", "Count_Person"
    ]
    # Deriving Measurement Method for the SV's
    df = _add_measurement_method(df, "SV", "Measurement_Method")
    return df[final_cols]


def _process_state_1990_1999(file_path):
    """
    Returns the Cleaned DataFrame consists
    state data for the year 1990-1999

    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    df = _load_df(file_path, "txt", header=None, skip_rows=15)
    cols = [
        "Year", "Location", "Age", "Male_WhiteAloneNotHispanicOrLatino",
        "Female_WhiteAloneNotHispanicOrLatino",
        "Male_NotHispanicOrLatino_Black", "Female_NotHispanicOrLatino_Black",
        "Male_NotHispanicOrLatino_AmericanIndianAndAlaskaNativeAlone",
        "Female_NotHispanicOrLatino_AmericanIndianAndAlaskaNativeAlone",
        "Male_NotHispanicOrLatino_AsianOrPacificIslander",
        "Female_NotHispanicOrLatino_AsianOrPacificIslander",
        "Male_HispanicOrLatino_WhiteAlone",
        "Female_HispanicOrLatino_WhiteAlone", "Male_HispanicOrLatino_Black",
        "Female_HispanicOrLatino_Black",
        "Male_HispanicOrLatino_AmericanIndianAndAlaskaNativeAlone",
        "Female_HispanicOrLatino_AmericanIndianAndAlaskaNativeAlone",
        "Male_HispanicOrLatino_AsianOrPacificIslander",
        "Female_HispanicOrLatino_AsianOrPacificIslander"
    ]
    df.columns = cols
    derived_cols = _state_1990_1999()
    # Deriving New Columns
    for dsv, sv in derived_cols.items():
        df[dsv] = df.loc[:, sv].sum(axis=1)
        cols.append(dsv)
    # Adding Leading Zeros for State's Fips Code.
    df["Location"] = df["Location"].astype('str').str.pad(width=2,
                                                          side="left",
                                                          fillchar="0")
    # Creating GeoId's using Fips Code
    df["Location"] = "geoId/" + df["Location"]
    f_cols = [val for val in cols if "Hispanic" in val]
    df = _transpose_df(df, ["Year", "Location", "Age"], f_cols)
    df["SV"] = df.apply(lambda row: _create_sv(row.SV, row.Age), axis=1)
    final_cols = [
        "Year", "Location", "SV", "Measurement_Method", "Count_Person"
    ]
    df = df.reset_index(drop=True)
    # Deriving Measurement Method for the SV's
    df = _add_measurement_method(df, "SV", "Measurement_Method")
    return df[final_cols]


def _process_nationals_2000_2009(file_path: str) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists
    nationals data for the year 2000-2009

    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    df = _load_df(file_path, "csv", header=0)
    df = df[(df["MONTH"] == 7) & (df["AGE"] != 999) &
            (df["YEAR"] != 2010)].reset_index(drop=True)
    cols = list(df.columns)
    # Mapping Dataset Headers to its FullForm
    cols_dict = get_cols_dict()
    for idx, val in enumerate(cols):
        cols[idx] = cols_dict.get(val, val)
    df.columns = cols
    derived_cols = _get_nationals_2000_2009()
    # Deriving New Columns
    for dsv, sv in derived_cols.items():
        df[dsv] = df.loc[:, sv].sum(axis=1)
        cols.append(dsv)
    f_cols = [val for val in cols if "Hispanic" in val]
    df = _transpose_df(df, ["Year", "Age"], f_cols)
    # Creating SV's name using SV, Age Columns
    df["SV"] = df.apply(lambda row: _create_sv(row.SV, row.Age), axis=1)
    df["Location"] = "country/USA"
    final_cols = [
        "Year", "Location", "SV", "Measurement_Method", "Count_Person"
    ]
    df = df.reset_index(drop=True)
    # Deriving Measurement Method for the SV's
    df = _add_measurement_method(df, "SV", "Measurement_Method")
    return df[final_cols]


def _process_state_2010_2020(file_path: str) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists
    state data for the year 2010-2020

    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    df = _load_df(file_path, "csv", header=0)
    df = df[(df["SEX"] != 0) & (df["ORIGIN"] != 0)].reset_index(drop=True)

    # Creating GeoId's for State FIPS Code
    df["STATE"] = "geoId/" + df["STATE"].astype("str").str.pad(
        width=2, side="left", fillchar="0")
    gender_dict = {1: "Male", 2: "Female"}
    origin_dict = {1: "NotHispanicOrLatino", 2: "HispanicOrLatino"}
    race_dict = {
        1: "WhiteAlone",
        2: "BlackOrAfricanAmericanAlone",
        3: "AmericanIndianAndAlaskaNativeAlone",
        4: "AsianAlone",
        5: "NativeHawaiianAndOtherPacificIslanderAlone",
        6: "TwoOrMoreRaces"
    }
    df["SEX"] = df["SEX"].map(gender_dict)
    df["ORIGIN"] = df["ORIGIN"].map(origin_dict)
    df["RACE"] = df["RACE"].map(race_dict)
    df["SV"] = df["SEX"] + '_' + df["ORIGIN"] + '_' + df["RACE"]
    df["SV"] = df["SV"].str.replace("NotHispanicOrLatino_WhiteAlone",
                                    "WhiteAloneNotHispanicOrLatino")
    req_cols = list(df.columns)
    req_cols = [req_cols[3]] + [req_cols[-1]] + [
        req_cols[8]
    ] + req_cols[11:21] + [req_cols[-2]]
    pop_cols = [val for val in req_cols if "POPESTIMATE" in val]
    # Deriving New Columns
    derived_cols_df = pd.DataFrame()
    derived_cols = _get_state_2010_2020("derived")
    for dsv, sv in derived_cols.items():
        flag = True
        for col in sv:
            tmp_derived_cols_df = df[df["SV"] == col][req_cols].reset_index(
                drop=True)
            if derived_cols_df.shape[0] == 0:
                derived_cols_df = tmp_derived_cols_df
            else:
                derived_cols_df[pop_cols] += tmp_derived_cols_df[pop_cols]
        if flag:
            derived_cols_df["SV"] = dsv
            df = df.append(derived_cols_df)
    # Deriving New Columns
    derived_cols_df = pd.DataFrame()
    derived_cols = _get_state_2010_2020("total")
    for dsv, sv in derived_cols.items():
        flag = True
        for col in sv:
            tmp_derived_cols_df = df[df["SV"] == col][req_cols].reset_index(
                drop=True)
            if derived_cols_df.shape[0] == 0:
                derived_cols_df = tmp_derived_cols_df
            else:
                derived_cols_df[pop_cols] += tmp_derived_cols_df[pop_cols]
        derived_cols_df["SV"] = dsv
        df = df.append(derived_cols_df)
    # Creating SV's name using SV, Age Column
    df["SV"] = df.apply(lambda row: _create_sv(row.SV, row.Age), axis=1)
    df = df[req_cols]
    req_cols = [
        col.replace("POPESTIMATE", "").replace("STATE", "Location")
        for col in req_cols
    ]
    df.columns = req_cols
    df = _transpose_df(df, req_cols[:2], req_cols[3:], default_col="Year")
    f_cols = ["Year", "Location", "SV", "Measurement_Method", "Count_Person"]
    df["Count_Person"] = df["Count_Person"].astype("int")
    # Deriving Measurement Method for the SV's
    df = _add_measurement_method(df, "SV", "Measurement_Method")
    return df[f_cols]


def _process_nationals_2010_2021(file_path: str) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists
    natioanls data for the year 2010-2021

    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    df = _load_df(file_path, "csv", header=0)
    df = df[(df["AGE"] != 999) & (df["MONTH"] == 7)].reset_index(drop=True)
    cols_dict = get_cols_dict()
    df.columns = df.columns.map(cols_dict)
    cols = df.columns.to_list()
    derived_cols = _nationals_2010_2021()
    # Deriving New Columns
    for dsv, sv in derived_cols.items():
        df[dsv] = df.loc[:, sv].sum(axis=1)
        cols.append(dsv)
    cols = ["Year", "Age"] + [col for col in cols if "Hispanic" in col]
    df = df[cols]
    df = _transpose_df(df, ["Year", "Age"], cols[2:])
    # Creating SV's name using SV, Age Column
    df["SV"] = df.apply(lambda row: _create_sv(row.SV, row.Age), axis=1)
    df["Location"] = "country/USA"
    df = df.drop(columns=["Age"])
    final_cols = [
        "Year", "Location", "SV", "Measurement_Method", "Count_Person"
    ]
    # Deriving Measurement Method for the SV's
    df = _add_measurement_method(df, "SV", "Measurement_Method")
    return df[final_cols]


def _process_state_1980_1989(file_path: str) -> str:
    """
    Returns the Cleaned DataFrame consists
    state data for the year 1980-1989

    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    df = _load_df(file_path, "txt", header=None)
    df[0] = df[0].astype('str').str.pad(width=5, side="left", fillchar="0")
    start, end = 0, 4
    pop_cols = []
    while True:
        age = f"{start}To{end}"
        if start == 85:
            pop_cols.append("85OrMore")
            break
        pop_cols.append(age)
        start += 5
        end += 5
    df.columns = [0] + pop_cols
    # Creating GeoId's for State FIPS Code
    df["Location"] = "geoId/" + df[0].str[:2]
    df["Year"] = "198" + df[0].str[2]
    df["Race"] = df[0].str[3]
    df["Sex"] = df[0].str[4]
    gender_dict = {'1': "Male", '2': "Female"}
    race_dict = {
        '1': "NotHispanicOrLatino_White",
        '2': "NotHispanicOrLatino_Black",
        '3': "NotHispanicOrLatino_AmericanIndianAndAlaskaNativeAlone",
        '4': "NotHispanicOrLatino_AsianOrPacificIslander",
        '5': "HispanicOrLatino_White",
        '6': "HispanicOrLatino_Black",
        '7': "HispanicOrLatino_AmericanIndianAndAlaskaNativeAlone",
        '8': "HispanicOrLatino_AsianOrPacificIslander",
    }
    df["Race"] = df["Race"].map(race_dict)
    df["Sex"] = df["Sex"].map(gender_dict)
    df = df.drop(columns=[0])
    df["SV"] = df["Sex"] + "_" + df["Race"]
    # Deriving New Columns
    derived_cols = _state_1980_1989()
    derived_cols_df = pd.DataFrame()
    df = df[["Year", "Location", "SV"] + pop_cols]
    for dsv, sv in derived_cols.items():
        flag = True
        for col in sv:
            derived_cols_tmp_df = df[df["SV"] == col].reset_index(drop=True)
            if derived_cols_df.shape[0] == 0:
                derived_cols_df = derived_cols_tmp_df
            else:
                derived_cols_df[pop_cols] += derived_cols_tmp_df[pop_cols]
        if flag:
            derived_cols_df["SV"] = dsv
            df = df.append(derived_cols_df)
    df = _transpose_df(df, ["Year", "Location", "SV"],
                       pop_cols,
                       default_col="Age")
    # Creating SV's name using SV, Age Column
    df["SV"] = df.apply(lambda row: _create_sv(row.SV, row.Age), axis=1)
    # Deriving Measurement Method for the SV's
    df = _add_measurement_method(df, "SV", "Measurement_Method")
    df = df[["Year", "Location", "SV", "Measurement_Method", "Count_Person"]]
    return df


def _process_state_2000_2010(file_path: str) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists
    state data for the year 2000-2010

    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    df = _load_df(file_path, "csv", header=0)
    df = df.drop(columns=["POPESTIMATE2010"])
    df = df[(df["STATE"] != 0)].reset_index(drop=True)
    df = df.reset_index()
    derived_cols_df = pd.DataFrame()
    for origin in [1, 2]:
        derived_cols_df = pd.concat([
            derived_cols_df, df[(df["ORIGIN"] == origin) & (df["SEX"] == 0) &
                                (df["RACE"] == 0) & (df["AGEGRP"] != 0)]
        ],
                                    ignore_index=True)
        # Deriving New Columns
        for sex in [0, 1, 2]:
            if sex == 0:
                for race in [1, 2, 3, 4, 5, 6]:
                    derived_cols_df = pd.concat([
                        derived_cols_df,
                        df[(df["ORIGIN"] == origin) & (df["SEX"] == 0) &
                           (df["RACE"] == race) & (df["AGEGRP"] != 0)]
                    ],
                                                ignore_index=True)
            else:
                derived_cols_df = pd.concat([
                    derived_cols_df, df[(df["ORIGIN"] == origin) &
                                        (df["SEX"] == sex) & (df["RACE"] == 0) &
                                        (df["AGEGRP"] != 0)]
                ],
                                            ignore_index=True)
    df = df[(df["SEX"] != 0) & (df["RACE"] != 0) & (df["ORIGIN"] != 0) &
            (df["AGEGRP"] != 0)].reset_index(drop=True)
    df = pd.concat([df, derived_cols_df], ignore_index=True)
    gender_dict = {0: "empty", 1: "Male", 2: "Female"}
    origin_dict = {1: "NotHispanicOrLatino", 2: "HispanicOrLatino"}
    race_dict = {
        0: "empty",
        1: "WhiteAlone",
        2: "BlackOrAfricanAmericanAlone",
        3: "AmericanIndianAndAlaskaNativeAlone",
        4: "AsianAlone",
        5: "NativeHawaiianAndOtherPacificIslanderAlone",
        6: "TwoOrMoreRaces"
    }
    df["RACE"] = df["RACE"].map(race_dict)
    df["ORIGIN"] = df["ORIGIN"].map(origin_dict)
    df["SEX"] = df["SEX"].map(gender_dict)
    df["SV"] = df["SEX"] + "_" + df["ORIGIN"] + "_" + df["RACE"]
    df["SV"] = df["SV"].str.replace("NotHispanicOrLatino_WhiteAlone",
                                    "WhiteAloneNotHispanicOrLatino")
    df["SV"] = df["SV"].str.replace("empty_", "").str.replace("_empty", "")
    df["Location"] = "geoId/" + df["STATE"].astype('str').str.pad(
        width=2, side="left", fillchar="0")
    cols = df.columns.to_list()
    # Creating Age Groups
    df["Age"] = df["AGEGRP"].apply(_get_age_grp)
    df["SV"] = df.apply(lambda row: _create_sv(row.SV, row.Age), axis=1)
    cols = ["Location", "SV"
           ] + [col for col in cols if col.startswith("POPESTIMATE")]
    df = df[cols]
    cols = [col.replace("POPESTIMATE", "") for col in cols]
    df.columns = cols
    df = _transpose_df(df, cols[:3], cols[3:], default_col="Year")
    df = df[["Year", "Location", "SV", "Count_Person"]]
    # Deriving Measurement Method for the SV's
    df = _add_measurement_method(df, "SV", "Measurement_Method")
    return df[["Year", "Location", "SV", "Measurement_Method", "Count_Person"]]


def _process_county_1990_1999(file_path: str) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists
    county data for the year 1990-1999

    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    f_list = []
    # Reading txt file and filtering required rows
    with open(file_path, "r", encoding="latin-1") as file:
        for lines in file.readlines():
            lines = lines.split(" ")
            lines = [line.strip() for line in lines if line.strip().isnumeric()]
            if len(lines) == 21:
                f_list.append(lines)
    df = pd.DataFrame(f_list)
    pop_cols = [
        "0To4", "5To9", "10To14", "15To19", "20To24", "25To29", "30To34",
        "35To39", "40To44", "45To49", "50To54", "55To59", "60To64", "65To69",
        "70To74", "75To79", "80To84", "85OrMore"
    ]
    df.columns = ["Year", "Location", "SV"] + pop_cols
    sv_dict = {
        '1': "Male_NotHispanicOrLatino_White",
        '2': "Female_NotHispanicOrLatino_White",
        '3': "Male_HispanicOrLatino_White",
        '4': "Female_HispanicOrLatino_White",
        '5': "Male_Black",
        '6': "Black_Female",
        '7': "Male_AmericanIndianAndAlaskaNativeAlone",
        '8': "Female_AmericanIndianAndAlaskaNativeAlone",
        '9': "Male_AsianOrPacificIslander",
        '10': "Female_AsianOrPacificIslander",
        '11': "Male_HispanicOrLatino",
        '12': "Female_HispanicOrLatino"
    }
    df["SV"] = df["SV"].map(sv_dict)
    # Deriving New Columns
    derived_df = pd.DataFrame()
    derived_cols = _county_1900_1999()
    for dsv, sv in derived_cols.items():
        flag = True
        for col in sv:
            derived_tmp_df = df[df["SV"] == col].reset_index(drop=True)
            if derived_df.shape[0] == 0:
                derived_df = derived_tmp_df
            else:
                derived_df[pop_cols] += derived_tmp_df[pop_cols]
        if flag:
            derived_df["SV"] = dsv
            df = df.append(derived_df)
    df = df.dropna()
    df = _transpose_df(df, ["Year", "Location", "SV"],
                       pop_cols,
                       default_col="Age")
    # Creating SV's name using SV, Age Column
    df["SV"] = df.apply(lambda row: _create_sv(row.SV, row.Age), axis=1)
    # Creating GeoId's for State FIPS Code
    df["Location"] = "geoId/" + df["Location"].astype("str").str.pad(
        width=5, side="left", fillchar="0")
    # Deriving Measurement Method for the SV's
    df = _add_measurement_method(df, "SV", "Measurement_Method")
    df = df[["Year", "Location", "SV", "Measurement_Method", "Count_Person"]]
    return df


def _process_county_2000_2009(file_path: str) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists
    county data for the year 2000-2009

    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    df = _load_df(file_path, "csv", header=0, encoding="latin-1")
    df = df[(~df["YEAR"].isin([1, 12, 13])) &
            (df["AGEGRP"] != 99)].reset_index(drop=True)
    df["YEAR"] = 1998 + df["YEAR"]

    cols = list(df.columns)
    # Mapping Dataset Headers to its FullForm
    cols_dict = get_cols_dict()
    for idx, val in enumerate(cols):
        cols[idx] = cols_dict.get(val, val)
    df.columns = cols
    df["STATE"] = df["STATE"].astype("str").str.pad(width=2,
                                                    side="left",
                                                    fillchar="0")
    df["COUNTY"] = df["COUNTY"].astype("str").str.pad(width=3,
                                                      side="left",
                                                      fillchar="0")
    df["Location"] = "geoId/" + df["STATE"] + df["COUNTY"]
    # Deriving New Columns
    derived_cols = _county_2000_2009()
    for dsv, sv in derived_cols.items():
        df[dsv] = df.loc[:, sv].sum(axis=1)
        cols.append(dsv)
    df["Age"] = df["AGEGRP"].apply(_get_age_grp2)
    f_cols = [val for val in cols if "Hispanic" in val]
    df = _transpose_df(df, ["Year", "Location", "Age"], f_cols)
    # Creating SV's name using SV, Age Column
    df["SV"] = df.apply(lambda row: _create_sv(row.SV, row.Age), axis=1)
    # Deriving Measurement Method for the SV's
    f_cols = ["Year", "Location", "SV", "Measurement_Method", "Count_Person"]
    df = _add_measurement_method(df, "SV", "Measurement_Method")
    return df[f_cols]


def _process_county_2010_2020(file_path: str) -> pd.DataFrame():
    """
    Returns the Cleaned DataFrame consists
    county data for the year 2010-2020

    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """

    df = _load_df(file_path, "csv", header=0, encoding='latin-1')
    df = df[(~df["YEAR"].isin([1, 2, 13])) &
            (df["AGEGRP"] != 0)].reset_index(drop=True)
    df["YEAR"] = df["YEAR"].astype('str').str.replace("14", "13").astype("int")
    df["YEAR"] = 2007 + df["YEAR"]
    # Mapping Dataset Headers to its FullForm
    cols_dict = get_cols_dict()
    cols = df.columns.to_list()
    for idx, val in enumerate(cols):
        cols[idx] = cols_dict.get(val, val)
    df.columns = cols
    df["STATE"] = df["STATE"].astype("str").str.pad(width=2,
                                                    side="left",
                                                    fillchar="0")
    df["COUNTY"] = df["COUNTY"].astype("str").str.pad(width=3,
                                                      side="left",
                                                      fillchar="0")
    df["Location"] = "geoId/" + df["STATE"] + df["COUNTY"]
    # Deriving New Columns
    derived_cols = _county_2010_2020()
    for dsv, sv in derived_cols.items():
        df[dsv] = df.loc[:, sv].sum(axis=1)
        cols.append(dsv)
    f_cols = [val for val in cols if "Hispanic" in val]
    df["Age"] = df["AGEGRP"].apply(_get_age_grp)
    df["Age"] = df["Age"].str.replace("85To89", "85OrMore")
    df = _transpose_df(df, ["Year", "Location", "Age"], f_cols)
    # Creating SV's name using SV, Age Column
    df["SV"] = df.apply(lambda row: _create_sv(row.SV, row.Age), axis=1)
    f_cols = ["Year", "Location", "SV", "Measurement_Method", "Count_Person"]
    # Deriving Measurement Method for the SV's
    df = _add_measurement_method(df, "SV", "Measurement_Method")
    return df[f_cols]


def _derive_nationals(df: pd.DataFrame) -> pd.DataFrame:
    df["Location"] = "country/USA"
    df = df.groupby(by=["Year", "Location", "SV", "Measurement_Method"]).agg({
        'Count_Person': 'sum'
    }).reset_index()
    return df


class USCensusPEPByASRH:
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files
    """

    def __init__(self, input_files: list, csv_file_path: str,
                 mcf_file_path: str, tmcf_file_path: str) -> None:
        self.input_files = input_files
        self.cleaned_csv_file_path = csv_file_path
        self.mcf_file_path = mcf_file_path
        self.tmcf_file_path = tmcf_file_path
        self.df = None
        self.file_name = None
        self.scaling_factor = 1

    def __generate_mcf(self, sv_list) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template
        Arguments:
            df_cols (list) : List of DataFrame Columns
        Returns:
            None
        """
        mcf_template = """Node: dcid:{}
typeOf: dcs:StatisticalVariable
populationType: dcs:Person{}{}{}{}
statType: dcs:measuredValue
measuredProperty: dcs:count
"""
        final_mcf_template = ""
        for sv in sv_list:
            if "Total" in sv:
                continue
            age = ''
            enthnicity = ''
            gender = ''
            race = ''
            sv_prop = sv.split("_")
            for prop in sv_prop:
                if prop in ["Count", "Person"]:
                    continue
                if "Years" in prop:
                    if "OrMoreYears" in prop:
                        age = "\nage: [" + prop.replace("OrMoreYears",
                                                        "") + " - Years]" + "\n"
                    elif "To" in prop:
                        age = "\nage: [" + prop.replace("Years", "").replace(
                            "To", " ") + " Years]" + "\n"
                    else:
                        age = "\nage: [Years " + prop.replace("Years",
                                                              "") + "]" + "\n"
                elif "Male" in prop or "Female" in prop:
                    gender = "gender: dcs:" + prop
                else:

                    if "race" in race:
                        race = race.strip() + "__" + prop + "\n"
                    else:
                        race = "race: dcs:" + prop + "\n"
            if gender == "":
                race = race.strip()
            final_mcf_template += mcf_template.format(sv, age, enthnicity, race,
                                                      gender) + "\n"
        # Writing Genereated MCF to local path.
        with open(self.mcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))

    def __generate_tmcf(self) -> None:
        """
        This method generates TMCF file w.r.t
        dataframe headers and defined TMCF template
        Arguments:
            df_cols (list) : List of DataFrame Columns
        Returns:
            None
        """
        tmcf_template = """Node: E:USA_Population_ASRH->E0
typeOf: dcs:StatVarObservation
variableMeasured: C:USA_Population_ASRH->SV
measurementMethod: C:USA_Population_ASRH->Measurement_Method
observationAbout: C:USA_Population_ASRH->Location
observationDate: C:USA_Population_ASRH->Year
observationPeriod: \"P1Y\"
value: C:USA_Population_ASRH->Count_Person 
"""

        # Writing Genereated TMCF to local path.
        with open(self.tmcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(tmcf_template.rstrip('\n'))

    def process(self):
        """
        This Method calls the required methods to generate cleaned CSV,
        MCF, and TMCF file
        """
        data_df = pd.DataFrame(columns=[[
            "Year", "Location", "SV", "Measurement_Method", "Count_Person"
        ]])
        # Creating Output Directory
        output_path = os.path.dirname(self.cleaned_csv_file_path)
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        sv_list = []
        f_names = []
        data_df.to_csv(self.cleaned_csv_file_path, index=False)
        for file_path in self.input_files:
            data_df = None
            if "sasr" in file_path:
                data_df = _process_state_1990_1999(file_path)
                if "sasrh" in file_path:
                    nat_df = _derive_nationals(deepcopy(data_df))
                    data_df = _merge_df(data_df, nat_df)
            elif "st-est00int-alldata" in file_path:
                data_df = _process_state_2000_2010(file_path)
            elif "SC-EST2020-ALLDATA6" in file_path:
                data_df = _process_state_2010_2020(file_path)
            elif "st_int_asrh" in file_path:
                data_df = _process_state_1980_1989(file_path)
            elif "CQI.TXT" in file_path:
                data_df = _process_nationals_1980_1989(file_path)
            elif "us-est00int-alldata" in file_path:
                data_df = _process_nationals_2000_2009(file_path)
            elif "NC-EST" in file_path:
                data_df = _process_nationals_2010_2021(file_path)
            elif "casrh" in file_path:
                data_df = _process_county_1990_1999(file_path)
            elif "co-est00int-alldata" in file_path:
                data_df = _process_county_2000_2009(file_path)
            elif "CC-EST2020" in file_path:
                data_df = _process_county_2010_2020(file_path)
            # Appending DataFrame to final CSV File
            data_df.to_csv(self.cleaned_csv_file_path,
                           mode="a",
                           header=False,
                           index=False)
            sv_list += data_df["SV"].to_list()

        sv_list = list(set(sv_list))
        sv_list.sort()
        self.__generate_mcf(sv_list)
        self.__generate_tmcf()
        print(f_names)


def main(_):
    input_path = FLAGS.input_path
    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]
    data_file_path = os.path.dirname(
        os.path.abspath(__file__)) + os.sep + "output"
    # Defining Output Files
    cleaned_csv_path = data_file_path + os.sep + "USA_Population_ASRH.csv"
    mcf_path = data_file_path + os.sep + "USA_Population_ASRH.mcf"
    tmcf_path = data_file_path + os.sep + "USA_Population_ASRH.tmcf"
    loader = USCensusPEPByASRH(ip_files, cleaned_csv_path, mcf_path, tmcf_path)
    loader.process()


if __name__ == "__main__":
    app.run(main)
