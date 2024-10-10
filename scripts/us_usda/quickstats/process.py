# Copyright 2021 Google LLC
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
"""Import USDA Agriculture Survey data.

To run this script, specify a USDA api key as follows:

python3 process.py --usda_api_key=<KEY>

You can request an API key here: https://quickstats.nass.usda.gov/api/

If the key is not specified as above, it falls back to using a key specified
in a GCS config file. However, that file is available to DC team members only.
"""

import csv
from datetime import datetime
from itertools import repeat
import json
import multiprocessing
from multiprocessing import get_context
import os
import sys

from absl import app
from absl import flags
from google.cloud import storage
from ratelimit import limits, sleep_and_retry
import requests

API_BASE = 'https://quickstats.nass.usda.gov/api'

CSV_COLUMNS = [
    'variableMeasured',
    'observationDate',
    'observationAbout',
    'value',
    'unit',
]

SKIPPED_VALUES = {'(D)', '(Z)'}

SKIPPED_COUNTY_CODES = set([
    '998',  # "OTHER" county code
])

_GCS_PROJECT_ID = 'datcom-204919'
_GCS_BUCKET = 'datcom-csv'
_GCS_FILE_PATH = 'usda/agriculture_survey/config.json'

_USDA_API_KEY = 'usda_api_key'

_FLAGS = flags.FLAGS

flags.DEFINE_string(_USDA_API_KEY, None, 'USDA quickstats API key.')
flags.DEFINE_integer(
    'start_year',
    os.getenv('start_year',
              datetime.now().year),
    'Year from which data is processed.',
)
flags.DEFINE_integer(
    'num_counties',
    os.getenv('num_counties', 100),
    'number of counties for which data is processed.',
)
flags.DEFINE_string('output_dir', 'output',
                    'Output firectory for generated files.')


def process_survey_data(year, svs, out_dir, usda_api_key):
    start = datetime.now()
    print('Start', year, '=', start)

    os.makedirs(get_parts_dir(out_dir, year), exist_ok=True)
    os.makedirs(get_response_dir(out_dir, year), exist_ok=True)

    print('Processing survey data for year', year)

    print('Getting county names')
    county_names = get_param_values('county_name', usda_api_key)
    county_names = county_names[:_FLAGS.num_counties]
    print('# counties =', len(county_names))

    pool_size = max(2, multiprocessing.cpu_count() - 1)

    with get_context("spawn").Pool(pool_size) as pool:
        pool.starmap(
            fetch_and_write,
            zip(county_names, repeat(year), repeat(svs), repeat(out_dir),
                repeat(usda_api_key)),
        )

    write_aggregate_csv(year, out_dir)

    end = datetime.now()
    print('End', year, '=', end)
    print('Duration', year, '=', str(end - start))


def get_parts_dir(out_dir, year):
    return f'{out_dir}/parts/{year}'


def get_response_dir(out_dir, year):
    return f'{out_dir}/response/{year}'


def get_response_file_path(out_dir, year, county):
    return f'{get_response_dir(out_dir, year)}/{county}.json'


def get_year_csv_file_path(out_dir, year):
    return f'{out_dir}/ag-{year}.csv'


def write_aggregate_csv(year, out_dir):
    parts_dir = get_parts_dir(out_dir, year)
    part_files = os.listdir(parts_dir)
    out_file = get_year_csv_file_path(out_dir, year)

    print('Writing aggregate CSV', out_file)

    with open(out_file, 'w', newline='') as out:
        csv_writer = csv.DictWriter(out,
                                    fieldnames=CSV_COLUMNS,
                                    lineterminator='\n')
        csv_writer.writeheader()
        for part_file in part_files:
            if part_file.endswith('.csv'):
                with open(f'{parts_dir}/{part_file}', 'r') as part:
                    csv_writer.writerows(csv.DictReader(part))


def write_consolidated_csv(years, out_dir):
    out_file = f'{out_dir}/consolidated.csv'

    print('Writing consolidated CSV', out_file)

    with open(out_file, 'w', newline='') as out:
        csv_writer = csv.DictWriter(out,
                                    fieldnames=CSV_COLUMNS,
                                    lineterminator='\n')
        csv_writer.writeheader()
        for year in years:
            with open(get_year_csv_file_path(out_dir, year), 'r') as part:
                csv_writer.writerows(csv.DictReader(part))


def fetch_and_write(county_name, year, svs, out_dir, usda_api_key):
    out_file = (
        f"{get_parts_dir(out_dir, year)}/{county_name.replace('[^a-zA-Z0-9]', '')}.csv"
    )
    api_data = get_survey_county_data(year, county_name, out_dir, usda_api_key)
    county_csv_rows = to_csv_rows(api_data, svs)
    print(
        'Writing',
        len(county_csv_rows),
        'rows for county',
        county_name,
        'to file',
        out_file,
    )
    with open(out_file, 'w', newline='') as out:
        write_csv(out, county_csv_rows)


