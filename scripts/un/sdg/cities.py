# Copyright 2023 Google LLC
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
'''Finds dcids for cities.

Produces:
* cities.csv: dcid for each city code
 
There are a few city codes that are still missing.
These can be manually filled in and verified.
**This script ideally shouldn't need to be run again.**

Usage: python3 cities.py <DATACOMMONS_API_KEY>
'''
import csv
import requests
import pandas as pd
import sys


def get_cities(json, api_key):
    '''Applies find entities API for given json.

    Args:
        json: Input json.
        api_key: API key.

    Returns:
        API response.
    '''
    return requests.post('https://api.datacommons.org/v1/bulk/find/entities',
                         headers={
                             'X-API-Key': api_key
                         },
                         json=json).json()


def write_cities(file, cities, api_key):
    '''Writes city codes and names to file.

    Args:
        file: Output file path.
        cities: Map of city names to codes. 
        api_key: API key.
    '''
    with open(file, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'dcid'])
        writer.writeheader()
        for city in list(cities.keys()):
            json = {'entities': [{'description': city}]}
            response = get_cities(json, api_key)
            try:
                for entity in response['entities']:
                    dcid = entity['dcids'][0] if 'dcids' in entity else ''
                    writer.writerow({
                        'name': cities[entity['description']],
                        'dcid': dcid
                    })
            except KeyError:
                writer.writerow({'name': cities[city], 'dcid': ''})


if __name__ == '__main__':
    df = pd.read_excel(f'sdg-dataset/output/SDG_cities_enumeration.xlsx')
    cities = {}
    for _, row in df.iterrows():
        cities[row['CITY_NAME'] + ', ' + row['GEO_AREA_NAME'].replace(
            '_', ' ').title()] = row['CITY_CODE']
    write_cities('cities_test.csv', cities, sys.argv[1])
