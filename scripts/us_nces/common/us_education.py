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

CODEDIR = os.path.dirname(__file__)
# For import common.replacement_functions
sys.path.insert(1, os.path.join(CODEDIR, '../../..'))
from util.statvar_dcid_generator import get_statvar_dcid


class USEducation:
    """
    USEducation is a base class which provides common implementation for
    generating CSV, MCF and tMCF files.
    """
    # Below variables will be initialized by sub-class (import specific)
    _import_name = ""
    _default_mcf_template = ""
    _split_headers_using_school_type = ""
    _possible_data_columns = None
    _exclude_data_columns = None

    def __init__(self,
                 input_files: list,
                 cleaned_csv_path: str = None,
                 mcf_file_path: str = None,
                 tmcf_file_path: str = None) -> None:
        self._input_files = input_files
        self._cleaned_csv_file_path = cleaned_csv_path
        self._mcf_file_path = mcf_file_path
        self._tmcf_file_path = tmcf_file_path
        self._year = None
        self._df = pd.DataFrame()
        if not os.path.exists(os.path.dirname(self._cleaned_csv_file_path)):
            os.mkdir(os.path.dirname(self._cleaned_csv_file_path))

    def set_cleansed_csv_file_path(self, cleansed_csv_file_path: str) -> None:
        self._cleaned_csv_file_path = cleansed_csv_file_path

    def set_mcf_file_path(self, mcf_file_path: str) -> None:
        self._mcf_file_path = mcf_file_path

    def set_tmcf_file_path(self, tmcf_file_path: str) -> None:
        self._tmcf_file_path = tmcf_file_path

    def input_file_to_df(self, f_path: str) -> pd.DataFrame:
        """Convert a file path to a dataframe."""
        with open(f_path, "r", encoding="UTF-8") as file:
            lines = file.readlines()
            # first six lines is data description and source we skip those
            assert all(lines[i] == '\n' for i in [1, 3, 5])
            # last seven lines is data legend and totals we skip those
            assert lines[-5].startswith('Data Source')
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

    def _generate_prop(self, data_df: pd.DataFrame):
        """
        Generate property columns in the dataframe data_df
        Args:
            data_df (pd.DataFrame): Input DataFrame
        Returns:
            _type_: _description_
        """
        for prop_, val_, format_ in DF_DEFAULT_MCF_PROP:
            data_df["prop_" + prop_] = format_((prop_, val_))

        for prop_ in SV_PROP_ORDER:
            if "prop_" + prop_ in data_df.columns.values.tolist():
                continue

            conf = FORM_STATVAR[prop_]
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
                                            replace_with_all_mappers=True)

            curr_val_mapper = dict(
                zip(unique_rows[column], unique_rows[curr_value_column]))

            data_df[curr_value_column] = data_df[column].map(curr_val_mapper)
        return data_df

    def _generate_stat_vars(self, data_df: pd.DataFrame,
                            prop_cols: str) -> pd.DataFrame:
        """
        Generates statvars using property columns.
        Args:
            data_df (pd.DataFrame): Input DataFrame
            prop_cols (str): property columns
        Returns:
            pd.DataFrame: DataFrame including statvar column
        """
        data_df['prop_node'] = '{' + \
                                    data_df[prop_cols].apply(
                                    lambda x: ','.join(x.dropna().astype(str)),
                                    axis=1) + \
                                '}'

        data_df['prop_node'] = data_df['prop_node'].apply(json.loads)
        data_df['sv_name'] = data_df['prop_node'].apply(get_statvar_dcid)
        data_df["sv_name"] = np.where(
            data_df["prop_measurementDenominator"].isin([np.nan]),
            data_df["sv_name"], data_df["sv_name"].str.replace("Count",
                                                               "Percent",
                                                               n=1))
        data_df['prop_node'] = data_df['sv_name'].apply(SV_NODE_FORMAT)

        stat_var_with_dcs = dict(zip(data_df["all_prop"], data_df['prop_node']))
        stat_var_without_dcs = dict(zip(data_df["all_prop"],
                                        data_df['sv_name']))

        return (stat_var_with_dcs, stat_var_without_dcs)

    def _generate_mcf_data(self, data_df: pd.DataFrame,
                           prop_cols: list) -> pd.DataFrame:

        data_df['mcf'] = data_df['prop_node'] + \
                    '\n' + \
                    data_df[prop_cols].apply(
                    func=lambda x: '\n'.join(x.dropna()),
                    axis=1).str.replace('"', '')
        mcf_mapper = dict(zip(data_df["all_prop"], data_df['mcf']))

        return mcf_mapper

    def _generate_stat_var_and_mcf(self, data_df: pd.DataFrame):
        """
        Generates the stat vars.
        Args:
            data_df (_type_): _description_
        Returns:
            _type_: _description_
        """
        prop_cols = ["prop_" + col for col in sorted(SV_PROP_ORDER)]

        data_df["all_prop"] = ""
        for col in prop_cols:
            data_df["all_prop"] += '_' + data_df[col]
        unique_props = data_df.drop_duplicates(subset=["all_prop"]).reset_index(
            drop=True)

        unique_props = unique_props.replace('', np.nan)
        stat_var_with_dcs, stat_var_without_dcs = self._generate_stat_vars(
            unique_props, prop_cols)
        mcf_mapper = self._generate_mcf_data(unique_props, prop_cols)

        data_df["prop_node"] = data_df["all_prop"].map(stat_var_with_dcs)
        data_df["sv_name"] = data_df["all_prop"].map(stat_var_without_dcs)
        data_df["mcf"] = data_df["all_prop"].map(mcf_mapper)

        data_df = data_df.drop(columns=["all_prop"]).reset_index(drop=True)
        data_df = data_df.drop(columns=prop_cols).reset_index(drop=True)

        return data_df

    def _parse_file(self, raw_df: pd.DataFrame,
                    school_type: str) -> pd.DataFrame:

        self._year = self._extract_year_from_headers(raw_df.columns.values.tolist())
        raw_df["year"] = "20" + self._year[-2:]

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
        data_cols = []

        for pattern in self._exclude_data_columns:
            pat = f"^((?!{pattern}).)*$"
            r = re.compile(pat)
            curr_cols = list(filter(r.match, curr_cols))

        for pattern in self._possible_data_columns:
            r = re.compile(pattern)
            data_cols += list(filter(r.match, curr_cols))

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
        df_merged = pd.DataFrame(columns=[
            "school_state_code", "year", "sv_name", "observation", "scaling_factor"
        ])
        df_merged.to_csv(self._cleaned_csv_file_path, index=False)
        c = 0
        unique_sv_names = []
        for input_file in sorted(self._input_files):
            c += 1
            print(f"{c} - {os.path.basename(input_file)}")

            raw_df = self.input_file_to_df(input_file)
            df_parsed = self._parse_file(raw_df, self._import_name)

            if df_parsed.shape[0] > 0:
                df_parsed = df_parsed.sort_values(
                by=["year", "sv_name", "school_state_code"])
                df_parsed = self._generate_prop(df_parsed)
                df_parsed = self._generate_stat_var_and_mcf(df_parsed)
                for col in df_parsed.columns.values.tolist():
                    df_parsed[col] = df_parsed[col].astype('str').str.replace("FeMale", "Female")
                df_parsed["scaling_factor"] = np.where(df_parsed["sv_name"].str.contains("Percent"),
                                                       100,'')
                df_final = df_parsed[[
                "school_state_code", "year", "sv_name", "observation", "scaling_factor"
                ]]
                df_final.to_csv(self._cleaned_csv_file_path, header=False, index=False, mode='a')

                df_parsed = df_parsed.drop_duplicates(subset=["sv_name"]).reset_index(drop=True)
                curr_sv_names = df_parsed["sv_name"].values.tolist()
                new_sv_names = list(set(curr_sv_names) - set(unique_sv_names))
                unique_sv_names = unique_sv_names + new_sv_names

                df_mcf = df_parsed[df_parsed["sv_name"].isin(new_sv_names)].reset_index(drop=False)
                dfs.append(df_mcf)

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
        unique_nodes_df = self._df.drop_duplicates(
            subset=["prop_node"]).reset_index(drop=True)

        mcf_ = unique_nodes_df.sort_values(by=["prop_node"])["mcf"].tolist()
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
