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

Usage: python3 air_quality.py <end_year>
'''
import csv, os, sys, requests, io, zipfile

from absl import app
from absl import flags
from absl import logging
from datetime import datetime

_FLAGS = flags.FLAGS

flags.DEFINE_integer('data_start_year', os.getenv('START_YEAR', '1980'),
                     'Process data starting from this year.')
flags.DEFINE_integer('data_end_year', os.getenv('END_YEAR',
                                                datetime.now().year),
                     'Process data upto this year.')

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_GCS_OUTPUT_DIR = os.path.join(_MODULE_DIR, 'gcs_output')
if not os.path.exists(_GCS_OUTPUT_DIR):
    os.makedirs(_GCS_OUTPUT_DIR)

_OUTPUT_FILE_PATH = os.path.join(_GCS_OUTPUT_DIR, 'output')
_INPUT_FILE_PATH = os.path.join(_GCS_OUTPUT_DIR, 'input_files')

if not os.path.exists(_OUTPUT_FILE_PATH):
    os.makedirs(_OUTPUT_FILE_PATH, exist_ok=True)

if not os.path.exists(_INPUT_FILE_PATH):
    os.makedirs(_INPUT_FILE_PATH, exist_ok=True)

# AQS parameter codes: https://aqs.epa.gov/aqsweb/documents/codetables/parameters.html
POLLUTANTS = {
    '44201': 'Ozone',
    '42401': 'SO2',
    '42101': 'CO',
    '42602': 'NO2',
    '88101': 'PM2.5',
    '81102': 'PM10',
}

CSV_COLUMNS = [
    'Date', 'Site_Number', 'Site_Name', 'Site_Location', 'County', 'Units',
    'Method', 'POC', 'Mean', 'Max', 'AQI', 'Mean_SV', 'Max_SV', 'AQI_SV',
    'Address'
]


# Convert to CamelCase (splitting on spaces)
# Example: Parts per million -> PartsPerMillion
def get_camel_case(s):
    if s == '' or s == ' - ':
        return ''
    elif s == "Micrograms/cubic meter (25 C)":
        return "MicrogramsPerCubicMeter_25C"
    elif s == "Micrograms/cubic meter (LC)":
        return "MicrogramsPerCubicMeter_lc"
    parts = s.lower().split()
    result = ''
    for i in range(len(parts)):
        result += parts[i][0].upper()
        if len(parts[i]) > 0:
            result += parts[i][1:]
    return result


def get_county(state_code, county_code):
    return 'dcid:geoId/' + state_code + county_code


# Example: Ozone 8-hour 2015 -> Ozone_8hour_2015
def get_pollutant_standard(s):
    return s.replace(' ', '_').replace('-', '')


def remove_double_quotes(address_string):
    """Removes all double-quote characters from a string."""
    return address_string.replace('"', '')


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
        monitors = {}
        keys = set()
        for observation in reader:
            # For a given site and pollutant standard, select the same monitor
            monitor_key = (
                observation['State Code'],
                observation['County Code'],
                observation['Site Num'],
                get_pollutant_standard(observation['Pollutant Standard']),
            )
            if monitor_key not in monitors:
                monitors[monitor_key] = observation['POC']
            elif monitors[monitor_key] != observation['POC']:
                continue
            key = (
                observation['Date Local'],
                observation['State Code'],
                observation['County Code'],
                observation['Site Num'],
                get_pollutant_standard(observation['Pollutant Standard']),
            )
            if key in keys:
                continue
            keys.add(key)
            suffix = POLLUTANTS[observation["Parameter Code"]]
            new_row = {
                'Date':
                    observation['Date Local'],
                'Site_Number':
                    'epa/{state}{county}{site}'.format(
                        state=observation['State Code'],
                        county=observation['County Code'],
                        site=observation['Site Num']),
                'Site_Name':
                    observation['Local Site Name'],
                'Site_Location':
                    '[latLong {lat} {long}]'.format(
                        lat=observation['Latitude'],
                        long=observation['Longitude']),
                'County':
                    'dcid:geoId/' + observation['State Code'] +
                    observation['County Code'],
                'POC':
                    observation['POC'],
                'Units':
                    get_camel_case(observation['Units of Measure']),
                'Method':
                    get_pollutant_standard(observation['Pollutant Standard']),
                'Mean':
                    observation['Arithmetic Mean'],
                'Max':
                    observation['1st Max Value'],
                'AQI':
                    observation['AQI'],
                'Mean_SV':
                    f'dcs:Mean_Concentration_AirPollutant_{suffix}',
                'Max_SV':
                    f'dcs:Max_Concentration_AirPollutant_{suffix}',
                'AQI_SV':
                    f'dcs:AirQualityIndex_AirPollutant_{suffix}',
                'Address':
                    remove_double_quotes(observation['Address'])
            }
            if new_row['County'].startswith('dcid:geoId/80'):
                print(f"Skipping row with State Code '80': {new_row['County']}")
                continue  # Move to the next iteration of the for loop
            writer.writerow(new_row)


def main(_):
    start_year = _FLAGS.data_start_year
    end_year = _FLAGS.data_end_year
    if end_year >= datetime.now().year:
        end_year = datetime.now().year - 1
    logging.info(f'Processing from {start_year} upto {end_year}')

    for year in range(start_year, int(end_year) + 1):
        file = f'EPA_AirQuality{year}.csv'
        output_file = os.path.join(_OUTPUT_FILE_PATH, file)

        create_csv(output_file)
        for pollutant in POLLUTANTS:
            filename = f'daily_{pollutant}_{year}'
            local_zip_filepath = os.path.join(_INPUT_FILE_PATH, filename)
            logging.info(f"downloading and processing the file {filename}")
            response = requests.get(
                f'https://aqs.epa.gov/aqsweb/airdata/{filename}.zip')
            logging.info(f'https://aqs.epa.gov/aqsweb/airdata/{filename}.zip')

            # Save the downloaded zip file locally
            with open(f'{local_zip_filepath}.zip', 'wb') as local_file:
                for chunk in response.iter_content(chunk_size=8192):
                    local_file.write(chunk)
            logging.info(
                f"Successfully downloaded and saved: {local_zip_filepath}")

            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                with zf.open(f'{filename}.csv', 'r') as infile:
                    reader = csv.DictReader(io.TextIOWrapper(infile, 'utf-8'))
                    write_csv(output_file, reader)


if __name__ == '__main__':
    app.run(main)
