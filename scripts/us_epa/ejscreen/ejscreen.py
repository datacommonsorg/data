# Copyright 2023 Google LLC
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

import io
import os
import zipfile
import requests
import pandas as pd
import json
from absl import logging, flags, app
import sys

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_MODULE_DIR, '../../../util/'))
print(_MODULE_DIR)
import file_util

logging.set_verbosity(logging.INFO)
logger = logging
_FLAGS = flags.FLAGS
flags.DEFINE_string('config_path',
                    'gs://unresolved_mcf/epa/ejscreen/config.json',
                    'Path to config file')

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_PATH = os.path.join(_MODULE_DIR, 'config.json')

# Load configuration from config.json
with open(_CONFIG_PATH, 'r') as f:
    config = json.load(f)

YEARS = config["YEARS"]
NORM_CSV_COLUMNS = config["NORM_CSV_COLUMNS"]
NORM_CSV_COLUMNS1 = config["NORM_CSV_COLUMNS1"]
CSV_COLUMNS_BY_YEAR = config["CSV_COLUMNS_BY_YEAR"]
ZIP_FILENAMES = config["ZIP_FILENAMES"]
FILENAMES = config["FILENAMES"]
TEMPLATE_MCF = config["TEMPLATE_MCF"]
BASE_URL = config["BASE_URL"]
URL_SUFFIX = config["URL_SUFFIX"]


# Function to build the correct URL for each year
def build_url(year, zip_filename=None):
    if zip_filename:
        # Construct the URL for the zip file
        if year in URL_SUFFIX:
            url = f'{BASE_URL}/{year}/{URL_SUFFIX[year]}/{zip_filename}.zip'
        else:
            url = f'{BASE_URL}/{year}/{zip_filename}.zip'
    else:
        # Construct the URL for the CSV file
        url = f'{BASE_URL}/{year}/{FILENAMES[year]}.csv'
    return url


# Data processing function
def write_csv(data, outfilename):
    full_df = pd.DataFrame()
    for curr_year, one_year_df in data.items():
        one_year_df['year'] = curr_year
        full_df = pd.concat([full_df, one_year_df], ignore_index=True)

    # Sort by FIPS and make into dcid
    full_df = full_df.rename(columns={'ID': 'FIPS'})
    full_df = full_df.sort_values(by=['FIPS'], ignore_index=True)
    full_df['FIPS'] = 'dcid:geoId/' + (
        full_df['FIPS'].astype(str).str.zfill(12))
    full_df = full_df.fillna('')
    full_df = full_df.replace('None', '')
    full_df.to_csv(outfilename, index=False)


def write_tmcf(outfilename):
    # Convert each item in TEMPLATE_MCF to a string, even if it's a dictionary
    if isinstance(TEMPLATE_MCF, list):
        # Convert each element to a string if it's not already
        template_content = "\n".join(str(item) for item in TEMPLATE_MCF)
    else:
        template_content = str(
            TEMPLATE_MCF
        )  # In case it's not a list, just convert it to a string

    with open(outfilename, 'w') as f_out:
        f_out.write(template_content)


def main(_):
    dfs = {}
    for year in YEARS:
        logger.info(f"Processing year: {year}")
        columns = CSV_COLUMNS_BY_YEAR[year]
        zip_filename = ZIP_FILENAMES.get(year, None)

        url = build_url(year, zip_filename)

        logger.info(f"Requesting file: {url}")
        response = requests.get(url, verify=False)

        if response.status_code == 200:
            if zip_filename:
                with zipfile.ZipFile(io.BytesIO(response.content)) as zfile:
                    with zfile.open(f'{FILENAMES[year]}.csv', 'r') as newfile:
                        dfs[year] = pd.read_csv(newfile,
                                                engine='python',
                                                encoding='latin1',
                                                usecols=columns)
            else:
                dfs[year] = pd.read_csv(io.StringIO(response.text),
                                        sep=',',
                                        usecols=columns)
            logger.info(
                f"File downloaded and processed for {year} successfully")
        else:
            logger.error(
                f"Failed to download file for {year}. HTTP Status Code: {response.status_code}"
            )

        # Rename columns to match other years
        if year == '2024':
            cols_renamed = dict(zip(columns, NORM_CSV_COLUMNS1))
        else:
            cols_renamed = dict(zip(columns, NORM_CSV_COLUMNS))

        dfs[year] = dfs[year].rename(columns=cols_renamed)
        logger.info(f"Columns renamed for {year} successfully")

        logger.info("Writing data to CSV")
        write_csv(dfs, 'ejscreen_airpollutants.csv')
        logger.info("Writing template to TMCF")
        write_tmcf('ejscreen.tmcf')
        logger.info("Process completed successfully")


if __name__ == '__main__':
    app.run(main)
