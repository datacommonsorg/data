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
'''This script does not use the most up-to-date schema format. 
It should only be used as an illustration of the SDMX -> MCF mapping.
Do not actually run!

Finds dcids for cities in input files.

Produces:
* preprocessed/cities.csv: dcid for each city name
 
Note: For cities where the find entities API did not return a dcid,
we tried manually searching for the dcid and filled these into the file.
There are a few city names that are still missing - these are left blank.
**This script ideally shouldn't need to be run again.**
Usage: python3 cities.py <API_KEY>
'''
import csv
import requests
import os
import sys

BATCH = 1


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
    '''Writes city dcids and names to file.
    Args:
        file: Output file path.
        cities: List of city dcids to process. 
        api_key: API key.
    '''
    with open(file, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'dcid'])
        writer.writeheader()
        city_list = list(cities.keys())
        for i in range(0, len(city_list), BATCH):
            json = {
                'entities': [{
                    'description': city
                } for city in city_list[i:i + BATCH]]
            }
            response = get_cities(json, api_key)
            print(response)
            try:
                for entity in response['entities']:
                    dcid = entity['dcids'][0] if 'dcids' in entity else ''
                    writer.writerow({
                        'name': cities[entity['description']],
                        'dcid': dcid
                    })
            except KeyError:
                writer.writerow({'name': cities[city_list[i]], 'dcid': ''})


if __name__ == '__main__':
    cities = set()
    for file in sorted(os.listdir('input')):
        code = file.removesuffix('.csv')
        with open('input/' + file) as f:
            reader = csv.DictReader(f)
            if '[Cities]' in reader.fieldnames:
                for row in reader:
                    cities.add(row['[Cities]'].replace('_', ' ').title() +
                               ', ' + row['GeoAreaName'])
    cities = sorted(cities)

    write_cities('preprocessed/cities2.csv', cities, sys.argv[1])
