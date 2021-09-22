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

POLLUTANTS = {
    'Ozone': 'Ozone',
    'SO2': 'SulfurDioxide',
    'CO': 'CarbonMonoxide',
    'NO2': 'NitrogenDioxide',
    'PM2.5': 'PM2.5',
    'PM10': 'PM10',
}

START_YEAR = 1980

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


def request_and_write_csv(csv_file_path, filename):
    response = requests.get(
        f'https://aqs.epa.gov/aqsweb/airdata/{filename}.zip')
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        with zf.open(f'{filename}.csv', 'r') as infile:
            reader = csv.DictReader(io.TextIOWrapper(infile, 'utf-8'))
            write_csv(csv_file_path, reader)


def write_tmcf(tmcf_file_path):
    with open(tmcf_file_path, 'w') as f_out:
        f_out.write(TEMPLATE_MCF)


if __name__ == '__main__':
    end_year = sys.argv[1]
    create_csv('EPA_AQI.csv')
    for year in range(START_YEAR, int(end_year) + 1):
        filename1 = f'daily_aqi_by_county_{year}'
        filename2 = f'daily_aqi_by_cbsa_{year}'
        request_and_write_csv('EPA_AQI.csv', filename1)
        request_and_write_csv('EPA_AQI.csv', filename2)
    write_tmcf('EPA_AQI.tmcf')
