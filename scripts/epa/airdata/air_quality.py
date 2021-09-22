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

# AQS parameter codes: https://aqs.epa.gov/aqsweb/documents/codetables/parameters.html
POLLUTANTS = {
    '44201': 'Ozone',
    '42401': 'SO2',
    '42101': 'CO',
    '42602': 'NO2',
    '88101': 'PM2.5',
    '81102': 'PM10',
}

START_YEAR = 1980

CSV_COLUMNS = [
    'Date', 'Site_Number', 'Site_Name', 'Site_Location', 'County', 'Units',
    'Method', 'POC', 'Mean', 'Max', 'AQI', 'Mean_SV', 'Max_SV', 'AQI_SV'
]

# Template MCF for StatVarObservation
TEMPLATE_MCF = '''
Node: E:EPA_AirQuality->E1
typeOf: dcs:StatVarObservation
variableMeasured: C:EPA_AirQuality->Mean_SV
measurementMethod: C:EPA_AirQuality->Method
observationDate: C:EPA_AirQuality->Date
observationAbout: E:EPA_AirQuality->E0
observationPeriod: "P1D"
value: C:EPA_AirQuality->Mean
unit: C:EPA_AirQuality->Units
airQualitySiteMonitor: C:EPA_AirQuality->POC

Node: E:EPA_AirQuality->E2
typeOf: dcs:StatVarObservation
variableMeasured: C:EPA_AirQuality->Max_SV
measurementMethod: C:EPA_AirQuality->Method
observationDate: C:EPA_AirQuality->Date
observationAbout: E:EPA_AirQuality->E0
observationPeriod: "P1D"
value: C:EPA_AirQuality->Max
unit: C:EPA_AirQuality->Units
airQualitySiteMonitor: C:EPA_AirQuality->POC

Node: E:EPA_AirQuality->E3
typeOf: dcs:StatVarObservation
variableMeasured: C:EPA_AirQuality->AQI_SV
measurementMethod: C:EPA_AirQuality->Method
observationDate: C:EPA_AirQuality->Date
observationAbout: E:EPA_AirQuality->E0
observationPeriod: "P1D"
value: C:EPA_AirQuality->AQI
airQualitySiteMonitor: C:EPA_AirQuality->POC
'''

# Template MCF for Air Quality Site
TEMPLATE_MCF_AIR_QUALITY_SITE = '''
Node: E:EPA_AirQuality->E0
typeOf: dcs:AirQualitySite
dcid: C:EPA_AirQuality->Site_Number
name: C:EPA_AirQuality->Site_Name
location: C:EPA_AirQuality->Site_Location
containedInPlace: C:EPA_AirQuality->County
'''


# Convert to CamelCase (splitting on spaces)
# Example: Parts per million -> PartsPerMillion
def get_camel_case(s):
    if s == '' or s == ' - ':
        return ''
    parts = s.lower().split()
    result = ''
    for i in range(len(parts)):
        result += parts[i][0].upper()
        if len(parts[i]) > 0:
            result += parts[i][1:]
    return result


# Example: Ozone 8-hour 2015 -> Ozone_8hour_2015
def get_pollutant_standard(s):
    return s.replace(' ', '_').replace('-', '')


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
            }
            writer.writerow(new_row)


def write_tmcf(tmcf_file_path):
    with open(tmcf_file_path, 'w') as f_out:
        f_out.write(TEMPLATE_MCF_AIR_QUALITY_SITE)
        f_out.write(TEMPLATE_MCF)


if __name__ == '__main__':
    end_year = sys.argv[1]
    create_csv('EPA_AirQuality.csv')
    for pollutant in POLLUTANTS:
        for year in range(START_YEAR, int(end_year) + 1):
            filename = f'daily_{pollutant}_{year}'
            print(filename)
            response = requests.get(
                f'https://aqs.epa.gov/aqsweb/airdata/{filename}.zip')
            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                with zf.open(f'{filename}.csv', 'r') as infile:
                    reader = csv.DictReader(io.TextIOWrapper(infile, 'utf-8'))
                    write_csv('EPA_AirQuality.csv', reader)
    write_tmcf('EPA_AirQuality.tmcf')
