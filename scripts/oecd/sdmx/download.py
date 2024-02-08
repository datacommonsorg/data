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
'''
Bulk downloads OECD datasets.

Note: this currently is a "best-effort" single pass and will just skip any
datasets with errors or failures. 

Produces: 
* identifiers.csv: Series codes and names.
* input/<CODE>.json: Folder of all fetched input datasets.

Usage: OPENSSL_CONF=openssl.cnf python3 download.py
'''
import csv
import json
import requests
import os
from xml.etree import ElementTree

PREFIX = '{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/'


def get_series():
    '''Gets all series.

    Returns:
        Map of series code -> name.
    '''
    series = {}
    response = requests.get(
        'https://stats.oecd.org/RestSDMX/sdmx.ashx/GetKeyFamily/all')
    root = ElementTree.fromstring(response.content)
    for child in root:
        for key in child:
            if key.tag == PREFIX + 'structure}KeyFamily' and 'id' in key.attrib:
                for attr in key:
                    if '{http://www.w3.org/XML/1998/namespace}lang' in attr.attrib and attr.attrib[
                            '{http://www.w3.org/XML/1998/namespace}lang'] == 'en':
                        series[key.attrib['id']] = attr.text
    return series


if __name__ == '__main__':

    # Precompute series list to avoid refetching on failure.
    with open('identifiers.csv', 'w') as f:
        series = get_series()
        writer = csv.writer(f)
        for s in sorted(series):
            writer.writerow([s, series[s]])

    if not os.path.exists('input'):
        os.makedirs('input')

    with open('identifiers.csv') as f_in:
        reader = csv.reader(f_in)
        for row in reader:
            identifier = row[0]
            print(identifier)
            try:
                result = requests.get(
                    f'http://stats.oecd.org/sdmx-json/data/{identifier}/all/all'
                )
                with open(f'input/{identifier}.json', 'w') as f_out:
                    try:
                        f_out.write(json.dumps(result.json()))
                    except:
                        print('Error parsing:', identifier)
            except:
                print('Error fetching data for:', identifier)
