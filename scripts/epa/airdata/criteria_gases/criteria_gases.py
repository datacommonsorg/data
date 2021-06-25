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
Generates cleaned CSV and template MCF files for the EPA AirData Criteria
Gases.

Usage: python3 criteria_gases.py
'''
import csv, os
from zipfile import ZipFile
from io import TextIOWrapper

SOURCE_DATA = "source_data"

CSV_COLUMNS = [
    'Date', 'Site_Number', 'Site_Name', 'Site_Location', 'County',
    'Mean', 'Max', 'AQI', 'Units', 'Method', 'POC',
    'Mean_SV', 'Max_SV', 'AQI_SV']

# Template MCF for StatVarObservation
TEMPLATE_MCF = '''
Node: E:EPA_CriteriaGases->E1
typeOf: dcs:StatVarObservation
variableMeasured: C:EPA_CriteriaGases->Mean_SV
measurementMethod: C:EPA_CriteriaGases->Method
observationDate: C:EPA_CriteriaGases->Date
observationAbout: E:EPA_CriteriaGases->E0
observationPeriod: dcs:"P1D"
value: C:EPA_CriteriaGases->Mean
unit: C:EPA_CriteriaGases->Units

Node: E:EPA_CriteriaGases->E2
typeOf: dcs:StatVarObservation
variableMeasured: C:EPA_CriteriaGases->Max_SV
measurementMethod: C:EPA_CriteriaGases->Method
observationDate: C:EPA_CriteriaGases->Date
observationAbout: E:EPA_CriteriaGases->E0
observationPeriod: dcs:"P1D"
value: C:EPA_CriteriaGases->Max
unit: C:EPA_CriteriaGases->Units

Node: E:EPA_CriteriaGases->E3
typeOf: dcs:StatVarObservation
variableMeasured: C:EPA_CriteriaGases->AQI_SV
measurementMethod: C:EPA_CriteriaGases->Method
observationDate: C:EPA_CriteriaGases->Date
observationAbout: E:EPA_CriteriaGases->E0
observationPeriod: dcs:"P1D"
value: C:EPA_CriteriaGases->AQI
'''

# Template MCF for Air Quality Site
TEMPLATE_MCF_AIR_QUALITY_SITE = '''
Node: E:EPA_CriteriaGases->E0
typeOf: dcs:AirQualitySite
dcid: C:EPA_CriteriaGases->Site_Number
name: C:EPA_CriteriaGases->Site_Name
location: C:EPA_CriteriaGases->Site_Location
containedInPlace: C:EPA_CriteriaGases->County
airQualitySiteMonitor: C:EPA_CriteriaGases->POC
'''

# Convert to CamelCase (splitting on spaces)
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


def get_pollutant_standard(s):
    return s.replace(' ', '_').replace('-', '')


# Hardcoded for consistency in StatisticalVariable names
def get_suffix(parameter):
    if parameter == '44201':
        return 'Ozone'
    elif parameter == '42401':
        return 'SO2'
    elif parameter == '42101':
        return 'CO'
    elif parameter == '42602':
        return 'NO2'
    return ''


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
        keys = set()
        for observation in reader:
            # Select only one observation for a given date, site, and pollutant standard
            # POC will be stored as airQualitySiteMonitor
            key = '{date}{state}{county}{site}{standard}'.format(
                date=observation['Date Local'],
                state=observation['State Code'],
                county=observation['County Code'],
                site=observation['Site Num'],
                standard=get_pollutant_standard(observation['Pollutant Standard']),
            )
            if key in keys:
                continue
            keys.add(key)
            suffix = get_suffix(observation["Parameter Code"])
            new_row = {
                'Date': observation['Date Local'],
                'Site_Number': 'epa/{state}{county}{site}'.format(
                    state=observation['State Code'],
                    county=observation['County Code'],
                    site=observation['Site Num']
                ),
                'Site_Name': observation['Local Site Name'],
                'Site_Location': '[latLong {lat} {long}]'.format(
                    lat=observation['Latitude'], long=observation['Longitude']),
                'County': 'dcid:geoId/' + observation['State Code'] + observation['County Code'],
                'Mean': observation['Arithmetic Mean'],
                'Max': observation['1st Max Value'],
                'AQI': observation['AQI'],
                'Units': get_camel_case(observation['Units of Measure']),
                'Method': get_pollutant_standard(observation['Pollutant Standard']),
                'POC': observation['POC'],
                'Mean_SV': f'dcs:Mean_Concentration_AirPollutant_{suffix}',
                'Max_SV': f'dcs:Max_Concentration_AirPollutant_{suffix}',
                'AQI_SV': f'dcs:AirQualityIndex_AirPollutant_{suffix}',
            }
            writer.writerow(new_row)


def write_tmcf(tmcf_file_path):
    with open(tmcf_file_path, 'w') as f_out:
        f_out.write(TEMPLATE_MCF_AIR_QUALITY_SITE)
        f_out.write(TEMPLATE_MCF)


if __name__ == '__main__':
    create_csv(f'EPA_CriteriaGases.csv')
    for (dirpath, dirnames, filenames) in os.walk(SOURCE_DATA):
        for filename in filenames:
            if filename.endswith('.zip'):
                print(filename)
                with ZipFile(dirpath + os.sep + filename) as zf:
                    with zf.open(filename[:-4] + '.csv', 'r') as infile:
                        reader = csv.DictReader(TextIOWrapper(infile, 'utf-8'))
                        write_csv(f'EPA_CriteriaGases.csv', reader)
    write_tmcf(f'EPA_CriteriaGases.tmcf')
