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
import urllib.request, json, csv

# Using the following pollutant standards for each pollutant:
PARAMETER_CODE = {
    '44201': ['Ozone', 'Ozone 8-hour 2015'], # Ozone
    '42401': ['SO2', 'SO2 1-hour 2010'],  # SO2 
    '42101': ['CO', 'CO 8-hour 1971'],  # CO
    '42602': ['NO2', 'NO2 1-hour'],  # NO2 
    '88101': ['PM2.5', 'PM25 24-hour 2012'],  # PM2.5 FRM/FEM Mass
    '81102': ['PM10', 'PM10 24-hour 2006'],  # PM10 Mass
}

STATE_CODES = 56

# Data will be collected from 1980 to latest available year
START_DATE, END_DATE = 1980, 2021

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
observationAbout: E:EPA_daily_air_quality->E{site}
observationPeriod: dcs:P1D
value: C:EPA_AirQuality->{var}
unit: C:EPA_AirQuality->Units_{pollutant}
'''

# Template MCF for Air Quality Site
TEMPLATE_MCF_AIR_QUALITY_SITE = '''
Node: E:EPA_AirQuality->E{index}
typeOf: dcs:AirQualitySite
dcid: C:EPA_AirQuality->Site_Number
name: C:EPA_AirQuality->Site_Name
location: C:EPA_AirQuality->Site_Location
containedInPlace: C:EPA_AirQuality->County
'''

def getDataUrl(param, year, state): 
    return f'https://aqs.epa.gov/data/api/dailyData/byState?email=test@aqs.api' \
        f'&key=test&param={param}&bdate={year}0101&edate={year}1231&state={state}'


def join(d, data):
    for observation in data: 
        # Skip observations that don't match selected pollutant standards
        if observation['pollutant_standard'] != PARAMETER_CODE[observation['parameter_code']][1]:
            continue
        
        key = (observation['date_local'], observation['site_number'])
        pollutant = PARAMETER_CODE[observation['parameter_code']][0]
        if key in d:
            d[key][f'Mean_Concentration_AirPollutant_{pollutant}'] = observation['arithmetic_mean']
            d[key][f'Max_Concentration_AirPollutant_{pollutant}'] = observation['first_max_value']
            d[key][f'AirQualityIndex_AirPollutant_{pollutant}'] = observation['aqi']
            d[key][f'Units_{pollutant}'] = observation['units_of_measure']
        else: 
            d[key] = {
                'Date': observation['date_local'],
                'Site_Number': 'epa/' + observation['site_number'],
                'Site_Name': observation['local_site_name'],
                'Site_Location': '[latLong {lat} {long}]'.format(
                    lat=observation['latitude'], long=observation['longitude']),
                'County': 'geoId/' + observation['state_code'] + observation['county_code'],  # geoID for county
                f'Mean_Concentration_AirPollutant_{pollutant}': observation['arithmetic_mean'],
                f'Max_Concentration_AirPollutant_{pollutant}': observation['first_max_value'],
                f'AirQualityIndex_AirPollutant_{pollutant}': observation['aqi'],
                f'Units_{pollutant}': observation['units_of_measure']
            }



def writeCSV(csv_file_path, d):
    with open(csv_file_path, 'w', newline='') as f_out:
        writer = csv.DictWriter(f_out,
                                fieldnames=CSV_COLUMNS,
                                lineterminator='\n')
        writer.writeheader()
        for key in d: 
            writer.writerow(d[key])



def writeTMCF(tmcf_file_path):
    with open(tmcf_file_path, 'w') as f_out:   
        i = 0
        for var in STATISTICAL_VARIABLES:
            f_out.write(
                TEMPLATE_MCF.format_map({
                    'index': i,
                    'var': var,
                    'site': i + 1,
                    'pollutant': var.split('_')[-1]
                }))
            f_out.write(
                TEMPLATE_MCF_AIR_QUALITY_SITE.format_map({
                    'index': i + 1,
                }))          
            i += 2


if __name__ == '__main__':
    #for param in PARAMETER_CODE: 
    #    for year in range(START_DATE, END_DATE + 1):
    #        for state in range(1, STATE_CODES + 1):
    #            print(getDataUrl(param, year, f"{state:02d}"))
    param = 44201
    year = 2021
    for state in range(1,2):
        with urllib.request.urlopen(getDataUrl(param, year, f"{state:02d}")) as url:
            response = json.loads(url.read().decode())
            if response['Header'][0]['rows'] == 0:  # Response failed or is empty
                continue
            data = response['Data']
            d = {}
            join(d, data)
    writeCSV('EPA_AirQuality.csv', d)
    writeTMCF('EPA_AirQuality.tmcf')