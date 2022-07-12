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
This module creates CSV files used for importing data into DC.
Below are list of files processed -
County
    1990 - 1999     Processed As Is
    2000 - 2009     Processed As Is
    2010 - 2020     Processed As Is
State
    1980 - 1989     Processed As Is
    1990 - 2999     Processed As Is
    2000 - 2009     Processed As Is
    2010 - 2020     Processed As Is
National
    1980 - 1989     Processed As Is
    1990 - 1999     Aggregted from State to National Level
    2000 - 2009     Processed As Is
    2010 - 2020     Processed As Is
Also SV aggregation are produced while processing above files.
E.g., Count_Person_10Years_White_HispanicOrLatino is calulated by addding
Count_Person_10Years_Male_WhiteHispanicOrLatino and
Count_Person_10Years_Female_WhiteHispanicOrLatino
Before running this module, run download.sh script, it downloads required
input files, creates necessary folders for processing.
Folder information
input_files - downloaded files (from US census website) are placed here
output_files - output files (mcf, tmcf and csv are written here)
"""

import os
from copy import deepcopy
import pandas as pd
import numpy as np
from absl import app
from cols_map import _get_mapper_cols_dict
from constants import INPUT_DIRS, INPUT_DIR

_CODEDIR = os.path.dirname(__file__)

_MCF_TEMPLATE = ("Node: dcid:{dcid}\n"
                 "typeOf: dcs:StatisticalVariable\n"
                 "populationType: dcs:Person\n"
                 "statType: dcs:measuredValue\n"
                 "measuredProperty: dcs:count\n"
                 "{xtra_pvs}")

_TMCF_TEMPLATE = (
    "Node: E:USA_Population_ASRH->E0\n"
    "typeOf: dcs:StatVarObservation\n"
    "variableMeasured: C:USA_Population_ASRH->SV\n"
    "measurementMethod: C:USA_Population_ASRH->Measurement_Method\n"
    "observationAbout: C:USA_Population_ASRH->Location\n"
    "observationDate: C:USA_Population_ASRH->Year\n"
    "observationPeriod: \"P1Y\"\n"
    "value: C:USA_Population_ASRH->Count_Person\n")


def _convert_to_int(data_df: pd.DataFrame) -> pd.DataFrame:
    for col in data_df.columns:
        data_df[col] = data_df[col].astype("int", errors="ignore")
    return data_df


def _derive_cols(data_df: pd.DataFrame, derived_cols: dict) -> pd.DataFrame:
    """
    Derive new columns using data_df and derived_cols dict
    Args:
        data_df (pd.DataFrame): Input DataFrame loaded with data.
        derived_cols (dict): derived_cols dict
                             where key represents dervied col and
                             values represents existing columns.

    Returns:
        pd.DataFrame: DataFrame
    """
    for dsv, sv in derived_cols.items():
        data_df[dsv] = data_df.loc[:, sv].apply(pd.to_numeric).sum(axis=1)
    return data_df


def _get_age_grp(age_grp: enumerate) -> str:
    """
    Returns Age Groups using age_grp index as below.
    0: ""
    1: 0To4
    2: 5To9
    3: 10To14
    ...
    ...
    18: 85
    Args:
        age_grp (int): Age Group Bucket Index

    Returns:
        str: Age Bucket Value
    """
    if age_grp == 0:
        return ""
    if age_grp == 18:
        return "85OrMore"
    start = 5 * (age_grp - 1)
    end = 5 * (age_grp) - 1
    return f"{start}To{end}"


def _get_age_grp_county_2000_2009(age_grp: enumerate) -> str:
    """
    Returns Age Groups using age_grp index as below,
    applies for country between years 2000 to 2009.
    0: "0"
    1: 1To4
    2: 5To9
    3: 10To14
    ...
    ...
    18: 85To89
    Args:
        age_grp (int): Age Group Bucket Index

    Returns:
        str: Age Bucket Value
    """
    if age_grp == 0:
        return "0"
    if age_grp == 1:
        return "1To4"
    if age_grp == 18:
        return "85OrMore"
    start = 5 * (age_grp - 1)
    end = 5 * (age_grp) - 1
    return f"{start}To{end}"


_COUNTY_2000_2009_INFO = {
    "year_range": "2000_2009",
    "exclude_year": [1, 12, 13],
    "exclude_age_grp": 99,
    "add_base_year": 1998,
    "derived_cols_string": "county_2000_2009",
    "replace_age_grp_from": "85To89",
    "replace_age_grp_to": "85",
    "age_grp_func": _get_age_grp_county_2000_2009
}

_COUNTY_2010_2020_INFO = {
    "year_range": "2010_2020",
    "exclude_year": [1, 2, 13],
    "exclude_age_grp": 0,
    "replace_year_from": "14",
    "replace_year_to": "13",
    "add_base_year": 2007,
    "derived_cols_string": "county_2010_2020",
    "replace_age_grp_from": "85To89",
    "replace_age_grp_to": "85",
    "age_grp_func": _get_age_grp
}


def _add_measurement_method(data_df: pd.DataFrame, src_col: str,
                            tgt_col: str) -> pd.DataFrame:
    """Adds Measurement Method either CensusPEPSurvey or
    dcAggregate/CensusPEPSurvey to tgt_col column.
    Args:
        data_df (pd.DataFrame): Input DataFrame
        src_col (str): SV Column Name
        tgt_col (str): Measurement Method Column

    Returns:
        pd.DataFrame: DataFrame with New Columns
    """
    data_df[tgt_col] = data_df[src_col].str.split("_").str[-1]
    data_df[tgt_col] = data_df[tgt_col].str.replace(r"^(?!computed).*",
                                                    "dcs:CensusPEPSurvey",
                                                    regex=True)
    data_df[tgt_col] = data_df[tgt_col].str.replace(
        "computed", "dcs:dcAggregate/CensusPEPSurvey", regex=False)

    # Dervied SV"s has "_computed" as part of the name,
    # to differentiate them with source generated SV"s
    # Removing "_computed" in the SV"s names.
    data_df[src_col] = data_df[src_col].str.replace("_computed", "")
    return data_df


def _measurement_conditions(sv: str, year: int) -> str:
    """
    Divides the Races before and after 2000, by using different measurement
    methods.
    Args:
        sv (str)  : SV Name
        int (str) : Year
    Returns:
        measurement_method (str) : Returns Measurement Method
    """
    measurement_method = ""
    if ((not sv.lower().endswith('male')) and
        (not sv.lower().endswith('latino') or
         "WhiteAloneNot" in sv)) and year >= 2000:
        measurement_method = "_Race2000Onwards"
    elif ((not sv.lower().endswith('male')) and
          (not sv.lower().endswith('latino') or
           "WhiteAloneNot" in sv)) and year < 2000:
        measurement_method = "_RaceUpto1999"
    else:
        measurement_method = ""
    return measurement_method


def _measurement_aggregate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Checks for aggregations done and makes all the years of that race and
    geographic location as Aggregated
    Args:
        df (pd.DataFrame) : Divided Dataframe to check
    Returns:
        df (pd.DataFrame) : DataFrame with Measurement Method
    """
    derived_df = df[df['Measurement_Method'].str.contains('dcAggregate')]
    aggregated_rows = set(derived_df['SV'] + derived_df['Location'])
    df['info'] = df['SV'] + df['Location']
    df['Measurement_Method'] = np.where(
        df['info'].isin(aggregated_rows),
        'dcs:dcAggregate/CensusPEPSurvey_PartialAggregate',
        df['Measurement_Method'])
    df = df.drop(columns=['info'])
    return df


