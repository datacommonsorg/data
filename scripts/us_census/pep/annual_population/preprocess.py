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
City
    1990 - 2019     Processed As Is

County
    1970 - 2020     Processed As Is

State
    1900 - 2020     Processed As Is

National
    1900 - 1979     Processed As Is
    1980 - 1989     Data is available in County File in the year 1980-1989
    1990 - 1999     Data is available in State File in the year 1990-1999
    2000 - 2009     Data is available in State File in the year 2000-2009
    2010 - 2020     Processed As Is

Before running this module, run download.sh script, it downloads required
input files, creates necessary folders for processing.
Folder information
input_files - downloaded files (from US census website) are placed here
output_files - output files (mcf, tmcf and csv are written here)
"""

import os
import sys
import json
import warnings
import requests
import time
import re
from datetime import datetime as dt

warnings.filterwarnings('ignore')
import pandas as pd
from absl import app
from absl import logging
from absl import flags
from retry import retry

_FLAGS = flags.FLAGS

flags.DEFINE_string('mode', '', 'Options: download or process')
flags.DEFINE_bool(
    'is_summary_levels', False,
    'Options: True for all summary_levels and False for only 162')

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_INPUT_FILE_PATH = os.path.join(_MODULE_DIR, 'input_files')
os.makedirs(_INPUT_FILE_PATH, exist_ok=True)
excel_file_name_pattern = r"NST-EST(\d{4})-POP\.xlsx"
sys.path.insert(1, _MODULE_DIR)
# pylint: disable=wrong-import-position
# pylint: disable=import-error
from clean import (clean_data_df, clean_1970_1989_county_txt,
                   process_states_1900_1969, process_states_1970_1979,
                   process_states_1980_1989, process_states_1990_1999)

from constants import (INPUT_DIRS, OUTPUT_DIR, SCALING_FACTOR_STATE_1900_1960,
                       USA, USA_GEO_ID, DISTRICT_OF_COLUMBIA_STATE_CODE,
                       DISTRICT_OF_COLUMBIA_COUNTY_CODE, INPUT_DIR)

sys.path.insert(1, os.path.join(_MODULE_DIR, '../../../../'))
import util.alpha2_to_dcid as alpha2todcid
import util.name_to_alpha2 as statetoshortform
import util.county_to_dcid as countytodcid
# pylint: enable=wrong-import-position
# pylint: enable=import-error
_FILES_TO_DOWNLOAD = []

USSTATE_MAP = alpha2todcid.USSTATE_MAP
COUNTY_MAP = countytodcid.COUNTY_MAP
_USSTATE_SHORT_FORM = statetoshortform.USSTATE_MAP

_STATE_CONFIG_PATH = os.path.join(_MODULE_DIR, "states_config.json")
with open(_STATE_CONFIG_PATH, encoding="utf-8") as states_file:
    _STATE_CONFIG = json.load(states_file)

_MCF_TEMPLATE = ("Node: dcid:Count_Person\n"
                 "typeOf: dcs:StatisticalVariable\n"
                 "populationType: dcs:Person\n"
                 "statType: dcs:measuredValue\n"
                 "measuredProperty: dcs:count\n")

_TMCF_TEMPLATE = ("Node: E:USA_Annual_Population->E0\n"
                  "typeOf: dcs:StatVarObservation\n"
                  "variableMeasured: dcs:Count_Person\n"
                  "measurementMethod: dcs:CensusPEPSurvey\n"
                  "observationAbout: C:USA_Annual_Population->Location\n"
                  "observationDate: C:USA_Annual_Population->Year\n"
                  "observationPeriod: \"P1Y\"\n"
                  "value: C:USA_Annual_Population->Count_Person \n")


def _load_data_df(path: str,
                  file_format: str,
                  header: str = None,
                  skip_rows: int = None,
                  encoding: str = None) -> pd.DataFrame:
    """
    Returns the DataFrame using input path and config.
    Args:
        path (str): Input File Path
        file_format (str): Input File Format
        header (str, optional): Input File Header Index. Defaults to None.
        skip_rows (int, optional): Skip Rows Value. Defaults to None.
        encoding (str, optional): Input File Encoding. Defaults to None.

    Returns:
        data_df (pd.DataFrame): Dataframe of input file
    """
    data_df = None
    if file_format.lower().endswith("csv"):
        data_df = pd.read_csv(path, header=header, encoding=encoding)
    elif file_format.lower() == "txt":
        data_df = pd.read_table(path,
                                index_col=False,
                                delim_whitespace=True,
                                engine='python',
                                header=header,
                                skiprows=skip_rows)
    elif file_format.lower() in ["xls", "xlsx"]:
        data_df = pd.read_excel(path, header=header)
    return data_df


def _geo_id(val: pd.Series) -> str:
    """
    Returns GeoID for State Or County.
    Args:
        val (str): FIPS Code

    Returns:
        str: State/County GeoId
    """
    res = "geoId/"
    state, county = val[0], val[1]
    if county == "000":
        return res + state
    return res + state + county


def _state_to_county_geoid(data_df: pd.DataFrame) -> dict:
    if len(data_df.columns) == 1:
        if data_df.values.size == 1:
            return data_df.values[0][0]
        return data_df.values.squeeze()
    grouped = data_df.groupby(data_df.columns[0])

    d = {k: _state_to_county_geoid(g.iloc[:, 1:]) for k, g in grouped}
    return d


def _unpivot_data_df(data_df: pd.DataFrame,
                     id_col: list,
                     data_cols: list,
                     default_col="Year") -> pd.DataFrame:
    """
    Unpivot a DataFrame from wide to long format.
    Before Transpose,
    data_df:
    Location    2010    2011    2012    2013
    geoId/01   14890   15678   16012   16234
    geoId/02   13452   11980   12121   12432
    id_col: ["Location"]
    data_cols: ["2010", "2011", "2012", "2013"]
    default_col: "Year"
    Result data_df:
    Year    Location   Count_Person
    2010    geoId/01          14890
    2010    geoId/02          13452
    2011    geoId/01          15678
    2011    geoId/02          11980
    2012    geoId/01          14890
    2012    geoId/02          13452
    2013    geoId/01          15678
    2013    geoId/02          11980

    Args:
        data_df (pd.DataFrame): Dataframe with cleaned data
        common_col (list): Dataframe Column list
        data_cols (list): Dataframe Column list
    Returns:
        pd.DataFrame: Dataframe
    """
    res_data_df = pd.DataFrame()
    res_data_df = pd.melt(data_df,
                          id_vars=id_col,
                          value_vars=data_cols,
                          var_name=default_col,
                          value_name='Count_Person')
    return res_data_df


def _remove_initial_dot_values(val: str) -> str:
    if val[0] == '.':
        return val[1:]
    return val


def _process_csv_file(data_df: pd.DataFrame, area: str) -> pd.DataFrame:
    """
    Clean the DataFrame loaded for CSV file.
    Args:
        data_df (pd.DataFrame): Dataframe loaded with a dataset
        area (str): Value from the 1st Column of data_df

    Returns:
        pd.DataFrame: Cleaned Dataframe
    """
    data_idx = data_df[data_df[0] == area].index.values[0]
    data_df = data_df.iloc[data_idx - 1:, :]
    year_idx = data_idx - 1
    res_data_df = pd.DataFrame()
    for col in data_df.columns[1:]:
        usa_idx = 2
        tmp_data_df = data_df[[0, col]].iloc[data_idx - 1:usa_idx, :]
        tmp_data_df.columns = ["Location", "Count_Person"]
        year = data_df.iat[year_idx - 1, col]
        if str(year).isnumeric():
            tmp_data_df['Year'] = year
        elif len(year.split(",")) == 1:
            continue
        else:
            tmp_data_df['Year'] = (year.split(",")[1].strip())
        res_data_df = pd.concat([res_data_df, tmp_data_df])
    res_data_df = res_data_df.dropna(subset=["Count_Person"])
    for col in res_data_df.columns:
        res_data_df[col] = res_data_df[col].str.replace(
            ",", "", regex=False).str.replace(".", "", regex=False)
    res_data_df = res_data_df.reset_index().drop(columns=['index'])
    return res_data_df


def _states_full_to_short_form(data_df: pd.DataFrame,
                               data_col: str,
                               new_col: str,
                               replace_key: str = " ") -> pd.DataFrame:
    short_forms = _USSTATE_SHORT_FORM
    data_df[new_col] = data_df[data_col].str.replace(
        replace_key, "",
        regex=False).apply(lambda row: short_forms.get(row, row))
    return data_df


def _state_to_geo_id(state: str) -> str:
    return USSTATE_MAP.get(state, state)


def _add_geo_id(data_df: pd.DataFrame, data_col: str,
                new_col: str) -> pd.DataFrame:
    data_df[new_col] = data_df[data_col].apply(
        lambda rec: USSTATE_MAP.get(rec, pd.NA))
    data_df = data_df.dropna(subset=[new_col])
    return data_df


def _county_to_dcid(geo_id_dict: dict, state_abbr: str, county: str) -> str:
    """
    Takes the county name and the state code it's contained in, the dcid of the
    county is returned.
    Args:
        state_abbr: The alpha2 code of the state.
        county: The county name.
    Returns:
        The dcid of the county in DC. Returns an empty string if the county is
        not found.
    """
    if state_abbr in geo_id_dict:
        if county in geo_id_dict[state_abbr]:
            return geo_id_dict[state_abbr][county]
    return county


def _process_nationals_1900_1979(ip_file: str, op_file: str) -> None:
    """
    Process the nationals data for the year 1900-1979.
    Args:
        ip_file (str): Input File Path
        op_file (str): Output File Path
    """
    with open(op_file, 'w', encoding='utf-8') as national_pop_stats:
        national_pop_stats.write("Year,Location,Count_Person")
        with open(ip_file, encoding='utf-8') as ipfile:

            for line in ipfile.readlines():
                # Example:
                # July 1, 1999      272,690,813          2,442,810        0.90

                if line.startswith(" July 1"):
                    # Index 9 to 13 provides Year from the line
                    # and 14 to 30 provides the population count
                    year = int(line[9:13])
                    if year >= 1980:
                        continue
                    national_pop_stats.write(
                        "\n" + str(year) + ",country/USA," +
                        line[14:30].replace(",", "").lstrip().rstrip())


def _process_nationals_1980_1989(ip_file: str) -> pd.DataFrame:
    """
    Process the nationals data for the year 1980-1989.
    Args:
        ip_file (str): Input FIle Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    usa_rows = ""
    with open(ip_file, "r", encoding="UTF-8") as raw_file:
        data = raw_file.readlines()
        # Extracting below row from the data and clean it.
        # 00000 United States 226542250 229465744 231664432 233792014 235824908
        # 00000 United States 237923734 240132831 242288936 244499004 246819222
        for line in data:
            if "United States" in line:
                usa_rows += line.replace("00000", "").strip() + " "
        usa_cleaned_row = [
            int(val) for val in usa_rows.split(" ") if val.isnumeric()
        ]
        year = [
            "1980", "1981", "1982", "1983", "1984", "1985", "1986", "1987",
            "1988", "1989"
        ]
        geo_id = "country/USA"
        #df_cols = [["Year", "Count_Person"]
        data_df = pd.DataFrame(usa_cleaned_row, columns=["Count_Person"])
        data_df["Year"] = year
        data_df["Location"] = geo_id
    return data_df


