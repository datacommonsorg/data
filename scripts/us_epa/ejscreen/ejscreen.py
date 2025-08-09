# Copyright 2023 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import io
import zipfile
import requests
import pandas as pd
import json
from absl import logging, flags, app
import sys
import time
from retry import retry

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_MODULE_DIR, '../../../util/'))
import file_util

logging.set_verbosity(logging.INFO)

_FLAGS = flags.FLAGS

flags.DEFINE_string('config_path',
                    'gs://unresolved_mcf/epa/ejscreen/config.json',
                    'Path to config file')
flags.DEFINE_string(
    'mode', '',
    'Mode of operation: "download" to only download, "process" to only process, leave empty for both.'
)


# Function to build the correct URL for each year
def build_url(year, zip_filename=None):
    if zip_filename:
        if year in URL_SUFFIX:
            url = f'{BASE_URL}/{year}/{URL_SUFFIX[year]}/{zip_filename}.zip'
        else:
            url = f'{BASE_URL}/{year}/{zip_filename}.zip'
    else:
        url = f'{BASE_URL}/{year}/{FILENAMES[year]}.csv'
    return url


@retry(tries=5, delay=5, backoff=5)
def download_with_retry(url):
    logging.info(f"Downloading URL : {url}")
    return requests.get(url=url, verify=False)


# Download the file and save it in the input folder
def download_file(url, year, input_folder, zip_filename=None):
    try:
        response = download_with_retry(url)
        if response.status_code == 200:
            os.makedirs(input_folder, exist_ok=True)

            file_path = os.path.join(
                input_folder, f'{year}.zip' if zip_filename else f'{year}.csv')
            with open(file_path, 'wb') as f:
                f.write(response.content)
            logging.info(f"File downloaded and saved as {file_path}")
            return
        else:
            logging.fatal(
                f"Failed to download file for {year}. HTTP Status Code: {response.status_code} URL : {url}"
            )
            raise RuntimeError(f"Failed to download file for {year}. HTTP Status Code: {response.status_code} URL : {url}")
    except Exception as e:
        logging.fatal(f"Failed to download file for {year} after {url} .")
        raise RuntimeError(f"Failed to download file for {year} after {url} .")


# Data processing function
def write_csv(data, outfilename):
    full_df = pd.DataFrame()
    for curr_year, one_year_df in data.items():
        one_year_df['year'] = curr_year
        full_df = pd.concat([full_df, one_year_df], ignore_index=True)

    full_df = full_df.rename(columns={'ID': 'FIPS'})
    full_df = full_df.sort_values(by=['FIPS'], ignore_index=True)
    full_df['FIPS'] = 'dcid:geoId/' + (
        full_df['FIPS'].astype(str).str.zfill(12))
    full_df = full_df.fillna('')
    full_df = full_df.replace('None', '')
    full_df.to_csv(outfilename, index=False)


def write_tmcf(outfilename):
    if isinstance(TEMPLATE_MCF, list):
        template_content = "\n".join(str(item) for item in TEMPLATE_MCF)
    else:
        template_content = str(TEMPLATE_MCF)

    with open(outfilename, 'w') as f_out:
        f_out.write(template_content)


def main(_):
    global URL_SUFFIX, BASE_URL, TEMPLATE_MCF, FILENAMES

    try:
        # Load configuration from config.json
        with file_util.FileIO(_FLAGS.config_path, 'r') as f:
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
        RENAME_COLUMNS_YEARS = config["RENAME_COLUMNS_YEARS"]

        dfs = {}
        input_folder = os.path.join(_MODULE_DIR, 'input')

        # Download files if the mode is 'download' or if no mode is specified
        if _FLAGS.mode == "" or _FLAGS.mode == "download":
            for year in YEARS:
                try:
                    logging.info(f"Processing year: {year}")
                    columns = CSV_COLUMNS_BY_YEAR[year]
                    zip_filename = ZIP_FILENAMES.get(year, None)

                    file_path = os.path.join(
                        input_folder,
                        f'{year}.zip' if zip_filename else f'{year}.csv')

                    if not os.path.exists(file_path):
                        logging.info(
                            f"File for {year} not found. Downloading...")
                        url = build_url(year, zip_filename)
                        download_file(url, year, input_folder, zip_filename)

                except Exception as e:
                    logging.fatal(f"Error processing data for year {year}: {e}")
                    raise RuntimeError(f"Error processing data for year {year}: {e}")
                    continue

        # Process files if the mode is 'process' or if no mode is specified
        if _FLAGS.mode == "" or _FLAGS.mode == "process":
            for year in YEARS:
                try:
                    logging.info(f"Processing data for year {year}")
                    columns = CSV_COLUMNS_BY_YEAR[year]
                    zip_filename = ZIP_FILENAMES.get(year, None)

                    file_path = os.path.join(
                        input_folder,
                        f'{year}.zip' if zip_filename else f'{year}.csv')

                    # Process the downloaded file
                    if zip_filename:
                        with zipfile.ZipFile(file_path, 'r') as zfile:
                            with zfile.open(f'{FILENAMES[year]}.csv',
                                            'r') as newfile:
                                dfs[year] = pd.read_csv(newfile,
                                                        engine='python',
                                                        encoding='latin1',
                                                        usecols=columns)
                    else:
                        dfs[year] = pd.read_csv(file_path,
                                                sep=',',
                                                usecols=columns)

                    logging.info(f"File processed for {year} successfully")

                    if year in RENAME_COLUMNS_YEARS:
                        cols_renamed = dict(zip(columns, NORM_CSV_COLUMNS1))
                    else:
                        cols_renamed = dict(zip(columns, NORM_CSV_COLUMNS))

                    dfs[year] = dfs[year].rename(columns=cols_renamed)
                    logging.info(f"Columns renamed for {year} successfully")

                except Exception as e:
                    logging.fatal(f"Error processing data for year {year}: {e}")
                    raise RuntimeError(f"Error processing data for year {year}: {e}")
                    continue
            

            # Write the combined data and template
            logging.info("Writing data to CSV")
            write_csv(dfs, 'ejscreen_airpollutants.csv')

            logging.info("Writing template to TMCF")
            write_tmcf('ejscreen.tmcf')

            logging.info("Process completed successfully")

    except Exception as e:
        logging.fatal(f"Unexpected error in the main process: {e}")
        raise RuntimeError(f"Unexpected error in the main process: {e}")


if __name__ == '__main__':
    app.run(main)
