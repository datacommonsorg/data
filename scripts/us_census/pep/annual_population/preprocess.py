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
import sys

import pandas as pd
from absl import app
from absl import flags

from state_to_geoid import USSTATE_MAP
from states_to_shortform import get_states
from county_to_dcid import COUNTY_MAP

from clean import (clean_df, clean_1970_1989_county_txt,
                   process_states_1900_1969, process_states_1970_1979,
                   get_state_file_config, process_states_1980_1989,
                   process_states_1990_1999)

pd.set_option("display.max_rows", None)

FLAGS = flags.FLAGS
default_input_path = os.path.dirname(
    os.path.abspath(__file__)) + os.sep + "input_data"

if ("ip_path" in sys.argv and len(sys.argv) > 2):
    default_input_path = sys.argv[2]
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")


def _load_df(path: str,
             file_format: str,
             header: str = None,
             skip_rows: int = None,
             encoding: str = None) -> pd.DataFrame:
    """

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
        #print(df)
    elif file_format.lower() == "txt":
        df = pd.read_table(path,
                           index_col=False,
                           delim_whitespace=True,
                           engine='python',
                           header=header,
                           skiprows=skip_rows)
        #print(df.head())
    elif file_format.lower() in ["xls", "xlsx"]:
        df = pd.read_excel(path, header=header)
    return df


def _find_file_format(path: str) -> str:
    return path[path.rfind('.') + 1:]


def _merge_df(df_1: pd.DataFrame, df_2: pd.DataFrame) -> pd.DataFrame:
    if df_1 is None:
        return df_2
    return pd.concat([df_1, df_2], axis=0)


def geo_id(val: str) -> str:
    res = "geoId/"
    state, county = val[0], val[1]
    if county == "000":
        return res + state
    return res + state + county


def _state_to_county_geoid(df: pd.DataFrame) -> dict:
    if len(df.columns) == 1:
        if df.values.size == 1:
            return df.values[0][0]
        return df.values.squeeze()
    grouped = df.groupby(df.columns[0])

    d = {k: _state_to_county_geoid(g.iloc[:, 1:]) for k, g in grouped}
    return d


def _transpose_df(df: pd.DataFrame, common_col: str,
                  data_cols: list) -> pd.DataFrame:
    """

    Args:
        df (pd.DataFrame): Dataframe with cleaned data
        common_col (str): Dataframe Column
        data_cols (list): Dataframe Column list

    Returns:
        pd.DataFrame: Dataframe with Location, Count_Person
    """
    res_df = pd.DataFrame()
    #print("df")
    #print(df.head())
    for col in data_cols:
        tmp_df = df[[common_col, col]]
        #print("tmp_df")
        #print(tmp_df.head())
        tmp_df.columns = ["Location", "Count_Person"]
        tmp_df["Year"] = col
        res_df = pd.concat([res_df, tmp_df])
    return res_df


def _remove_initial_dot_values(val: str) -> str:
    if val[0] == '.':
        return val[1:]
    return val


def _clean_csv(df: pd.DataFrame, area: str) -> pd.DataFrame:
    """

    Args:
        df (pd.DataFrame): Dataframe loaded with a dataset
        area (str): Value from the 1st Column of df

    Returns:
        pd.DataFrame: Cleaned Dataframe
    """
    data_idx = df[df[0] == area].index.values[0]
    df = df.iloc[data_idx - 1:, :]
    year_idx = data_idx - 1
    res_df = pd.DataFrame()
    for col in df.columns[1:]:
        usa_idx = 2
        tmp_df = df[[0, col]].iloc[data_idx - 1:usa_idx, :]
        tmp_df.columns = ["Location", "Count_Person"]
        year = df.iat[year_idx - 1, col]
        if str(year).isnumeric():
            tmp_df['Year'] = year
        elif len(year.split(",")) == 1:
            continue
        else:
            tmp_df['Year'] = (year.split(",")[1].strip())
        res_df = pd.concat([res_df, tmp_df])
    res_df = res_df.dropna(subset=["Count_Person"])
    for col in res_df.columns:
        res_df[col] = res_df[col].str.replace(",", "").str.replace(".", "")
    res_df = res_df.reset_index().drop(columns=['index'])
    return res_df


def _states_full_to_short_form(df: pd.DataFrame,
                               data_col: str,
                               new_col: str,
                               replace_key: str = " ") -> pd.DataFrame:
    short_forms = get_states()
    df[new_col] = df[data_col].str.replace(
        replace_key, "").apply(lambda row: short_forms.get(row, row))
    return df


def _state_to_geo_id(state: str) -> str:
    return USSTATE_MAP.get(state, state)


def _add_geo_id(df: pd.DataFrame, data_col: str, new_col: str) -> pd.DataFrame:
    df[new_col] = df[data_col].apply(lambda rec: USSTATE_MAP.get(rec, pd.NA))

    df = df.dropna(subset=[new_col])
    return df


def _shortform_to_geoid(df: pd.DataFrame) -> pd.DataFrame:
    df['Location'] = df['Short_Form'].apply(
        lambda rec: USSTATE_MAP.get(rec, pd.NA))
    df = df.dropna(subset=['Location'])
    return df


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


def _clean_nationals_1900_1999(ip_file: str, op_file: str) -> None:
    with open(op_file, 'w', encoding='utf-8') as national_pop_stats:
        national_pop_stats.write("Year,Location,Count_Person")
        with open(ip_file, encoding='utf-8') as file:
            for line in file.readlines():
                if line.startswith(" July 1"):
                    national_pop_stats.write(
                        "\n" + line[9:13] + ",country/USA," +
                        line[14:30].replace(",", "").lstrip().rstrip())


def _clean_nationals_2010_2020(ip_file: str, op_file: str) -> None:
    """

    Args:
        ip_file (str): Input File Path
        op_file (str): Output File Path
    """
    with open(op_file, 'w', encoding='utf-8') as national_pop_stats:
        national_pop_stats.write("Year,Location,Count_Person")
        with open(ip_file, encoding='utf-8') as file:
            for line in file.readlines():
                if line.find("POPESTIMATE2010") != -1:
                    header = line.strip('\n').split(",")
                elif line.find("United States") != -1:
                    values = line.strip('\n').split(",")
        for k, v in dict(zip(header, values)).items():
            if k.find('POPESTIMATE2') != -1:
                national_pop_stats.write("\n" + k[-4:] + ",country/USA," + v)


def _process_county_file_99c8_00(file_path: str) -> pd.DataFrame:
    """
    Args:
        file_path (str): Input file path

    Returns:
        pd.DataFrame: Dataframe with processed county
                      data from 1990 to 1999
    """
    df = None
    with open(file_path, encoding='ISO-8859-1') as file:
        with open("outfile.csv", "w+", encoding="UTF-8") as outfile:
            outfile.write("Year,Location,Count_Person\n")
            for line in file.readlines():
                if line.startswith("Block 2:"):
                    break
                if line[0].isnumeric():
                    tmp_line = line.strip().replace(",", "").replace(" ", ",")
                    while ",," in tmp_line:
                        tmp_line = tmp_line.replace(",,", ",")
                    tmp_line = tmp_line.split(",")
                    fips_code = None
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
    df = pd.read_csv("outfile.csv")
    df = df[df["Location"] != "country/USA"]
    os.remove("outfile.csv")
    return df


def _process_county_e8089co_e7079co(file_path: str) -> pd.DataFrame:
    """_summary_

    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Returns the Processed DataFrame of County data
                      for years 1970-1989
    """
    skip_rows = 23
    first_df_cols = [
        "Fips_Code", "Location", "Tmp_Row", "1970", "1971", "1972", "1973",
        "1974", "tmp1", "tmp2"
    ]
    second_df_cols = [
        "Fips_Code", "Location", "Tmp_Row", "1975", "1976", "1977", "1978",
        "1979", "tmp1", "tmp2"
    ]
    if "e8089co.txt" in file_path:
        skip_rows = 0
        first_df_cols = [
            "Fips_Code", "Location", "Tmp_Row", "1980", "1981", "1982", "1983",
            "1984", "tmp1", "tmp2"
        ]
        second_df_cols = [
            "Fips_Code", "Location", "Tmp_Row", "1985", "1986", "1987", "1988",
            "1989", "tmp1", "tmp2"
        ]
    df = _load_df(file_path, "txt", None, skip_rows)
    df = clean_1970_1989_county_txt(df, first_df_cols, second_df_cols)
    df = _transpose_df(df, "Location", df.columns[1:])
    return df


def _process_county_coest2020(file_path: str) -> pd.DataFrame:
    """
    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Returns the Processed DataFrame of County data
                      for year 2020
    """
    df = _load_df(file_path, "csv", header=0, encoding='ISO-8859-1')

    cols = [
        "STATE", "COUNTY", "STNAME", "CTYNAME", "POPESTIMATE2010",
        "POPESTIMATE2011", "POPESTIMATE2012", "POPESTIMATE2013",
        "POPESTIMATE2014", "POPESTIMATE2015", "POPESTIMATE2016",
        "POPESTIMATE2017", "POPESTIMATE2018", "POPESTIMATE2019",
        "POPESTIMATE042020", "POPESTIMATE2020"
    ]
    df = df[cols]
    idx = df[(df["STATE"] == 11) & df["COUNTY"] == 1].index.values[0]
    df.loc[idx, "CTYNAME"] = "Washington County"

    df['COUNTY'] = df['COUNTY'].astype('str').str.pad(3,
                                                      side='left',
                                                      fillchar='0')
    df['STATE'] = df['STATE'].astype('str').str.pad(2,
                                                    side='left',
                                                    fillchar='0')
    df['Location'] = df[["STATE", "COUNTY"]].apply(geo_id, axis=1)
    df.columns = df.columns.str.replace('POPESTIMATE', '')
    #geoId = df[["STNAME", "CTYNAME", "Location"]]
    df = df.drop(columns=["STATE", "COUNTY", "STNAME", "CTYNAME", "042020"])
    #print(geoId.head())
    df = _transpose_df(df, "Location", df.columns[:-1])

    return df


def _process_counties(file_path: str) -> pd.DataFrame:
    """

    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Processed County DataFrame
    """
    df = None

    if "99c8_00.txt" in file_path:
        df = _process_county_file_99c8_00(file_path)
        df = df[df["Location"].str.len() != 8]
    elif "e8089co.txt" in file_path or "e7079co.txt" in file_path:
        df = _process_county_e8089co_e7079co(file_path)
        df = df[df["Location"].str.len() != 8]
    elif "co-est2020" in file_path:
        df = _process_county_coest2020(file_path)
    elif "co-est2021" in file_path:
        df = _load_df(file_path, "xlsx", header=3)
        df.columns = ["Location", "tmp1", "tmp2", "2021"]
        df = _transpose_df(df, "Location", ["2021"])
        df = df.dropna(subset=["Count_Person"])
        df["Count_Person"] = df["Count_Person"].astype('int')
        df["Location"] = df["Location"].str.replace(".", "")
    elif "co-est" in file_path:
        df = _load_df(file_path, "csv", encoding='ISO-8859-1')
        df = clean_df(df, "csv")
        df = df.dropna(subset=[11, 12])
        cols = [
            "2000", "2001", "2002", "2003", "2004", "2005", "2006", "2007",
            "2008", "2009", "Location"
        ]
        geo, df = df[0], df.iloc[:, 2:12]
        df['Location'] = geo
        df.columns = cols
        df = df.reset_index().drop(columns=["index"])
        df["Location"] = df["Location"].apply(_remove_initial_dot_values)
        state = df.loc[0, 'Location']
        df['State'] = state
        df['State'] = df['State'].str.replace(" ", "")
        df = _states_full_to_short_form(df, 'State', 'State')
        if state == "District of Columbia":
            df.loc[1, "Location"] = "Washington County"
        df["Location"] = df.apply(
            lambda x: _county_to_dcid(COUNTY_MAP, x.State, x.Location), axis=1)
        #county_fips_code = county_geoid()
        #df["Location"] = df.apply(
        #    lambda x: _county_to_dcid(county_fips_code, x.State, x.Location),
        #    axis=1)
        df.loc[0, 'Location'] = df.loc[0, 'State']
        df["Location"] = df["Location"].apply(_state_to_geo_id)
        df = _transpose_df(df, "Location", df.columns[:-2])
        df["Count_Person"] = df["Count_Person"].str.replace(",", "")
        df = df[["Year", "Location", "Count_Person"]]
        #print(df.head())
    df = df[df["Location"] != "country/USA"]
    return df


def _first_non_zero_val(place: str, cousub: str, concit: str) -> str:
    """

    Args:
        place (str): PLACE FIPS Code
        cousub (str): COUSUB FIPS Code
        concit (str): CONCIT FIPS Code

    Returns:
        str: Returns First Non-Zero FIPS Code
    """
    if place not in ['00000', '99990']:
        return place
    if cousub not in ['00000', '99990']:
        return cousub
    return concit


def _get_city_geo_id(county: str, place: str, cousub: str, concit: str,
                     name: str) -> str:
    """

    Args:
        county (str): COUNTY FIPS Code
        place (str): PLACE FIPS Code
        cousub (str): COUSUB FIPS Code
        concit (str): CONCIT FIPS Code
        name (str): Name of the Area

    Returns:
        str: _description_
    """
    res = None
    if "county" in name.lower():
        return pd.NA
    if "census area" in name.lower():
        return pd.NA
    if "borough" in name.lower():
        res = _first_non_zero_val(place, cousub, concit)
    elif name.lower().endswith("borough"):
        res = _first_non_zero_val(place, cousub, concit)
    elif "city" in name.lower():
        res = _first_non_zero_val(place, cousub, concit)
    elif "township" in name.lower() or "CDP" in name.lower():
        res = _first_non_zero_val(place, cousub, concit)
    elif "town" in name.lower():
        res = _first_non_zero_val(place, cousub, concit)
    elif "village" in name.lower():
        res = _first_non_zero_val(place, cousub, concit)
    elif "municipality" in name.lower():
        res = _first_non_zero_val(place, cousub, concit)
    elif "metropolitan" in name.lower():
        res = _first_non_zero_val(place, cousub, concit)
    else:
        res = county + cousub
    return res


def _process_city_1990_1999(file_path: str) -> pd.DataFrame:
    """

    Args:
        file_path (str): Input File Path

    Returns:
        pd.DataFrame: Processed City DataFrame
    """
    with open(file_path, "r", encoding="UTF-8") as file:
        search_str1 = "7/1/99    7/1/98    7/1/97    7/1/96    7/1/95    7/1/94"
        search_str2 = "7/1/93    7/1/92    7/1/91    7/1/90      Base"
        with open("out.csv", "w", encoding="UTF-8") as outfile:
            outfile.write("Year,Location,Count_Person\n")
            cols = None
            flag = None
            for line in file.readlines():
                if len(line.strip()) == 0:
                    continue
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
                if flag:
                    #print(line)
                    data = line.split(" ")
                    data = [val.strip() for val in data if val != '']
                    if not data[1].isnumeric():
                        continue
                    if data[1] == "76870" and data[2] == "Stanley":
                        data[1] = "76780"
                    if data[1] == "06242" and data[2] == "Beach":
                        data[1] = "06000"
                    loc = "geoId/" + f"{int(data[0]):02d}" \
                                   + f"{int(data[1]):05d}"
                    for year, val in dict(zip(cols, data[-len(cols):])).items():
                        outfile.write(f"{year},{loc},{val}\n")
        df = pd.read_csv("out.csv", header=0)
        os.remove("out.csv")
        return df


def _process_cities(file_path: str, file_name: str) -> pd.DataFrame:
    """

    Args:
        file_path (str): Input File Path
        file_name (str): Input File Name

    Returns:
        pd.DataFrame: Processed City DataFrame
    """
    df = None
    if file_name in ['su-99-7_us.txt']:
        df = _process_city_1990_1999(file_path)
    if "sub-est2010-alt" in file_name or "sub-est2019_all" in file_name:
        df = _load_df(file_path,
                      file_format="csv",
                      header=0,
                      encoding="ISO-8859-1")
        df = df[df["SUMLEV"] == 162]
        #res_df = df.sort_values(by=[
        #    "STATE", "COUNTY", "PLACE", "COUSUB", "CONCIT", "NAME", "STNAME"
        #])
        #res_df.to_csv("sort_by.csv", index=False)
        df['STATE'] = df['STATE'].astype('str').str.pad(2,
                                                        side='left',
                                                        fillchar='0')
        #df['COUNTY'] = df['COUNTY'].astype('str').str.pad(3,
        #                                                  side='left',
        #                                                  fillchar='0')
        df['PLACE'] = df['PLACE'].astype('str').str.pad(5,
                                                        side='left',
                                                        fillchar='0')
        #df['COUSUB'] = df['COUSUB'].astype('str').str.pad(5,
        #                                                  side='left',
        #                                                  fillchar='0')
        #df['CONCIT'] = df['CONCIT'].astype('str').str.pad(5,
        #                                                  side='left',
        #                                                  fillchar='0')
        #df["PLACE"] = df["PLACE"].str.replace("99990", "00000")
        #df["Location"] = df.apply(
        #    lambda row: "geoId/" + row.STATE + _get_city_geo_id(
        #        row.COUNTY, row.PLACE, row.COUSUB, row.CONCIT, row.NAME),
        #    axis=1)
        #df = df.dropna()
        #df["STNAME"] = df["STNAME"].str.lower()
        #df["NAME"] = df["NAME"].str.lower()
        #df = df.drop_duplicates(subset=["NAME", "STNAME"], keep="last")
        #df = df[~df["Location"].str.endswith("00000")]
        #df = df.drop_duplicates(subset=["Location"], keep="last")
        df["Location"] = "geoId/" + df["STATE"] + df["PLACE"]
        key = "POPESTIMATE07"
        final_cols = [
            "Location", "2000", "2001", "2002", "2003", "2004", "2005", "2006",
            "2007", "2008", "2009"
        ]
        if "sub-est2019_all" in file_name:
            key = "POPESTIMATE"
            final_cols = [
                "Location", "2010", "2011", "2012", "2013", "2014", "2015",
                "2016", "2017", "2018", "2019"
            ]

        df.columns = df.columns.str.replace(key, '')
        df = df[final_cols]
        df = _transpose_df(df, common_col="Location", data_cols=df.columns[1:])
        #print(df.groupby(by="Location").count())
    return df


class USCensusPEPAnnualPopulation:
    """
    This Class has requried methods to generate Cleaned CSV,
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

    def __transform_df(self, df: pd.DataFrame, area: str) -> pd.DataFrame:
        df = _clean_csv(df, area)
        df = _states_full_to_short_form(df, "Location", "Short_Form")
        df = _add_geo_id(df, "Short_Form", "Location")

        output_path = self.cleaned_csv_file_path[:self.cleaned_csv_file_path.
                                                 rfind("/")]
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        return df[["Year", "Location", "Count_Person"]]

    def __generate_mcf(self) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template
        Arguments:
            df_cols (list) : List of DataFrame Columns
        Returns:
            None
        """
        mcf_template = """Node: dcid:Count_Person