def _process_nationals_1990_1999(ip_file: str) -> pd.DataFrame:
    """
    Process the nationals data for the year 1990-1999.
    Args:
        ip_file (str): Input FIle Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    data_df = _load_data_df(path=ip_file, file_format="csv", header=1)

    df_cols = [
        "Year", "Age", "Count_Person", "Count_Person_Male",
        "Count_Person_Female"
    ]
    data_df.columns = df_cols
    data_df = data_df[(data_df["Age"] == "All Age") &
                      (data_df["Year"].str.startswith("July"))].reset_index(
                          drop=True)
    data_df["Year"] = data_df["Year"].str.replace("July 1, ", "")
    data_df = data_df.drop(
        columns=["Age", "Count_Person_Male", "Count_Person_Female"])
    data_df["Location"] = "country/USA"
    data_df = data_df[["Year", "Location", "Count_Person"]]
    return data_df


def _process_nationals_2010_2020(ip_file: str, op_file: str) -> None:
    """
    Process the nationals data for the year 2010-2020.
    Args:
        ip_file (str): Input File Path
        op_file (str): Output File Path
    """
    with open(op_file, 'w', encoding='utf-8') as national_pop_stats:
        national_pop_stats.write("Year,Location,Count_Person")
        with open(ip_file, encoding='utf-8') as ipfile:
            for line in ipfile.readlines():
                if "POPESTIMATE2010" in line:
                    header = line.strip('\n').split(",")
                elif USA in line:
                    values = line.strip('\n').split(",")
        for k, v in dict(zip(header, values)).items():
            if "POPESTIMATE2" in k:
                # k contains values such as POPESTIMATE2010,POPESTIMATE2011,
                # POPESTIMATE2012 and index at [-4:] provides year value
                national_pop_stats.write("\n" + k[-4:] + ",country/USA," + v)


def _process_nationals_2020_2029(ip_file: str, op_file: str) -> None:
    """
    Process the nationals data for the year 2020-2022.
    Args:
        ip_file (str): Input File Path
        op_file (str): Output File Path
    """
    with open(op_file, 'w', encoding='utf-8') as national_pop_stats:
        national_pop_stats.write("Year,Location,Count_Person")
        with open(ip_file, encoding='utf-8') as ipfile:
            for line in ipfile.readlines():
                if "POPESTIMATE2020" in line:
                    header = line.strip('\n').split(",")
                elif USA in line:
                    values = line.strip('\n').split(",")
        for k, v in dict(zip(header, values)).items():
            if "POPESTIMATE2" in k:
                # k contains values such as POPESTIMATE2010,POPESTIMATE2011,
                # POPESTIMATE2012 and index at [-4:] provides year value
                national_pop_stats.write("\n" + k[-4:] + ",country/USA," + v)


def _process_nationals_2000_2009(file_path: str) -> pd.DataFrame:
    """
    Process the nationals data for the year 2000-2009.
    Args:
        file_path (str): Input FIle Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    data_df = pd.DataFrame()
    data_df = _load_data_df(path=file_path, file_format="csv", header=3)

    pop_cols = [
        "2000", "2001", "2002", "2003", "2004", "2005", "2006", "2007", "2008",
        "2009"
    ]
    df_cols = ["Region", "042000"] + pop_cols + ["042010", "072010"]
    data_df.columns = df_cols
    data_df = data_df[data_df["Region"] == USA]
    for col in pop_cols:
        data_df[col] = data_df[col].str.replace(",", "")

    data_df = _unpivot_data_df(data_df, ["Region"], pop_cols)
    data_df["Location"] = USA_GEO_ID
    return data_df


