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

Usage: python3 criteria_gases.py <POLLUTANT_ID>
'''
import csv, os, sys
from zipfile import ZipFile
from io import TextIOWrapper

SOURCE_DATA = "source_data"

CSV_COLUMNS = ['Date', 'Site_Number', 'Site_Name', 'Site_Location', 'County']

POLLUTANT_STANDARD = {
    '44201': ['Ozone_8hour_2015'],
    '42401': ['SO2_1hour_2010', 'SO2_3hour_1971'],
    '42101': ['CO_1hour_1971', 'CO_8hour_1971'],
    '42602': ['NO2_1hour'],
}

# Template MCF for StatVarObservation
TEMPLATE_MCF = '''
Node: E:EPA_CriteriaGases->E{mean_index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:Mean_Concentration_AirPollutant_{suffix}
measurementMethod: C:EPA_CriteriaGases->Method_{suffix}
observationDate: C:EPA_CriteriaGases->Date
observationAbout: E:EPA_CriteriaGases->E0
observationPeriod: dcs:"P1D"
value: C:EPA_CriteriaGases->Mean_Concentration_AirPollutant_{suffix}
unit: C:EPA_CriteriaGases->Units_{suffix}

Node: E:EPA_CriteriaGases->E{max_index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:Max_Concentration_AirPollutant_{suffix}
measurementMethod: C:EPA_CriteriaGases->Method_{suffix}
observationDate: C:EPA_CriteriaGases->Date
observationAbout: E:EPA_CriteriaGases->E0
observationPeriod: dcs:"P1D"
value: C:EPA_CriteriaGases->Max_Concentration_AirPollutant_{suffix}
unit: C:EPA_CriteriaGases->Units_{suffix}

Node: E:EPA_CriteriaGases->E{aqi_index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:AirQualityIndex_AirPollutant_{suffix}
observationDate: C:EPA_CriteriaGases->Date
observationAbout: E:EPA_CriteriaGases->E0
observationPeriod: dcs:"P1D"
value: C:EPA_CriteriaGases->AirQualityIndex_AirPollutant_{suffix}
'''

# Template MCF for Air Quality Site
TEMPLATE_MCF_AIR_QUALITY_SITE = '''
Node: E:EPA_CriteriaGases->E0
typeOf: dcs:AirQualitySite
dcid: C:EPA_CriteriaGases->Site_Number
name: C:EPA_CriteriaGases->Site_Name
location: C:EPA_CriteriaGases->Site_Location
containedInPlace: C:EPA_CriteriaGases->County
'''

# Convert to CamelCase (splitting on spaces)
def get_camel_case(camel_case, s):
    if s in camel_case:
        return camel_case[s]
    parts = s.lower().split()
    result = ''
    for i in range(len(parts)):
        result += parts[i][0].upper()
        if len(parts[i]) > 0: 
            result += parts[i][1:]
    camel_case[s] = result
    return result


# Hardcoded for consistency in StatisticalVariable names
def get_suffix(parameter, standard):
    if parameter == 'Ozone':
        if standard == 'Ozone 8-hour 2015':
            return 'Ozone_8hour_2015'
        return 'Ozone'
    elif parameter == 'Sulfur dioxide':
        if standard == 'SO2 1-hour 2010':
            return 'SO2_1hour_2010'
        elif standard == 'SO2 3-hour 1971':
            return 'SO2_3hour_1971'
        return 'SO2'
    elif parameter == 'Carbon monoxide':
        if standard == 'CO 1-hour 1971':
            return 'CO_1hour_1971'
        elif standard == 'CO 8-hour 1971':
            return 'CO_8hour_1971'
        return 'CO'
    elif parameter == 'Nitrogen dioxide (NO2)':
        if standard == 'NO2 1-hour':
            return 'NO2_1hour'
        return 'NO2'
    return ''

def join(d, observation, camel_case):
    site = 'epa/{state}{county}{site}'.format(
        state=observation['State Code'], county=observation['County Code'], site=observation['Site Num'])
    key = (observation['Date Local'], site)
    suffix = get_suffix(observation['Parameter Name'], observation['Pollutant Standard'])
    if key in d:
        d[key][f'Mean_Concentration_AirPollutant_{suffix}'] = observation['Arithmetic Mean']
        d[key][f'Max_Concentration_AirPollutant_{suffix}'] = observation['1st Max Value']
        d[key][f'AirQualityIndex_AirPollutant_{suffix}'] = observation['AQI']
        d[key][f'Units_{suffix}'] = get_camel_case(camel_case, observation['Units of Measure'])
        d[key][f'Method_{suffix}'] = get_camel_case(camel_case, observation['Method Name'])
    else: 
        d[key] = {
            'Date': observation['Date Local'],
            'Site_Number': site,
            'Site_Name': observation['Local Site Name'],
            'Site_Location': '[latLong {lat} {long}]'.format(
                lat=observation['Latitude'], long=observation['Longitude']),
            'County': 'dcid:geoId/' + observation['State Code'] + observation['County Code'],  # geoID for county
            f'Mean_Concentration_AirPollutant_{suffix}': observation['Arithmetic Mean'],
            f'Max_Concentration_AirPollutant_{suffix}': observation['1st Max Value'],
            f'AirQualityIndex_AirPollutant_{suffix}': observation['AQI'],
            f'Units_{suffix}': get_camel_case(camel_case, observation['Units of Measure']),
            f'Method_{suffix}': get_camel_case(camel_case, observation['Method Name']),
        }

def write_csv(csv_file_path, d, pollutant):
    with open(csv_file_path, 'w', newline='') as f_out:
        columns = CSV_COLUMNS
        for i in range(len(POLLUTANT_STANDARD[pollutant])):
            suffix = POLLUTANT_STANDARD[pollutant][i]
            columns.append(f'Mean_Concentration_AirPollutant_{suffix}')
            columns.append(f'Max_Concentration_AirPollutant_{suffix}')
            columns.append(f'AirQualityIndex_AirPollutant_{suffix}')
            columns.append(f'Units_{suffix}')
            columns.append(f'Method_{suffix}')
        writer = csv.DictWriter(f_out,
                                fieldnames=columns,
                                lineterminator='\n')
        writer.writeheader()
        for key in d: 
            writer.writerow(d[key])


def write_tmcf(tmcf_file_path, pollutant):
    with open(tmcf_file_path, 'w') as f_out:   
        f_out.write(TEMPLATE_MCF_AIR_QUALITY_SITE)
        for i in range(len(POLLUTANT_STANDARD[pollutant])):
            f_out.write(
                TEMPLATE_MCF.format_map({
                    'mean_index': (3 * i) + 1, 
                    'max_index': (3 * i) + 2,
                    'aqi_index': (3 * i) + 3,
                    'suffix': POLLUTANT_STANDARD[pollutant][i]
                }))


if __name__ == '__main__':
    pollutant = sys.argv[1]
    camel_case = {
        '': '',
        ' - ': '',
    }
    d = {}   
    for (dirpath, dirnames, filenames) in os.walk(SOURCE_DATA + '/' + pollutant):
        for filename in filenames:
            if filename.endswith('.zip'):
                print(filename)
                with ZipFile(dirpath + os.sep + filename) as zf:
                    with zf.open(filename[:-4] + '.csv', 'r') as infile:
                        reader = csv.DictReader(TextIOWrapper(infile, 'utf-8'))
                        for row in reader:
                            join(d, row, camel_case)
    write_csv(f'EPA_CriteriaGases_{pollutant}.csv', d, pollutant) 
    write_tmcf(f'EPA_CriteriaGases_{pollutant}.tmcf', pollutant)
    