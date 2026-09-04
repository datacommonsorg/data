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
import numpy as np
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
def add_prefix_zero(value, length=11):
    return str(value).zfill(length)


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
                            if "County" in input_file_name and "PM" in input_file_name:
                                num_shards = 4
                                base_name, ext = os.path.splitext(
                                    output_file_name)
                                shard_paths = []
                                for idx in range(num_shards):
                                    shard_file_name = f"{base_name}_{idx}{ext}"
                                    if not os.path.isabs(shard_file_name):
                                        shard_output_path = os.path.join(
                                            outputpath, shard_file_name)
                                    else:
                                        shard_output_path = shard_file_name
                                    shard_paths.append(shard_output_path)

                                with open(input_file_path, 'r') as f:
                                    total_rows = sum(1 for _ in f) - 1
                                base_size = total_rows // num_shards
                                rem_size = total_rows % num_shards
                                shard_sizes = [
                                    base_size + 1 if i < rem_size else base_size
                                    for i in range(num_shards)
                                ]

                                chunk_size = 500_000
                                shard_idx = 0
                                shard_written = 0
                                first_chunk = True

                                for chunk in pd.read_csv(input_file_path,
                                                         chunksize=chunk_size):
                                    chunk["date"] = pd.to_datetime(
                                        chunk["date"],
                                        format="%d%b%Y",
                                        errors="raise").dt.strftime("%Y-%m-%d")
                                    chunk["statefips"] = chunk[
                                        "statefips"].astype(str).str.zfill(2)
                                    chunk["countyfips"] = chunk[
                                        "countyfips"].astype(str).str.zfill(3)
                                    chunk["dcid"] = "geoId/" + chunk[
                                        "statefips"] + chunk["countyfips"]

                                    if first_chunk:
                                        for p in shard_paths:
                                            pd.DataFrame(
                                                columns=chunk.columns).to_csv(
                                                    p, index=False)
                                        first_chunk = False

                                    start_idx = 0
                                    while start_idx < len(chunk):
                                        if shard_idx < num_shards - 1:
                                            remaining_in_shard = shard_sizes[
                                                shard_idx] - shard_written
                                            end_idx = min(
                                                start_idx + remaining_in_shard,
                                                len(chunk))
                                        else:
                                            end_idx = len(chunk)

                                        sub_chunk = chunk.iloc[
                                            start_idx:end_idx]

                                        sub_chunk.to_csv(shard_paths[shard_idx],
                                                         mode='a',
                                                         header=False,
                                                         float_format='%.6f',
                                                         index=False)
                                        shard_written += len(sub_chunk)
                                        start_idx = end_idx

                                        if shard_idx < num_shards - 1 and shard_written >= shard_sizes[
                                                shard_idx]:
                                            shard_idx += 1
                                            shard_written = 0

                                for p in shard_paths:
                                    logging.info(
                                        f"Finished cleaning file {os.path.basename(p)}!"
                                    )
                            elif "County" in input_file_name and "Ozone" in input_file_name:
                                chunk_size = 500_000
                                first_chunk = True
                                for chunk in pd.read_csv(input_file_path,
                                                         chunksize=chunk_size):
                                    chunk["date"] = pd.to_datetime(
                                        chunk["date"],
                                        format="%d%b%Y",
                                        errors="raise").dt.strftime("%Y-%m-%d")
                                    chunk["statefips"] = chunk[
                                        "statefips"].astype(str).str.zfill(2)
                                    chunk["countyfips"] = chunk[
                                        "countyfips"].astype(str).str.zfill(3)
                                    chunk["dcid"] = "geoId/" + chunk[
                                        "statefips"] + chunk["countyfips"]
                                    if first_chunk:
                                        chunk.to_csv(output_file_path,
                                                     float_format='%.6f',
                                                     index=False)
                                        first_chunk = False
                                    else:
                                        chunk.to_csv(output_file_path,
                                                     mode='a',
                                                     header=False,
                                                     float_format='%.6f',
                                                     index=False)
                                logging.info(
                                    f"Finished cleaning file {output_file_name}!"
                                )
                            else:
                                data = pd.read_csv(input_file_path)
                                data["date"] = pd.to_datetime(
                                    data["date"],
                                    format="%d%b%Y",
                                    errors="raise").dt.strftime("%Y-%m-%d")

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
                                                'countyfips', 'ctfips',
                                                'latitude', 'longitude'
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
                                                'countyfips', 'ctfips',
                                                'latitude', 'longitude',
                                                census_tract + '_stdd'
                                            ],
                                            value_vars=[
                                                str(census_tract + '_pred')
                                            ],
                                            var_name='StatisticalVariable',
                                            value_name='Value')
                                    data.rename(columns={
                                        census_tract + '_stdd': 'Error'
                                    },
                                                inplace=True)
                                    data['ctfips'] = data['ctfips'].astype(
                                        str).str.zfill(11)
                                    data["dcid"] = "geoId/" + data[
                                        "ctfips"].astype(str)
                                    data['StatisticalVariable'] = data[
                                        'StatisticalVariable'].map(STATVARS)
                                data.to_csv(output_file_path,
                                            float_format='%.6f',
                                            index=False)
                                logging.info(
                                    f"Finished cleaning file {output_file_name}!"
                                )
                        except Exception as e:
                            logging.error(
                                f"Error cleaning {input_file_name}: {e}")
                            raise
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