def _process_states_2000_2009(file_path: str) -> pd.DataFrame:
    """
    Process the states data for the year 2000-2009.
    Args:
        file_path (str): Input FIle Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    data_df = pd.DataFrame()
    data_df = _load_data_df(
        path=file_path,
        file_format="csv",
    )

    pop_cols = [str(yr) for yr in range(2000, 2010)]
    df_cols = ["Region", "042000"] + pop_cols + ["042010", "072010"]
    data_df.columns = df_cols
    for col in pop_cols:
        data_df[col] = data_df[col].str.replace(",", "")
    data_df = data_df.dropna()
    data_df['Region'] = data_df['Region'].apply(_remove_initial_dot_values)
    data_df = _states_full_to_short_form(data_df, "Region",
                                         "Location_short_form")
    data_df = _add_geo_id(data_df, "Location_short_form", "Location")
    data_df = _unpivot_data_df(data_df, ["Location"], pop_cols)
    return data_df


def _process_nationals_2021(file_path: str) -> pd.DataFrame:
    data_df = pd.DataFrame()
    data_df = _load_data_df(path=file_path, file_format="xlsx", header=3)
    df_cols = ["Location", "042020", "072020", "2021"]
    data_df.columns = df_cols
    data_df = data_df[data_df["Location"] == USA]
    data_df = _unpivot_data_df(data_df, ["Location"], ["2021"])
    data_df["Location"] = USA_GEO_ID
    return data_df


def _process_nationals_2029(file_path: str) -> pd.DataFrame:
    data_df = pd.DataFrame()
    data_df = _load_data_df(path=file_path, file_format="xlsx", header=3)
    df_cols = ["Location", "042020", "072020", "072021", "2022", "2023"]
    unpivot_cols = ["2022", "2023"]
    # extend df_cols & unpivot_cols with all years > 2023
    newly_added_years = [
        str(x)
        for x in data_df.columns.to_list()
        if isinstance(x, int) and x > 2023
    ]
    df_cols.extend(newly_added_years)
    unpivot_cols.extend(newly_added_years)
    data_df.columns = df_cols
    data_df = data_df[data_df["Location"] == USA]
    data_df = _unpivot_data_df(data_df, ["Location"], unpivot_cols)
    data_df["Location"] = USA_GEO_ID
    return data_df


def _process_states_2021(file_path: str) -> pd.DataFrame:
    """
    Process the nationals data for the year 2021.
    Args:
        file_path (str): Input FIle Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    data_df = pd.DataFrame()
    data_df = _load_data_df(path=file_path, file_format="xlsx", header=8)
    df_cols = ["Region", "042020", "072020", "2021"]
    data_df.columns = df_cols
    data_df["Region"] = data_df["Region"].str.replace(".", "", regex=False)
    data_df = _states_full_to_short_form(data_df, "Region",
                                         "Location_short_form")
    data_df = _add_geo_id(data_df, "Location_short_form", "Location")
    data_df = _unpivot_data_df(data_df, ["Location"], ["2021"])
    return data_df