def get_survey_county_data(year, county, out_dir, usda_api_key):
    print('Getting', year, 'survey data for county', county)

    response_file = get_response_file_path(out_dir, year, county)
    if os.path.exists(response_file):
        print('Reading response from file', response_file)
        with open(response_file, 'r') as f:
            response = json.load(f)
    else:
        params = {
            'key': usda_api_key,
            'source_desc': 'SURVEY',
            'year': year,
            'county_name': county,
        }
        response = get_data(params)
        with open(response_file, 'w') as f:
            print('Writing response to file', response_file)
            json.dump(response, f, indent=2)

    if 'data' not in response:
        eprint('No api records found for county', county)
        return {'data': []}

    print('# api records for', county, '=', len(response['data']))
    return response


@sleep_and_retry
@limits(calls=10, period=60)
def get_data(params):
    return requests.get(f'{API_BASE}/api_GET', params=params).json()


def get_param_values(param, usda_api_key):
    params = {'key': usda_api_key, 'param': param}
    response = requests.get(f'{API_BASE}/get_param_values',
                            params=params).json()
    return [] if param not in response else response[param]


"""Converts a quickstats data row to a DC CSV row.

data = quickstats data row
svs = {name: {name: ..., sv: ..., unit: ...}}

returns = {variableMeasured: ..., observationAbout: ..., value: ..., unit: ...}
"""


def to_csv_row(data_row, svs):
    name = data_row['short_desc']
    if (data_row['domaincat_desc'] and
            data_row['domaincat_desc'] != 'NOT SPECIFIED'):
        name = f"{name}%%{data_row['domaincat_desc']}"

    if name not in svs:
        eprint('SKIPPED, No SV mapped for', name)
        return None

    county_code = data_row['county_code']
    if county_code in SKIPPED_COUNTY_CODES:
        eprint('SKIPPED, Unsupported county code', county_code)
        return None

    value = ((data_row['value'] if 'value' in data_row else
              data_row['Value']).strip().replace(',', ''))
    if value in SKIPPED_VALUES:
        eprint('SKIPPED, Invalid value', f"'{value}'", 'for', name)
        return None
    value = int(value)

    observation_about = (
        f"dcid:geoId/{data_row['state_fips_code']}{county_code}"
        if data_row['state_fips_code'] else 'dcid:country/USA')

    sv = svs[name]

    return {
        'variableMeasured': sv['sv'],
        'observationDate': data_row['year'],
        'observationAbout': observation_about,
        'value': value,
        'unit': sv['unit'],
    }


def to_csv_rows(api_data, svs):
    csv_rows = []

    for data_row in api_data['data']:
        csv_row = to_csv_row(data_row, svs)
        if csv_row:
            csv_rows.append(csv_row)

    return csv_rows


def load_svs():
    svs = {}
    with open('sv.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            svs[row['name']] = row
    return svs


def write_csv(out, rows):
    writer = csv.DictWriter(out, fieldnames=CSV_COLUMNS, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def get_all_counties(usda_api_key):
    svs = load_svs()
    process_survey_data(2023, svs, 'output', usda_api_key)


def get_multiple_years(usda_api_key):
    start = datetime.now()
    print('Start', start)

    out_dir = _FLAGS.output_dir
    svs = load_svs()
    years = range(_FLAGS.start_year, datetime.now().year + 1)
    for year in years:
        process_survey_data(year, svs, out_dir, usda_api_key)

    write_consolidated_csv(years, out_dir)

    end = datetime.now()
    print('End', end)
    print('Duration', str(end - start))


def get_cloud_config():
    print('Getting cloud config.')
    storage_client = storage.Client(_GCS_PROJECT_ID)
    bucket = storage_client.bucket(_GCS_BUCKET)
    blob = bucket.blob(_GCS_FILE_PATH)
    return json.loads(blob.download_as_string(client=None))


def load_usda_api_key():
    if get_usda_api_key() is None:
        _FLAGS.set_default(_USDA_API_KEY, get_cloud_config()[_USDA_API_KEY])


def get_usda_api_key():
    _FLAGS(sys.argv)
    return _FLAGS.usda_api_key


def main(_):
    load_usda_api_key()
    usda_api_key = get_usda_api_key()
    print('USDA API key', usda_api_key)
    get_multiple_years(usda_api_key)


if __name__ == '__main__':
    app.run(main)
