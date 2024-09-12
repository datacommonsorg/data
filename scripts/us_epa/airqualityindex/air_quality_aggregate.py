# Copyright 2019 Google LLC
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

_FLAGS = flags.FLAGS

flags.DEFINE_integer('aggregate_start_year', os.getenv('START_YEAR', '1980'),
                     'Process data starting from this year.')
flags.DEFINE_integer('aggregate_end_year',
                     os.getenv('END_YEAR',
                               datetime.now().year),
                     'Process data upto this year.')

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
    with open(csv_file_path, 'w', newline='') as f_out:
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


def download_zip_file(url, filename):
    """Downloads a ZIP file from the given URL and saves it locally.

  Args:
      url: The URL of the ZIP file to download.
      filename: The local filename to save the downloaded ZIP file.
  """

    response = requests.get(url)

    if response.status_code == 200:  # Check for successful response (200 OK)
        with open(filename, 'wb') as f:
            f.write(response.content)
        logging.info(f'Downloaded ZIP file: {filename}')
    else:
        logging.error(f'Error downloading file: {response.status_code}')


def request_and_write_csv(csv_file_path, filename):
    response = requests.get(
        f'https://aqs.epa.gov/aqsweb/airdata/{filename}.zip')
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        with zf.open(f'{filename}.csv', 'r') as infile:
            reader = csv.DictReader(io.TextIOWrapper(infile, 'utf-8'))
            write_csv(csv_file_path, reader)
    #Calling method to download zip file locally
    download_zip_file(f'https://aqs.epa.gov/aqsweb/airdata/{filename}.zip',
                      filename)


def write_tmcf(tmcf_file_path):
    with open(tmcf_file_path, 'w') as f_out:
        f_out.write(TEMPLATE_MCF)


def main(_):
    start_year = _FLAGS.aggregate_start_year
    end_year = _FLAGS.aggregate_end_year
    if end_year >= datetime.now().year:
        end_year = datetime.now().year - 1
    logging.info(f'Processing from {start_year} to {end_year}')
    create_csv('EPA_AQI.csv')
    for year in range(start_year, int(end_year) + 1):
        filename1 = f'daily_aqi_by_county_{year}'
        filename2 = f'daily_aqi_by_cbsa_{year}'
        request_and_write_csv('EPA_AQI.csv', filename1)
        request_and_write_csv('EPA_AQI.csv', filename2)
    write_tmcf('EPA_AQI.tmcf')


if __name__ == '__main__':
    app.run(main)