def _process_states_2029(file_path: str) -> pd.DataFrame:
    """
    Process the state data from 2022 to 2029.
    Args:
        file_path (str): Input FIle Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    data_df = pd.DataFrame()
    df_cols = [
        "Region", "ignore_col1", "ignore_col2", "ignore_col3", "2022", "2023"
    ]
    unpivot_cols = ["2022", "2023"]
    try:
        # extend df_cols & unpivot_cols with all years > 2023
        year_column_row = _load_data_df(
            path=file_path, file_format="xlsx",
            header=0).iloc[2:3].values.flatten().tolist()
        if year_column_row:
            newly_added_years = [
                str(int(x))
                for x in year_column_row
                if isinstance(x, float) and x > 2023
            ]
            df_cols.extend(newly_added_years)
            unpivot_cols.extend(newly_added_years)
    except:
        # this error can be ignored
        pass
    data_df = _load_data_df(path=file_path, file_format="xlsx", header=8)
    data_df.columns = df_cols

    data_df["Region"] = data_df["Region"].str.replace(".", "", regex=False)
    data_df = _states_full_to_short_form(data_df, "Region",
                                         "Location_short_form")
    data_df = _add_geo_id(data_df, "Location_short_form", "Location")
    data_df = _unpivot_data_df(data_df, ["Location"], unpivot_cols)
    return data_df


def _process_county_file_99c8_00(file_path: str) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists
    county data for the year 1990 to 1999.
    Args:
        file_path (str): Input file path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    with open(file_path, encoding='ISO-8859-1') as ipfile:
        with open("outfile.csv", "w+", encoding="UTF-8") as outfile:
            outfile.write("Year,Location,Count_Person\n")
            for line in ipfile.readlines():
                if line.startswith("Block 2:"):
                    break
                if line[0].isnumeric():
                    tmp_line = line.strip().replace(",", "").replace(" ", ",")
                    while ",," in tmp_line:
                        tmp_line = tmp_line.replace(",,", ",")
                    tmp_line = tmp_line.split(",")
                    if tmp_line[-2] == "United":
                        continue
                    fips_code = "geoId/" + tmp_line[1]
                    years_list = list(range(2000, 1989, -1))
                    for idx, val in enumerate(years_list):
                        if idx == 0:
                            continue
                        outfile.write(
                            str(val) + ',' + str(fips_code) + "," +
                            str(tmp_line[idx + 2]) + "\n")
    data_df = pd.read_csv("outfile.csv")
    data_df = data_df[data_df["Location"] != "country/USA"]
    os.remove("outfile.csv")
    return data_df


def _process_county_e8089co_e7079co(file_path: str) -> pd.DataFrame:
    """
    Process DataFrame of County data for years 1970-1989.
    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    # skip_rows is helpful in skipping intial unwanted rows from the source.
    skip_rows = 23
    first_data_df_cols = [
        "Fips_Code", "Location", "extra_Location", "1970", "1971", "1972",
        "1973", "1974", "extra_data_col_1", "extra_data_col_2"
    ]
    second_data_df_cols = [
        "Fips_Code", "Location", "extra_Location", "1975", "1976", "1977",
        "1978", "1979", "extra_data_col_1", "extra_data_col_2"
    ]
    if "e8089co.txt" in file_path:
        skip_rows = 0
        first_data_df_cols = [
            "Fips_Code", "Location", "extra_Location", "1980", "1981", "1982",
            "1983", "1984", "extra_data_col_1", "extra_data_col_2"
        ]
        second_data_df_cols = [
            "Fips_Code", "Location", "extra_Location", "1985", "1986", "1987",
            "1988", "1989", "extra_data_col_1", "extra_data_col_2"
        ]
    data_df = _load_data_df(file_path, "txt", None, skip_rows)
    data_df = clean_1970_1989_county_txt(data_df, first_data_df_cols,
                                         second_data_df_cols)
    data_df = _unpivot_data_df(data_df, "Location", data_df.columns[1:])
    return data_df


