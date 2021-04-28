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
"""Converts a single dataset into 2 jsonl's: one each for series and category data.

These jsonl's can then be imported to bq using the associated schema bq_schema_*.json

To import to bigquery:
- run this script: `python3 generate_jsonl_for_bq.py`
- copy tmp_bq_import/ to gcs: `gsutil -m cp -r bq_import gs://us_eia/`
- load data into bigquery:
    ```
    bq load \
        --source_format=NEWLINE_DELIMITED_JSON \
        google.com:datcom-store-dev.import_us_eia.all_series \
        gs://us_eia/bq_import/*.series.jsonl \
        bq_schema_series.json
    bq load \
        --source_format=NEWLINE_DELIMITED_JSON \
        google.com:datcom-store-dev.import_us_eia.all_categories \
        gs://us_eia/bq_import/*.categories.jsonl \
        bq_schema_categories.json
    ```
"""

import os
import json
import sys

IN_DATA_PATH = 'tmp_raw_data'
OUT_DATA_PATH = 'tmp_bq_import'
DATASETS = ['AEO.2014', 'AEO.2015', 'AEO.2016', 'AEO.2017', 'AEO.2018', 'AEO.2019', 'AEO.2020', 'AEO.2021', 'COAL', 'EBA', 'ELEC', 'EMISS', 'IEO.2017', 'IEO.2019', 'INTL', 'NG', 'NUC_STATUS', 'PET', 'PET_IMPORTS', 'SEDS', 'STEO', 'TOTAL']

def extract_series_to_jsonl(line, dataset):
    json_data = json.loads(line)
    # convert data to a flat list
    nested_data = json_data['data']
    list_data = []
    for [k,v] in nested_data:
        d = { 'date': k }
        try:
            d['value'] = float(v)
        except:
            d['value_note'] = v
        list_data.append(d)
    json_data['data'] = list_data
    json_data['len_data'] = len(list_data)
    json_data['dataset'] = dataset
    return json_data

def extract_category_to_jsonl(line, dataset):
    json_data = json.loads(line)
    json_data['len_childseries'] = len(json_data['childseries'])
    json_data['dataset'] = dataset
    return json_data

def process_dataset(dataset, in_file_path, out_file_path):
    with open(in_file_path) as data_fp:
        with open(out_file_path + '.series.jsonl', 'w+') as series_fp:
            with open(out_file_path + '.categories.jsonl', 'w+') as category_fp:
                for line in data_fp:
                    data = json.loads(line)
                    series_id = data.get('series_id', None)
                    if series_id:
                        jsonl = extract_series_to_jsonl(line, dataset)
                        series_fp.write(json.dumps(jsonl))
                        series_fp.write('\n')
                    category_id = data.get('category_id', None)
                    if category_id:
                        jsonl = extract_category_to_jsonl(line, dataset)
                        category_fp.write(json.dumps(jsonl))
                        category_fp.write('\n')

def process_single(subdir, file):
    dataset = os.path.split(subdir)[-1]
    in_file_path = os.path.join(subdir, file)
    out_file_path = f'{OUT_DATA_PATH}/{dataset}'
    process_dataset(dataset, in_file_path, out_file_path)

def process_all():
    for subdir, dirs, files in os.walk(IN_DATA_PATH):
        dirs.sort()
        for file in sorted(files):
            if not file.endswith('.txt'):
                continue
            print(f'Processing {subdir}/{file}')
            process_single(subdir, file)

if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) == 0:
        print('Processing all files')
        process_all()
    else:
        print(f'Processing {args[0]}/{args[1]}')
        process_single(args[0], args[1])
