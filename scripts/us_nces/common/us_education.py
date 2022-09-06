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
This Python module is generalized to work with different Eurostat import such as
Physical Activity, BMI, Alcohol Consumption, Tobacco Consumption...

EuroStat class in this module provides methods to generate processed CSV, MCF &
TMCF files.

_propety_correction() and _sv_name_correction() are abstract methods, these 
method needs to implemented by Subclasses.
"""
import functools
import io
import json
import os
import sys
import re
import pandas as pd
import numpy as np
from absl import app, flags

from replacement_functions import replace_values
from prop_conf import *

CODEDIR = os.path.dirname(__file__)
# For import common.replacement_functions
sys.path.insert(1, os.path.join(CODEDIR, '../../..'))
from util.statvar_dcid_generator import get_statvar_dcid

_FLAGS = flags.FLAGS
default_input_path = os.path.join(CODEDIR, "input_files")
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")

_TMCF_TEMPLATE = ("{school_type}")
SPLIT_HEADER_ON_SCHOOL_TYPE = "[Private School]"


class USEducation:
    """
    USEducation is a base class which provides common implementation for generating 
    CSV, MCF and tMCF files.
    """
    # Below variables will be initialized by sub-class (import specific)
    _school_type = ""
    _default_mcf_template = ""

    def __init__(self, input_files: list, csv_file_path: str,
                 mcf_file_path: str, tmcf_file_path: str) -> None:
        self._input_files = input_files
        self._cleaned_csv_file_path = csv_file_path
        self._mcf_file_path = mcf_file_path
        self._tmcf_file_path = tmcf_file_path
        self._df = pd.DataFrame()

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
        year_pattern = r"(\[(Private|Public) School\])(\s)(?P<year>\d\d\d\d-\d\d)"
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
                col.split(SPLIT_HEADER_ON_SCHOOL_TYPE)[0].strip())
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
            data_df[curr_prop_column] = data_df[curr_prop_column].str.split(
                pattern, expand=True)[position]
            data_df[curr_prop_column] = data_df[curr_prop_column].fillna('None')

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
            print(unique_rows[["curr_prop", curr_value_column]])
            unique_rows = self._apply_regex(unique_rows, conf,
                                            curr_value_column)
            print(unique_rows[["curr_prop", curr_value_column]])

            # unique_rows[curr_value_column] = unique_rows[curr_value_column].apply(
            #     conf["update_value"])
            unique_rows[curr_value_column] = unique_rows[[
                "curr_prop", curr_value_column
            ]].apply(conf["pv_format"], axis=1)
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
        data_df['prop_Node'] = '{' + \
                                    data_df[prop_cols].apply(
                                    lambda x: ','.join(x.dropna().astype(str)),
                                    axis=1) + \
                                    '}'

        data_df['prop_Node'] = data_df['prop_Node'].apply(json.loads)
        data_df['sv'] = data_df['prop_Node'].apply(get_statvar_dcid)
        data_df['prop_Node'] = data_df['sv'].apply(SV_NODE_FORMAT)

        stat_var_with_dcs = dict(zip(data_df["all_prop"], data_df['prop_Node']))
        stat_var_without_dcs = dict(zip(data_df["all_prop"], data_df['sv']))

        return (stat_var_with_dcs, stat_var_without_dcs)

    def _generate_mcf(self, data_df: pd.DataFrame,
                      prop_cols: list) -> pd.DataFrame:

        data_df['mcf'] = data_df['prop_Node'] + \
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
        prop_cols = ["prop_" + col for col in SV_PROP_ORDER]

        data_df["all_prop"] = ""
        for col in prop_cols:
            data_df["all_prop"] += '_' + data_df[col]
        unique_props = data_df.drop_duplicates(subset=["all_prop"]).reset_index(
            drop=True)

        unique_props = unique_props.replace('', np.nan)

        stat_var_with_dcs, stat_var_without_dcs = self._generate_stat_vars(
            unique_props, prop_cols)
        mcf_mapper = self._generate_mcf(unique_props, prop_cols)

        data_df["prop_Node"] = data_df["all_prop"].map(stat_var_with_dcs)
        data_df["sv"] = data_df["all_prop"].map(stat_var_without_dcs)
        data_df["mcf"] = data_df["all_prop"].map(mcf_mapper)

        data_df = data_df.drop(columns=["all_prop"]).reset_index(drop=True)
        data_df = data_df.drop(columns=prop_cols).reset_index(drop=True)

        return data_df

    def _write_to_mcf_file(self, data_df: pd.DataFrame, mcf_file_path: str):
        """
        Writing MCF nodes to a local file.
        Args:
            data_df (pd.DataFrame): Input DataFrame
            mcf_file_path (str): MCF file
        """

        unique_nodes_df = data_df.drop_duplicates(
            subset=["prop_Node"]).reset_index(drop=True)

        mcf_ = unique_nodes_df.sort_values(by=["prop_Node"])["mcf"].tolist()
        mcf_ = "\n\n".join(mcf_)

        with open(mcf_file_path, "w", encoding="UTF-8") as file:
            file.write(mcf_)

    def _parse_file(self, raw_df: pd.DataFrame,
                    school_type: str) -> pd.DataFrame:

        year = self._extract_year_from_headers(raw_df.columns.values.tolist())
        raw_df["year"] = year

        df_cleaned = self._clean_data(raw_df)

        for col in df_cleaned.columns.values.tolist():
            df_cleaned[col] = \
                df_cleaned[col].astype('str').str.strip()

        df_cleaned = self._clean_columns(df_cleaned)
        df_cleaned["school_state_code"] = df_cleaned[[
            "School ID - NCES Assigned", "ANSI/FIPS State Code"
        ]].apply("_".join, axis=1)

        df_cleaned = df_cleaned.melt(
            id_vars=['school_state_code', 'year'],
            value_vars=[
                'Grade 10 Students', 'Grade 11 Students', 'Grade 12 Students',
                'American Indian/Alaska Native Students',
                'Asian or Asian/Pacific Islander Students'
            ],
            var_name='sv_name',
            value_name='observation')

        df_cleaned['observation'] = pd.to_numeric(df_cleaned['observation'],
                                                  errors='coerce')
        df_cleaned = replace_values(df_cleaned)

        df_cleaned["observation"] = df_cleaned["observation"].replace(
            to_replace={'': pd.NA})
        df_cleaned = df_cleaned.dropna(subset=['observation'])
        return df_cleaned

    def _merge_csvs_helper(self, df_left, df_right):
        cols_only_in_right = df_right.columns.difference(df_left.columns)
        return pd.merge(df_left,
                        df_right[cols_only_in_right],
                        left_index=True,
                        right_index=True,
                        how='outer')

    def get_join_col(self):
        """Get the join column for a given school type."""

        school_type_to_join_col = {
            'district': [
                'Agency ID - NCES Assigned [District] Latest available year'
            ],
            'publicschool': [
                'School ID - NCES Assigned [Public School] Latest available year'
            ],
            'privateschool': [
                'School ID - NCES Assigned [Private School] Latest available year'
            ],
        }
        if self._school_type in school_type_to_join_col:
            return school_type_to_join_col[self._school_type]
        raise ValueError(f'Invalid school_type {(self._school_type)}')

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
        join_col = self.get_join_col()
        for input_file in self._input_files:
            raw_df = self.input_file_to_df(input_file)
            df_parsed = self._parse_file(raw_df, self._school_type)
        df_parsed = self._generate_prop(df_parsed)
        df_parsed = self._generate_stat_var_and_mcf(df_parsed)
        self._write_to_mcf_file(
            df_parsed,
            "scripts/us_nces/demographics/private_school/Education.mcf")
        df_cleaned.to_csv("Education.csv", index=False)
        # df_parsed = df_parsed.set_index(join_col)
        # dfs.append(df)

        # merged_df = functools.reduce(self._merge_csvs_helper, dfs)
        return self._df

    def generate_mcf(self) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template

        Args:
            sv_list (list) : List of DataFrame Columns

        Returns:
            None    
        """
        pass

    def generate_tmcf(self) -> None:
        """
        This method generates TMCF file w.r.t
        dataframe headers and defined TMCF template.

        Args:
            None

        Returns:
            None
        """
        pass
        # tmcf = _TMCF_TEMPLATE.format(import_name=self._school_type)
        # # Writing Genereated TMCF to local path.
        # with open(self._tmcf_file_path, 'w+', encoding='utf-8') as f_out:
        #     f_out.write(tmcf.rstrip('\n'))