def _process_county_coest2020(file_path: str) -> pd.DataFrame:
    """
    Process DataFrame of County data for year 2020.
    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    data_df = _load_data_df(file_path, "csv", header=0, encoding='ISO-8859-1')

    cols = [
        "STATE", "COUNTY", "STNAME", "CTYNAME", "POPESTIMATE2010",
        "POPESTIMATE2011", "POPESTIMATE2012", "POPESTIMATE2013",
        "POPESTIMATE2014", "POPESTIMATE2015", "POPESTIMATE2016",
        "POPESTIMATE2017", "POPESTIMATE2018", "POPESTIMATE2019",
        "POPESTIMATE042020", "POPESTIMATE2020"
    ]
    data_df = data_df[cols]
    # Modifying actual city name for State: District of Columbia
    # and City Name: District of Columbia. This is havind duplicate
    idx = data_df[(data_df["STATE"] == DISTRICT_OF_COLUMBIA_STATE_CODE) &
                  (data_df["COUNTY"] == DISTRICT_OF_COLUMBIA_COUNTY_CODE)]\
                      .index.values[0]
    data_df.loc[idx, "CTYNAME"] = "Washington County"

    data_df['COUNTY'] = data_df['COUNTY'].astype('str').str.pad(3,
                                                                side='left',
                                                                fillchar='0')
    data_df['STATE'] = data_df['STATE'].astype('str').str.pad(2,
                                                              side='left',
                                                              fillchar='0')

    data_df.insert(0, 'Location', data_df[["STATE", "COUNTY"]].apply(_geo_id,
                                                                     axis=1))
    if data_df.shape != data_df[data_df['Location'].str.startswith(
            'geo')].shape:
        logging.info(f"Check this file {file_path}")
    data_df.columns = data_df.columns.str.replace('POPESTIMATE', '')

    # Dropping Unwanted Columns
    data_df = data_df.drop(
        columns=["STATE", "COUNTY", "STNAME", "CTYNAME", "042020"])
    data_df = _unpivot_data_df(data_df, ["Location"], data_df.columns[1:])
    return data_df


def _process_county_coest2029(file_path: str) -> pd.DataFrame:
    """
    Process DataFrame of County data for year 2020.
    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    data_df = _load_data_df(file_path, "csv", header=0, encoding='ISO-8859-1')

    cols = ["STATE", "COUNTY", "STNAME", "CTYNAME"]
    popestimate_cols = [
        col for col in data_df.columns if str(col).startswith("POPESTIMATE")
    ]
    cols.extend(popestimate_cols)
    data_df = data_df[cols]
    # Modifying actual city name for State: District of Columbia
    # and City Name: District of Columbia. This is havind duplicate
    idx = data_df[(data_df["STATE"] == DISTRICT_OF_COLUMBIA_STATE_CODE) &
                  (data_df["COUNTY"] == DISTRICT_OF_COLUMBIA_COUNTY_CODE)]\
                      .index.values[0]
    data_df.loc[idx, "CTYNAME"] = "Washington County"

    data_df['COUNTY'] = data_df['COUNTY'].astype('str').str.pad(3,
                                                                side='left',
                                                                fillchar='0')
    data_df['STATE'] = data_df['STATE'].astype('str').str.pad(2,
                                                              side='left',
                                                              fillchar='0')

    data_df.insert(0, 'Location', data_df[["STATE", "COUNTY"]].apply(_geo_id,
                                                                     axis=1))
    if data_df.shape != data_df[data_df['Location'].str.startswith(
            'geo')].shape:
        logging.info(f"Check this file {file_path}")

    data_df.columns = data_df.columns.str.replace('POPESTIMATE', '')

    # Dropping Unwanted Columns
    data_df = data_df.drop(columns=["STATE", "COUNTY", "STNAME", "CTYNAME"])
    data_df = _unpivot_data_df(data_df, ["Location"], data_df.columns[1:])
    return data_df


