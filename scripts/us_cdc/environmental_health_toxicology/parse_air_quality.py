# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
import pandas as pd
from absl import app, logging, flags
from pathlib import Path
import sys

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_MODULE_DIR, '../../../util/'))
import file_util

_FLAGS = flags.FLAGS
flags.DEFINE_string('input_file_path', 'input_files', 'Input files path')
flags.DEFINE_string(
    'config_file', 'gs://unresolved_mcf/cdc/environmental/import_configs.json',
    'Config file path')
flags.DEFINE_string('output_file_path', 'output', 'Output files path')
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_INPUT_FILE_PATH = None
_OUTPUT_FILE_PATH = None
record_count_query = '?$query=select%20count(*)%20as%20COLUMN_ALIAS_GUARD__count'

# Mapping of column names in file to StatVar names.
STATVARS = {
    "DS_PM_pred": "Mean_Concentration_AirPollutant_PM2.5",
    "ds_pm_pred": "Mean_Concentration_AirPollutant_PM2.5",
    "ds_pm_stdd": "Mean_Concentration_AirPollutant_PM2.5_StandardError",
    "DS_O3_pred": "Mean_Concentration_AirPollutant_Ozone",
    "ds_o3_pred": "Mean_Concentration_AirPollutant_Ozone",
    "PM25_max_pred": "Max_Concentration_AirPollutant_PM2.5",
    "PM25_med_pred": "Median_Concentration_AirPollutant_PM2.5",
    "PM25_mean_pred": "Mean_Concentration_AirPollutant_PM2.5",
    "PM25_pop_pred": "PopulationWeighted_Concentration_AirPollutant_PM2.5",
    "O3_max_pred": "Max_Concentration_AirPollutant_Ozone",
    "O3_med_pred": "Median_Concentration_AirPollutant_Ozone",
    "O3_mean_pred": "Mean_Concentration_AirPollutant_Ozone",
    "O3_pop_pred": "PopulationWeighted_Concentration_AirPollutant_Ozone"
}

# Mapping of month abbreviations to month numbers.
MONTH_MAP = {
    "JAN": 1,
    "FEB": 2,
    "MAR": 3,
    "APR": 4,
    "MAY": 5,
    "JUN": 6,
    "JUL": 7,
    "AUG": 8,
    "SEP": 9,
    "OCT": 10,
    "NOV": 11,
    "DEC": 12
}


# this method is applicable only for "census tract PM25"
def add_prefix_zero(value, length):
    return value.zfill(length)


def clean_air_quality_data(configs, importname, inputpath, outputpath):
    """
    Args:
        configs: dictionary of all info required for this import 
                such as source urls, input and output file names
                for the 4 cdc imports.
        importname: name of the import
        inputpath: path to a comma-separated CDC air quality data file
        outputpath: path for the cleaned csv to be stored
    Returns:
        a cleaned csv file
    """
    try:
        global output_file_name
        logging.info(f"import name from command line {importname}")
        for config in configs:
            if config["import_name"] == importname:
                files = config["files"]
                for file_info in files:
                    output_file_name = file_info["output_file_name"]
                    input_file_name = file_info["input_file_name"]
                    input_file_path = os.path.join(inputpath, input_file_name)
                    output_file_path = os.path.join(outputpath,
                                                    output_file_name)
                    logging.info(f"input_file_name: {input_file_name}")
                    logging.info(f"output_file_name: {output_file_name}")
                    if str(input_file_name).endswith('.csv'):
                        logging.info(f"Cleaning {input_file_name} ....")
                        logging.info(f"Cleaning {input_file_path} ....")
                        try:
                            data = pd.read_csv(input_file_path)
                            data["date"] = pd.to_datetime(data["date"],
                                                          yearfirst=True)
                            data["date"] = pd.to_datetime(data["date"],
                                                          format="%Y-%m-%d")

                            if "PM2.5" in input_file_name:
                                census_tract = "ds_pm"
                            elif "Ozone" in input_file_name:
                                census_tract = "ds_o3"
                            if "Census" in input_file_name:
                                if "PM2.5" in input_file_name:
                                    data = pd.melt(
                                        data,
                                        id_vars=[
                                            'year', 'date', 'statefips',
                                            'countyfips', 'ctfips', 'latitude',
                                            'longitude'
                                        ],
                                        value_vars=[
                                            str(census_tract + '_pred'),
                                            str(census_tract + '_stdd')
                                        ],
                                        var_name='StatisticalVariable',
                                        value_name='Value')
                                elif "Ozone" in input_file_name:
                                    data = pd.melt(
                                        data,
                                        id_vars=[
                                            'year', 'date', 'statefips',
                                            'countyfips', 'ctfips', 'latitude',
                                            'longitude', census_tract + '_stdd'
                                        ],
                                        value_vars=[
                                            str(census_tract + '_pred')
                                        ],
                                        var_name='StatisticalVariable',
                                        value_name='Value')
                                data.rename(
                                    columns={census_tract + '_stdd': 'Error'},
                                    inplace=True)
                                max_length = data['ctfips'].astype(
                                    str).str.len().max()
                                data['ctfips'] = data['ctfips'].astype(
                                    str).apply(lambda x: add_prefix_zero(
                                        x, max_length))
                                data["dcid"] = "geoId/" + data["ctfips"].astype(
                                    str)
                                data['StatisticalVariable'] = data[
                                    'StatisticalVariable'].map(STATVARS)
                            elif "County" in input_file_name and "PM" in input_file_name:
                                data["statefips"] = data["statefips"].astype(
                                    str).str.zfill(2)
                                data["countyfips"] = data["countyfips"].astype(
                                    str).str.zfill(3)
                                data["dcid"] = "geoId/" + data[
                                    "statefips"] + data["countyfips"]
                            elif "County" in input_file_name and "Ozone" in input_file_name:
                                data["statefips"] = data["statefips"].astype(
                                    str).str.zfill(2)
                                data["countyfips"] = data["countyfips"].astype(
                                    str).str.zfill(3)
                                data["dcid"] = "geoId/" + data[
                                    "statefips"] + data["countyfips"]
                            data.to_csv(output_file_path,
                                        float_format='%.6f',
                                        index=False)
                            logging.info(
                                f"Finished cleaning file {output_file_name}!")
                        except:
                            logging.info("Not reading input file...!")
    except Exception as e:
        logging.fatal(f"Error while processing the data: {e}")


def main(_):
    """Main function to generate the cleaned csv file."""
    global _INPUT_FILE_PATH, _OUTPUT_FILE_PATH
    _INPUT_FILE_PATH = _FLAGS.input_file_path
    _INPUT_FILE_PATH = os.path.join(_MODULE_DIR, _FLAGS.input_file_path)
    Path(_INPUT_FILE_PATH).mkdir(parents=True, exist_ok=True)
    _OUTPUT_FILE_PATH = os.path.join(_MODULE_DIR, _FLAGS.output_file_path)
    Path(_OUTPUT_FILE_PATH).mkdir(parents=True, exist_ok=True)
    importname = sys.argv[1]
    logging.info(f'Loading config: {_FLAGS.config_file}')
    with file_util.FileIO(_FLAGS.config_file, 'r') as f:
        config = json.load(f)
    logging.info("Started processing the script...!")
    clean_air_quality_data(config, importname, _INPUT_FILE_PATH,
                           _OUTPUT_FILE_PATH)
    logging.info("Finished processing the script...!")


if __name__ == "__main__":
    app.run(main)
