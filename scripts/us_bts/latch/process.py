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
import re

from copy import deepcopy
import pandas as pd
import numpy as np
from absl import app, flags

_CODEDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, _CODEDIR)

# pylint: disable=wrong-import-position
from constants import (TMCF_TEMPLATE, MCF_TEMPLATE, HEADERMAP, CONF_2009_FILE,
                       CONF_2017_FILE, DEFAULT_SV_PROP, FINAL_DATA_COLS,
                       HHSIZE_NOOFVEHICLES_MAPPER, DEFAULT_MEASUREMENT_METHOD,
                       ACS_SRUVEY_MEASUREMENT_METHOD, RENAME_COLUMNS, PADDING,
                       FORM_SV)

from mcf_config import MCF_TEMPLATE_MAPPER

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
    dtype_conv = conf.get("dtype_conv", {})
    for col, dtype in dtype_conv.items():
        data_df[col] = data_df[col].astype(dtype)

    cols_mapper = conf.get("col_values_mapper", {})
    for col, values_mapper in cols_mapper.items():
        data_df[col] = data_df[col].map(values_mapper)

    return data_df


def _update_headers(headers: list) -> list:
    """
    Updating header values in headers to its complete form.
    Example:
        short form                           full form
    pmiles_3mem_2veh      PersonMilesTraveled__With2AvailableVehicles_3Persons
    vtrip_5mem_1veh      VehicleTripsTraveled__With1AvailableVehicles_5Persons

    Args:
        headers (list): List of header values in short form

    Returns:
        list: List of header values in complete form
    """
    updated_headers = []
    for header in headers:
        matchobj = re.match(r'(\w+)(_)(\d)(mem_)(\d)(veh)', header, re.M | re.I)
        if matchobj is not None:
            updated_headers.append((
                f"{HEADERMAP[matchobj.group(1)]}_" + \
                    f"With{matchobj.group(5)}AvailableVehicles_" + \
                        f"{matchobj.group(3)}Persons"
            ))
        else:
            updated_headers.append(HEADERMAP[header])
    return updated_headers


# pylint: disable=line-too-long
def _update_sv_col(data_df: pd.DataFrame) -> pd.DataFrame:
    """
    Updates sv column in data_df dataframe.

    Args:
        data_df (pd.DataFrame): Input DataFrame

    Returns:
        data_df (pd.DataFrame): DataFrame with updated sv column
    """

    data_df["measuredProperty"] = data_df[
        "householdSize_numberOfVehicles"].str.split("_With").str[0]
    for old_val, new_val in HHSIZE_NOOFVEHICLES_MAPPER.items():
        data_df["householdSize_numberOfVehicles"] = data_df["householdSize_numberOfVehicles"]\
                                .str.replace(old_val, new_val)
    data_df["sv"] = ""
    for spec in FORM_SV:
        spec_type = spec.split(":", maxsplit=1)[0]
        if spec_type == "col":
            data_df['sv'] += data_df[spec.split(":")[1]]
        else:
            data_df['sv'] += spec.split(":")[1]
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
    # Filtering flag_manhattan_trt column with 0 value,
    # Possible values are below
    # 1 = tract in Manhattan, NY; 0 = otherwise
    # Creating measurement column
    mm_cols = conf.get("measurement_method_cols", [])
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
    data_df = _apply_filters(data_df, file_conf)

    data_df = _column_operations(data_df, file_conf)
    data_df['measurement_method'] = DEFAULT_MEASUREMENT_METHOD
    # Checking additional_process in the dictionary,
    # if True then performing additional process
    xtra_process = file_conf.get("additional_process", False)
    if xtra_process:
        data_df = _additional_process_2017(data_df, file_conf)

    # Updating pop_cols to its complete names
    updated_pop_cols = _update_headers(pop_cols)
    data_df.columns = basic_cols + updated_pop_cols + ['measurement_method']
    data_df = data_df.rename(columns=RENAME_COLUMNS)
    data_df = data_df.melt(
        id_vars=["geoid", "urban_group", "measurement_method"],
        value_vars=updated_pop_cols,
        var_name="householdSize_numberOfVehicles",
        value_name="observation")
    data_df = _update_sv_col(data_df)

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


def _generate_mcf(sv_names: list, mcf_file_path: str) -> None:
    """
    This method generates MCF file w.r.t
    dataframe headers and defined MCF template

    Args:
        sv_names (list): List of Statistical Variables
        mcf_file_path (str): Output MCF File Path
    """
    mcf_nodes = []
    dcid_nodes = {}
    for sv in sv_names:
        pvs = []
        sv_pvs = deepcopy(DEFAULT_SV_PROP)
        for prop, prop_conf in MCF_TEMPLATE_MAPPER.items():
            if prop in sv:
                regex = prop_conf.get("regex", False)
                if regex:
                    prop_val = regex(sv)
                prop_key = prop_conf["key"]
                prop_val = prop_conf["value"](prop_val)
                pvs.append(prop_conf["format"](prop_key, prop_val))
                sv_pvs[prop_key] = prop_val
        resolved_dcid = get_statvar_dcid(sv_pvs)
        dcid_nodes[sv] = resolved_dcid
        mcf_nodes.append(
            MCF_TEMPLATE.format(dcid=resolved_dcid, xtra_pvs='\n'.join(pvs)))
    mcf = '\n'.join(mcf_nodes)
    # Writing Genereated MCF to local path.
    with open(mcf_file_path, 'w+', encoding='utf-8') as f_out:
        f_out.write(mcf.rstrip('\n'))
    return dcid_nodes


def _generate_tmcf(tmcf_file_path: str) -> None:
    """
    This method generates TMCF file w.r.t
    dataframe headers and defined TMCF template.

    Args:
        tmcf_file_path (str): Output TMCF File Path
    """
    with open(tmcf_file_path, 'w+', encoding='utf-8') as f_out:
        f_out.write(TMCF_TEMPLATE.rstrip('\n'))


def process(input_files: list, cleaned_csv_file_path: str, mcf_file_path: str,
            tmcf_file_path: str):
    """
    Process Input Raw Files and apply transformations to generate final
    CSV, MCF and TMCF files.
    """
    final_df = pd.DataFrame()
    sv_names = []
    for file_path in input_files:
        print("--------")
        print(os.path.basename(file_path))
        if "latch_2017-b" in file_path:
            conf = CONF_2017_FILE
        elif "NHTS_2009_transfer" in file_path:
            conf = CONF_2009_FILE
        data_df = _process_household_transportation(file_path, conf)
        data_df = data_df.dropna(subset=["observation"])
        final_df = pd.concat([final_df, data_df[FINAL_DATA_COLS]])
        sv_names += data_df["sv"].to_list()
    final_df = _promote_measurement_method(final_df)
    sv_names = list(set(sv_names))
    sv_names.sort()
    updated_sv = _generate_mcf(sv_names, mcf_file_path)
    final_df["sv"] = final_df["sv"].map(updated_sv)
    _generate_tmcf(tmcf_file_path)
    final_df = final_df.sort_values(by=["year", "location", "sv"])
    final_df.to_csv(cleaned_csv_file_path, index=False)


def main(_):
    input_path = _FLAGS.input_path
    try:
        ip_files = os.listdir(input_path)
    except FileNotFoundError:
        logger.error("Run the download.py script first.")
        sys.exit(1)
    ip_files = [os.path.join(input_path, file) for file in ip_files]
    # ip_files = [ip_files[0]]
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