typeOf: dcs:StatisticalVariable
populationType: dcs:Person
statType: dcs:measuredValue
measuredProperty: dcs:count
"""
        # Writing Genereated MCF to local path.
        with open(self.mcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(mcf_template.rstrip('\n'))

    def __generate_tmcf(self) -> None:
        """
        This method generates TMCF file w.r.t
        dataframe headers and defined TMCF template
        Arguments:
            df_cols (list) : List of DataFrame Columns
        Returns:
            None
        """
        tmcf_template = """Node: E:USA_Annual_Population->E0
typeOf: dcs:StatVarObservation
variableMeasured: dcs:Count_Person
measurementMethod: dcs:CensusPEPSurvey
observationAbout: C:USA_Annual_Population->Location
observationDate: C:USA_Annual_Population->Year
observationPeriod: \"P1Y\"
value: C:USA_Annual_Population->Count_Person 
"""

        # Writing Genereated TMCF to local path.
        with open(self.tmcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(tmcf_template.rstrip('\n'))

    def process(self):
        """
        This Method calls the required methods to generate cleaned CSV,
        MCF, and TMCF file
        """

        for file in self.input_files:
            file_name = os.path.basename(file)
            print(file_name)
            #print(f"file name {file_name}")
            file_format = _find_file_format(file)

            op_file = "output" + os.sep + file_name.replace(".txt", ".csv")
            if "popclockest.txt" in file:
                _clean_nationals_1900_1999(file, op_file)
                df = _load_df(op_file, "csv", 0)
                os.remove(op_file)
            elif "nst-est2020.csv" in file:
                _clean_nationals_2010_2020(file, op_file)
                df = _load_df(op_file, "csv", 0)
                os.remove(op_file)
            elif "st7080ts" in file:
                df = process_states_1970_1979(file)
            elif "st8090ts" in file:
                df = process_states_1980_1989(file)
                df["Location"] = df["Location"].apply(_state_to_geo_id)
            elif "st-99-03" in file:
                df = process_states_1990_1999(file)
                df = _states_full_to_short_form(df, "Location", "Location")
                df["Location"] = df["Location"].apply(_state_to_geo_id)

            elif file_name.startswith("st"):
                states_conf = get_state_file_config()
                df = process_states_1900_1969(states_conf, file, file_name,
                                              1000)

            elif file_name in ["e8089co.txt", "e7079co.txt", "99c8_00.txt"
                              ] or "co-est" in file_name:
                df = _process_counties(file)
            elif file_name in [
                    'su-99-7_us.txt', "sub-est2010-alt.csv",
                    "sub-est2019_all.csv"
            ]:
                df = _process_cities(file, file_name)
                #print(df.head())
                #df = df.drop_duplicates(subset=["Year", "Location"])
            else:
                df = _load_df(file, file_format)
                df = clean_df(df, file_format)
                area = "United States"
                df = self.__transform_df(df, area)

            df["file_name"] = file_name
            self.df = _merge_df(self.df, df)
        self.df[["Year", "Location",
                 "Count_Person"]].to_csv(self.cleaned_csv_file_path,
                                         index=False)
        #tmp_df = self.df["Location"]
        #tmp_df.groupby().value_counts().to_csv("loc.csv")
        self.__generate_mcf()
        self.__generate_tmcf()


def main(_):
    input_path = FLAGS.input_path

    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]

    # Defining Output file names
    data_file_path = os.path.dirname(
        os.path.abspath(__file__)) + os.sep + "output"
    cleaned_csv_path = data_file_path + os.sep + "USA_Annual_Population.csv"
    mcf_path = data_file_path + os.sep + "USA_Annual_Population.mcf"
    tmcf_path = data_file_path + os.sep + "USA_Annual_Population.tmcf"

    loader = USCensusPEPAnnualPopulation(ip_files, cleaned_csv_path, mcf_path,
                                         tmcf_path)

    loader.process()


if __name__ == "__main__":
    app.run(main)