def _process_counties(file_path: str) -> pd.DataFrame:
    """
    Processes County data and Returns DataFrame.
    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Processed County DataFrame
    """
    data_df = None
    future_year_file_list = [f"co-est{x}-alldata" for x in range(2024, 2030)]

    if "99c8_00.txt" in file_path:
        data_df = _process_county_file_99c8_00(file_path)
        data_df = data_df[data_df["Location"].str.len() != 8]
    elif "e8089co.txt" in file_path or "e7079co.txt" in file_path:
        data_df = _process_county_e8089co_e7079co(file_path)
        data_df = data_df[data_df["Location"].str.len() != 8]
    elif "co-est2020" in file_path:
        data_df = _process_county_coest2020(file_path)
    elif "co-est2023-alldata" in file_path:
        data_df = _process_county_coest2029(file_path)
    elif "co-est2021" in file_path:
        data_df = _load_data_df(file_path, "xlsx", header=4)
        data_df.columns = ["Region", "04_2020", "2020", "2021"]
        data_df = data_df.dropna(subset=["04_2020"])
        data_df["Region"] = data_df["Region"].apply(_remove_initial_dot_values)
        data_df["County"] = data_df["Region"].str.split(", ").str[0]
        data_df["State"] = data_df["Region"].str.split(", ").str[1]
        data_df = _states_full_to_short_form(data_df, "State", "State")
        data_df["Location"] = data_df.apply(
            lambda x: _county_to_dcid(COUNTY_MAP, x.State, x.County), axis=1)
        data_df = _unpivot_data_df(data_df, ["Location"], ["2020", "2021"])
    elif any([x for x in future_year_file_list if x in file_path]):
        data_df = _process_county_coest2029(file_path)
    elif "co-est" in file_path:
        data_df = _load_data_df(file_path, "csv", encoding='ISO-8859-1')
        data_df = clean_data_df(data_df, "csv")
        data_df = data_df.dropna(subset=[11, 12])
        cols = [
            "2000", "2001", "2002", "2003", "2004", "2005", "2006", "2007",
            "2008", "2009", "Location"
        ]
        geo, data_df = data_df[0], data_df.iloc[:, 2:12]

        data_df['Location'] = geo
        data_df.columns = cols
        data_df = data_df.reset_index().drop(columns=["index"])
        data_df["Location"] = data_df["Location"].apply(
            _remove_initial_dot_values)
        state = data_df.loc[0, 'Location']
        data_df['State'] = state
        data_df['State'] = data_df['State'].str.replace(" ", "", regex=False)
        data_df = _states_full_to_short_form(data_df, 'State', 'State')
        if state == "District of Columbia":
            data_df.loc[1, "Location"] = "Washington County"
        data_df["Location"] = data_df.apply(
            lambda x: _county_to_dcid(COUNTY_MAP, x.State, x.Location), axis=1)

        data_df.loc[0, 'Location'] = data_df.loc[0, 'State']
        data_df["Location"] = data_df["Location"].apply(_state_to_geo_id)
        data_df = data_df.iloc[1:, :]
        data_df = _unpivot_data_df(data_df, ["Location"], data_df.columns[:-2])
        data_df["Count_Person"] = data_df["Count_Person"].str.replace(
            ",", "", regex=False)
        data_df = data_df[["Year", "Location", "Count_Person"]]

    data_df = data_df[data_df["Location"] != "country/USA"]
    return data_df


def _process_city_1990_1999(file_path: str) -> pd.DataFrame:
    """
    Process DataFrame of County data for year 1990 to 1999
    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Processed City DataFrame
    """
    with open(file_path, "r", encoding="UTF-8") as ipfile:
        search_str1 = "7/1/99    7/1/98    7/1/97    7/1/96    7/1/95    7/1/94"
        search_str2 = "7/1/93    7/1/92    7/1/91    7/1/90      Base"
        with open("out.csv", "w", encoding="UTF-8") as outfile:
            outfile.write("Year,Location,Count_Person\n")
            cols = None
            flag = None
            for line in ipfile.readlines():
                # Skipping Unwanted Lines
                if len(line.strip()) == 0:
                    continue
                # Skipping Unwanted Lines
                if line.startswith("Block 2 of 2:") or line.startswith(
                        "Abbreviations:"):
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
                # Processing Actual data rows
                if flag:
                    data = line.split(" ")
                    data = [val.strip() for val in data if val != '']
                    if not data[1].isnumeric():
                        continue
                    # Mapping the below cities and geoId as per DataCommons
                    if data[1] == "76870" and data[2] == "Stanley":
                        data[1] = "76780"
                    if data[1] == "06242" and data[2] == "Beach":
                        data[1] = "06000"
                    loc = "geoId/" + f"{int(data[0]):02d}" \
                                   + f"{int(data[1]):05d}"
                    for year, val in dict(zip(cols, data[-len(cols):])).items():
                        outfile.write(f"{year},{loc},{val}\n")
        data_df = pd.read_csv("out.csv", header=0)
        os.remove("out.csv")
        return data_df


def _process_cities(file_path: str,
                    is_summary_levels: bool = False) -> pd.DataFrame:
    """
    Process DataFrame of Cities dataset
    Args:
        file_path (str): Input File Path
        is_summary_levels (bool): True for all Summary levels, False for Summary levels 162

    Returns:
        pd.DataFrame: Processed City DataFrame
    """
    data_df = None
    file_name_with_ext = os.path.basename(file_path)
    file_name_without_ext = os.path.splitext(file_name_with_ext)[0]
    if file_name_without_ext == 'su-99-7_us':
        data_df = _process_city_1990_1999(file_path)
    if file_name_without_ext in [
            "sub-est2010-alt", "SUB-EST2020_ALL", "sub-est2021_all"
    ] or file_name_without_ext.startswith("sub-est202"):
        data_df = _load_data_df(file_path,
                                file_format="csv",
                                header=0,
                                encoding="ISO-8859-1")
        # excluding SUMLEV=170 as no placed mapping in DC
        data_df = data_df[data_df['SUMLEV'] != 170]
        # drop place code 99990 codes
        data_df = data_df[data_df['PLACE'] != 99990]

        if not is_summary_levels:
            data_df = data_df[data_df['SUMLEV'] == 162]

        # generate FIPS code as perSUMLEV 040
        data_df['Location'] = data_df.apply(lambda x: _generate_fips_code(x),
                                            axis=1)

        data_df.dropna(subset=['Location'], inplace=True)

        key = "POPESTIMATE"
        if "sub-est2010-alt" == file_name_without_ext:
            key = "POPESTIMATE07"
        col_mapping = {}
        pop_cols = []
        df_cols = data_df.columns
        for c in df_cols:
            if c.startswith(key):
                yr = c.replace(key, '')
                if len(yr) == 4:
                    col_mapping[c] = yr
                    pop_cols.append(yr)

        data_df = data_df.rename(columns=col_mapping, errors="raise")
        final_cols = ["Location"] + pop_cols
        data_df = data_df[final_cols]
        data_df = _unpivot_data_df(data_df, ["Location"], pop_cols)

    return data_df


