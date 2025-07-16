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
    2017    latch_2017-b
    2009    NHTS_2009_transfer (one file per state, 50 Files)

Before running this module, run input_files.py script, it downloads required
input files, creates necessary folders for processing.
Folder information
input_files - downloaded files (from US census website) are placed here
output_files - output files (mcf, tmcf and csv are written here)
"""
from asyncio.log import logger
import os
import sys
import json

import pandas as pd
import numpy as np
from absl import app, flags

_CODEDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, _CODEDIR)

# pylint: disable=wrong-import-position
# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
from constants import *
# pylint: enable=wildcard-import
# pylint: enable=unused-wildcard-import

sys.path.insert(1, os.path.join(_CODEDIR, '../../../util/'))

# pylint: disable=import-error
from statvar_dcid_generator import get_statvar_dcid
# pylint: enable=import-error
# pylint: enable=wrong-import-position
_FLAGS = flags.FLAGS
_DEFAULT_INPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "input_files")

flags.DEFINE_string("input_path", _DEFAULT_INPUT_PATH,
                    "Import Data File's List")


def _promote_measurement_method(data_df: pd.DataFrame) -> pd.DataFrame:
    """
    Promote Measurement method for SV's having two different
    measurement methods for same year and place.

    Args:
        data_df (pd.DataFrame): Input DataFrame

    Returns:
        pd.DataFrame: DataFrame
    """
    acs_survey_df = data_df[data_df["measurement_method"] ==
                            ACS_SRUVEY_MEASUREMENT_METHOD].reset_index(
                                drop=True)

    acs_survey_rows = list(acs_survey_df['location'] + '_' +
                           acs_survey_df['sv'])

    data_df['info'] = data_df['location'] + '_' + data_df['sv']

    # Adding Measurement Method based on a condition
    data_df['measurement_method'] = np.where(
        data_df['info'].isin(acs_survey_rows), ACS_SRUVEY_MEASUREMENT_METHOD,
        data_df['measurement_method'])

    data_df = data_df.drop(columns=["info"])

    return data_df


def _column_operations(data_df: pd.DataFrame, conf: dict) -> pd.DataFrame:
    """
    Performs Column operations such as data type conversion,
    values mapping to original metadata.

    Args:
        data_df (pd.DataFrame): Input DataFrame
        conf (dict): Config

    Returns:
        pd.DataFrame: _description_
    """
    dtype_conv = conf.get("dtype_conv", {})
    for col, dtype in dtype_conv.items():
        data_df[col] = data_df[col].astype(dtype)

    cols_mapper = conf.get("col_values_mapper", {})
    for col, values_mapper in cols_mapper.items():
        data_df[col] = data_df[col].map(values_mapper)

    return data_df


def _filter_equals(data_df: pd.DataFrame, conf: dict) -> pd.DataFrame:

    filter_equals = conf.get("equals", False)
    if filter_equals:
        for col, value in filter_equals.items():
            data_df = data_df[data_df[col] == value]

    return data_df


def _filter_dropna(data_df: pd.DataFrame, conf: dict):

    filter_dropna = conf.get("dropna", False)
    if filter_dropna:
        data_df = data_df.dropna(subset=filter_dropna)

    return data_df


def _apply_filters(data_df, file_conf):

    # Removing null values from urban_group column
    filters = file_conf.get("filters", False)

    if filters:
        data_df = _filter_equals(data_df, file_conf["filters"])
        data_df = _filter_dropna(data_df, file_conf["filters"])

    return data_df


# pylint: enable=line-too-long
def _additional_process_2017(data_df: pd.DataFrame, conf: dict) -> pd.DataFrame:
    """
    Performs additional processing on data_df dataframe for the year 2017.

    Args:
        data_df (pd.DataFrame): Input DataFrame

    Returns:
        pd.DataFrame: Output DataFrame
    """
    mm_cols = conf.get("cols_for_measurement_method", [])
    if mm_cols != []:
        data_df['measurement_method'] = DEFAULT_MEASUREMENT_METHOD + \
                                        data_df.loc[:,mm_cols].sum(axis=1)

    return data_df


def _process_household_transportation(input_file: str,
                                      file_conf: dict) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists
    transportation household data for years 2009, 2017.

    Args:
        input_file (str): DataFrame having raw data

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    data_df = pd.read_csv(filepath_or_buffer=input_file,
                          sep=file_conf["input_file_delimiter"])

    basic_cols = file_conf.get("basic_cols", [])
    # Creating Population Columns
    pop_cols = file_conf.get("pop_cols", []) + file_conf.get("extra_cols", [])

    data_df = data_df[basic_cols + pop_cols]
    data_df = data_df.rename(columns=RENAME_COLUMNS)

    columns_info = [basic_cols, pop_cols]
    for column_var in columns_info:
        for idx, column in enumerate(column_var):
            column_var[idx] = RENAME_COLUMNS.get(column, column)

    data_df = _apply_filters(data_df, file_conf)

    data_df = _column_operations(data_df, file_conf)

    data_df['measurement_method'] = DEFAULT_MEASUREMENT_METHOD

    # Checking additional_process in the dictionary,
    # if True then performing additional process
    xtra_process = file_conf.get("additional_process", False)
    if xtra_process:
        data_df = _additional_process_2017(data_df, file_conf)

    id_vars = [col for col in data_df.columns if col not in pop_cols]

    data_df = data_df.melt(id_vars=id_vars,
                           value_vars=pop_cols,
                           var_name=MELT_VAR_COL,
                           value_name=MELT_OBV_COL)

    # Adding Leading Zeros for Fips Code in the geoid column.
    # Before padding STATE = 9009990000
    # After padding STATE = 09009990000
    data_df["geoid"] = data_df["geoid"].astype("str").str.pad(
        width=PADDING["width"],
        side=PADDING["side"],
        fillchar=PADDING["fillchar"])

    data_df["location"] = "geoId/" + data_df["geoid"]
    data_df["year"] = file_conf["year"]

    return data_df


def _generate_tmcf(tmcf_file_path: str) -> None:
    """
    This method generates TMCF file w.r.t
    dataframe headers and defined TMCF template.

    Args:
        tmcf_file_path (str): Output TMCF File Path
    """
    with open(tmcf_file_path, 'w+', encoding='utf-8') as f_out:
        f_out.write(TMCF_TEMPLATE.rstrip('\n'))


def _apply_regex(data_df: pd.DataFrame, conf: dict, curr_prop_column: str):
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

    return data_df


def _generate_prop(data_df: pd.DataFrame):
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
        unique_rows = _apply_regex(unique_rows, conf, curr_value_column)
        unique_rows[curr_value_column] = unique_rows[curr_value_column].apply(
            conf["update_value"])
        unique_rows[curr_value_column] = unique_rows[[
            "curr_prop", curr_value_column
        ]].apply(conf["pv_format"], axis=1)

        curr_val_mapper = dict(
            zip(unique_rows[column], unique_rows[curr_value_column]))
        data_df[curr_value_column] = data_df[column].map(curr_val_mapper)

    return data_df


def _generate_stat_vars(data_df: pd.DataFrame, prop_cols: str) -> pd.DataFrame:
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


def _generate_mcf(data_df: pd.DataFrame, prop_cols: list) -> pd.DataFrame:

    data_df['mcf'] = data_df['prop_Node'] + \
                '\n' + \
                data_df[prop_cols].apply(
                func=lambda x: '\n'.join(x.dropna()),
                axis=1).str.replace('"', '')
    mcf_mapper = dict(zip(data_df["all_prop"], data_df['mcf']))

    return mcf_mapper


def _generate_stat_var_and_mcf(data_df: pd.DataFrame):
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

    stat_var_with_dcs, stat_var_without_dcs = _generate_stat_vars(
        unique_props, prop_cols)
    mcf_mapper = _generate_mcf(unique_props, prop_cols)

    data_df["prop_Node"] = data_df["all_prop"].map(stat_var_with_dcs)
    data_df["sv"] = data_df["all_prop"].map(stat_var_without_dcs)
    data_df["mcf"] = data_df["all_prop"].map(mcf_mapper)

    data_df = data_df.drop(columns=["all_prop"]).reset_index(drop=True)
    data_df = data_df.drop(columns=prop_cols).reset_index(drop=True)

    return data_df


def _write_to_mcf_file(data_df: pd.DataFrame, mcf_file_path: str):
    """
    Writing MCF nodes to a local file.
    Args:
        data_df (pd.DataFrame): Input DataFrame
        mcf_file_path (str): MCF file
    """

    unique_nodes_df = data_df.drop_duplicates(subset=["prop_Node"]).reset_index(
        drop=True)

    mcf_ = unique_nodes_df.sort_values(by=["prop_Node"])["mcf"].tolist()
    if URBAN_RURAL_MCF_NODE:
        mcf_.append(URBAN_RURAL_MCF_NODE)

    mcf_ = "\n\n".join(mcf_)

    with open(mcf_file_path, "w", encoding="UTF-8") as file:
        file.write(mcf_)


def _post_process(data_df: pd.DataFrame, cleaned_csv_file_path: str,
                  mcf_file_path: str, tmcf_file_path: str):
    """
    Post Processing on the transformed dataframe such as
    1. Create stat-vars
    2. Create mcf file
    3. Create tmcf file

    Args:
        data_df (pd.DataFrame): _description_
        cleaned_csv_file_path (str): _description_
        mcf_file_path (str): _description_
        tmcf_file_path (str): _description_
    """

    data_df = _generate_prop(data_df)
    data_df = _generate_stat_var_and_mcf(data_df)
    _write_to_mcf_file(data_df, mcf_file_path)

    _generate_tmcf(tmcf_file_path)

    data_df = _promote_measurement_method(data_df)
    data_df = data_df.sort_values(by=["year", "location", "sv"])
    data_df[FINAL_DATA_COLS].to_csv(cleaned_csv_file_path, index=False)


def process(input_files: list, cleaned_csv_file_path: str, mcf_file_path: str,
            tmcf_file_path: str):
    """
    Process Input Raw Files and apply transformations to generate final
    CSV, MCF and TMCF files.
    """
    final_df = pd.DataFrame()

    for file_path in input_files:

        if "latch_2017-b" in file_path:
            conf = CONF_2017_FILE
        elif "NHTS_2009_transfer" in file_path:
            conf = CONF_2009_FILE

        data_df = _process_household_transportation(file_path, conf)
        data_df = data_df.dropna(subset=["observation"])
        final_df = pd.concat([final_df, data_df])

    _post_process(final_df, cleaned_csv_file_path, mcf_file_path,
                  tmcf_file_path)


def main(_):

    input_path = _FLAGS.input_path
    try:
        ip_files = os.listdir(input_path)
    except FileNotFoundError:
        logger.error("Run the download.py script first.")
        sys.exit(1)
    ip_files = [os.path.join(input_path, file) for file in ip_files]
    output_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "output_files")
    # Creating Output Directory
    if not os.path.exists(output_file_path):
        os.mkdir(output_file_path)
    # Defining Output Files

    cleaned_csv_path = os.path.join(output_file_path,
                                    "us_transportation_household.csv")
    mcf_path = os.path.join(output_file_path, "us_transportation_household.mcf")
    tmcf_path = os.path.join(output_file_path,
                             "us_transportation_household.tmcf")
    process(ip_files, cleaned_csv_path, mcf_path, tmcf_path)


if __name__ == "__main__":
    app.run(main)
