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

Downloads data from UN Stats API to be used in further processing.

Produces:
* input/ directory containing csv files for each series
* preprocessed/attributes.csv: metadata about attributes
* preprocessed/dimensions.csv: metadata about dimensions
* output/series.mcf: MCF for each series
Note: Downloading all the data is very slow and prone to crashes.
This script ideally shouldn't need to be run again.
Usage: python3 preprocess.py
'''
import csv
import os
import requests

from util import *

API_PREFIX = 'https://unstats.un.org/SDGAPI/v1/sdg/Series/'
HEADERS = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'application/octet-stream'
}


def add_concepts(code, concept, concept_set):
    '''Adds concepts from given series code to concept_set.
    Args:
        code: Series code.
        concept: Type of concept ('Attributes' | 'Dimensions').
        concept_set: Current set of concepts.
    '''
    response = requests.get(f'{API_PREFIX}{code}/{concept}').json()
    for entry in response:
        for c in entry['codes']:
            concept_set.add(
                (entry['id'], c['code'], c['description'], c['sdmx']))


def write_concepts(file, concept_set):
    '''Writes concepts from concept_set to file.
    Args:
        path: File path to write to.
        concept_set: Current set of concepts.
    '''
    with open(file, 'w') as f:
        writer = csv.writer(f)
        for row in sorted(concept_set):
            writer.writerow(list(row))


if __name__ == '__main__':
    if not os.path.exists('input'):
        os.makedirs('input')
    if not os.path.exists('preprocessed'):
        os.makedirs('preprocessed')
    if not os.path.exists('output'):
        os.makedirs('output')

    series = requests.get(f'{API_PREFIX}List?allreleases=false').json()
    codes = {s['code']: s['description'] for s in series}

    attributes = set()
    dimensions = set()
    with open('output/series.mcf', 'w') as f_series:
        for code in sorted(codes):
            print(code)
            data = {'seriesCodes': code}
            text = requests.post(f'{API_PREFIX}DataCSV',
                                 data=data,
                                 headers=HEADERS).text.rstrip('\x00')
            with open(f'input/{code}.csv', 'w') as f_code:
                f_code.write(text)
            add_concepts(code, 'Attributes', attributes)
            add_concepts(code, 'Dimensions', dimensions)
            f_series.write(
                SERIES_TEMPLATE.format_map({
                    'dcid': 'SDG_' + code,
                    'description': format_description(codes[code])
                }))

    write_concepts('preprocessed/attributes.csv', attributes)
    write_concepts('preprocessed/dimensions.csv', dimensions)