def _generate_fips_code(row_data) -> str:
    geo_id = None
    if row_data['SUMLEV'] == 40:
        geo_id = str(row_data['STATE']).zfill(2)
    elif row_data['SUMLEV'] == 50:
        geo_id = str(row_data['STATE']).zfill(2) + str(
            row_data['COUNTY']).zfill(3)
    elif row_data['SUMLEV'] == 61:
        geo_id = str(row_data['STATE']).zfill(2) + str(
            row_data['COUNTY']).zfill(3) + str(row_data['COUSUB']).zfill(5)
    elif row_data['SUMLEV'] in [71, 157, 162, 172]:
        geo_id = str(row_data['STATE']).zfill(2) + str(
            row_data['PLACE']).zfill(5)
    if geo_id:
        geo_id = "geoId/" + geo_id
    return geo_id


def _generate_mcf(mcf_file_path) -> None:
    """
    This method generates MCF file w.r.t
    dataframe headers and defined MCF template

    Returns:
        None
    """
    # Writing Genereated MCF to local path.
    with open(mcf_file_path, 'w+', encoding='utf-8') as f_out:
        f_out.write(_MCF_TEMPLATE.rstrip('\n'))


def _generate_tmcf(tmcf_file_path) -> None:
    """
    This method generates TMCF file w.r.t
    dataframe headers and defined TMCF template

    Returns:
        None
    """
    # Writing Genereated TMCF to local path.
    with open(tmcf_file_path, 'w+', encoding='utf-8') as f_out:
        f_out.write(_TMCF_TEMPLATE.rstrip('\n'))


def process(input_path, cleaned_csv_file_path: str, mcf_file_path: str,
            tmcf_file_path: str, is_summary_levels: bool):
    """
    This Method calls the required methods to generate cleaned CSV,
    MCF, and TMCF file
    """
    input_files = []
    input_files += [
        os.path.join(input_path, file)
        for file in sorted(os.listdir(input_path))
    ]

    final_df = pd.DataFrame()
    if not os.path.exists(os.path.dirname(cleaned_csv_file_path)):
        os.mkdir(os.path.dirname(cleaned_csv_file_path))
    processed_count = 0
    total_files_to_process = len(input_files)
    logging.info(f"No of files to be processed {len(input_files)}")

    try:
        for file in input_files:
            data_df = pd.DataFrame()
            file_name = os.path.basename(file)
            logging.info(f"Processing {file_name}")
            op_file = os.path.join(os.path.dirname(cleaned_csv_file_path),
                                   file_name.replace(".txt", ".csv"))
            if "popclockest.txt" in file:
                _process_nationals_1900_1979(file, op_file)
                data_df = _load_data_df(op_file, "csv", 0)
                os.remove(op_file)
            elif "us-est90int-08" in file:
                data_df = _process_nationals_1990_1999(file)
            elif "st-est00int-01" in file:
                nat_df = _process_nationals_2000_2009(file)
                state_df = _process_states_2000_2009(file)
                data_df = pd.concat([nat_df, state_df])
            elif "nst-est2020.csv" in file:
                _process_nationals_2010_2020(file, op_file)
                data_df = _load_data_df(op_file, "csv", 0)
                os.remove(op_file)
            elif "NST-EST2023-POPCHG2020_2023.csv" in file:
                _process_nationals_2020_2029(file, op_file)
                data_df = _load_data_df(op_file, "csv", 0)
                os.remove(op_file)
            elif "NST-EST2021-POP" in file:
                nat_df = _process_nationals_2021(file)
                state_df = _process_states_2021(file)
                data_df = pd.concat([nat_df, state_df])
            elif re.match(excel_file_name_pattern, file_name):
                nat_df = _process_nationals_2029(file)
                state_df = _process_states_2029(file)
                data_df = pd.concat([nat_df, state_df])
            elif file_name in [
                    "st0009ts.txt", "st1019ts.txt", "st2029ts.txt",
                    "st3039ts.txt", "st4049ts.txt", "st5060ts.txt",
                    "st6070ts.txt"
            ]:
                data_df = process_states_1900_1969(
                    _STATE_CONFIG, file, file_name,
                    SCALING_FACTOR_STATE_1900_1960)
            elif "st7080ts" in file:
                data_df = process_states_1970_1979(file)
            elif "st8090ts" in file:
                data_df = process_states_1980_1989(file)
                data_df["Location"] = data_df["Location"].apply(
                    _state_to_geo_id)
            elif "st-99-03" in file:
                data_df = process_states_1990_1999(file)
                data_df = _states_full_to_short_form(data_df, "Location",
                                                     "Location")
                data_df["Location"] = data_df["Location"].apply(
                    _state_to_geo_id)
            elif "e8089co.txt" in file:
                nat_df = _process_nationals_1980_1989(file)
                county_df = _process_counties(file)
                data_df = pd.concat([nat_df, county_df])
            elif file_name in ["e7079co.txt", "99c8_00.txt"
                              ] or "co-est" in file_name:
                data_df = _process_counties(file)
            elif file_name in [
                    'su-99-7_us.txt', "sub-est2010-alt.csv",
                    "SUB-EST2020_ALL.csv", "sub-est2021_all.csv"
            ] or file_name.startswith("sub-est202"):
                data_df = _process_cities(file, is_summary_levels)

            if not data_df.empty:
                processed_count += 1
                # data_df['len'] = data_df['Location'].astype(str).map(len)
                # geo_code_len = data_df['len'].unique()
                # if 13 in geo_code_len:
                #     pass
                final_df = pd.concat([final_df, data_df], axis=0)
            else:
                logging.error(f"Failed to process {file}")
    except Exception as e:
        logging.fatal(f"Error while processing files {e}")

    logging.info(f"No of files processed {processed_count}")
    if processed_count >= total_files_to_process & total_files_to_process > 0:
        final_df["Year"] = final_df["Year"].astype("int")
        final_df = final_df.sort_values(by=["Location", "Year"])
        final_df = final_df.drop_duplicates(["Year", "Location"])
        final_df["Count_Person"] = final_df["Count_Person"].astype("int")
        final_df[["Year", "Location",
                  "Count_Person"]].to_csv(cleaned_csv_file_path, index=False)
        _generate_mcf(mcf_file_path)
        _generate_tmcf(tmcf_file_path)
    else:
        logging.fatal(
            "The script has been terminated due to a mismatch between the number of files expected to be processed and the actual number processed"
        )


