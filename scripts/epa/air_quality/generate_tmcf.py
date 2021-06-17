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
Generates cleaned CSV and template MCF files for the EPA Outdoor Air Quality.

Usage: python3 generate_tmcf.py
'''
import csv, os
from zipfile import ZipFile
from io import TextIOWrapper

SOURCE_DATA = "source_data"

# Using the following pollutant standards for each pollutant:
PARAMETER_CODE = {
    '44201': ['Ozone', 'Ozone 8-hour 2015'], # Ozone
    '42401': ['SO2', 'SO2 1-hour 2010'],  # SO2 
    '42101': ['CO', 'CO 8-hour 1971'],  # CO
    '42602': ['NO2', 'NO2 1-hour'],  # NO2 
    '88101': ['PM2.5', 'PM25 24-hour 2012'],  # PM2.5 FRM/FEM Mass
    '81102': ['PM10', 'PM10 24-hour 2006'],  # PM10 Mass
}

STATISTICAL_VARIABLES = [
    'Mean_Concentration_AirPollutant_Ozone', 
    'Max_Concentration_AirPollutant_Ozone', 
    'AirQualityIndex_AirPollutant_Ozone',
    'Mean_Concentration_AirPollutant_SO2', 
    'Max_Concentration_AirPollutant_SO2', 
    'AirQualityIndex_AirPollutant_SO2',
    'Mean_Concentration_AirPollutant_CO', 
    'Max_Concentration_AirPollutant_CO', 
    'AirQualityIndex_AirPollutant_CO',
    'Mean_Concentration_AirPollutant_NO2', 
    'Max_Concentration_AirPollutant_NO2', 
    'AirQualityIndex_AirPollutant_NO2',
    'Mean_Concentration_AirPollutant_PM2.5', 
    'Max_Concentration_AirPollutant_PM2.5', 
    'AirQualityIndex_AirPollutant_PM2.5',
    'Mean_Concentration_AirPollutant_PM10', 
    'Max_Concentration_AirPollutant_PM10', 
    'AirQualityIndex_AirPollutant_PM10',
]

CSV_COLUMNS = [
    'Date', 'Site_Number', 'Site_Name', 'Site_Location', 'County', 
    'Units_Ozone', 'Units_SO2', 'Units_CO', 'Units_NO2', 'Units_PM2.5', 'Units_PM10'
] + STATISTICAL_VARIABLES

# Template MCF for StatVarObservation
TEMPLATE_MCF = '''
Node: E:EPA_AirQuality->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{var}
observationDate: C:EPA_AirQuality->Date
observationAbout: E:EPA_daily_air_quality->E0
observationPeriod: dcs:P1D
value: C:EPA_AirQuality->{var}
unit: C:EPA_AirQuality->Units_{pollutant}
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

def join(d, observation):
    # Skip observations that don't match selected pollutant standards
    if observation['Pollutant Standard'] != PARAMETER_CODE[observation['Parameter Code']][1]:
        return
    
    key = (observation['Date Local'], observation['Site Num'])
    pollutant = PARAMETER_CODE[observation['Parameter Code']][0]
    if key in d:
        d[key][f'Mean_Concentration_AirPollutant_{pollutant}'] = observation['Arithmetic Mean']
        d[key][f'Max_Concentration_AirPollutant_{pollutant}'] = observation['1st Max Value']
        d[key][f'AirQualityIndex_AirPollutant_{pollutant}'] = observation['AQI']
        d[key][f'Units_{pollutant}'] = observation['Units of Measure']
    else: 
        d[key] = {
            'Date': observation['Date Local'],
            'Site_Number': 'epa/' + observation['Site Num'],
            'Site_Name': observation['Local Site Name'],
            'Site_Location': '[latLong {lat} {long}]'.format(
                lat=observation['Latitude'], long=observation['Longitude']),
            'County': 'geoId/' + observation['State Code'] + observation['County Code'],  # geoID for county
            f'Mean_Concentration_AirPollutant_{pollutant}': observation['Arithmetic Mean'],
            f'Max_Concentration_AirPollutant_{pollutant}': observation['1st Max Value'],
            f'AirQualityIndex_AirPollutant_{pollutant}': observation['AQI'],
            f'Units_{pollutant}': observation['Units of Measure']
        }


def write_csv(csv_file_path, d):
    with open(csv_file_path, 'w', newline='') as f_out:
        writer = csv.DictWriter(f_out,
                                fieldnames=CSV_COLUMNS,
                                lineterminator='\n')
        writer.writeheader()
        for key in d: 
            writer.writerow(d[key])


def write_tmcf(tmcf_file_path):
    with open(tmcf_file_path, 'w') as f_out:   
        f_out.write(TEMPLATE_MCF_AIR_QUALITY_SITE)    
        for i in range(len(STATISTICAL_VARIABLES)):
            f_out.write(
                TEMPLATE_MCF.format_map({
                    'index': i + 1,
                    'var': STATISTICAL_VARIABLES[i],
                    'pollutant': STATISTICAL_VARIABLES[i].split('_')[-1]
                }))


if __name__ == '__main__':
    d = {}
    for (dirpath, dirnames, filenames) in os.walk(SOURCE_DATA):
        for filename in filenames:
            if filename.endswith('.zip'):
                print(filename)
                with ZipFile(dirpath + os.sep + filename) as zf:
                    with zf.open(filename[:-4] + '.csv', 'r') as infile:
                        reader = csv.DictReader(TextIOWrapper(infile, 'utf-8'))
                        for row in reader:
                            join(d, row)
    write_csv('EPA_AirQuality.csv', d)
    write_tmcf('EPA_AirQuality.tmcf')