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
This Python module is generalized to work with different USEducation import
such as Private Education & Public Education.

USEducation class in this module provides methods to generate processed CSV, MCF &
TMCF files.
"""
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

import io
import json
import os
import sys
import re
import pandas as pd
import numpy as np

pd.set_option("display.max_columns", None)

from common.replacement_functions import replace_values
from common.prop_conf import *
from common.place_conf import *

CODEDIR = os.path.dirname(__file__)
# For import common.replacement_functions
sys.path.insert(1, os.path.join(CODEDIR, '../../..'))
from util.statvar_dcid_generator import get_statvar_dcid
from common.dcid_existance import *


class USEducation:
    """
    USEducation is a base class which provides common implementation for
    generating CSV, MCF and tMCF files.
    """
    # Below variables will be initialized by sub-class (import specific)
    _import_name = ""
    _default_mcf_template = ""
    _split_headers_using_school_type = ""
    _include_columns = None
    _exclude_columns = None
    _include_col_place = None
    _exclude_col_place = None
    _generate_statvars = True

    def __init__(self,
                 input_files: list,
                 cleaned_csv_path: str = None,
                 mcf_file_path: str = None,
                 tmcf_file_path: str = None,
                 cleaned_csv_place: str = None,
                 tmcf_file_place: str = None) -> None:
        self._input_files = input_files
        self._cleaned_csv_file_path = cleaned_csv_path
        self._mcf_file_path = mcf_file_path
        self._tmcf_file_path = tmcf_file_path
        self._csv_file_place = cleaned_csv_place
        self._tmcf_file_place = tmcf_file_place
        self._temp_csv_place = os.path.join(
            os.path.dirname(cleaned_csv_place),
            "us_nces_demographics_private_place_temp.csv")
        self._year = None
        self._final_df_public = pd.DataFrame(columns=[
            'County_code', 'Public_School_Name', 'School_Id', 'Lowest_Grade',
            'Highest_Grade', 'PhoneNumber', 'State_code', 'Physical_Address',
            'City', 'ZIP'
        ])
        self._df = pd.DataFrame()
        self._final_df_district = pd.DataFrame()
        if not os.path.exists(os.path.dirname(self._cleaned_csv_file_path)):
            os.mkdir(os.path.dirname(self._cleaned_csv_file_path))
        if not os.path.exists(os.path.dirname(self._csv_file_place)):
            os.mkdir(os.path.dirname(self._csv_file_place))

    def set_cleansed_csv_file_path(self, cleansed_csv_file_path: str) -> None:
        self._cleaned_csv_file_path = cleansed_csv_file_path

    def set_mcf_file_path(self, mcf_file_path: str) -> None:
        self._mcf_file_path = mcf_file_path

    def set_tmcf_file_path(self, tmcf_file_path: str) -> None:
        self._tmcf_file_path = tmcf_file_path

    def set_tmcf_place_path(self, tmcf_file_place: str) -> None:
        self._tmcf_file_place = tmcf_file_place

    def input_file_to_df(self, f_path: str) -> pd.DataFrame:
        """Convert a file path to a dataframe."""
        with open(f_path, "r", encoding="UTF-8") as file:
            lines = file.readlines()
            # first six lines is data description and source we skip those
            #assert all(lines[i] == '\n' for i in [1, 3, 5])
            # last seven lines is data legend and totals we skip those
            #assert lines[-5].startswith('Data Source')
            f_content = io.StringIO('\n'.join(lines[6:-5]))
            return pd.read_csv(f_content)

    def _extract_year_from_headers(self, headers: list) -> str:
        year_pattern = r"(\[District||(Private|Public) School\])(\s)(?P<year>\d\d\d\d-\d\d)"
        for header in headers:
            match = re.search(year_pattern, header)
            if match:
                year = match.groupdict()["year"]
                break
        return year

    def _clean_data(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        regex_patterns = [(r'^=\"(.*)\"$', r'\1'),
                          (r'^-(-?)(\s?)([a-zA-Z0-9\s]*)(-?)$', r'\3')]

        for pattern, pos in regex_patterns:
            raw_df = raw_df.replace(to_replace={re.compile(pattern): pos},
                                    regex=True)

        for col in ["Private School Name", "Public School Name"]:
            if col in raw_df.columns.values.tolist():
                raw_df[col] = \
                    raw_df[col].str.replace('"', '\'')

        return raw_df

    def _clean_columns(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        cleaned_columns = []
        for col in raw_df.columns.values.tolist():
            cleaned_columns.append(
                col.split(self._split_headers_using_school_type)[0].strip())
        raw_df.columns = cleaned_columns
        return raw_df

    def _apply_regex(self, data_df: pd.DataFrame, conf: dict,
                     curr_prop_column: str):
        """
        Extracts the required words using regex.
        Args:
            data_df (pd.DataFrame): _description_
            conf (dict): _description_
            curr_prop_column (str): _description_
        Returns:
            _type_: _description_
        """
        regex = conf.get("regex", False)

        if regex:
            pattern = regex["pattern"]
            position = regex["position"]
            if True in data_df[curr_prop_column].str.contains(
                    pattern).values.tolist():
                data_df[curr_prop_column] = data_df[curr_prop_column].str.split(
                    pattern, expand=True)[position]
                data_df[curr_prop_column] = data_df[curr_prop_column].fillna(
                    'None')
            else:
                data_df[curr_prop_column] = 'None'
        return data_df

    def _generate_prop(self,
                       data_df: pd.DataFrame,
                       default_mcf_prop: list = None,
                       sv_prop_order: list = None,
                       node_configs: dict = None):
        """
        Generate property columns in the dataframe data_df
        Args:
            data_df (pd.DataFrame): Input DataFrame
        Returns:
            _type_: _description_
        """
        for prop_, val_, format_ in default_mcf_prop:
            data_df["prop_" + prop_] = format_((prop_, val_))

        for prop_ in sv_prop_order:
            if "prop_" + prop_ in data_df.columns.values.tolist():
                continue

            conf = node_configs[prop_]
            data_df["curr_prop"] = prop_
            column = conf["column"]
            curr_value_column = "prop_" + prop_

            unique_rows = data_df.drop_duplicates(subset=[column]).reset_index(
                drop=True)
            unique_rows[curr_value_column] = unique_rows[column]
            unique_rows = self._apply_regex(unique_rows, conf,
                                            curr_value_column)
            if conf.get("update_value", False):
                unique_rows[curr_value_column] = unique_rows[
                    curr_value_column].apply(conf["update_value"])

            unique_rows[curr_value_column] = unique_rows[[
                "curr_prop", curr_value_column
            ]].apply(conf["pv_format"], axis=1)
            unique_rows[[curr_value_column
                        ]] = replace_values(unique_rows[[curr_value_column]],
                                            replace_with_all_mappers=False,
                                            regex_flag=True)
            curr_val_mapper = dict(
                zip(unique_rows[column], unique_rows[curr_value_column]))

            data_df[curr_value_column] = data_df[column].map(curr_val_mapper)
        return data_df

    def _generate_stat_vars(self, data_df: pd.DataFrame, prop_cols: str,
                            sv_node_column: str) -> pd.DataFrame:
        """
        Generates statvars using property columns.
        Args:
            data_df (pd.DataFrame): Input DataFrame
            prop_cols (str): property columns
        Returns:
            pd.DataFrame: DataFrame including statvar column
        """

        data_df[sv_node_column] = '{' + \
                                    data_df[prop_cols].apply(
                                    lambda x: ','.join(x.dropna().astype(str)),
                                    axis=1) + \
                                '}'

        data_df[sv_node_column] = data_df[sv_node_column].apply(json.loads)
        data_df['sv_name'] = data_df[sv_node_column].apply(get_statvar_dcid)
        data_df["sv_name"] = np.where(
            data_df["prop_measurementDenominator"].isin([np.nan]),
            data_df["sv_name"], data_df["sv_name"].str.replace("Count",
                                                               "Percent",
                                                               n=1))
        data_df[sv_node_column] = data_df['sv_name'].apply(SV_NODE_FORMAT)

        stat_var_with_dcs = dict(
            zip(data_df["all_prop"], data_df[sv_node_column]))
        stat_var_without_dcs = dict(zip(data_df["all_prop"],
                                        data_df['sv_name']))

        return (stat_var_with_dcs, stat_var_without_dcs)

    def _generate_mcf_data(self, data_df: pd.DataFrame,
                           prop_cols: list) -> pd.DataFrame:

        data_df['mcf'] = \
                    data_df[prop_cols].apply(
                    func=lambda x: '\n'.join(x.dropna()),
                    axis=1).str.replace('"', '')
        mcf_mapper = dict(zip(data_df["all_prop"], data_df['mcf']))

        return mcf_mapper

    def _generate_stat_var_and_mcf(self,
                                   data_df: pd.DataFrame,
                                   sv_prop_order: list = None):
        """
        Generates the stat vars.
        Args:
            data_df (_type_): _description_
        Returns:
            _type_: _description_
        """

        prop_cols = ["prop_" + col for col in sorted(sv_prop_order)]

        data_df["all_prop"] = ""
        for col in prop_cols:
            data_df["all_prop"] += '_' + data_df[col]
        sv_node_column = "prop_sv_node"
        data_df["prop_sv_node"] = ""
        unique_props = data_df.drop_duplicates(subset=["all_prop"]).reset_index(
            drop=True)

        unique_props = unique_props.replace('', np.nan)
        if self._generate_statvars:
            stat_var_with_dcs, stat_var_without_dcs = self._generate_stat_vars(
                unique_props, prop_cols, sv_node_column)
            prop_cols.insert(0, sv_node_column)
            data_df["prop_node"] = data_df["all_prop"].map(stat_var_with_dcs)
            data_df["sv_name"] = data_df["all_prop"].map(stat_var_without_dcs)
        mcf_mapper = self._generate_mcf_data(unique_props, prop_cols)
        data_df["mcf"] = data_df["all_prop"].map(mcf_mapper)
        data_df = data_df.drop(columns=["all_prop"]).reset_index(drop=True)
        data_df = data_df.drop(columns=prop_cols).reset_index(drop=True)
        return data_df

    def _parse_file(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        df_append = []
        df_final_place = pd.DataFrame()
        self._year = self._extract_year_from_headers(
            raw_df.columns.values.tolist())

        raw_df["year"] = self._year[0:4].strip()

        df_cleaned = self._clean_data(raw_df)

        for col in df_cleaned.columns.values.tolist():
            df_cleaned[col] = \
                df_cleaned[col].astype('str').str.strip()

        df_cleaned = self._clean_columns(df_cleaned)

        if self._import_name == "private_school":
            df_cleaned["school_state_code"] = \
                "nces/" + df_cleaned["School ID - NCES Assigned"] + \
                '_' + df_cleaned["ANSI/FIPS State Code"]
        elif self._import_name == "public_school":
            df_cleaned["school_state_code"] = \
                "nces/" + df_cleaned["School ID - NCES Assigned"]
        elif self._import_name == "district_school":
            df_cleaned["school_state_code"] = \
                "geoId/sch" + df_cleaned["Agency ID - NCES Assigned"]

        curr_cols = df_cleaned.columns.values.tolist()
        curr_place = curr_cols
        data_cols = []
        data_place = []
        for pattern in self._exclude_columns:
            pat = f"^((?!{pattern}).)*$"
            r = re.compile(pat)
            curr_cols = list(filter(r.match, curr_cols))

        for pattern in self._include_columns:
            r = re.compile(pattern)
            data_cols += list(filter(r.match, curr_cols))

        for pattern in self._exclude_col_place:
            pat = f"^((?!{pattern}).)*$"
            r = re.compile(pat)
            curr_place = list(filter(r.match, curr_place))

        for pattern in self._include_col_place:
            r = re.compile(pattern)
            data_place += list(filter(r.match, curr_place))

        df_place = df_cleaned[data_place]

        if self._import_name == "private_school":
            df_place['year'] = self._year[0:4].strip()
            df_place_col = pd.DataFrame(columns=[
                "year", "school_state_code", "ZIP", "ZIP + 4", "County_code",
                "Private_School_Name", "SchoolID", "School_Type",
                "Lowest_Grade", "Highest_Grade", "SchoolGrade",
                "School_Religion", "School_Religion_Affliation",
                "Physical_Address", "PhoneNumber", "Coeducational", "State_code"
            ])
            if not os.path.exists(self._temp_csv_place):

                df_place_col.to_csv(self._temp_csv_place, index=False)
            else:
                df_place.drop_duplicates(inplace=True)
                df_place_col.to_csv(self._temp_csv_place,
                                    index=False,
                                    header=False,
                                    mode='a')
            df_place['ZIP'] = pd.to_numeric(df_place['ZIP'], errors='coerce')
            df_place['ANSI/FIPS County Code'] = pd.to_numeric(
                df_place['ANSI/FIPS County Code'], errors='coerce')

            df_place = df_place.fillna(-1)
            float_col = df_place.select_dtypes(include=['float64'])
            for col in float_col.columns.values:
                df_place[col] = df_place[col].astype('int64')
                df_place[col] = df_place[col].astype("str").str.replace(
                    "-1", "")
            df_place['Phone Number'] = pd.to_numeric(df_place['Phone Number'],
                                                     errors='coerce')

            df_place['ZIP'] = df_place['ZIP'].astype(str).str.zfill(5)
            df_place['ZIP'] = "zip/" + df_place['ZIP']

            df_place['State_code'] = "geoId/" + df_place['ANSI/FIPS State Code']
            df_place['ANSI/FIPS County Code'] = df_place[
                'ANSI/FIPS County Code'].astype(str).str.zfill(5)
            df_place['County_code'] = df_place['ANSI/FIPS County Code'].apply(
                lambda x: 'geoId/' + x if x != '' else '')
            df_place["Physical Address"] = df_place[
                "Physical Address"] + " " + df_place["City"] + " " + df_place[
                    "ZIP + 4"]
            df_place = df_place.loc[:, ~df_place.columns.duplicated()]
            df_place = df_place.rename(
                columns={
                    "Private School Name":
                        "Private_School_Name",
                    "School ID - NCES Assigned":
                        "SchoolID",
                    "School Type":
                        "School_Type",
                    "School's Religious Affiliation or Orientation":
                        "School_Religion_Affliation",
                    "Religious Orientation":
                        "School_Religion",
                    "Physical Address":
                        "Physical_Address",
                    "Phone Number":
                        "PhoneNumber",
                    "Lowest Grade Taught":
                        "Lowest_Grade",
                    "Highest Grade Taught":
                        "Highest_Grade",
                    "School Level":
                        "SchoolGrade"
                })

            # df_place = df_place.applymap(lambda x: x.strip()
            #                              if isinstance(x, str) else x)

            df_place = replace_values(df_place,
                                      replace_with_all_mappers=False,
                                      regex_flag=False)
            col_to_dcs = [
                "School_Type", "School_Religion", "Coeducational",
                "Lowest_Grade", "Highest_Grade", "SchoolGrade"
            ]
            for col in col_to_dcs:
                df_place[col] = df_place[col].replace(to_replace={'': pd.NA})
                df_place[col] = "dcs:" + df_place[col]
            df_place = df_place[[
                "year", "school_state_code", "ZIP", "ZIP + 4", "County_code",
                "Private_School_Name", "SchoolID", "School_Type",
                "Lowest_Grade", "Highest_Grade", "SchoolGrade",
                "School_Religion", "School_Religion_Affliation",
                "Physical_Address", "PhoneNumber", "Coeducational", "State_code"
            ]]

            df_final_place = pd.concat([df_final_place, df_place])
            df_place.to_csv(self._temp_csv_place,
                            index=False,
                            header=False,
                            mode='a')

        if self._import_name == "district_school":
            df_place['year'] = self._year[0:4].strip()

            df_place = df_place.loc[:, ~df_place.columns.duplicated()]
            df_place['ContainedInPlace'] = "geoId/" + df_place[
                'ANSI/FIPS State Code']
            df_place['geoID'] = "sch" + df_place['Agency ID - NCES Assigned']
            df_place = df_place.rename(
                columns={
                    'Location ZIP': 'ZIP',
                    'County Number': 'County_code',
                    'Agency Name': 'District_School_name',
                    'Agency ID - NCES Assigned': 'School_ID',
                    'Agency Type': 'School_Type',
                    'State Agency ID': 'State_school_ID',
                    'Phone Number': 'PhoneNumber',
                    'ANSI/FIPS State Code': 'State_code',
                    'Location Address 1': 'Physical_Address',
                    'Location City': 'City',
                    'Agency Level (SY 2017-18 onward)': 'Agency_level',
                    "Lowest Grade Offered": "Lowest_Grade_Dist",
                    "Highest Grade Offered": "Highest_Grade_Dist",
                    "State Name": "State_Name",
                    "Location ZIP4": "Location_ZIP4",
                    "State Abbr": "State_Abbr"
                })
            df_place = replace_values(df_place)
            col_to_dcs = ['Lowest_Grade_Dist', 'Highest_Grade_Dist', 'Locale']
            for col in col_to_dcs:
                df_place[col] = df_place[col].replace(to_replace={'': pd.NA})
                df_place[col] = "dcs:" + df_place[col]
            df_place["Physical_Address"] = np.where(
                df_place['Location_ZIP4'] == "",
                (df_place["Physical_Address"] + " " + df_place["City"] + "," +
                 df_place["State_Abbr"] + " " + df_place["ZIP"]),
                (df_place["Physical_Address"] + " " + df_place["City"] + "," +
                 df_place["State_Abbr"] + " " + df_place["ZIP"] + "-" +
                 df_place['Location_ZIP4']))
            df_place['County_code'] = "geoId/" + df_place['County_code']
            df_place['State_code'] = "geoId/" + df_place['State_code']

            self._final_df_district = pd.concat(
                [self._final_df_district, df_place])

        if self._import_name == "public_school":
            df_place['year'] = self._year[0:4].strip()
            df_place = df_place.loc[:, ~df_place.columns.duplicated()]
            df_place = df_place.rename(
                columns={
                    'County Number':
                        'County_code',
                    'School Name':
                        'Public_School_Name',
                    'School ID - NCES Assigned':
                        'School_Id',
                    'Lowest Grade Offered':
                        'Lowest_Grade',
                    'Highest Grade Offered':
                        'Highest_Grade',
                    'Phone Number':
                        'PhoneNumber',
                    'ANSI/FIPS State Code':
                        'State_code',
                    'Location Address 1':
                        'Physical_Address',
                    'Location City':
                        'City',
                    'Location ZIP':
                        'ZIP',
                    'Magnet School':
                        'Magnet_School',
                    'Charter School':
                        'Charter_School',
                    'School Type':
                        'School_Type_Public',
                    'Title I School Status':
                        'Title_I_School_Status',
                    'National School Lunch Program':
                        'National_School_Lunch_Program',
                    'School Level (SY 2017-18 onward)':
                        'School_Level',
                    'State School ID':
                        'State_School_ID',
                    'State Agency ID':
                        'State_Agency_ID',
                    'State Abbr':
                        'State_Abbr',
                    'Agency Name':
                        'Agency_Name',
                    'Location ZIP4':
                        'Location_ZIP4',
                    'Agency ID - NCES Assigned':
                        'State_District_ID'
                })
            df_place = replace_values(df_place)
            col_to_dcs = [
                'Lowest_Grade', 'Highest_Grade', 'Locale',
                'National_School_Lunch_Program', 'Magnet_School',
                'Charter_School', 'School_Type', 'Title_I_School_Status'
            ]
            for col in col_to_dcs:
                if col in df_place.columns.to_list():
                    df_place[col] = df_place[col].replace(
                        to_replace={'': pd.NA})
                    df_place[col] = "dcs:" + df_place[col]
            df_place['ZIP'] = "zip/" + df_place['ZIP']
            df_place['State_code'] = "geoId/" + df_place['State_code']
            df_place['County_code'] = df_place['County_code'].apply(
                lambda x: 'geoId/' + x if x != '' else '')

            df_place["Physical_Address"] = np.where(
                df_place['Location_ZIP4'] == "",
                (df_place["Physical_Address"] + " " + df_place["City"] + "," +
                 df_place["State_Abbr"] + " " + df_place["ZIP"]),
                (df_place["Physical_Address"] + " " + df_place["City"] + "," +
                 df_place["State_Abbr"] + " " + df_place["ZIP"] + "-" +
                 df_place['Location_ZIP4']))
            self._final_df_public = pd.concat([self._final_df_public, df_place])

        if not self._generate_statvars:
            return df_cleaned[data_cols]

        df_cleaned = df_cleaned.melt(id_vars=['school_state_code', 'year'],
                                     value_vars=data_cols,
                                     var_name='sv_name',
                                     value_name='observation')

        df_cleaned['observation'] = pd.to_numeric(df_cleaned['observation'],
                                                  errors='coerce')

        df_cleaned["observation"] = df_cleaned["observation"].replace(
            to_replace={'': pd.NA})
        df_cleaned = df_cleaned.dropna(subset=['observation'])

        return df_cleaned

    def generate_csv(self) -> pd.DataFrame:
        """
        This Method calls the required methods to generate
        cleaned CSV, MCF, and TMCF file.

        Args:
            None

        Returns:
            pd.DataFrame
        """

        dfs = []
        df_parsed = None
        if self._generate_statvars:
            df_merged = pd.DataFrame(columns=[
                "school_state_code", "year", "sv_name", "observation",
                "scaling_factor"
            ])
            df_merged.to_csv(self._cleaned_csv_file_path, index=False)
        c = 0
        unique_sv_names = []
        for input_file in sorted(self._input_files):
            c += 1
            print(f"{c} - {os.path.basename(input_file)}")

            raw_df = self.input_file_to_df(input_file)
            df_parsed = self._parse_file(raw_df)
            if df_parsed.shape[0] > 0:
                if self._generate_statvars:
                    df_parsed = df_parsed.sort_values(
                        by=["year", "sv_name", "school_state_code"])
                    df_parsed = self._generate_prop(df_parsed,
                                                    DF_DEFAULT_MCF_PROP,
                                                    SV_PROP_ORDER, FORM_STATVAR)
                    df_parsed = self._generate_stat_var_and_mcf(
                        df_parsed, SV_PROP_ORDER)
                    for col in df_parsed.columns.values.tolist():
                        df_parsed[col] = df_parsed[col].astype(
                            'str').str.replace("FeMale", "Female")
                    df_parsed["scaling_factor"] = np.where(
                        df_parsed["sv_name"].str.contains("Percent"), 100, '')
                    df_final = df_parsed[[
                        "school_state_code", "year", "sv_name", "observation",
                        "scaling_factor"
                    ]]
                    df_final.to_csv(self._cleaned_csv_file_path,
                                    header=False,
                                    index=False,
                                    mode='a')

                    df_parsed = df_parsed.drop_duplicates(
                        subset=["sv_name"]).reset_index(drop=True)
                    curr_sv_names = df_parsed["sv_name"].values.tolist()
                    new_sv_names = list(
                        set(curr_sv_names) - set(unique_sv_names))
                    unique_sv_names = unique_sv_names + new_sv_names

                    df_parsed = df_parsed[df_parsed["sv_name"].isin(
                        new_sv_names)].reset_index(drop=False)
                dfs.append(df_parsed)

        if self._import_name == "private_school":
            df_final_private = pd.read_csv(self._temp_csv_place)
            df_final_private = df_final_private.sort_values(by=["year"],
                                                            ascending=False)

            df_final_private['PhoneNumber'] = df_final_private[
                'PhoneNumber'].astype('Int64').astype(str)
            df_final_private['PhoneNumber'] = df_final_private[
                'PhoneNumber'].replace('<NA>', '', regex=True)
            zip_list = list(pd.unique(df_final_private['ZIP']))
            county_list = list(pd.unique(df_final_private['County_code']))

            config = {
                'dc_api_batch_size': 200,
                'dc_api_retries': 3,
                'dc_api_retry_sec': 5,
                'dc_api_use_cache': False,
                'dc_api_root': None
            }
            dcid_check_zip = dc_api_get_defined_dcids(zip_list, config)
            dcid_check_county = dc_api_get_defined_dcids(county_list, config)

            df_final_private['ZIP'] = df_final_private['ZIP'].apply(
                lambda x: x if dcid_check_zip[x] else '')

            df_final_private['County_code'] = df_final_private[
                'County_code'].apply(lambda x: x
                                     if dcid_check_county[x] else '')

            df_final_private['County_code'] = df_final_private[
                'County_code'].astype(str)

            df_final_private['ContainedInPlace'] = df_final_private[
                'ZIP'].apply(lambda x: x + ',' if x != '' else ''
                            ) + df_final_private['County_code'].apply(
                                lambda x: x + ',' if x != '' else ''
                            ) + df_final_private['State_code']
            df_final_private['ContainedInPlace'] = df_final_private[
                'ContainedInPlace'].astype(str)
            df_final_private["Physical_Address"] = df_final_private[
                "Physical_Address"].str.title()

            df_final_private["Private_School_Name"] = np.where(
                df_final_private["Private_School_Name"].str.len() <= 4,
                df_final_private["Private_School_Name"],
                df_final_private["Private_School_Name"].str.title())
            df_final_private = df_final_private.drop_duplicates(
                subset=["SchoolID"]).reset_index(drop=True)
            df_final_private.drop_duplicates(inplace=True)
            df_final_private.to_csv(self._csv_file_place, index=False)

        if self._import_name == "district_school":
            self._final_df_district = self._final_df_district.sort_values(
                by=["year"], ascending=False)
            self._final_df_district = self._final_df_district.drop_duplicates(
                subset=["School_ID"]).reset_index(drop=True)
            county_list = list(pd.unique(
                self._final_df_district['County_code']))
            config = {
                'dc_api_batch_size': 200,
                'dc_api_retries': 3,
                'dc_api_retry_sec': 5,
                'dc_api_use_cache': False,
                'dc_api_root': None
            }
            dcid_check_county = dc_api_get_defined_dcids(county_list, config)

            self._final_df_district['County_code'] = self._final_df_district[
                'County_code'].apply(lambda x: x
                                     if dcid_check_county[x] else '')

            self._final_df_district['County_code'] = self._final_df_district[
                'County_code'].astype(str)
            self._final_df_district[
                'ContainedInPlace'] = self._final_df_district[
                    'County_code'].apply(
                        lambda x: x + ',' if x != '' else ''
                    ) + self._final_df_district['State_code']
            self._final_df_district[
                "Physical_Address"] = self._final_df_district[
                    "Physical_Address"].str.title()

            self._final_df_district["District_School_name"] = np.where(
                self._final_df_district["District_School_name"].str.len() <= 4,
                self._final_df_district["District_School_name"],
                self._final_df_district["District_School_name"].str.title())
            self._final_df_district.to_csv(self._csv_file_place, index=False)

        if self._import_name == "public_school":
            self._final_df_public = self._final_df_public.sort_values(
                by=["year"], ascending=False)
            self._final_df_public = self._final_df_public.drop_duplicates(
                subset=["School_Id"]).reset_index(drop=True)
            zip_list = list(pd.unique(self._final_df_public['ZIP']))
            county_list = list(pd.unique(self._final_df_public['County_code']))
            if '' in county_list:
                county_list.remove("")

            config = {
                'dc_api_batch_size': 200,
                'dc_api_retries': 3,
                'dc_api_retry_sec': 5,
                'dc_api_use_cache': False,
                'dc_api_root': None
            }
            dcid_check_zip = dc_api_get_defined_dcids(zip_list, config)
            dcid_check_county = dc_api_get_defined_dcids(county_list, config)
            dcid_check_county[""] = False
            self._final_df_public['ZIP'] = self._final_df_public['ZIP'].apply(
                lambda x: x if dcid_check_zip[x] else '')

            self._final_df_public['County_code'] = self._final_df_public[
                'County_code'].apply(lambda x: x
                                     if dcid_check_county[x] else '')

            self._final_df_public['County_code'] = self._final_df_public[
                'County_code'].astype(str)

            self._final_df_public['ContainedInPlace'] = self._final_df_public[
                'ZIP'].apply(lambda x: x + ',' if x != '' else ''
                            ) + self._final_df_public['County_code'].apply(
                                lambda x: x + ',' if x != '' else ''
                            ) + self._final_df_public['State_code']
            self._final_df_public['ContainedInPlace'] = self._final_df_public[
                'ContainedInPlace'].astype(str)
            self._final_df_public["Physical_Address"] = self._final_df_public[
                "Physical_Address"].apply(lambda x: x.title())
            self._final_df_public["Public_School_Name"] = np.where(
                self._final_df_public["Public_School_Name"].str.len() <= 4,
                self._final_df_public["Public_School_Name"],
                self._final_df_public["Public_School_Name"].apply(
                    lambda x: x.title()))
            self._final_df_public.to_csv(self._csv_file_place, index=False)

        df_merged = pd.DataFrame()
        for df in dfs:
            df_merged = pd.concat([df_merged, df])
        self._df = df_merged

    def generate_mcf(self) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template

        Args:
            sv_list (list) : List of DataFrame Columns

        Returns:
            None    
        """
        if self._generate_statvars:
            unique_nodes_df = self._df.drop_duplicates(
                subset=["prop_node"]).reset_index(drop=True)

            mcf_ = unique_nodes_df.sort_values(by=["prop_node"])["mcf"].tolist()
        else:
            mcf_ = self._df["mcf"].tolist()
        mcf_ = "\n\n".join(mcf_)

        with open(self._mcf_file_path, "w", encoding="UTF-8") as file:
            file.write(mcf_)

    def generate_tmcf(self) -> None:
        """
        This method generates TMCF file w.r.t
        dataframe headers and defined TMCF template.

        Args:
            None

        Returns:
            None
        """

        tmcf = TMCF_TEMPLATE.format(import_name=self._import_name)
        # Writing Genereated TMCF to local path.
        with open(self._tmcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(tmcf.rstrip('\n'))

    def _generate_tmcf_private(self) -> None:
        """
        This method generates TMCF file w.r.t
        dataframe headers and defined TMCF template

        Args:
            df_cols (list) : List of DataFrame Columns

        Returns:
            None
        """
        with open(self._tmcf_file_place, 'w+', encoding='utf-8') as f_out:
            f_out.write(TMCF_TEMPLATE_PLACE_PRIVATE.rstrip('\n'))

    def _generate_tmcf_district(self) -> None:
        """
        This method generates TMCF file w.r.t
        dataframe headers and defined TMCF template

        Args:
            df_cols (list) : List of DataFrame Columns

        Returns:
            None
        """
        with open(self._tmcf_file_place, 'w+', encoding='utf-8') as f_out:
            f_out.write(TMCF_TEMPLATE_PLACE_DISTRICT.rstrip('\n'))

    def _generate_tmcf_public(self) -> None:
        """
        This method generates TMCF file w.r.t
        dataframe headers and defined TMCF template

        Args:
            df_cols (list) : List of DataFrame Columns

        Returns:
            None
        """
        with open(self._tmcf_file_place, 'w+', encoding='utf-8') as f_out:
            f_out.write(TMCF_TEMPLATE_PLACE_PUBLIC.rstrip('\n'))

    def create_place_nodes(self):
        self.generate_csv()
        df_parsed = self._df
        df_parsed = self._generate_prop(df_parsed, DF_DEFAULT_TMCF_PROP,
                                        SV_PROP_ORDER_PLACE, PLACE_STATVAR)

        # df_parsed = self._generate_stat_var_and_mcf(df_parsed, SV_PROP_ORDER_PLACE)
        self._df = df_parsed
