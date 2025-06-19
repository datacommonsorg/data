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


CSV_URLS = frozendict.frozendict(
    {"daily_aqi": "https://aqs.epa.gov/aqsweb/airdata/"})

POLLUTANTS = {
    'Ozone': 'Ozone',
    'SO2': 'SulfurDioxide',
    'CO': 'CarbonMonoxide',
    'NO2': 'NitrogenDioxide',
    'PM2.5': 'PM2.5',
    'PM10': 'PM10',
}

CSV_COLUMNS = ['Date', 'Place', 'AQI', 'Pollutant', 'Site']

# Template MCF for StatVarObservation
TEMPLATE_MCF = '''
Node: E:EPA_AQI->E0
typeOf: dcs:StatVarObservation
variableMeasured: dcs:AirQualityIndex_AirPollutant
observationDate: C:EPA_AQI->Date
observationAbout: C:EPA_AQI->Place
observationPeriod: "P1D"
value: C:EPA_AQI->AQI
definingPollutant: C:EPA_AQI->Pollutant
definingAirQualitySite: C:EPA_AQI->Site
'''


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


def download_url(_INPUT_FILE_PATH):
    """
    Downloads daily Air Quality Index (AQI) data from the EPA AirData website
    for a specified range of years and saves the zip files locally.

    It iterates through years from 'aggregate_start_year' to 'aggregate_end_year'
    (defined in absl flags) and attempts to download two types of files for each
    year: 'daily_aqi_by_county' and 'daily_aqi_by_cbsa'.

    Each download attempt includes retries (configured by the @retry decorator
    on `retry_method`) and checks the HTTP response status code to ensure data
    availability. Fatal logging messages are issued if no data is found or
    if a 404 Not Found error occurs.

    Args:
        _INPUT_FILE_PATH (str): The local directory path where the downloaded
                                 zip files will be saved.
    """

    start_year = _FLAGS.aggregate_start_year
    end_year = _FLAGS.aggregate_end_year
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


def process(_INPUT_FILE_PATH):
    """
    Processes the downloaded EPA AirData zip files, extracts the relevant CSV
    data, transforms it, and writes it to a consolidated output CSV file.
    It also generates a template MCF file for the data.

    The method iterates through each year from 'aggregate_start_year' to
    'aggregate_end_year' (defined in absl flags). For each year, it attempts
    to process two types of files: 'daily_aqi_by_county' and 'daily_aqi_by_cbsa'.

    It expects these files to be present as zipped archives in the
    `_INPUT_FILE_PATH` directory. Each zip file is opened, and the contained
    CSV file is read. Data rows are then transformed (e.g., 'Place' DCID generation,
    'Pollutant' DCID mapping) and appended to a single output CSV file named
    'EPA_AQI.csv'.

    Error handling is included to catch issues like missing zip files or
    missing CSV files within a zip archive, logging fatal errors accordingly.

    Args:
        _INPUT_FILE_PATH (str): The local directory path where the downloaded
                                 zip files are located.
    """
    output_file_name = f'EPA_AQI.csv'
    #Creating the output csv file beofre
    create_csv(output_file_name)
    start_year = _FLAGS.aggregate_start_year
    end_year = _FLAGS.aggregate_end_year
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

    if mode == "" or mode == "download":
        logging.info(f'inside mode {mode}')
        #downloading zip file for 'daily_aqi_by_county'
        logging.info(f'downloading zipped files')
        download_url(input_file_path)

    if mode == "" or mode == "process":
        logging.info(f'inside mode {mode}')
        process(input_file_path)


if __name__ == '__main__':
    app.run(main)
