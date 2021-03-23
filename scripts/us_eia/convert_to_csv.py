# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Converts a single dataset into 2 csv's: one each for series and category data."""

import csv
import json
import sys

SERIES_KEYS = [
    'series_id',
    'name',
    'units',
    'f',
    'description',
    'start',
    'end',
    'lastHistoricalPeriod',
    'last_updated',
]

CATEGORY_KEYS = [
    'category_id',
    'parent_category_id',
    'name',
    'notes',
    'childseries'
]

all_series_keys = set()
all_category_keys = set()

def extract_series_to_csv(json_data):
    csv_data = []
    for k in SERIES_KEYS:
        csv_data.append(json_data.get(k, ''))
    csv_data.append(len(json_data.get('data', [])))
    all_series_keys.update(json_data.keys())
    return csv_data

def extract_category_to_csv(json_data):
    csv_data = []
    for k in CATEGORY_KEYS:
        csv_data.append(json_data.get(k, ''))
    csv_data.append(len(json_data.get('childseries', [])))
    all_category_keys.update(json_data.keys())
    return csv_data

def main(file_path):
    with open(file_path) as data_fp:

        with open(file_path + '.series.csv', 'w+') as series_fp:
            series_writer = csv.writer(series_fp, quoting=csv.QUOTE_MINIMAL)
            series_writer.writerow(SERIES_KEYS + ['# data'])

            with open(file_path + '.categories.csv', 'w+') as category_fp:
                category_writer = csv.writer(category_fp, quoting=csv.QUOTE_MINIMAL)
                category_writer.writerow(CATEGORY_KEYS + ['# children'])

                for line in data_fp:
                    data = json.loads(line)
                    series_id = data.get('series_id', None)
                    if series_id:
                        series_writer.writerow(extract_series_to_csv(data))
                    category_id = data.get('category_id', None)
                    if category_id:
                        category_writer.writerow(extract_category_to_csv(data))

    print(f'Other series keys: {all_series_keys.difference(SERIES_KEYS)}')
    print(f'Other category keys: {all_category_keys.difference(CATEGORY_KEYS)}')

if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) == 0:
        raise SystemExit(f'Usage: {sys.argv[0]} <file_path>')
    main(args[0])