def add_future_year_urls():
    """ This method will generate future URLs specified in the urls_to_scan object.
        If valid URL, it will append to the _FILES_TO_DOWNLOAD global variable.

        Args: None
        Returns: None
    """
    global _FILES_TO_DOWNLOAD
    with open(os.path.join(_MODULE_DIR, 'input_url.json'), 'r') as inpit_file:
        _FILES_TO_DOWNLOAD = json.load(inpit_file)
    urls_to_scan = [
        "https://www2.census.gov/programs-surveys/popest/datasets/2020-{YEAR}/cities/totals/sub-est{YEAR}.csv",
        "https://www2.census.gov/programs-surveys/popest/datasets/2020-{YEAR}/counties/totals/co-est{YEAR}-alldata.csv",
        "https://www2.census.gov/programs-surveys/popest/tables/2020-{YEAR}/state/totals/NST-EST{YEAR}-POP.xlsx",
        "https://www2.census.gov/programs-surveys/popest/datasets/2020-{YEAR}/state/totals/NST-EST{YEAR}-POPCHG2020_{YEAR}.csv"
    ]
    # This method will get the latest year URLs available for the years 2023 to 2030
    for url in urls_to_scan:
        for future_year in range(2030, 2022, -1):
            url_to_check = url.format(YEAR=future_year)
            try:
                logging.info(f"checking furute url if available {url_to_check}")
                check_url = requests.head(url_to_check, allow_redirects=True)
                if check_url.status_code == 200:
                    logging.info(f"Furute url found {url_to_check}")
                    _FILES_TO_DOWNLOAD.append({"download_path": url_to_check})
                    break
            except:
                logging.error(f"URL is not accessable {url_to_check}")


@retry(tries=5, delay=5, backoff=5)
def download_with_retry(url, file_name_to_save):
    logging.info(f"Downloaded file : {file_name_to_save} - URL {url}")
    return requests.get(url=url, stream=True)


def download_files():
    """ This method will download data from the URLs specified in the input_url.json file.
        If any download attempt fails, the script will terminate.

        Args: None
        Returns: None
    """
    global _FILES_TO_DOWNLOAD
    if not os.path.exists(_INPUT_FILE_PATH):
        os.makedirs(_INPUT_FILE_PATH)
    try:
        for file_to_dowload in _FILES_TO_DOWNLOAD:
            file_name_to_save = None
            url = file_to_dowload['download_path']
            if 'file_name' in file_to_dowload and len(
                    file_to_dowload['file_name'] > 5):
                file_name_to_save = file_to_dowload['file_name']
            else:
                file_name_to_save = url.split('/')[-1]
            if 'file_path' in file_to_dowload:
                if not os.path.exists(
                        os.path.join(_INPUT_FILE_PATH,
                                     file_to_dowload['file_path'])):
                    os.makedirs(
                        os.path.join(_INPUT_FILE_PATH,
                                     file_to_dowload['file_path']))
                file_name_to_save = file_to_dowload[
                    'file_path'] + file_name_to_save

            response = download_with_retry(url, file_name_to_save)
            if response.status_code == 200:
                with open(os.path.join(_INPUT_FILE_PATH, file_name_to_save),
                          'wb') as f:
                    f.write(response.content)
                    file_to_dowload['is_downloaded'] = True

    except Exception as e:
        logging.fatal(f"Error occurred in download method {e}")


def main(_):
    mode = _FLAGS.mode
    is_summary_levels = _FLAGS.is_summary_levels

    # Defining Output file names
    data_file_path = os.path.join(_MODULE_DIR, OUTPUT_DIR)
    os.makedirs(data_file_path, exist_ok=True)
    cleaned_csv_path = os.path.join(data_file_path, "usa_annual_population.csv")
    mcf_path = os.path.join(data_file_path, "usa_annual_population.mcf")
    tmcf_path = os.path.join(data_file_path, "usa_annual_population.tmcf")

    if mode == "" or mode == "download":
        add_future_year_urls()
        download_files()
    if mode == "" or mode == "process":
        process(_INPUT_FILE_PATH, cleaned_csv_path, mcf_path, tmcf_path,
                is_summary_levels)


if __name__ == "__main__":
    app.run(main)
