# Copyright 2020 Google LLC
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
'''
Downloads and converts BLS CPI raw csv files to csv files of two columns:
"date" and "cpi", where "date" is of the form "YYYY-MM" and "cpi" is numeric.

Usage: python3 generate_csv.py
'''
import io
import requests
import frozendict
import pandas as pd
from absl import flags
from absl import app
from absl import logging
from retry import retry

import os
from pathlib import Path
'''Defining the retry_method which will accepts below parameters
   url: input url
   headers: headers if you want to set
'''
global buffer


@retry(tries=3, delay=5, backoff=5)
def retry_method(url, header):
    return requests.get(url, headers=header)


# Dict from series names to download links
CSV_URLS = frozendict.frozendict({
    "cpi_u": "https://download.bls.gov/pub/time.series/cu/cu.data.1.AllItems",
    "cpi_w": "https://download.bls.gov/pub/time.series/cw/cw.data.1.AllItems",
    "c_cpi_u": "https://download.bls.gov/pub/time.series/su/su.data.1.AllItems"
})
_FLAGS = flags.FLAGS
flags.DEFINE_integer(
    'start_date', 1946,
    'Data will process from assigned date which date format is <YYYY>')
flags.DEFINE_string('input_path1', 'input_files', 'Input files path')
flags.DEFINE_string('output_path1', 'output', 'Output files path')
flags.DEFINE_string('mode', '', 'Options: download or process')
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_INPUT_FILE_PATH = None
_OUTOUT_FILE_PATH = None

header = {
    'User-Agent':
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Content-Type':
        'application/octet-stream',
}

# Dict from series names to series IDs
SERIES_IDS = frozendict.frozendict({
    "cpi_u": "CUSR0000SA0",
    "cpi_w": "CWSR0000SA0",
    "c_cpi_u": "SUUR0000SA0E"
})


def downloadUrl(_INPUT_FILE_PATH):

    for series_name, url in CSV_URLS.items():
        #Retry method is calling
        response = retry_method(url, header=header)
        #Start saving file locally
        logging.info(
            f'Downloading files from url {url} and svae to path {_INPUT_FILE_PATH}'
        )
        response.raise_for_status()

        if response.status_code != 200:
            logging.fatal(
                f"No data available for URL: {url}. Aborting download.")

        elif response.status_code == 200:
            if not response.content:
                logging.fatal(
                    f"No data available for URL: {url}. Aborting download.")
            filename = f"{series_name}.csv"
            logging.info(
                f'filename: {filename} _INPUT_FILE_PATH : {_INPUT_FILE_PATH}')
            file_path = os.path.join(_INPUT_FILE_PATH, filename)
            with open(file_path, 'wb') as f:
                f.write(response.content)
        #End file after saving locally


def process(_INPUT_FILE_PATH, _OUTOUT_FILE_PATH, date_from_start_processing):

    # The raw csv has four columns: "series_id", "year", "period", "value",
    # and "footnote_codes".
    # "value" is the CPI values.
    # "year" is of the form "YYYY".
    # "period" is the months of the observations and is of the form "MM"
    # preceded by char 'M', e.g. "M05".
    for series_name, url in CSV_URLS.items():
        series_id = SERIES_IDS[series_name]
        try:
            #in_df = pd.read_csv(buffer, sep=r"\s+", dtype="str")
            logging.info(
                f'_INPUT_FILE_PATH inside process method=========== {_INPUT_FILE_PATH} series_id======={series_id} series_name=========={series_name} _OUTOUT_FILE_PATH========{_OUTOUT_FILE_PATH}'
            )
            in_df = pd.read_csv(_INPUT_FILE_PATH + "/" + series_name + ".csv",
                                sep=r"\s+",
                                dtype="str")
            # "M13" is annual averages
            in_df = in_df[(in_df["series_id"] == series_id) &
                          (in_df["period"] != "M13")]
            # Format "date" column as "YYYY-MM"
            in_df["date"] = in_df["year"] + "-" + in_df["period"].str[-2:]
            in_df = in_df[["date", "value"]]
            in_df.columns = ["date", "cpi"]
            # Convert 'date' column to datetime format
            logging.info(
                f"date_from_start_processing {date_from_start_processing}")
            in_df['date'] = pd.to_datetime(in_df['date'], format='%Y-%m')
            in_df = in_df[in_df['date'].dt.year > int(
                date_from_start_processing)]
            in_df['date'] = in_df['date'].dt.strftime('%Y-%m')
            logging.info(
                f"Data frame before writing to output csv file {in_df}")
            in_df.to_csv(_OUTOUT_FILE_PATH + "/" + series_name + ".csv",
                         index=False)
        except Exception as e:
            logging.fatal(
                f"Error while processing input files {e} {date_from_start_processing}"
            )


def main(_):
    """Runs the script. See module docstring."""
    mode = _FLAGS.mode
    _INPUT_FILE_PATH = os.path.join(MODULE_DIR, _FLAGS.input_path1)
    _OUTOUT_FILE_PATH = os.path.join(MODULE_DIR, _FLAGS.output_path1)
    date_from_start_processing = _FLAGS.start_date
    Path(_OUTOUT_FILE_PATH).mkdir(parents=True, exist_ok=True)
    Path(_INPUT_FILE_PATH).mkdir(parents=True, exist_ok=True)

    if mode == "" or mode == "download":
        downloadUrl(_INPUT_FILE_PATH)
    if mode == "" or mode == "process":
        process(_INPUT_FILE_PATH, _OUTOUT_FILE_PATH, date_from_start_processing)


if __name__ == "__main__":
    app.run(main)
