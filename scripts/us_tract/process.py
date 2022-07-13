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

import os
import re
import sys
import pandas as pd
from absl import app
from absl import flags

_CODEDIR = os.path.basename(__file__)
sys.path.insert(1, _CODEDIR)

# pylint: disable=wrong-import-position
from constants import (TMCF_TEMPLATE, MCF_TEMPLATE, INCOMPLETE_ACS,
                       HOUSEHOLD_PV, NUM_OF_VEHICLES_PV, HEADERMAP, URBAN,
                       CONF_2009_FILE, CONF_2017_FILE, ACS_LT_MOR)
# pylint: enable=wrong-import-position
_FLAGS = flags.FLAGS
_DEFAULT_INPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "input_files")

flags.DEFINE_string("input_path", _DEFAULT_INPUT_PATH,
                    "Import Data File's List")


def _update_headers(headers: list) -> list:
    """
    Updating header values in headers to its complete form.
    Example:
        short form                           full form
    pmiles_3mem_2veh         PersonMiles__With2AvailableVehicles_3Person
     vtrip_5mem_1veh        VehicleTrips__With1AvailableVehicles_5Person
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
                        f"{matchobj.group(3)}Person"
            ))
        else:
            updated_headers.append(HEADERMAP[header])
    return updated_headers


def _update_sv_col(data_df: pd.DataFrame) -> pd.DataFrame:
    """
    Updates sv column in data_df dataframe.
    Example:
    Input: data_df[['sv']]
                                             sv
                                    PersonMiles
                                   VehicleTrips
     PersonTrips_With1AvailableVehicles_2Person
    VehicleMiles_With4AvailableVehicles_4Person

    In-Processing: data_df[[ "sv", "sv_first_part", "sv_last_part"]]

                                                 sv   sv_first_part
                                        PersonMiles     PersonMiles
                                       VehicleTrips    VehicleTrips
         PersonTrips_With1AvailableVehicles_2Person     PersonTrips
        VehicleMiles_With4AvailableVehicles_4Person    VehicleMiles

                                  sv_last_part


                With1AvailableVehicles_2Person
                With4AvailableVehicles_4Person

    Output: data_df[["sv"]]
                                                                          sv
                                    Mean_PersonMiles_Household_Weekday_Urban
                                   Mean_VehicleTrips_Household_Weekday_Urban
     Mean_PersonTrips_Household_Weekday_With1AvailableVehicles_2Person_Urban
    Mean_VehicleMiles_Household_Weekday_With4AvailableVehicles_4Person_Urban

    Args:
        data_df (pd.DataFrame): Input DataFrame

    Returns:
        data_df (pd.DataFrame): DataFrame with updated sv column
    """
    data_df["sv_first_part"] = data_df["sv"].str.split("_With").str[0]
    data_df["sv_last_part"] = data_df["sv"]\
                                .str.replace("PersonMiles", "")\
                                .str.replace("PersonTrips", "")\
                                .str.replace("VehicleMiles", "")\
                                .str.replace("VehicleTrips", "")
    data_df['sv'] = "Mean_" + data_df[
        'sv_first_part'] + "_Household" + "_Weekday" + data_df[
            'sv_last_part'] + "_" + data_df['urban_group']
    return data_df


def _additional_process_2017(data_df: pd.DataFrame) -> pd.DataFrame:
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
    data_df = data_df[data_df['flag_manhattan_trt'] == 0]
    data_df = data_df[~data_df['urban_group'].isna()]
    # Mapping to actual values
    data_df['flag_acs_lt_moe'] = data_df['flag_acs_lt_moe'].map(ACS_LT_MOR)
    data_df['flag_incomplete_acs'] = data_df['flag_incomplete_acs'].map(
        INCOMPLETE_ACS)
    # Creating measurement column
    data_df['measurement_method'] = \
            'NationalHouseholdTransportationSurveyEstimates' + \
                data_df['flag_acs_lt_moe'] + \
                    data_df['flag_incomplete_acs']
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
    basic_cols = file_conf["basic_cols"]
    # Creating Population Columns
    pop_cols = []
    pop_cols += file_conf["pop_cols"]
    for xtra_cols in file_conf["extra_cols"]:
        pop_cols += xtra_cols
    req_cols = basic_cols + pop_cols
    data_df = data_df[req_cols]
    # Checking additional_process in the dictionary,
    # if True then performing additional process
    xtra_process = file_conf.get("additional_process", False)
    if xtra_process:
        data_df = _additional_process_2017(data_df)
    else:
        data_df['measurement_method'] = \
            'NationalHouseholdTransportationSurveyEstimates'
    # Removing null values from urban_group column
    data_df = data_df.dropna(subset=["urban_group"])
    data_df['urban_group'] = data_df['urban_group'].astype('int').map(URBAN)
    # Updating pop_cols to its complete names
    updated_pop_cols = _update_headers(pop_cols)
    data_df.columns = basic_cols + updated_pop_cols + ['measurement_method']
    data_df = data_df.rename(columns={"geocode": "geoid"})
    data_df = data_df.melt(
        id_vars=["geoid", "urban_group", "measurement_method"],
        value_vars=updated_pop_cols,
        var_name="sv",
        value_name="observation")
    data_df = _update_sv_col(data_df)
    # Adding Leading Zeros for Fips Code in the geoid column.
    # Before padding STATE = 9009990000
    # After padding STATE = 09009990000
    data_df["geoid"] = data_df["geoid"].astype("str").str.pad(width=11,
                                                              side="left",
                                                              fillchar="0")
    data_df["location"] = "geoId/" + data_df["geoid"]
    data_df["year"] = file_conf["year"]
    return data_df


def _generate_mcf(sv_list: list, mcf_file_path: str) -> None:
    """
    This method generates MCF file w.r.t
    dataframe headers and defined MCF template
    Args:
        sv_list (list): List of Statistical Variables
        mcf_file_path (str): Output MCF File Path
    """
    mcf_nodes = []
    for sv in sv_list:
        pvs = []
        name_pv = []
        dcid = sv
        sv_prop = [prop.strip() for prop in sv.split("_")]
        for prop in sv_prop:
            if prop in [
                    "PersonMiles", "PersonTrips", "VehicleTrips", "VehicleMiles"
            ]:
                prop = prop[0].lower() + prop[1:]
                pvs.append(f"measuredProperty: dcs:{prop}")
                name_pv.append(f"{prop}")
            elif prop in [
                    "1Person", "2Person", "3Person", "4Person", "5Person"
            ]:
                pv = HOUSEHOLD_PV.format(person=prop.replace('Person', ''))
                pvs.append(f"householdSize: {pv}")
                name_pv.append(f"{prop}")
            elif "AvailableVehicles" in prop:
                prop = prop.replace("With", "")\
                    .replace("AvailableVehicles", "")
                pv = NUM_OF_VEHICLES_PV.format(vehicle=prop)
                pvs.append(f"numberOfVehicles: {pv}")
                name_pv.append(f"{prop}")
            elif prop in ["Urban", "Rural", "SemiUrban"]:
                pvs.append(f"placeOfResidenceClassification: dcs:{prop}")
                name_pv.append(f"{prop}")
        mcf_nodes.append(MCF_TEMPLATE.format(dcid=dcid,
                                             xtra_pvs='\n'.join(pvs)))
    mcf = '\n'.join(mcf_nodes)
    # Writing Genereated MCF to local path.
    with open(mcf_file_path, 'w+', encoding='utf-8') as f_out:
        f_out.write(mcf.rstrip('\n'))


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
    final_cols = ["year", "location", "sv", "observation", "measurement_method"]
    final_df = pd.DataFrame()
    sv_list = []
    for file_path in input_files:
        if "latch_2017-b" in file_path:
            conf = CONF_2017_FILE
        elif "NHTS_2009_transfer" in file_path:
            conf = CONF_2009_FILE
        data_df = _process_household_transportation(file_path, conf)
        data_df = data_df.dropna(subset=["observation"])
        final_df = pd.concat([final_df, data_df[final_cols]])
        sv_list += data_df["sv"].to_list()
    final_df.to_csv(cleaned_csv_file_path, index=False)
    sv_list = list(set(sv_list))
    sv_list.sort()
    _generate_mcf(sv_list, mcf_file_path)
    _generate_tmcf(tmcf_file_path)


def main(_):
    input_path = _FLAGS.input_path
    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]
    data_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "output_files")
    # Creating Output Directory
    if not os.path.exists(data_file_path):
        os.mkdir(data_file_path)
    # Defining Output Files
    cleaned_csv_path = data_file_path + os.sep + \
        "us_transportation_household.csv"
    mcf_path = data_file_path + os.sep + \
        "us_transportation_household.mcf"
    tmcf_path = data_file_path + os.sep + \
        "us_transportation_household.tmcf"
    process(ip_files, cleaned_csv_path, mcf_path,\
        tmcf_path)


if __name__ == "__main__":
    app.run(main)
