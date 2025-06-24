# Copyright 2025 Google LLC
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
Generates cleaned CSV and template MCF files for the EPA AirData.
This includes aggregate API measurements at the county/CSBA level.

Usage: python3 air_quality_aggregate.py <end_year>
'''
import csv, os, sys, requests, io, zipfile

from absl import app
from absl import flags
from absl import logging
from datetime import datetime
from retry import retry
import frozendict
import os
from pathlib import Path
import time

_FLAGS = flags.FLAGS

flags.DEFINE_integer('aggregate_start_year', os.getenv('START_YEAR', '1980'),
                     'Process data starting from this year.')
flags.DEFINE_integer('aggregate_end_year',
                     os.getenv('END_YEAR',
                               datetime.now().year),
                     'Process data upto this year.')
flags.DEFINE_string('input_file_path', 'input_files', 'Input files path')
flags.DEFINE_string('output_file_path', 'output', 'Output files path')
flags.DEFINE_string('mode', '', 'Options: download or process')
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


@retry(tries=3, delay=5, backoff=5)
def retry_method(url):
    return requests.get(url)


POLLUTANTS = {
    'Ozone': 'Ozone',
    'SO2': 'SulfurDioxide',
    'CO': 'CarbonMonoxide',
    'NO2': 'NitrogenDioxide',
    'PM2.5': 'PM2.5',
    'PM10': 'PM10',
}

CSV_COLUMNS = ['Date', 'Place', 'AQI', 'Pollutant', 'Site']


def get_place(observation):
    if 'State Code' and 'County Code' in observation:
        return 'dcid:geoId/' + observation['State Code'] + observation[
            'County Code']
    elif 'CBSA Code' in observation:
        return 'dcid:geoId/C' + observation['CBSA Code']
    else:
        return None


def create_csv(csv_file_path):
    logging.info(f'Inside create csv value of {csv_file_path}')
    output_file_path = os.path.join(MODULE_DIR, _FLAGS.output_file_path)
    file_path = os.path.join(output_file_path, csv_file_path)
    logging.info(f'file_path {file_path}')
    with open(file_path, 'w', newline='') as f_out:
        writer = csv.DictWriter(f_out,
                                fieldnames=CSV_COLUMNS,
                                lineterminator='\n')
        writer.writeheader()


def write_csv(csv_file_path, reader):
    with open(csv_file_path, 'a', newline='') as f_out:
        writer = csv.DictWriter(f_out,
                                fieldnames=CSV_COLUMNS,
                                lineterminator='\n')
        for observation in reader:
            place = get_place(observation)
            if not place:
                continue
            new_row = {
                'Date':
                    observation['Date'],
                'Place':
                    place,
                'AQI':
                    observation['AQI'],
                'Pollutant':
                    'dcs:' + POLLUTANTS[observation['Defining Parameter']],
                'Site':
                    'dcid:epa/' + observation['Defining Site'].replace('-', '')
            }
            writer.writerow(new_row)


def download_url(_INPUT_FILE_PATH, start_year, end_year, CSV_URLS):
    """
    Downloads daily Air Quality Index (AQI) data zip files from the EPA AirData
    website for a specified range of years and saves them locally.

    It iterates through years from `start_year` (inclusive) to `end_year` (exclusive).
    For each year, it constructs file names for both county-level and CBSA-level
    AQI data (e.g., 'daily_aqi_by_county_YYYY.zip', 'daily_aqi_by_cbsa_YYYY.zip').
    Args:
        _INPUT_FILE_PATH (str): The local directory path where the downloaded
                                 zip files will be saved.
        start_year (int): The starting year (inclusive) from which to download data.
        end_year (int): The ending year (exclusive) up to which to download data.
                        Data for `end_year - 1` will be the last year downloaded.
        CSV_URLS (frozendict.frozendict): A frozendict where keys are series names
                                          (e.g., "daily_aqi") and values are the
                                          base URLs for the EPA AirData files.
                                          This dictionary is expected to provide
                                          the root URL to which file names are appended.
    """

    for year in range(start_year, int(end_year)):
        logging.info(f'year: {year}')
        file_names = [
            f'daily_aqi_by_county_{year}', f'daily_aqi_by_cbsa_{year}'
        ]
        # Iterate over the list of file names (county and cbsa)
        for file_name in file_names:
            logging.info(f'Processing file: {file_name}')

            for series_name, url in CSV_URLS.items():
                #Retry method is calling
                url = f"{url}{file_name}.zip"
                logging.info(f'============url {url}')
                response = retry_method(url)
                logging.info(
                    f'Downloading files from url {url} and save to path {_INPUT_FILE_PATH}'
                )
                logging.info(f'raise_for_status {response.status_code}')
                response.raise_for_status()

                if response.status_code != 200:
                    logging.fatal(
                        f"No data available for URL: {url}. Aborting download.")
                elif (response.status_code == 404):
                    logging.fatal(
                        f"Not Found for url: {url}. Aborting download.")
                elif response.status_code == 200:
                    if not response.content:
                        logging.fatal(
                            f"No data available for URL: {url}. Aborting download."
                        )
                    input_file_name = f"{file_name}.zip"
                    logging.info(
                        f'filename: {input_file_name} _INPUT_FILE_PATH : {_INPUT_FILE_PATH}'
                    )
                    file_path = os.path.join(_INPUT_FILE_PATH, input_file_name)
                    #download zip file locally
                    with open(file_path, 'wb') as f:
                        f.write(response.content)


def process(_INPUT_FILE_PATH, start_year, end_year):
    """
    Processes downloaded EPA AirData zip files, extracts, transforms, and
    consolidates the data into a single output CSV file.

    This method iterates through a specified range of years, from `start_year`
    up to (but not including) `end_year`. For each year, it expects to find
    two zipped files in the `_INPUT_FILE_PATH` directory:
    'daily_aqi_by_county_{year}.zip' and 'daily_aqi_by_cbsa_{year}.zip'.

    Args:
        _INPUT_FILE_PATH (str): The local directory path where the downloaded
                                 zip files (e.g., 'daily_aqi_by_county_2020.zip')
                                 are stored.
        start_year (int): The starting year (inclusive) from which to begin
                          processing data.
        end_year (int): The ending year (exclusive) for which to process data.
                        Processing will stop at `end_year - 1`.
    """
    output_file_name = f'EPA_AQI.csv'
    #Creating the output csv file beofre
    create_csv(output_file_name)
    for year in range(start_year, int(end_year)):
        logging.info(f'year: {year}')
        file_names = [
            f'daily_aqi_by_county_{year}', f'daily_aqi_by_cbsa_{year}'
        ]
        # Iterate over the list of file names (county and cbsa)
        for file_name in file_names:
            logging.info(f'Processing file: {file_name}')

            try:
                file_path = os.path.join(_INPUT_FILE_PATH, file_name)
                output_file_path = os.path.join(MODULE_DIR,
                                                _FLAGS.output_file_path,
                                                output_file_name)
                logging.info(
                    f'csv_file_path, output_file_path from request_and_write_csv  {output_file_name} {output_file_path}'
                )
                file_path_with_filename = f"{file_path}.zip"
                with open(file_path_with_filename, 'rb') as zip_file:
                    with zipfile.ZipFile(zip_file) as zf:
                        try:
                            with zf.open(f'{file_name}.csv', 'r') as infile:
                                reader = csv.DictReader(
                                    io.TextIOWrapper(infile, 'utf-8'))
                                write_csv(output_file_path, reader)
                        except FileNotFoundError:
                            raise FileNotFoundError(
                                f"CSV file '{file_name}.csv' not found in the ZIP archive"
                            )

            except Exception as e:
                logging.fatal(
                    f"Error while processing input files {e} {output_file_name}{output_file_name}"
                )


def main(_):
    mode = _FLAGS.mode
    input_file_path = os.path.join(MODULE_DIR, _FLAGS.input_file_path)
    output_file_path = os.path.join(MODULE_DIR, _FLAGS.output_file_path)
    Path(output_file_path).mkdir(parents=True, exist_ok=True)
    Path(input_file_path).mkdir(parents=True, exist_ok=True)
    start_year = _FLAGS.aggregate_start_year
    end_year = _FLAGS.aggregate_end_year
    CSV_URLS = frozendict.frozendict(
        {"daily_aqi": "https://aqs.epa.gov/aqsweb/airdata/"})

    if mode == "" or mode == "download":
        logging.info(f'inside mode {mode}')
        #downloading zip file for 'daily_aqi_by_county'
        logging.info(f'downloading zipped files')
        download_url(input_file_path, start_year, end_year, CSV_URLS)

    if mode == "" or mode == "process":
        logging.info(f'inside mode {mode}')
        process(input_file_path, start_year, end_year)


if __name__ == '__main__':
    app.run(main)
