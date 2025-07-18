# Copyright 2025 Google LLC
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
import csv
import io
import json
import os
import re
import sys
import warnings
import numpy as np
import pandas as pd
from absl import logging
from google.cloud import storage

#To remove the futurewarning and DeprecationWarning of the imports
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=DeprecationWarning)
warnings.simplefilter(action='ignore', category=SyntaxWarning)
pd.set_option("display.max_columns", None)

CODEDIR = os.path.dirname(__file__)
sys.path.insert(1, os.path.join(CODEDIR, '../../..'))

from common.dcid__mcf_existance import check_dcid_existence
from common.prop_conf import *
from common.replacement_functions import (replace_values, _UNREADABLE_TEXT)
from util.alpha2_to_dcid import USSTATE_MAP
from util.dc_api_wrapper import dc_api_is_defined_dcid
from util.statvar_dcid_generator import get_statvar_dcid


def log_method_execution(func):
    """
    Decorator to log the execution of methods within a class.

    Logs the start and end of each method, and logs errors using logging.error 
    and critical errors using logging.fatal.

    Args:
        func: The method to be decorated.

    Returns:
        The decorated method.
    """

    def wrapper(*args, **kwargs):
        try:
            logging.info(f"Starting method: {func.__qualname__}")
            result = func(*args, **kwargs)
            logging.info(f"Finished method: {func.__qualname__}")
            return result
        except Exception as e:
            logging.error(f"Error executing method: {func.__qualname__}")
            logging.error(f"Error message: {e}")
            raise

    return wrapper


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
    _observation_period = None
    _key_col_place = None
    _exclude_list = None
    _school_id = None
    _renaming_columns = None

    def __init__(self,
                 input_files: list,
                 cleaned_csv_path: str = None,
                 mcf_file_path: str = None,
                 tmcf_file_path: str = None,
                 cleaned_csv_place: str = None,
                 duplicate_csv_place: str = None,
                 tmcf_file_place: str = None) -> None:
        self.storage_client = storage.Client()
        self._input_files = input_files
        self._cleaned_csv_file_path = cleaned_csv_path
        self._mcf_file_path = mcf_file_path
        self._tmcf_file_path = tmcf_file_path
        self._csv_file_place = cleaned_csv_place
        self._duplicate_csv_place = duplicate_csv_place
        self._tmcf_file_place = tmcf_file_place
        self._year = None
        self._df = pd.DataFrame()
        self._final_df_place = pd.DataFrame()
        if not os.path.exists(os.path.dirname(self._cleaned_csv_file_path)):
            os.mkdir(os.path.dirname(self._cleaned_csv_file_path))
        if not os.path.exists(os.path.dirname(self._csv_file_place)):
            os.mkdir(os.path.dirname(self._csv_file_place))
        if not os.path.exists(os.path.dirname(self._duplicate_csv_place)):
            os.mkdir(os.path.dirname(self._duplicate_csv_place))

    def set_cleansed_csv_file_path(self, cleansed_csv_file_path: str) -> None:
        self._cleaned_csv_file_path = cleansed_csv_file_path

    def set_mcf_file_path(self, mcf_file_path: str) -> None:
        self._mcf_file_path = mcf_file_path

    def set_tmcf_file_path(self, tmcf_file_path: str) -> None:
        self._tmcf_file_path = tmcf_file_path

    def set_tmcf_place_path(self, tmcf_file_place: str) -> None:
        self._tmcf_file_place = tmcf_file_place

    # @log_method_execution
    # def input_file_to_df(self, f_path: str) -> pd.DataFrame:
    #     """Convert a file path to a dataframe."""
    #     with open(f_path, "r", encoding="UTF-8") as file:
    #         lines = file.readlines()
    #         # first six lines is data description and source we skip those
    #         #assert all(lines[i] == '\n' for i in [1, 3, 5])
    #         # last seven lines is data legend and totals we skip those
    #         #assert lines[-5].startswith('Data Source')
    #         f_content = io.StringIO('\n'.join(lines[6:-5]))
    #         return pd.read_csv(f_content)
    # @log_method_execution # Keep your decorator
    def input_file_to_df(self, f_path: str) -> pd.DataFrame:
        """
        Convert a GCS file URI to a dataframe, skipping header/footer lines.
        f_path is expected to be a GCS URI (gs://bucket/path/to/file.csv)
        """
        logging.info(f"Attempting to read file from GCS: {f_path}")

        try:
            # Parse the GCS URI to get bucket name and blob name
            # Example f_path: 'gs://unresolved_mcf/us_nces/demographics/private_school/semi_automation_input_files/1997/ELSI_csv_export_...'
            if not f_path.startswith("gs://"):
                raise ValueError(
                    "File path must be a GCS URI starting with 'gs://'")

            # Split the URI into bucket_name and blob_name
            uri_parts = f_path[5:].split('/', 1)  # [5:] to remove "gs://"
            bucket_name = uri_parts[0]
            blob_name = uri_parts[1]

            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)

            # Download the file content as bytes
            file_content_bytes = blob.download_as_bytes()

            # Decode bytes to a string (assuming UTF-8 for CSVs)
            file_content_string = file_content_bytes.decode("UTF-8")

            # Split the content into lines
            lines = file_content_string.splitlines()

            # Apply your existing logic to skip header/footer lines
            # first six lines is data description and source we skip those
            # last seven lines is data legend and totals we skip those
            # Adjusting `lines[6:-5]` if your actual file structure has changed.
            # From your comment: "first six lines is data description and source we skip those" (lines 0-5)
            # "last seven lines is data legend and totals we skip those" (lines -7 to -1)
            # So, lines[6:-7] if you want to exclude the last 7.
            # Your original code was lines[6:-5] - let's stick to that.

            if len(lines) < 11:  # 6 (header) + 5 (footer) = 11 lines minimum
                logging.warning(
                    f"File {f_path} has fewer than 11 lines, skipping line-trimming might be problematic."
                )
                f_content_to_parse = io.StringIO(
                    file_content_string)  # Use full content if too short
            else:
                f_content_to_parse = io.StringIO('\n'.join(lines[6:-5]))

            df = pd.read_csv(f_content_to_parse)
            logging.info(
                f"Successfully converted {f_path} to DataFrame with shape {df.shape}."
            )
            return df

        except Exception as e:
            logging.error(f"Failed to convert {f_path} to DataFrame: {e}")
            raise  # Re-raise the exception to propagate the error

    @log_method_execution
    def _extract_year_from_headers(self, headers: list) -> str:
        """Extracting year from the headers."""
        year_pattern = r"\[(District|((Private|Public) School))\](\s)(?P<year>\d\d\d\d-\d\d)"
        for header in headers:
            match = re.search(year_pattern, header)
            if match:
                year = match.groupdict()["year"]
                break
        return year

    @log_method_execution
    def _clean_data(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """
        Extracts the required words using regex.
        Args:
            data_df (pd.DataFrame): _description_
            conf (dict): _description_
            curr_prop_column (str): _description_
        Returns:
            raw_df: DataFrame
        """
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

    @log_method_execution
    def _clean_columns(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        '''
        Extracts the required name from the column name
        ex: 'State Name [Private School] Latest available year' -> 'State Name'
        Args:
            raw_df (pd.DataFrame): Input DataFrame
        Returns:
            raw_df (pd.DataFrame): cleaned header DataFrame
        '''
        cleaned_columns = []
        for col in raw_df.columns.values.tolist():
            cleaned_columns.append(
                col.split(self._split_headers_using_school_type)[0].strip())
        raw_df.columns = cleaned_columns
        return raw_df

    @log_method_execution
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

    @log_method_execution
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

    @log_method_execution
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

    @log_method_execution
    def _generate_mcf_data(self, data_df: pd.DataFrame,
                           prop_cols: list) -> pd.DataFrame:
        '''
        Mapps the property according to the value from prop_conf file from 
        common folder.
        Args:
            data_df (pd.DataFrame): Input DataFrame
            prop_cols (list): property columns
        Returns:
            mcf_mapper (dict): property mapped columns
            data_df (pd.DataFrame): new mcf column which consists the dictionary
        '''

        data_df['mcf'] = \
                    data_df[prop_cols].apply(
                    func=lambda x: '\n'.join(x.dropna()),
                    axis=1).str.replace('"', '')
        mcf_mapper = dict(zip(data_df["all_prop"], data_df['mcf']))
        return mcf_mapper

    @log_method_execution
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

    @log_method_execution
    def _verify_year_uniqueness(self, headers: list) -> bool:
        """
        Checks for particual year in the file which is being executed and
        gives an error if any other 'year column' is being executed.
        Args:
            headers: list
        Returns:
            bool: _description_
        """
        year_pattern = r"\[(District|((Private|Public) School))\](\s)(?P<year>\d\d\d\d-\d\d)"
        year_match = True
        for header in headers:
            match = re.search(year_pattern, header)
            if match:
                year = match.groupdict()["year"]
                if year != self._year:
                    year_match = False
                    logging.info(
                        f"Column {header} is not for expectd year {self._year}")
        return year_match

    @log_method_execution
    def _transform_private_place(self):
        """
        The Data for Place Entities is cleaned and written to a file.
        """
        # Renaming column names in the dataframe.
        self._final_df_place = self._final_df_place.rename(
            columns=self._renaming_columns)
        # Filling zip and county numbers upto 5 digits and adding prefixes.
        self._final_df_place['ZIP'] = self._final_df_place['ZIP'].astype(
            str).str.zfill(5)
        self._final_df_place['ZIP'] = "zip/" + self._final_df_place['ZIP']
        self._final_df_place['County_code'] = self._final_df_place[
            'County_code'].astype(str).str.zfill(5)
        self._final_df_place['County_code'] = self._final_df_place[
            'County_code'].apply(lambda x: 'geoId/' + x if x != '' else '')
        self._final_df_place[
            'State_code'] = "geoId/" + self._final_df_place['State_code']

        def add_leading_zero(text):
            parts = text.split('/')
            if len(parts) == 2 and len(parts[1]) == 1:
                return f"{parts[0]}/0{parts[1]}"
            else:
                return text

        self._final_df_place['State_code'] = self._final_df_place[
            'State_code'].apply(add_leading_zero)
        # Renaming the property values according to DataCommons.
        self._final_df_place = replace_values(self._final_df_place,
                                              replace_with_all_mappers=False,
                                              regex_flag=False)
        self._final_df_place["ZIP4"] = np.where(
            (self._final_df_place["ZIP4"].str.len() > 5),
            (self._final_df_place["ZIP4"].str[:5] + '-' +
             self._final_df_place["ZIP4"].str[5:]),
            (self._final_df_place["ZIP4"]))
        self._final_df_place["Physical_Address"] = self._final_df_place[
            "Physical_Address"].astype(
                str) + " " + self._final_df_place["City"].astype(str)
        self._final_df_place["Physical_Address"] = self._final_df_place[
            "Physical_Address"].str.title()
        self._final_df_place["Physical_Address"] = self._final_df_place[
            "Physical_Address"].astype(str) + " " + self._final_df_place[
                'State_Abbr'] + " " + self._final_df_place["ZIP4"].astype(str)
        # List of columns to be considered under 'dcs'
        col_to_dcs = [
            "School_Type", "School_Religion", "Coeducational", "Lowest_Grade",
            "Highest_Grade", "SchoolGrade"
        ]
        for col in col_to_dcs:
            self._final_df_place[col] = self._final_df_place[col].apply(
                lambda x: 'dcs:' + str(x) if x != '' else '')
        # Creating a unique list for zip and county
        zip_list = list(pd.unique(self._final_df_place['ZIP']))
        county_list = list(pd.unique(self._final_df_place['County_code']))
        config = {
            'dc_api_batch_size': 200,
            'dc_api_retries': 3,
            'dc_api_retry_sec': 5,
            'dc_api_use_cache': False,
            'dc_api_root': None
        }
        # Passing the list through API call for checking its existance.
        dcid_check_zip = dc_api_is_defined_dcid(zip_list, config)
        dcid_check_county = dc_api_is_defined_dcid(county_list, config)
        # Considering only the existing zip and county codes.
        self._final_df_place['ZIP'] = self._final_df_place['ZIP'].apply(
            lambda x: x if dcid_check_zip[x] else '')
        self._final_df_place['County_code'] = self._final_df_place[
            'County_code'].apply(lambda x: x if dcid_check_county[x] else '')
        # Generating a column for place property.
        self._final_df_place['ContainedInPlace'] = self._final_df_place[
            'ZIP'].apply(lambda x: x + ',' if x != '' else ''
                        ) + self._final_df_place['County_code'].apply(
                            lambda x: x + ',' if x != '' else ''
                        ) + self._final_df_place['State_code']
        # Camel casing Physical Address and School Name.

        self._final_df_place["Physical_Address"] = self._final_df_place[
            "Physical_Address"].str.replace("Po Box", "PO Box")
        self._final_df_place["Private_School_Name"] = np.where(
            self._final_df_place["Private_School_Name"].str.len() <= 4,
            self._final_df_place["Private_School_Name"],
            self._final_df_place["Private_School_Name"].str.title())
        # Sorting values in descending order and dropping duplicates.
        self._final_df_place = self._final_df_place.sort_values(by=["year"],
                                                                ascending=False)
        self._final_df_place = self._final_df_place.drop_duplicates(
            subset=["school_state_code"]).reset_index(drop=True)

    @log_method_execution
    def _transform_public_place(self):
        """
        The Data for Place Entities is cleaned and written to a file.
        """
        # Renaming Column Names
        self._final_df_place = self._final_df_place.rename(
            columns=self._renaming_columns)
        # Renaming the property values according to DataCommons.
        self._final_df_place = replace_values(self._final_df_place,
                                              replace_with_all_mappers=False,
                                              regex_flag=False)
        # Files before the year 2017 and files 2017 onwards have different
        # column name for the same entity'School_Level'. Hence, combining both
        # columns under one common column.
        # Define the column names for clarity
        col_pre_2017 = 'School_Level_16'
        col_post_2017 = 'School_Level_17'
        final_col = 'School_Level'

        # Ensure both potential source columns exist. If not, create them with NaN.
        if col_pre_2017 not in self._final_df_place.columns:
            self._final_df_place[col_pre_2017] = np.nan
        if col_post_2017 not in self._final_df_place.columns:
            self._final_df_place[col_post_2017] = np.nan

        # Use .combine_first() to merge the two columns intelligently.
        # This takes values from 'School_Level_17' and fills its missing spots
        # with values from 'School_Level_16'.
        self._final_df_place[final_col] = self._final_df_place[
            col_post_2017].combine_first(self._final_df_place[col_pre_2017])

        # (Optional but recommended) Clean up the old columns
        self._final_df_place.drop(columns=[col_pre_2017, col_post_2017],
                                  inplace=True)

        # Restructuring School District ID according to Data Commons.
        self._final_df_place["State_District_ID"] = \
            "geoId/sch" + self._final_df_place["State_District_ID"].astype(str)

        # List of columns to be considered under 'dcs'
        col_to_dcs = [
            'Lowest_Grade_Public', 'Highest_Grade_Public', 'Locale',
            'National_School_Lunch_Program', 'Magnet_School', 'Charter_School',
            'School_Type', 'Title_I_School_Status', 'State_District_ID',
            'School_Level'
        ]
        for col in col_to_dcs:
            if col in self._final_df_place.columns.to_list():
                self._final_df_place[col] = self._final_df_place[col].replace(
                    to_replace={'': pd.NA})
                self._final_df_place[col] = "dcs:" + self._final_df_place[col]
        # Adding prefixes to ZIP, State and County code.
        self._final_df_place['ZIP'] = 'zip/' + self._final_df_place['ZIP']
        self._final_df_place['County_code'] = self._final_df_place[
            'County_code'].astype(str)
        self._final_df_place['State_code'] = self._final_df_place[
            'State_code'].astype(str)
        # In some cases The state code is not valid or is not a state.
        # For example: state_code:59, 63
        # In such cases, the state code is replaced with first 2 characters of
        # its respective county code
        self._final_df_place["State_code"] = np.where(
            self._final_df_place["State_code"].str.contains("59|63"),
            (self._final_df_place['County_code'].astype(str).str[:2]),
            (self._final_df_place["State_code"]))

        self._final_df_place['County_code'] = self._final_df_place[
            'County_code'].apply(lambda x: 'geoId/' + x if x != '' else '')
        self._final_df_place['State_code'] = self._final_df_place[
            'State_code'].apply(lambda x: 'geoId/' + x if x != '' else '')
        # Generates State code by mapping state abbrevation and USSTATE map
        # to fill the empty values in the state code column.
        self._final_df_place['State_code'] = np.where(
            self._final_df_place['State_code'] == "",
            (self._final_df_place['State_Abbr'].map(USSTATE_MAP)),
            (self._final_df_place['State_code']))
        # Creating a unique list for zip,state and county.
        zip_list = list(pd.unique((self._final_df_place['ZIP'])))
        county_list = list(pd.unique(self._final_df_place['County_code']))
        state_list = list(pd.unique(self._final_df_place['State_code']))
        # removing empty values from the list which are from source.
        if '' in county_list:
            county_list.remove("")
        if '' in state_list:
            state_list.remove("")

        config = {
            'dc_api_batch_size': 200,
            'dc_api_retries': 3,
            'dc_api_retry_sec': 5,
            'dc_api_use_cache': False,
            'dc_api_root': None
        }
        # Passing the list through API call for checking its existance.
        dcid_check_zip = dc_api_is_defined_dcid(zip_list, config)
        dcid_check_county = dc_api_is_defined_dcid(county_list, config)
        dcid_check_state = dc_api_is_defined_dcid(state_list, config)
        # After passing through check, the empty values are assigned as False.
        dcid_check_county[""] = False
        dcid_check_state[""] = False
        # Considering only the existing zip, state and county codes.
        self._final_df_place['ZIP'] = self._final_df_place['ZIP'].apply(
            lambda x: x if dcid_check_zip[x] else '')

        self._final_df_place['County_code'] = self._final_df_place[
            'County_code'].apply(lambda x: x if dcid_check_county[x] else '')

        self._final_df_place['State_code'] = self._final_df_place[
            'State_code'].apply(lambda x: x if dcid_check_state[x] else '')
        # Reverse mapping State abbrevations from the current state_code
        # column to combine Physical Address with State Abbrevation.
        state_abbr = {v: k for k, v in USSTATE_MAP.items()}
        self._final_df_place['Validated_State_Abbr'] = self._final_df_place[
            'State_code'].replace(state_abbr)
        # Generating a column for place property.
        self._final_df_place['ContainedInPlace'] = self._final_df_place[
            'ZIP'].apply(lambda x: x + ',' if x != '' else ''
                        ) + self._final_df_place['County_code'].apply(
                            lambda x: x + ',' if x != '' else ''
                        ) + self._final_df_place['State_code'].apply(
                            lambda x: x if x != '' else '')
        self._final_df_place['ZIP'] = self._final_df_place['ZIP'].str.replace(
            "zip/", "")
        self._final_df_place["Physical_Address"] = self._final_df_place[
            "Physical_Address"] + " " + self._final_df_place["City"]
        # Camel casing Physical Address
        self._final_df_place["Physical_Address"] = self._final_df_place[
            "Physical_Address"].str.title()
        # Created a column School_Management for State Name as NCES_BureauOfIndianEducation
        # and NCES_DepartmentOfDefenseEducationActivity as they are outlyin areas of United States.
        self._final_df_place["School_Management"] = np.where(
            self._final_df_place["State_Name"].str.contains(
                "NCES_BureauOfIndianEducation|NCES_DepartmentOfDefenseEducationActivity"
            ), self._final_df_place["State_Name"], '')
        # Checking if state code is not null and respectively adding state
        # abbrevation to physical address.
        self._final_df_place["Physical_Address"] = np.where(
            self._final_df_place['State_code'] == "",
            (self._final_df_place["Physical_Address"]),
            (self._final_df_place["Physical_Address"] + " " +
             self._final_df_place["Validated_State_Abbr"]))
        # Checking if ZIP4 is not null and respectively adding it
        # to physical address.
        self._final_df_place["Physical_Address"] = np.where(
            self._final_df_place['Location_ZIP4'] == "",
            (self._final_df_place["Physical_Address"] + " " +
             self._final_df_place["ZIP"]),
            (self._final_df_place["Physical_Address"] + " " +
             self._final_df_place["ZIP"] + "-" +
             self._final_df_place['Location_ZIP4']))

        self._final_df_place["Physical_Address"] = self._final_df_place[
            "Physical_Address"].str.replace("Po Box", "PO BOX")
        # Camel casing Public School Name and if the length of the school name
        # is less than 4 then the school name remains the same. Most of them
        # are abbrevations.
        self._final_df_place["Public_School_Name"] = np.where(
            self._final_df_place["Public_School_Name"].str.len() <= 4,
            self._final_df_place["Public_School_Name"],
            self._final_df_place["Public_School_Name"].astype(str).apply(
                lambda x: x.title()))
        # Sorting the values by descending order in year and dropping duplicates.
        self._final_df_place = self._final_df_place.sort_values(by=["year"],
                                                                ascending=False)
        self._final_df_place = self._final_df_place.reset_index(
            drop=True)  # Added this line
        self._final_df_place = self._final_df_place.drop_duplicates(
            subset=["school_state_code"]).reset_index(drop=True)

    @log_method_execution
    def _transform_district_place(self):
        """
        The Data for Place Entities is cleaned and written to a file.
        """
        self._final_df_place[
            'geoID'] = "sch" + self._final_df_place['Agency ID - NCES Assigned']
        self._final_df_place = self._final_df_place.rename(
            columns=self._renaming_columns)
        # Renaming the property values according to DataCommons.
        self._final_df_place = replace_values(self._final_df_place,
                                              replace_with_all_mappers=False,
                                              regex_flag=False)
        self._final_df_place['County_code'] = self._final_df_place[
            'County_code'].astype(str)
        self._final_df_place['State_code'] = self._final_df_place[
            'State_code'].astype(str)
        # In some cases The state code is not valid or is not a state.
        # For example: state_code:59, 63
        # In such cases, the state code is replaced with first 2 characters of
        # its respective county code
        self._final_df_place["State_code"] = np.where(
            self._final_df_place["State_code"].str.contains("59|63"),
            (self._final_df_place['County_code'].astype(str).str[:2]),
            (self._final_df_place["State_code"]))

        self._final_df_place['County_code'] = self._final_df_place[
            'County_code'].apply(lambda x: 'geoId/' + x if x != '' else '')
        self._final_df_place['State_code'] = self._final_df_place[
            'State_code'].apply(lambda x: 'geoId/' + x if x != '' else '')
        # Generates State code by mapping state abbrevation and USSTATE map
        # to fill the empty values in the state code column.
        self._final_df_place['State_code'] = np.where(
            self._final_df_place['State_code'] == "",
            (self._final_df_place['State_Abbr'].map(USSTATE_MAP)),
            (self._final_df_place['State_code']))
        # Creating a unique list of Sate Code and removing null values from source.
        state_list = list(pd.unique(self._final_df_place['State_code']))
        if '' in state_list:
            state_list.remove("")
        config = {
            'dc_api_batch_size': 200,
            'dc_api_retries': 3,
            'dc_api_retry_sec': 5,
            'dc_api_use_cache': False,
            'dc_api_root': None
        }
        dcid_check_state = dc_api_is_defined_dcid(state_list, config)
        dcid_check_state[""] = False
        # Generating a column for place property.
        self._final_df_place['ContainedInPlace'] = self._final_df_place[
            'State_code'].apply(lambda x: x if dcid_check_state[x] else '')
        # Reverse mapping State abbrevations from the current state_code
        # column to combine Physical Address with State Abbrevation.
        state_abbr = {v: k for k, v in USSTATE_MAP.items()}
        self._final_df_place['Validated_State_Abbr'] = self._final_df_place[
            'State_code'].replace(state_abbr)
        # Camel casing Physical Address
        self._final_df_place["Physical_Address"] = self._final_df_place[
            "Physical_Address"] + " " + self._final_df_place["City"]
        self._final_df_place["Physical_Address"] = self._final_df_place[
            "Physical_Address"].str.title()

        self._final_df_place["Physical_Address"] = np.where(
            self._final_df_place['ContainedInPlace'] == "",
            (self._final_df_place["Physical_Address"]),
            (self._final_df_place["Physical_Address"] + " " +
             self._final_df_place["Validated_State_Abbr"]))

        self._final_df_place["Physical_Address"] = np.where(
            self._final_df_place['Location_ZIP4'] == "",
            (self._final_df_place["Physical_Address"] + " " +
             self._final_df_place["ZIP"]),
            (self._final_df_place["Physical_Address"] + " " +
             self._final_df_place["ZIP"] + "-" +
             self._final_df_place['Location_ZIP4']))
        self._final_df_place["Physical_Address"] = self._final_df_place[
            "Physical_Address"].str.replace("Po Box", "PO Box")
        self._final_df_place["District_School_name"] = np.where(
            self._final_df_place["District_School_name"].str.len() <= 4,
            self._final_df_place["District_School_name"],
            self._final_df_place["District_School_name"].str.title())
        # Created a column School_Management for State Name as NCES_BureauOfIndianEducation
        # and NCES_DepartmentOfDefenseEducationActivity as they are outlyin areas of United States.
        self._final_df_place["School_Management"] = np.where(
            self._final_df_place["State_Name"].str.contains(
                "NCES_BureauOfIndianEducation|NCES_DepartmentOfDefenseEducationActivity"
            ), self._final_df_place["State_Name"], '')

        col_to_dcs = [
            'Lowest_Grade_Dist', 'Highest_Grade_Dist', 'Locale',
            'ContainedInPlace'
        ]
        for col in col_to_dcs:
            self._final_df_place[col] = self._final_df_place[col].replace(
                to_replace={'': pd.NA})
            self._final_df_place[col] = "dcs:" + self._final_df_place[col]
        self._final_df_place = self._final_df_place.sort_values(by=["year"],
                                                                ascending=False)
        self._final_df_place = self._final_df_place.drop_duplicates(
            subset=["school_state_code"]).reset_index(drop=True)

    @log_method_execution
    def _parse_file(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        '''
        This method combines and melts all the columns to one Final DataFrame.
        The final dataframe consists the preferred columns based on place or 
        demographics data.
        Args:
            raw_df (pd.DataFrame): cleaned Dataframes
        Returns:
            pd.DataFrame
        '''
        # Extracting year from the input file
        self._year = self._extract_year_from_headers(
            raw_df.columns.values.tolist())

        # Checks for a different year column in the input file
        year_check = self._verify_year_uniqueness(
            raw_df.columns.values.tolist())
        if not year_check:
            logging.info(
                f"Some columns in file are not of expected year {self._year} - correct the download config. Exiting.."
            )

        # Extracting the lower interval year as per DataCommons K12 Import
        raw_df["year"] = self._year[0:4].strip()

        # Clean the data
        df_cleaned = self._clean_data(raw_df)

        # Convert all columns to string and strip whitespaces
        for col in df_cleaned.columns.values.tolist():
            df_cleaned[col] = df_cleaned[col].astype('str').str.strip()

        # Clean columns
        df_cleaned = self._clean_columns(df_cleaned)
        # Adding prefix to the SchoolID as per DataCommons
        if self._import_name == "private_school":
            df_cleaned["school_state_code"] = \
                "nces/" + df_cleaned["School ID - NCES Assigned"]
        elif self._import_name == "public_school":
            # Ensure School ID is formatted correctly with leading zeros
            df_cleaned["School ID (12-digit) - NCES Assigned"] = df_cleaned[
                "School ID (12-digit) - NCES Assigned"].astype(str).str.zfill(
                    12)
            df_cleaned["school_state_code"] = "nces/" + df_cleaned[
                "School ID (12-digit) - NCES Assigned"]
        elif self._import_name == "district_school":
            df_cleaned['Agency ID - NCES Assigned'] = df_cleaned[
                'Agency ID - NCES Assigned'].astype(str).str.zfill(7)
            df_cleaned["school_state_code"] = \
                "geoId/sch" + df_cleaned["Agency ID - NCES Assigned"]

        curr_cols = df_cleaned.columns.values.tolist()
        curr_place = curr_cols
        data_cols = []
        data_place = []
        # Excludes the column name that are not required for Demographics.
        for pattern in self._exclude_columns:
            pat = f"^((?!{pattern}).)*$"
            r = re.compile(pat)
            curr_cols = list(filter(r.match, curr_cols))
        # Consideres only the column name patterns required for Demographics.
        for pattern in self._include_columns:
            r = re.compile(pattern)
            data_cols += list(filter(r.match, curr_cols))
        # Excludes the column name that are not required for Place Data.
        for pattern in self._exclude_col_place:
            pat = f"^((?!{pattern}).)*$"
            r = re.compile(pat)
            curr_place = list(filter(r.match, curr_place))
        # Consideres only the column name patterns required for Place Data.
        for pattern in self._include_col_place:
            r = re.compile(pattern)
            data_place += list(filter(r.match, curr_place))

        # Creating a list which is used to check for null values
        col_list = [*data_cols, *data_place]
        col_list = list(set(col_list))
        # Creating an exclude_list which has columns that will not be null.
        # Creating a drop_list through which the exclude_list items will be
        # removed
        drop_list = [
            item for item in col_list if item not in self._exclude_list
        ]
        # Replacing '–','†' with nan values.
        df_cleaned = df_cleaned.replace(_UNREADABLE_TEXT)
        # Writing duplicate school IDs to a file.
        df_duplicate = df_cleaned.copy()
        df_duplicate = df_duplicate[df_duplicate.duplicated(
            subset=self._school_id)]
        if df_duplicate.shape[0] >= 1:
            df_duplicate.to_csv(self._duplicate_csv_place,
                                index=False,
                                mode='a',
                                header=False)
        # Dropping school IDs whose entities are null based on the drop_list
        df_cleaned = df_cleaned.dropna(how='all', subset=drop_list)
        # Passing data_place list that contain columns required for place entities.
        df_place = df_cleaned[data_place]
        df_cleaned = df_cleaned.sort_values(by=data_cols, ascending=True)
        # Dropping Duplicate Schools based on School ID which is sort_value.
        df_cleaned = df_cleaned.drop_duplicates(subset=self._school_id,
                                                keep="first")

        if self._import_name in [
                "private_school", "district_school", "public_school"
        ]:
            df_place.loc[:, 'year'] = self._year[0:4].strip()

            df_place = df_place.loc[:, ~df_place.columns.duplicated()]
            if self._final_df_place.shape[0] > 0:

                #Merge the place columns for the current year which is across different files.
                df_dist_tmp = self._final_df_place.loc[
                    self._final_df_place['year'] == self._year[0:4].strip()]

                if df_dist_tmp.shape[0] > 0:
                    #If current year data is already there in main df - merge the columns

                    # Remove common columns excluding key columns so as to remove duplicates.
                    rem_common_columns = list(
                        set(df_place.columns.to_list()) -
                        set(self._key_col_place))

                    df_dist_tmp = df_dist_tmp.loc[:, ~df_dist_tmp.columns.
                                                  isin(rem_common_columns)]

                    # Merge the different files columns of same year with key columns

                    df_dist_tmp = pd.merge(df_dist_tmp,
                                           df_place,
                                           how="outer",
                                           on=self._key_col_place)

                else:
                    # The current year data not present in final df

                    df_dist_tmp = df_place

                # Concat the current processing year data to final place df

                self._final_df_place = pd.concat([
                    self._final_df_place.loc[self._final_df_place['year'] !=
                                             self._year[0:4].strip()],
                    df_dist_tmp
                ])

            else:
                # For the first file being processed set the final place dataframe to place columns from the current file.

                self._final_df_place = df_place

        if not self._generate_statvars:
            return df_cleaned[data_cols]
        # Melting all the columns to its respective observation.
        df_cleaned = df_cleaned.melt(id_vars=['school_state_code', 'year'],
                                     value_vars=data_cols,
                                     var_name='sv_name',
                                     value_name='observation')

        df_cleaned['observation'] = pd.to_numeric(df_cleaned['observation'],
                                                  errors='coerce')
        # Dropping empty obsevation values.
        df_cleaned["observation"] = df_cleaned["observation"].replace(
            to_replace={'': pd.NA})
        # Drop rows where the 'observation' column has negative values
        df_cleaned = df_cleaned[df_cleaned["observation"] >= 0]
        df_cleaned = df_cleaned.dropna(subset=['observation'])
        return df_cleaned

    @log_method_execution
    def dropping_scalingFactor_unit(self, df: pd.DataFrame) -> pd.DataFrame:
        '''
        Dropping the scalingFactor and unit for Pupil/Teacher Ratio variable.
        The values are not multiples of 100.
        Args:
            raw_df (pd.DataFrame): cleaned Dataframes
        Returns:
            pd.DataFrame
        '''
        df["scaling_factor"] = np.where(
            df["sv_name"].str.contains(
                "Percent_Student_AsAFractionOf_Count_Teacher"), '',
            df["scaling_factor"])
        df["unit"] = np.where(
            df["sv_name"].str.contains(
                "Percent_Student_AsAFractionOf_Count_Teacher"), '', df["unit"])
        return df

    @log_method_execution
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
                "scaling_factor", "unit"
            ])
            df_merged.to_csv(self._cleaned_csv_file_path, index=False)
        c = 0
        unique_sv_names = []
        city_dict = {}

        for input_file in sorted(self._input_files):
            c += 1
            logging.info(f"{c} - {os.path.basename(input_file)}")

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
                # Adding new columns scaling_factor:100 and unit:dcs:Percent
                #  wherever the SV is Percent.
                    df_parsed["scaling_factor"] = np.where(
                        df_parsed["sv_name"].str.contains("Percent"), '100', '')
                    df_parsed["unit"] = np.where(
                        df_parsed["sv_name"].str.contains("Percent"),
                        "dcs:Percent", '')
                    df_clean = self.dropping_scalingFactor_unit(df_parsed)
                    df_final = df_clean[[
                        "school_state_code", "year", "sv_name", "observation",
                        "scaling_factor", "unit"
                    ]]
                    # Dropping Duplicates and writing to a file
                    df_final.drop_duplicates(inplace=True)
                    df_final.to_csv(self._cleaned_csv_file_path,
                                    header=False,
                                    index=False,
                                    mode='a')
                    # The column unique SVs are extracted for MCF properties.
                    df_parsed = df_parsed.drop_duplicates(
                        subset=["sv_name"]).reset_index(drop=True)
                    curr_sv_names = df_parsed["sv_name"].values.tolist()
                    new_sv_names = list(
                        set(curr_sv_names) - set(unique_sv_names))
                    unique_sv_names = unique_sv_names + new_sv_names

                    df_parsed = df_parsed[df_parsed["sv_name"].isin(
                        new_sv_names)].reset_index(drop=False)
                dfs.append(df_parsed)
        # Based on the import_name, the place data is executed and written to a
        # file.
        if self._import_name == "private_school":
            self._transform_private_place()

            self._final_df_place.to_csv(self._csv_file_place,
                                        index=False,
                                        quoting=csv.QUOTE_NONNUMERIC)
            for Physical_Address, group in self._final_df_place.groupby(
                    'Physical_Address'):
                if len(group) > 1:
                    city_dict[Physical_Address] = group[
                        'school_state_code'].tolist()

        if self._import_name == "district_school":
            self._transform_district_place()
            self._final_df_place.to_csv(self._csv_file_place,
                                        index=False,
                                        quoting=csv.QUOTE_NONNUMERIC)

        if self._import_name == "public_school":
            self._transform_public_place()
            self._final_df_place.to_csv(self._csv_file_place,
                                        index=False,
                                        quoting=csv.QUOTE_NONNUMERIC)

        df_merged = pd.DataFrame()
        self._df = pd.concat(dfs)

    @log_method_execution
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

        f_deno = []
        for dcnode in mcf_:
            deno_matched = re.findall("(Node: dcid:)(\w+)", dcnode)[0][1]
            f_deno.append(deno_matched)
        # Passes the Node through check_dcid_existance to check if the SV is
        # already existing.
        node_status = check_dcid_existence(f_deno)
        f_deno = []
        for dcnode in mcf_:
            deno_matched = re.findall("(Node: dcid:)(\w+)", dcnode)[0][1]
            status = node_status[deno_matched]
            if not status:
                f_deno.append(dcnode)

        mcf_ = "\n\n".join(f_deno)
        with open(self._mcf_file_path, "w", encoding="UTF-8") as file:
            file.write(mcf_)

    @log_method_execution
    def generate_tmcf(self) -> None:
        """
        This method generates TMCF file w.r.t
        dataframe headers and defined TMCF template.
        Args:
            None

        Returns:
            None
        """

        tmcf = TMCF_TEMPLATE.format(import_name=self._import_name,
                                    observation_period=self._observation_period)
        # Writing Genereated TMCF to local path.
        with open(self._tmcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(tmcf.rstrip('\n'))

        # Generating tmcf file for NCES place entities based on the import name.
        if self._import_name == "private_school":
            with open(self._tmcf_file_place, 'w+', encoding='utf-8') as f_out:
                f_out.write(TMCF_TEMPLATE_PLACE_PRIVATE.rstrip('\n'))

        if self._import_name == "district_school":
            with open(self._tmcf_file_place, 'w+', encoding='utf-8') as f_out:
                f_out.write(TMCF_TEMPLATE_PLACE_DISTRICT.rstrip('\n'))

        if self._import_name == "public_school":
            with open(self._tmcf_file_place, 'w+', encoding='utf-8') as f_out:
                f_out.write(TMCF_TEMPLATE_PLACE_PUBLIC.rstrip('\n'))
