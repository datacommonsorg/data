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
'''
Author: Padma Gundapaneni @padma-g
Date: 7/28/21
Description: This script cleans up a csv file on census tract or county level
air quality (ozone or 2.5 PM) data downloaded from the CDC.
URL: https://data.cdc.gov/browse?category=Environmental+Health+%26+Toxicology
@input_file   filepath to the original csv that needs to be cleaned
@output_file  filepath to the csv to which the cleaned data is written
python3 parse_air_quality.py input_file output_file
'''

import json
import os
import requests
import pandas as pd
from absl import app, logging, flags
from retry import retry
from pathlib import Path
import sys

_FLAGS = flags.FLAGS

flags.DEFINE_string('mode', '', 'Options: download or process')
flags.DEFINE_string('input_file_path', 'input_files', 'Input files path')
flags.DEFINE_string('output_file_path', 'output', 'Output files path')

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_INPUT_FILE_PATH = None
_OUTOUT_FILE_PATH = None

#Making a dictionary to keep each all 4 imports and it's correspondence download
# source url and output path to save final output
import_configs = [{
    "import_name":
        "CDC_PM25CensusTract",
    "files": [{
        "url": "https://data.cdc.gov/resource/v5qq-ktfc.csv",
        "input_file_name": "PM2.5CensusTractPollution_input_0.csv",
        "output_file_name": "PM2.5CensusTract_0.csv"
    }, {
        "url": "https://data.cdc.gov/resource/ujra-cbx5.csv",
        "input_file_name": "PM2.5CensusTractPollution_input_1.csv",
        "output_file_name": "PM2.5CensusTract_1.csv"
    }, {
        "url": "https://data.cdc.gov/resource/qjxm-7fny.csv",
        "input_file_name": "PM2.5CensusTractPollution_input_2.csv",
        "output_file_name": "PM2.5CensusTract_2.csv"
    }, {
        "url": "https://data.cdc.gov/resource/96sd-hxdt.csv",
        "input_file_name": "PM2.5CensusTractPollution_input_3.csv",
        "output_file_name": "PM2.5CensusTract_3.csv"
    }]
}, {
    "import_name":
        "CDC_OzoneCensusTract",
    "files": [{
        "url": "https://data.cdc.gov/resource/v76h-zdce.csv",
        "input_file_name": "Census_Tract_Level_Ozone_Concentrations_input.csv",
        "output_file_name": "Census_Tract_Level_Ozone_Concentrations_0.csv"
    }, {
        "url":
            "https://data.cdc.gov/resource/xm94-zmtx.csv",
        "input_file_name":
            "Census_Tract_Level_Ozone_Concentrations_input_1.csv",
        "output_file_name":
            "Census_Tract_Level_Ozone_Concentrations_1.csv"
    }, {
        "url":
            "https://data.cdc.gov/resource/847z-pxin.csv",
        "input_file_name":
            "Census_Tract_Level_Ozone_Concentrations_input_2.csv",
        "output_file_name":
            "Census_Tract_Level_Ozone_Concentrations_2.csv"
    }, {
        "url":
            "https://data.cdc.gov/resource/hf2a-3ebq.csv",
        "input_file_name":
            "Census_Tract_Level_Ozone_Concentrations_input_3.csv",
        "output_file_name":
            "Census_Tract_Level_Ozone_Concentrations_3.csv"
    }]
}, {
    "import_name":
        "CDC_PM25County",
    "files": [{
        "url": "https://data.cdc.gov/resource/dqwm-pbi7.csv",
        "input_file_name": "PM2.5County_input.csv",
        "output_file_name": "PM25county.csv"
    }]
}, {
    "import_name":
        "CDC_OzoneCounty",
    "files": [{
        "url": "https://data.cdc.gov/resource/jcn4-jcv5.csv",
        "input_file_name": "OzoneCounty_input.csv",
        "output_file_name": "OzoneCounty.csv"
    }]
}]

record_count_query = '?$query=select%20count(*)%20as%20COLUMN_ALIAS_GUARD__count'

