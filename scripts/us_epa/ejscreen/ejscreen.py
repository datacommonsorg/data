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
from absl import logging

logging.set_verbosity(logging.INFO)
logger = logging

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
URL_TEMPLATE = config["URL_TEMPLATE"]
URL_TEMPLATE_NON_ZIPPED = config["URL_TEMPLATE_NON_ZIPPED"]

# data: dictionary of dataframes in the format {year: dataframe}
# outfilename: name of the csv that data will be written to
# write_csv concatenates the dataframe from each year together

def write_csv(data, outfilename):
    full_df = pd.DataFrame()
    for curr_year, one_year_df in data.items():
        one_year_df['year'] = curr_year
        full_df = pd.concat([full_df, one_year_df], ignore_index=True)

    # sort by FIPS and make into dcid
    full_df = full_df.rename(columns={'ID': 'FIPS'})
    full_df = full_df.sort_values(by=['FIPS'], ignore_index=True)
    full_df['FIPS'] = 'dcid:geoId/' + (
        full_df['FIPS'].astype(str).str.zfill(12))
    full_df = full_df.fillna('')
    full_df = full_df.replace('None', '')
    full_df.to_csv(outfilename, index=False)

def write_tmcf(outfilename):
    with open(outfilename, 'w') as f_out:
        f_out.write(TEMPLATE_MCF)

if __name__ == '__main__':
    dfs = {}
    for year in YEARS:
        logger.info(f"Processing year: {year}")
        columns = CSV_COLUMNS_BY_YEAR[year]
        zip_filename = ZIP_FILENAMES.get(year, None)

        # Check if the year has a zip file or not
        if zip_filename:
            url = URL_TEMPLATE.format(year=year, zip_filename=zip_filename)
            logger.info(f"Requesting file: {url}")
            response = requests.get(url, verify=False)

            if response.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(response.content)) as zfile:
                    with zfile.open(f'{FILENAMES[year]}.csv', 'r') as newfile:
                        dfs[year] = pd.read_csv(newfile, usecols=columns)
                logger.info(f"File downloaded and processed for {year} successfully")
            else:
                logger.error(f"Failed to download file for {year}. HTTP Status Code: {response.status_code}")
        else:
            url = URL_TEMPLATE_NON_ZIPPED.format(year=year, filename=FILENAMES[year])
            logger.info(f"Requesting CSV file: {url}")
            response = requests.get(url, verify=False)

            if response.status_code == 200:
                dfs[year] = pd.read_csv(io.StringIO(response.text), sep=',', usecols=columns)
                logger.info(f"CSV downloaded and processed for {year} successfully")
            else:
                logger.error(f"Failed to download CSV for {year}. HTTP Status Code: {response.status_code}")

        # Rename weird column names to match other years
        if year == '2024':
            cols_renamed = dict(zip(columns, NORM_CSV_COLUMNS1))
        else:
            cols_renamed = dict(zip(columns, NORM_CSV_COLUMNS))

        dfs[year] = dfs[year].rename(columns=cols_renamed)
        logger.info(f"Columns renamed for {year} successfully")

    logger.info("Writing data to csv")
    write_csv(dfs, 'ejscreen_airpollutants.csv')
    logger.info("Writing template to tmcf")
    write_tmcf('ejscreen.tmcf')
    logger.info("Process completed successfully")