def _measurement_method(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates measurement method based on provided guidlines.
    Args:
        df (pd.DataFrame) : Dataframe to add columns
    Returns:
        df (pd.DataFrame) : Dataframe with added columns
    """

    df = _measurement_aggregate(df)
    func = np.vectorize(_measurement_conditions)
    race_year = func(df['SV'], df['Year'].astype('int'))
    df['Measurement_Method'] = df['Measurement_Method'] + race_year
    return df


def _load_data_df(path: str,
                  file_format: str,
                  header: str = None,
                  skip_rows: int = None,
                  encoding: str = "UTF-8") -> pd.DataFrame:
    """
    Returns the DataFrame using input path and config.
    Args:
        path (str): Input File Path
        file_format (str): Input File Format [csv, txt, xls, xlsx]
        header (str, optional): Input Dataset Header Row Line Number.
        DataFrame will consider header value and make it as header.
        Defaults to None.
        skip_rows (int, optional): Skip Rows Value for txt files.
        This is helpful to skip initial rows in txt file.Defaults to None.
        encoding (str, optional): Input File Encoding while
        loading data into DataFrame.Defaults to None.

    Returns:
        data_df (pd.DataFrame): Dataframe of input file
    """
    data_df = None
    if file_format.lower() == "csv":
        data_df = pd.read_csv(path, header=header, encoding=encoding)
    elif file_format.lower() == "txt":
        data_df = pd.read_table(path,
                                index_col=False,
                                delim_whitespace=True,
                                engine="python",
                                header=header,
                                skiprows=skip_rows,
                                encoding=encoding)
    elif file_format.lower() in ["xls", "xlsx"]:
        data_df = pd.read_excel(path, header=header)
    data_df = _convert_to_int(data_df)
    return data_df


def _create_sv_with_age(desc: str, age: str) -> str:
    # Age 85+ and 100+ are represented as individual
    # age numbers such as  85, 100.
    # Adding "OrMoreYears" for 85 and 100 Ages.
    if age in {100, 85}:
        return f"Count_Person_{age}OrMoreYears_{desc}"
    return f"Count_Person_{age}Years_{desc}"


def _process_nationals_1980_1989(file_path: str) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists
    national data for the year 1980-1989.

    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    data_df = _load_data_df(path=file_path,
                            file_format="txt",
                            header=None,
                            skip_rows=1)
    # Extracting Year from the file name and adding "7" to it
    # to filter the dataframe as it provides
    # population estimates for april(4) and july(7) month.
    yr = "7" + os.path.basename(file_path)[1:3]
    # col at index 1 in DataFrame contains date values, example as below
    # 488, 488100,788,788100 where 4 or 7 represents month, 88 represents year,
    # 100 represents age.
    yr_100 = yr + "100"
    yr, yr_100 = int(yr), int(yr_100)
    # Age is at index 2 column, but for age 100, it is present in index 1
    # column as 788100, so filtering that row separately
    # and loading it to another DataFrame yr_100_data_df
    # yr_100_data_df contains rows with age 100
    yr_100_data_df = data_df[data_df[1] == yr_100].iloc[:, 1:].reset_index(
        drop=True)
    data_df = data_df[data_df[1] == yr].iloc[:, 1:].reset_index(drop=True)
    cols = [
        "Year", "Age", "Total_Population", "Total_Male_Population",
        "Total_Female_Population", "Male_WhiteAlone_Population",
        "Female_WhiteAlone_Population",
        "Male_BlackOrAfricanAmericanAlone_Population",
        "Female_BlackOrAfricanAmericanAlone_Population",
        "Male_AmericanIndianAndAlaskaNativeAlone",
        "Female_AmericanIndianAndAlaskaNativeAlone",
        "Male_AsianOrPacificIslander", "Female_AsianOrPacificIslander",
        "Male_HispanicOrLatino", "Female_HispanicOrLatino",
        "Male_WhiteAloneNotHispanicOrLatino",
        "Female_WhiteAloneNotHispanicOrLatino",
        "Male_NotHispanicOrLatino_BlackOrAfricanAmericanAlone",
        "Female_NotHispanicOrLatino_BlackOrAfricanAmericanAlone",
        "Male_NotHispanicOrLatino_AmericanIndianAndAlaskaNativeAlone",
        "Female_NotHispanicOrLatino_AmericanIndianAndAlaskaNativeAlone",
        "Male_NotHispanicOrLatino_AsianOrPacificIslander",
        "Female_NotHispanicOrLatino_AsianOrPacificIslander"
    ]
    data_df.columns = cols
    # Appending yr_100_data_df to data_df(which contains age for 1 to 99)
    if yr_100_data_df.shape[0] > 0:
        yr_100_data_df.insert(0, 0, yr)
        yr_100_data_df[1] = 100
        # column 23 has NAN value, and dropping that column
        yr_100_data_df = yr_100_data_df.drop(columns=[23])
        yr_100_data_df.columns = cols
        data_df = pd.concat([data_df, yr_100_data_df]).reset_index(drop=True)
    # Type casting dataframe values to int.
    data_df = _convert_to_int(data_df)
    # Creating Year Column
    data_df["Year"] = "19" + data_df["Year"].astype("str").str[-2:]
    hispanic_cols = _get_mapper_cols_dict("nationals_1980_1999_hispanic")
    # Deriving Columns for HispanicOrLatino Origin
    for dsv, sv in hispanic_cols.items():
        data_df[sv[1:]] = -data_df[sv[1:]]
        data_df[dsv] = data_df.loc[:, sv].sum(axis=1)
        data_df[sv[1:]] = -data_df[sv[1:]]
        cols.append(dsv)
    # Deriving New Columns
    derived_cols = _get_mapper_cols_dict("nationals_1980_1999_derived")
    data_df = _derive_cols(data_df, derived_cols)
    # Extracting columns having Hispanic and NotHispanic
    pop_cols = [
        val for val in cols + list(derived_cols.keys()) if "Hispanic" in val
    ]
    # Unpivot a DataFrame from wide to long format.
    # Before Transpose,
    # df:
    # Year    Age   HispaicOrLatino_Male  HispaicOrLatino_Female
    # 1999    1                    14890                   15678
    # 1999    2                    13452                   11980
    # id_col: ["Year", "Age"]
    # data_cols: ["HispaicOrLatino_Male", "HispaicOrLatino_Female"]
    # default_col: "SV"
    # Result df:
    # Year    Age                     SV  Count_Person
    # 1999    1     HispaicOrLatino_Male         14890
    # 1999    2     HispaicOrLatino_Male         13452
    # 1999    1   HispaicOrLatino_Female         15678
    # 1999    2   HispaicOrLatino_Female         11980
    data_df = pd.melt(data_df,
                      id_vars=["Year", "Age"],
                      value_vars=pop_cols,
                      var_name="SV",
                      value_name='Count_Person')
    # Creating SV"s name using SV, Age Column
    data_df["SV"] = data_df.apply(
        lambda row: _create_sv_with_age(row.SV, row.Age), axis=1)
    data_df["SV"] = data_df["SV"].str.replace("85OrMore", "85")
    data_df["Location"] = "country/USA"
    final_cols = [
        "Year", "Location", "SV", "Measurement_Method", "Count_Person"
    ]
    # Deriving Measurement Method for the SV"s
    data_df = _add_measurement_method(data_df, "SV", "Measurement_Method")
    return data_df[final_cols]


def _derive_nationals_1990_1999(data_df: pd.DataFrame) -> pd.DataFrame:
    data_df["Location"] = "country/USA"
    data_df = data_df.groupby(
        by=["Year", "Location", "SV", "Measurement_Method"]).agg({
            "Count_Person": "sum"
        }).reset_index()
    return data_df


def _process_nationals_2000_2009(file_path: str) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists
    nationals data for the year 2000-2009.

    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    data_df = _load_data_df(path=file_path, file_format="csv", header=0)
    # Considering Month = 7(July) and Skipping Age:999(Total Age)
    # Skipping Year: 2010
    data_df = data_df[(data_df["MONTH"] == 7) & (data_df["AGE"] != 999) &
                      (data_df["YEAR"] != 2010)].reset_index(drop=True)
    # data_df columns
    # 'MONTH', 'YEAR', 'AGE', 'TOT_POP', 'TOT_MALE', 'TOT_FEMALE', 'WA_MALE',
    # 'WA_FEMALE', 'BA_MALE', 'BA_FEMALE', 'IA_MALE', 'IA_FEMALE', 'AA_MALE',
    # 'AA_FEMALE', 'NA_MALE', 'NA_FEMALE', 'TOM_MALE', 'TOM_FEMALE',
    # 'NH_MALE', 'NH_FEMALE', 'NHWA_MALE', 'NHWA_FEMALE', 'NHBA_MALE',
    # 'NHBA_FEMALE', 'NHIA_MALE', 'NHIA_FEMALE', 'NHAA_MALE', 'NHAA_FEMALE',
    # 'NHNA_MALE', 'NHNA_FEMALE', 'NHTOM_MALE', 'NHTOM_FEMALE', 'H_MALE',
    # 'H_FEMALE', 'HWA_MALE', 'HWA_FEMALE', 'HBA_MALE', 'HBA_FEMALE',
    # 'HIA_MALE', 'HIA_FEMALE', 'HAA_MALE', 'HAA_FEMALE', 'HNA_MALE',
    # 'HNA_FEMALE', 'HTOM_MALE', 'HTOM_FEMALE'
    cols = list(data_df.columns)
    # Mapping Dataset Headers to its FullForm
    cols_mapper = _get_mapper_cols_dict("header_mappers")
    cols_with_full_name = []
    for val in cols:
        cols_with_full_name.append(cols_mapper.get(val, val))
    data_df.columns = cols_with_full_name
    derived_cols = _get_mapper_cols_dict("nationals_2000_2009")
    # Deriving New Columns
    data_df = _derive_cols(data_df, derived_cols)
    pop_cols = [
        val for val in cols_with_full_name + list(derived_cols.keys())
        if "Hispanic" in val
    ]
    data_df = pd.melt(data_df,
                      id_vars=["Year", "Age"],
                      value_vars=pop_cols,
                      var_name="SV",
                      value_name='Count_Person')
    # Creating SV"s name using SV, Age Columns
    data_df["SV"] = data_df.apply(
        lambda row: _create_sv_with_age(row.SV, row.Age), axis=1)
    data_df["Location"] = "country/USA"
    final_cols = [
        "Year", "Location", "SV", "Measurement_Method", "Count_Person"
    ]
    data_df = data_df.reset_index(drop=True)
    # Deriving Measurement Method for the SV"s
    data_df = _add_measurement_method(data_df, "SV", "Measurement_Method")
    return data_df[final_cols]


def _process_nationals_2010_2021(file_path: str) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists
    natioanls data for the year 2010-2021.

    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    data_df = _load_data_df(path=file_path, file_format="csv", header=0)
    # Considering Month = 7(July) and Skipping Age:999(Total Age)
    data_df = data_df[(data_df["AGE"] != 999) &
                      (data_df["MONTH"] == 7)].reset_index(drop=True)
    cols_mapper = _get_mapper_cols_dict("header_mappers")
    data_df.columns = data_df.columns.map(cols_mapper)
    cols = data_df.columns.to_list()
    derived_cols = _get_mapper_cols_dict("nationals_2010_2021")
    # Deriving New Columns
    data_df = _derive_cols(data_df, derived_cols)
    # Extracting columns having Hispanic and NotHispanic
    cols = ["Year", "Age"] + [
        col for col in cols + list(derived_cols.keys()) if "Hispanic" in col
    ]
    data_df = data_df[cols]
    data_df = pd.melt(data_df,
                      id_vars=["Year", "Age"],
                      value_vars=cols[2:],
                      var_name="SV",
                      value_name='Count_Person')
    # Creating SV"s name using SV, Age Column
    data_df["SV"] = data_df.apply(
        lambda row: _create_sv_with_age(row.SV, row.Age), axis=1)
    data_df["SV"] = data_df["SV"].str.replace("85OrMore", "85")
    data_df["Location"] = "country/USA"
    data_df = data_df.drop(columns=["Age"])
    final_cols = [
        "Year", "Location", "SV", "Measurement_Method", "Count_Person"
    ]
    # Deriving Measurement Method for the SV"s
    data_df = _add_measurement_method(data_df, "SV", "Measurement_Method")
    return data_df[final_cols]


def _process_state_1980_1989(file_path: str) -> str:
    """
    Returns the Cleaned DataFrame consists
    state data for the year 1980-1989.

    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    data_df = _load_data_df(path=file_path, file_format="txt", header=None)
    # Adding Leading Zeros for Fips Code in the zeroth column.
    #  Before padding STATE = 1006, After padding STATE = 01006
    data_df[0] = data_df[0].astype("str").str.pad(width=5,
                                                  side="left",
                                                  fillchar="0")
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
    data_df.columns = [0] + pop_cols
    # Creating GeoId"s for State FIPS Code
    # Sample data_df[0]: 06212
    # data_df[0]: geoId(0,1)_Year(2)_Race(3)_Sex(4)
    data_df["Location"] = "geoId/" + data_df[0].str[:2]
    data_df["Year"] = "198" + data_df[0].str[2]
    data_df["Race"] = data_df[0].str[3]
    data_df["Sex"] = data_df[0].str[4]
    gender_mapper = {"1": "Male", "2": "Female"}
    race_mapper = {
        "1": "WhiteAloneNotHispanicOrLatino",
        "2": "NotHispanicOrLatino_BlackOrAfricanAmericanAlone",
        "3": "NotHispanicOrLatino_AmericanIndianAndAlaskaNativeAlone",
        "4": "NotHispanicOrLatino_AsianOrPacificIslander",
        "5": "HispanicOrLatino_WhiteAlone",
        "6": "HispanicOrLatino_BlackOrAfricanAmericanAlone",
        "7": "HispanicOrLatino_AmericanIndianAndAlaskaNativeAlone",
        "8": "HispanicOrLatino_AsianOrPacificIslander",
    }
    data_df["Race"] = data_df["Race"].map(race_mapper)
    data_df["Sex"] = data_df["Sex"].map(gender_mapper)
    data_df = data_df.drop(columns=[0])
    data_df["SV"] = data_df["Sex"] + "_" + data_df["Race"]
    # Deriving New Columns
    # Type Casting the pop_cols to integer/float using pd.to_numeric function
    data_df[pop_cols] = data_df[pop_cols].apply(pd.to_numeric)
    derived_cols = _get_mapper_cols_dict("state_1980_1989")
    data_df = data_df[["Year", "Location", "SV"] + pop_cols]
    for dsv, sv in derived_cols.items():
        tmp_derived_cols_df = data_df[data_df["SV"].isin(sv)].reset_index(
            drop=True)
        tmp_derived_cols_df["SV"] = dsv
        tmp_derived_cols_df = tmp_derived_cols_df.groupby(
            ["Year", "Location", "SV"]).sum().reset_index()
        data_df = pd.concat([data_df, tmp_derived_cols_df])
    data_df = pd.melt(data_df,
                      id_vars=["Year", "Location", "SV"],
                      value_vars=pop_cols,
                      var_name="Age",
                      value_name='Count_Person')
    # Creating SV"s name using SV, Age Column
    data_df["SV"] = data_df.apply(
        lambda row: _create_sv_with_age(row.SV, row.Age), axis=1)
    # Deriving Measurement Method for the SV"s
    data_df = _add_measurement_method(data_df, "SV", "Measurement_Method")
    data_df = data_df[[
        "Year", "Location", "SV", "Measurement_Method", "Count_Person"
    ]]
    return data_df


def _process_state_1990_1999(file_path):
    """
    Returns the Cleaned DataFrame consists
    state data for the year 1990-1999.

    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    data_df = _load_data_df(path=file_path,
                            file_format="txt",
                            header=None,
                            skip_rows=15)
    cols = [
        "Year", "Location", "Age", "Male_WhiteAloneNotHispanicOrLatino",
        "Female_WhiteAloneNotHispanicOrLatino",
        "Male_NotHispanicOrLatino_BlackOrAfricanAmericanAlone",
        "Female_NotHispanicOrLatino_BlackOrAfricanAmericanAlone",
        "Male_NotHispanicOrLatino_AmericanIndianAndAlaskaNativeAlone",
        "Female_NotHispanicOrLatino_AmericanIndianAndAlaskaNativeAlone",
        "Male_NotHispanicOrLatino_AsianOrPacificIslander",
        "Female_NotHispanicOrLatino_AsianOrPacificIslander",
        "Male_HispanicOrLatino_WhiteAlone",
        "Female_HispanicOrLatino_WhiteAlone",
        "Male_HispanicOrLatino_BlackOrAfricanAmericanAlone",
        "Female_HispanicOrLatino_BlackOrAfricanAmericanAlone",
        "Male_HispanicOrLatino_AmericanIndianAndAlaskaNativeAlone",
        "Female_HispanicOrLatino_AmericanIndianAndAlaskaNativeAlone",
        "Male_HispanicOrLatino_AsianOrPacificIslander",
        "Female_HispanicOrLatino_AsianOrPacificIslander"
    ]
    data_df.columns = cols
    derived_cols = _get_mapper_cols_dict("state_1990_1999")
    # Deriving New Columns
    data_df = _derive_cols(data_df, derived_cols)

    # Adding Leading Zeros for State"s Fips Code.
    # Before padding Location = 6, After padding Location = 06
    data_df["Location"] = data_df["Location"].astype("str").str.pad(
        width=2, side="left", fillchar="0")
    # Creating GeoId"s using Fips Code
    data_df["Location"] = "geoId/" + data_df["Location"]
    # Extracting columns having Hispanic and NotHispanic
    pop_cols = [
        val for val in cols + list(derived_cols.keys()) if "Hispanic" in val
    ]
    data_df = pd.melt(data_df,
                      id_vars=["Year", "Location", "Age"],
                      value_vars=pop_cols,
                      var_name="SV",
                      value_name='Count_Person')
    data_df["SV"] = data_df.apply(
        lambda row: _create_sv_with_age(row.SV, row.Age), axis=1)
    final_cols = [
        "Year", "Location", "SV", "Measurement_Method", "Count_Person"
    ]
    data_df = data_df.reset_index(drop=True)
    # Deriving Measurement Method for the SV"s
    data_df = _add_measurement_method(data_df, "SV", "Measurement_Method")
    return data_df[final_cols]


def _process_state_2000_2010(file_path: str) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists
    state data for the year 2000-2010.

    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    data_df = _load_data_df(path=file_path, file_format="csv", header=0)
    data_df = data_df.drop(columns=["POPESTIMATE2010"])
    # STATE COLUMN with 0 value has national data,
    # So, skipping  the national data rows
    data_df = data_df[(data_df["STATE"] != 0)].reset_index(drop=True)
    data_df = data_df.reset_index()
    derived_cols_df = pd.DataFrame()
    gender_mapper = {0: "empty", 1: "Male", 2: "Female"}
    origin_mapper = {1: "NotHispanicOrLatino", 2: "HispanicOrLatino"}
    race_mapper = {
        0: "empty",
        1: "WhiteAlone",
        2: "BlackOrAfricanAmericanAlone",
        3: "AmericanIndianAndAlaskaNativeAlone",
        4: "AsianAlone",
        5: "NativeHawaiianAndOtherPacificIslanderAlone",
        6: "TwoOrMoreRaces"
    }
    # Deriving New Columns and actual values for below numbers are
    # represented in above dictonaries
    for origin in [1, 2]:
        derived_cols_df = pd.concat([
            derived_cols_df,
            data_df[(data_df["ORIGIN"] == origin) & (data_df["SEX"] == 0) &
                    (data_df["RACE"] == 0) & (data_df["AGEGRP"] != 0)]
        ],
                                    ignore_index=True)
        for sex in [0, 1, 2]:
            if sex == 0:
                for race in [1, 2, 3, 4, 5, 6]:
                    derived_cols_df = pd.concat([
                        derived_cols_df, data_df[(data_df["ORIGIN"] == origin) &
                                                 (data_df["SEX"] == 0) &
                                                 (data_df["RACE"] == race) &
                                                 (data_df["AGEGRP"] != 0)]
                    ],
                                                ignore_index=True)
            else:
                derived_cols_df = pd.concat([
                    derived_cols_df, data_df[(data_df["ORIGIN"] == origin) &
                                             (data_df["SEX"] == sex) &
                                             (data_df["RACE"] == 0) &
                                             (data_df["AGEGRP"] != 0)]
                ],
                                            ignore_index=True)
    data_df = data_df[(data_df["SEX"] != 0) & (data_df["RACE"] != 0) &
                      (data_df["ORIGIN"] != 0) &
                      (data_df["AGEGRP"] != 0)].reset_index(drop=True)
    data_df = pd.concat([data_df, derived_cols_df], ignore_index=True)
    data_df["RACE"] = data_df["RACE"].map(race_mapper)
    data_df["ORIGIN"] = data_df["ORIGIN"].map(origin_mapper)
    data_df["SEX"] = data_df["SEX"].map(gender_mapper)
    data_df[
        "SV"] = data_df["SEX"] + "_" + data_df["ORIGIN"] + "_" + data_df["RACE"]
    # Replacing NotHispanicOrLatino_WhiteAlone with
    # existing Datacommons PV WhiteAloneNotHispanicOrLatino
    data_df["SV"] = data_df["SV"].str.replace("NotHispanicOrLatino_WhiteAlone",
                                              "WhiteAloneNotHispanicOrLatino")
    data_df["SV"] = data_df["SV"].str.replace("empty_",
                                              "").str.replace("_empty", "")
    # Adding Leading Zeros for State"s Fips Code.
    # Before padding STATE = 6, After padding STATE = 06
    data_df["Location"] = "geoId/" + data_df["STATE"].astype("str").str.pad(
        width=2, side="left", fillchar="0")
    # data_df.columns
    # 'index', 'REGION', 'DIVISION', 'STATE', 'NAME', 'SEX', 'ORIGIN', 'RACE',
    # 'AGEGRP', 'ESTIMATESBASE2000', 'POPESTIMATE2000', 'POPESTIMATE2001',
    # 'POPESTIMATE2002', 'POPESTIMATE2003', 'POPESTIMATE2004',
    # 'POPESTIMATE2005', 'POPESTIMATE2006', 'POPESTIMATE2007',
    # 'POPESTIMATE2008', 'POPESTIMATE2009', 'CENSUS2010POP',
    # 'SV', 'Location'
    cols = data_df.columns.to_list()
    # Creating Age Groups
    data_df["Age"] = data_df["AGEGRP"].apply(_get_age_grp)
    data_df["SV"] = data_df.apply(
        lambda row: _create_sv_with_age(row.SV, row.Age), axis=1)
    req_cols = ["Location", "SV"
               ] + [col for col in cols if col.startswith("POPESTIMATE")]
    data_df = data_df[req_cols]
    pop_cols = [
        col.replace("POPESTIMATE", "")
        for col in req_cols
        if col.startswith("POPESTIMATE")
    ]
    data_df.columns = data_df.columns.str.replace("POPESTIMATE", "")
    # data_df Columns
    # ["Location", "SV", "2000", "2001", "2002", "2003",
    # "2004", "2005", "2006", "2007", "2008", "2009"]
    data_df = pd.melt(data_df,
                      id_vars=["Location", "SV"],
                      value_vars=pop_cols,
                      var_name="Year",
                      value_name='Count_Person')
    data_df = data_df[["Year", "Location", "SV", "Count_Person"]]
    # Deriving Measurement Method for the SV"s
    data_df = _add_measurement_method(data_df, "SV", "Measurement_Method")
    return data_df[[
        "Year", "Location", "SV", "Measurement_Method", "Count_Person"
    ]]


def _process_state_2010_2020(file_path: str) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists
    state data for the year 2010-2020.

    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    data_df = _load_data_df(path=file_path, file_format="csv", header=0)
    # SKipping Sex: 0, Origin: 0 which represents Total Count
    data_df = data_df[(data_df["SEX"] != 0) &
                      (data_df["ORIGIN"] != 0)].reset_index(drop=True)

    # Creating GeoId"s for State FIPS Code
    # Before padding STATE = 6, After padding STATE = 06
    data_df["STATE"] = "geoId/" + data_df["STATE"].astype("str").str.pad(
        width=2, side="left", fillchar="0")
    gender_mapper = {1: "Male", 2: "Female"}
    origin_mapper = {1: "NotHispanicOrLatino", 2: "HispanicOrLatino"}
    race_mapper = {
        1: "WhiteAlone",
        2: "BlackOrAfricanAmericanAlone",
        3: "AmericanIndianAndAlaskaNativeAlone",
        4: "AsianAlone",
        5: "NativeHawaiianAndOtherPacificIslanderAlone",
        6: "TwoOrMoreRaces"
    }
    data_df["SEX"] = data_df["SEX"].map(gender_mapper)
    data_df["ORIGIN"] = data_df["ORIGIN"].map(origin_mapper)
    data_df["RACE"] = data_df["RACE"].map(race_mapper)
    data_df[
        "SV"] = data_df["SEX"] + "_" + data_df["ORIGIN"] + "_" + data_df["RACE"]
    data_df["SV"] = data_df["SV"].str.replace("NotHispanicOrLatino_WhiteAlone",
                                              "WhiteAloneNotHispanicOrLatino")
    cols = list(data_df.columns)
    # data_df Columns
    # ["SUMLEV", "REGION", "DIVISION", "STATE", "NAME", "SEX", "ORIGIN",
    # "RACE", "AGE", "CENSUS2010POP", "ESTIMATESBASE2010", "POPESTIMATE2010",
    # "POPESTIMATE2011", "POPESTIMATE2012", "POPESTIMATE2013",
    # "POPESTIMATE2014", "POPESTIMATE2015", "POPESTIMATE2016",
    # "POPESTIMATE2017", "POPESTIMATE2018", "POPESTIMATE2019",
    # "POPESTIMATE042020", "POPESTIMATE2020", "SV"]
    column_indexes = {
        "STATE": 3,
        "SV": 23,
        "AGE": 8,
        "POPULATION_EST_2010_2019_START": 11,
        "POPULATION_EST_2010_2019_END": 21,
        "POPULATION_EST_2020": 22
    }
    req_cols = [cols[column_indexes["STATE"]]] + [
        cols[column_indexes["SV"]]
    ] + [cols[column_indexes["AGE"]]
        ] + cols[column_indexes["POPULATION_EST_2010_2019_START"]:
                 column_indexes["POPULATION_EST_2010_2019_END"]] + [
                     cols[column_indexes["POPULATION_EST_2020"]]
                 ]
    pop_cols = [val for val in req_cols if "POPESTIMATE" in val]
    # Deriving New Columns
    # Type Casting the pop_cols to integer/float using pd.to_numeric function
    data_df[pop_cols] = data_df[pop_cols].apply(pd.to_numeric)
    derived_cols = _get_mapper_cols_dict("state_2010_2020_hispanic")
    for dsv, sv in derived_cols.items():
        tmp_derived_cols_df = data_df[data_df["SV"].isin(
            sv)][req_cols].reset_index(drop=True)
        tmp_derived_cols_df["SV"] = dsv
        tmp_derived_cols_df = tmp_derived_cols_df.groupby(
            ["STATE", "SV", "AGE"]).sum().reset_index()
        data_df = pd.concat([data_df, tmp_derived_cols_df])
    # Deriving New Columns
    derived_cols = _get_mapper_cols_dict("state_2010_2020_total")
    for dsv, sv in derived_cols.items():
        tmp_derived_cols_df = data_df[data_df["SV"].isin(
            sv)][req_cols].reset_index(drop=True)
        tmp_derived_cols_df["SV"] = dsv
        tmp_derived_cols_df = tmp_derived_cols_df.groupby(
            ["STATE", "SV", "AGE"]).sum().reset_index()
        data_df = pd.concat([data_df, tmp_derived_cols_df])
    # Creating SV"s name using SV, Age Column

    data_df["SV"] = data_df.apply(
        lambda row: _create_sv_with_age(row.SV, row.AGE), axis=1)
    data_df = data_df[req_cols]
    req_cols = [
        col.replace("POPESTIMATE", "").replace("STATE", "Location")
        for col in req_cols
    ]
    data_df.columns = req_cols
    # data_df Columns or req_cols are below
    # ["Location", "SV", "AGE", "2010", "2011", "2012",
    # "2013", "2014", "2015", "2016", "2017", "2018", "2019", "2020"]
    data_df = pd.melt(data_df,
                      id_vars=["SV", "Location", "AGE"],
                      value_vars=req_cols[3:],
                      var_name="Year",
                      value_name='Count_Person')
    f_cols = ["Year", "Location", "SV", "Measurement_Method", "Count_Person"]
    data_df["Count_Person"] = data_df["Count_Person"].astype("int")
    # Deriving Measurement Method for the SV"s
    data_df = _add_measurement_method(data_df, "SV", "Measurement_Method")
    return data_df[f_cols]


def _process_county_1990_1999(file_path: str) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists
    county data for the year 1990-1999.

    Args:
        file_path (str): Input File Path.

    Returns:
        pd.DataFrame: Cleaned DataFrame.
    """
    final_data = []
    # Reading txt file and filtering required rows
    prev_origin_race_cat = None
    curr_origin_race_cat = None
    data = []
    skipped_rows = []
    with open(file_path, "r", encoding="latin-1") as file:
        for lines in file.readlines():
            lines = lines.split(" ")
            lines = [line.strip() for line in lines if line.strip().isnumeric()]
            if len(lines) == 21:
                data.append(lines)
                if prev_origin_race_cat is None:
                    prev_origin_race_cat = lines[2]
                elif curr_origin_race_cat is None:
                    curr_origin_race_cat = lines[2]
                if len(data) == 2:
                    # Row level aggregation is calculated
                    # thru pairs (1,2), (3,4) and (11,12)
                    # Dervied SV"s are below
                    # WhiteAloneNotHispanicOrLatino: 1 + 2
                    # HispanicOrLatino_WhiteAlone: 3 + 4
                    # HispanicOrLatino: 11 + 12
                    # Few rows were dropped due to unreadable characters,
                    # aggregation can be performed only when the pairs
                    # are available
                    if [prev_origin_race_cat,
                            curr_origin_race_cat] in [["1", "2"], ["3", "4"],
                                                      ["11", "12"]]:
                        final_data = final_data + data
                        data = []
                        prev_origin_race_cat = None
                        curr_origin_race_cat = None
                    else:
                        skipped_rows.append(data.pop(0))
                        prev_origin_race_cat = curr_origin_race_cat
                        curr_origin_race_cat = None
    data_df = pd.DataFrame(final_data)
    skipped_data_df = pd.DataFrame(skipped_rows)
    pop_cols = [
        "0To4", "5To9", "10To14", "15To19", "20To24", "25To29", "30To34",
        "35To39", "40To44", "45To49", "50To54", "55To59", "60To64", "65To69",
        "70To74", "75To79", "80To84", "85OrMore"
    ]
    data_df.columns = ["Year", "Location", "SV"] + pop_cols
    skipped_data_df.columns = ["Year", "Location", "SV"] + pop_cols
    sv_mapper = {
        "1": "Male_WhiteAloneNotHispanicOrLatino",
        "2": "Female_WhiteAloneNotHispanicOrLatino",
        "3": "Male_HispanicOrLatino_WhiteAlone",
        "4": "Female_HispanicOrLatino_WhiteAlone",
        "5": "Male_BlackOrAfricanAmericanAlone",
        "6": "Female_BlackOrAfricanAmericanAlone",
        "7": "Male_AmericanIndianAndAlaskaNativeAlone",
        "8": "Female_AmericanIndianAndAlaskaNativeAlone",
        "9": "Male_AsianOrPacificIslander",
        "10": "Female_AsianOrPacificIslander",
        "11": "Male_HispanicOrLatino",
        "12": "Female_HispanicOrLatino"
    }
    # Removing SV"s from 5 to 10 as they are not part of origin
    # HispanicOrlatino (or) NotHispanicOrLatino
    data_df = data_df[~data_df["SV"].isin(["5", "6", "7", "8", "9", "10"]
                                         )].reset_index(drop=True)
    skipped_data_df = skipped_data_df[~skipped_data_df["SV"].isin(
        ["5", "6", "7", "8", "9", "10"])].reset_index(drop=True)
    data_df["SV"] = data_df["SV"].map(sv_mapper)
    skipped_data_df["SV"] = skipped_data_df["SV"].map(sv_mapper)
    derived_cols = _get_mapper_cols_dict("county_1900_1999")
    data_df[pop_cols] = data_df[pop_cols].apply(pd.to_numeric)
    data = None
    for dsv, sv in derived_cols.items():
        data = data_df[data_df["SV"].isin(sv)].reset_index(drop=True)
        data["SV"] = dsv
        data = data.groupby(["Year", "Location", "SV"]).sum().reset_index()
        data_df = pd.concat([data_df, data])
    data_df = pd.concat([data_df, skipped_data_df])
    data_df = data_df.dropna()
    data_df = pd.melt(data_df,
                      id_vars=["Year", "Location", "SV"],
                      value_vars=pop_cols,
                      var_name="Age",
                      value_name='Count_Person')
    # Creating SV"s name using SV, Age Column
    data_df["SV"] = data_df.apply(
        lambda row: _create_sv_with_age(row.SV, row.Age), axis=1)
    # Creating GeoId"s for County FIPS Code
    # Before padding Location = 1001, After padding Location = 01001
    data_df["Location"] = "geoId/" + data_df["Location"].astype("str").str.pad(
        width=5, side="left", fillchar="0")
    # Deriving Measurement Method for the SV"s
    data_df = _add_measurement_method(data_df, "SV", "Measurement_Method")
    data_df = data_df[[
        "Year", "Location", "SV", "Measurement_Method", "Count_Person"
    ]]
    return data_df


def _process_county_2000_2020(file_path: str,
                              county_conf: dict) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists
    county data for the year 2000-2020.

    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    data_df = _load_data_df(path=file_path,
                            file_format="csv",
                            header=0,
                            encoding="latin-1")
    data_df = data_df[(~data_df["YEAR"].isin(county_conf["exclude_year"])) & (
        data_df["AGEGRP"] != county_conf["exclude_age_grp"])].reset_index(
            drop=True)
    if "replace_year_from" in county_conf.keys():
        data_df["YEAR"] = data_df["YEAR"].astype("str").str.replace(
            county_conf["replace_year_from"],
            county_conf["replace_year_to"]).astype("int")
    data_df["YEAR"] = county_conf["add_base_year"] + data_df["YEAR"]
    # Mapping Dataset Headers to its FullForm
    cols_mapper = _get_mapper_cols_dict("header_mappers")
    cols = data_df.columns.to_list()
    for idx, val in enumerate(cols):
        cols[idx] = cols_mapper.get(val, val)
    data_df.columns = cols
    # Adding Leading Zeros for State's Fips Code.
    #  Before padding STATE = 6, After padding STATE = 06
    data_df["STATE"] = data_df["STATE"].astype("str").str.pad(width=2,
                                                              side="left",
                                                              fillchar="0")
    # Adding Leading Zeros for County's Fips Code.
    # Before padding COUNTY = 20, After padding COUNTY = 020
    data_df["COUNTY"] = data_df["COUNTY"].astype("str").str.pad(width=3,
                                                                side="left",
                                                                fillchar="0")
    data_df["Location"] = "geoId/" + data_df["STATE"] + data_df["COUNTY"]
    # Deriving New Columns
    derived_cols = _get_mapper_cols_dict(county_conf["derived_cols_string"])
    data_df = _derive_cols(data_df, derived_cols)
    cols = cols + list(derived_cols.keys())
    f_cols = [val for val in cols if "Hispanic" in val]
    data_df["Age"] = data_df["AGEGRP"].apply(county_conf["age_grp_func"])
    if "replace_age_grp_from" in county_conf.keys():
        data_df["Age"] = data_df["Age"].str.replace(
            county_conf["replace_age_grp_from"],
            county_conf["replace_age_grp_to"])
    data_df = pd.melt(data_df,
                      id_vars=["Year", "Location", "Age"],
                      value_vars=f_cols,
                      var_name="SV",
                      value_name='Count_Person')
    data_df["SV"] = data_df.apply(
        lambda row: _create_sv_with_age(row.SV, row.Age), axis=1)
    f_cols = ["Year", "Location", "SV", "Measurement_Method", "Count_Person"]
    # Deriving Measurement Method for the SV"s
    data_df = _add_measurement_method(data_df, "SV", "Measurement_Method")
    return data_df[f_cols]


def _generate_mcf(sv_list, mcf_file_path) -> None:
    """
    This method generates MCF file w.r.t
    dataframe headers and defined MCF template
    Arguments:
        data_df_cols (list) : List of DataFrame Columns
    Returns:
        None
    """

    mcf_nodes = []
    for sv in sv_list:
        if "Total" in sv:
            continue
        pvs = []
        dcid = sv
        race = ""
        race_idx = 0
        sv_prop = sv.split("_")
        for prop in sv_prop:
            if prop in ["Count", "Person"]:
                continue
            if "Years" in prop:
                if "OrMoreYears" in prop:
                    pvs.append("age: [" + prop.replace("OrMoreYears", "") +
                               " - Years]")
                elif "To" in prop:
                    pvs.append("age: [" +
                               prop.replace("Years", "").replace("To", " ") +
                               " Years]")
                else:
                    pvs.append("age: [Years " + prop.replace("Years", "") + "]")
            elif "Male" in prop or "Female" in prop:
                pvs.append("gender: dcs:" + prop)
            else:

                if "race" in race:
                    race = pvs.pop(race_idx) + "__" + prop
                    pvs.append(race)
                else:
                    race = "race: dcs:" + prop
                    race_idx = len(pvs)
                    pvs.append(race)
        node = _MCF_TEMPLATE.format(dcid=dcid, xtra_pvs='\n'.join(pvs))
        mcf_nodes.append(node)
    # Writing Genereated MCF to local path.
    mcf = '\n'.join(mcf_nodes)
    with open(mcf_file_path, "w+", encoding="utf-8") as f_out:
        f_out.write(mcf.rstrip("\n"))


def _generate_tmcf(tmcf_file_path) -> None:
    """
    This method generates TMCF file w.r.t
    dataframe headers and defined TMCF template.
    Arguments:
        data_df_cols (list) : List of DataFrame Columns
    Returns:
        None
    """
    # Writing Genereated TMCF to local path.
    with open(tmcf_file_path, "w+", encoding="utf-8") as f_out:
        f_out.write(_TMCF_TEMPLATE.rstrip("\n"))


def process(input_files: list, cleaned_csv_file_path: str, mcf_file_path: str,
            tmcf_file_path: str):
    """
    This method generates cleaned CSV, MCF and tMCF files
    """
    # Creating Output Directory
    output_path = os.path.dirname(cleaned_csv_file_path)
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    sv_list = []
    data_df = pd.DataFrame(columns=[[
        "Year", "Location", "SV", "Measurement_Method", "Count_Person"
    ]])
    data_df.to_csv(cleaned_csv_file_path, index=False)
    for file_path in input_files:
        data_df = None
        if "sasr" in file_path:
            data_df = _process_state_1990_1999(file_path)
            if "sasrh" in file_path:
                nat_data_df = _derive_nationals_1990_1999(deepcopy(data_df))
                data_df = pd.concat([data_df, nat_data_df], axis=0)
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
            data_df = _process_county_2000_2020(file_path,
                                                _COUNTY_2000_2009_INFO)
        elif "CC-EST2020" in file_path:
            data_df = _process_county_2000_2020(file_path,
                                                _COUNTY_2010_2020_INFO)
        data_df = _convert_to_int(data_df)

        data_df.to_csv(cleaned_csv_file_path,
                       mode="a",
                       header=False,
                       index=False)
        sv_list += data_df["SV"].to_list()
    sv_list = list(set(sv_list))
    sv_list.sort()
    data_df = pd.read_csv(cleaned_csv_file_path, header=0)
    data_df = _measurement_method(data_df)
    data_df.to_csv(cleaned_csv_file_path, index=False)
    _generate_mcf(sv_list, mcf_file_path)
    _generate_tmcf(tmcf_file_path)


def main(_):
    ip_files = []
    for dir_path in INPUT_DIRS:
        files_dir = os.path.join(_CODEDIR, INPUT_DIR, dir_path)
        ip_files += [
            os.path.join(files_dir, file)
            for file in sorted(os.listdir(files_dir))
        ]
    #sys.exit(0)
    data_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "output_files")

    # Defining Output Files
    cleaned_csv_path = os.path.join(data_file_path, "usa_population_asrh.csv")
    mcf_path = os.path.join(data_file_path, "usa_population_asrh.mcf")
    tmcf_path = os.path.join(data_file_path, "usa_population_asrh.tmcf")
    process(ip_files, cleaned_csv_path, mcf_path, tmcf_path)


if __name__ == "__main__":
    app.run(main)