# Mapping of column names in file to StatVar names.
STATVARS = {
    "DS_PM_pred": "Mean_Concentration_AirPollutant_PM2.5",
    "ds_pm_pred": "Mean_Concentration_AirPollutant_PM2.5",
    "ds_pm_stdd": "Mean_Concentration_AirPollutant_PM2.5_StandardError",
    "DS_O3_pred": "Mean_Concentration_AirPollutant_Ozone",
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


def clean_air_quality_data(file_path, output_file, importname):
    """
    Args:
        file_path: path to a comma-separated CDC air quality data file
        output_file: path for the cleaned csv to be stored
    Returns:
        a cleaned csv file
    """
    global output_file_name
    logging.info(f"import name from command line {importname}")
    for config1 in import_configs:
        if config1["import_name"] == importname:
            files = config1["files"]
            for file_info in files:
                output_file_name = file_info["output_file_name"]
                logging.info(f"output_file_name: {output_file_name}")

                for file in os.listdir(file_path):
                    logging.info(f"file_path: {file_path}")

                    if str(file).endswith('.csv'):
                        logging.info(f"Cleaning {file} ....")
                        data = pd.read_csv(os.path.join(file_path, file))
                        data["date"] = pd.to_datetime(data["date"],
                                                      yearfirst=True)
                        data["date"] = pd.to_datetime(data["date"],
                                                      format="%Y-%m-%d")

                        if "PM2.5" in file:
                            census_tract = "ds_pm"
                        elif "Ozone" in file:
                            census_tract = "ds_o3"
                        if "Census" in file:
                            if "PM2.5" in file:
                                data = pd.melt(data,
                                               id_vars=[
                                                   'year', 'date', 'statefips',
                                                   'countyfips', 'ctfips',
                                                   'latitude', 'longitude'
                                               ],
                                               value_vars=[
                                                   str(census_tract + '_pred'),
                                                   str(census_tract + '_stdd')
                                               ],
                                               var_name='StatisticalVariable',
                                               value_name='Value')

                            elif "Ozone" in file:
                                data = pd.melt(
                                    data,
                                    id_vars=[
                                        'year', 'date', 'statefips',
                                        'countyfips', 'ctfips', 'latitude',
                                        'longitude', census_tract + '_stdd'
                                    ],
                                    value_vars=[str(census_tract + '_pred')],
                                    var_name='StatisticalVariable',
                                    value_name='Value')
                            data.rename(
                                columns={census_tract + '_stdd': 'Error'},
                                inplace=True)
                            max_length = data['ctfips'].astype(
                                str).str.len().max()
                            data['ctfips'] = data['ctfips'].astype(str).apply(
                                lambda x: add_prefix_zero(x, max_length))
                            data["dcid"] = "geoId/" + data["ctfips"].astype(str)
                            data['StatisticalVariable'] = data[
                                'StatisticalVariable'].map(STATVARS)
                        elif "County" in file and "PM" in file:
                            data["statefips"] = data["statefips"].astype(
                                str).str.zfill(2)
                            data["countyfips"] = data["countyfips"].astype(
                                str).str.zfill(3)
                            data["dcid"] = "geoId/" + data["statefips"] + data[
                                "countyfips"]
                        elif "County" in file and "Ozone" in file:
                            data["statefips"] = data["statefips"].astype(
                                str).str.zfill(2)
                            data["countyfips"] = data["countyfips"].astype(
                                str).str.zfill(3)
                            data["dcid"] = "geoId/" + data["statefips"] + data[
                                "countyfips"]
                        output_file_path_with_file_name = output_file + "/" + output_file_name
                        data.to_csv(output_file_path_with_file_name,
                                    float_format='%.6f',
                                    index=False)
                        logging.info(
                            f"Finished cleaning file {output_file_name}!")


def download_files(importname):
    global _INPUT_FILE_PATH
    global import_name
    global url_new

    @retry(tries=3, delay=2, backoff=2)
    def download_with_retry(url, input_file_name):
        logging.info(f"Downloading file from URL: {url}")
        response = requests.get(url)
        response.raise_for_status()
        if response.status_code == 200:
            if not response.content:
                logging.fatal(
                    f"No data available for URL: {url}. Aborting download.")
                return
            filename = os.path.join(_INPUT_FILE_PATH, input_file_name)
            with open(filename, 'wb') as f:
                f.write(response.content)
        else:
            logging.error(
                f"Failed to download file from URL: {url}. Status code: {response.status_code}"
            )

    try:
        logging.info(f"import name from command line {importname}")
        for config in import_configs:
            import_name = config["import_name"]
        for config1 in import_configs:
            if config1["import_name"] == importname:
                import_name = config1["import_name"]
                files = config1["files"]
                for file_info in files:
                    url_new = file_info["url"]
                    logging.info(f"URL from link {url_new}")
                    input_file_name = file_info["input_file_name"]
                    logging.info(f"Input File Name {input_file_name}")

                    get_record_count = requests.get(
                        url_new.replace('.csv', record_count_query))
                    if get_record_count.status_code == 200:
                        record_count = json.loads(
                            get_record_count.text
                        )[0]['COLUMN_ALIAS_GUARD__count']
                        logging.info(
                            f"Numbers of records found for the URL {url_new} is {record_count}"
                        )
                        url_new = f"{url_new}?$limit={record_count}&$offset=0"
                        download_with_retry(url_new, input_file_name)

    except Exception as e:
        logging.fatal(f"Error downloading URL {url_new} - {e}")


def main(_):
    """Main function to generate the cleaned csv file."""
    global _INPUT_FILE_PATH, _OUTOUT_FILE_PATH
    _INPUT_FILE_PATH = os.path.join(_MODULE_DIR, _FLAGS.input_file_path)
    _OUTOUT_FILE_PATH = os.path.join(_MODULE_DIR, _FLAGS.output_file_path)
    Path(_INPUT_FILE_PATH).mkdir(parents=True, exist_ok=True)
    Path(_OUTOUT_FILE_PATH).mkdir(parents=True, exist_ok=True)
    mode = _FLAGS.mode
    # Get command-line arguments
    importname = sys.argv[1]

    if mode == "":
        logging.info(f"Inside mode download and process")
        download_files(importname)
        clean_air_quality_data(_INPUT_FILE_PATH, _OUTOUT_FILE_PATH, importname)

    if mode == "download":
        logging.info(f"Inside mode download")
        download_files(importname)
    if mode == "process":
        logging.info(f"Inside mode process")
        clean_air_quality_data(_INPUT_FILE_PATH, _OUTOUT_FILE_PATH, importname)


if __name__ == "__main__":
    app.run(main)
