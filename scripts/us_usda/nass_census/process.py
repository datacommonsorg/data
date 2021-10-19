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

"""Import USDA Census of Agriculture."""

import csv
import io
from google.cloud import storage

CSV_COLUMNS = [
    'variableMeasured',
    'observationAbout',
    'value',
    'unit',
]

SKIPPED_VALUES = [
    '(D)',
    '(Z)',
]


def get_statvars(filename):
    d = {}
    f = open(filename)
    lines = f.readlines()
    for l in lines:
        l = l[:-1]  # trim newline character
        p = l.split('^')
        d[p[0]] = tuple(p[1:])
    f.close()
    return d


def write_csv(reader, out, d):
    writer = csv.DictWriter(out, fieldnames=CSV_COLUMNS, lineterminator='\n')
    writer.writeheader()
    for r in reader:
        key = r['SHORT_DESC']
        if r['DOMAINCAT_DESC']:
            key += '%%' + r['DOMAINCAT_DESC']
        if key not in d:
            continue
        if r['VALUE'] in SKIPPED_VALUES:
            continue
        value = d[key]
        if r['AGG_LEVEL_DESC'] == 'NATIONAL':
            observationAbout = 'dcid:country/USA'
        elif r['AGG_LEVEL_DESC'] == 'STATE':
            observationAbout = 'dcid:geoId/' + r['STATE_FIPS_CODE']
        elif r['AGG_LEVEL_DESC'] == 'COUNTY':
            observationAbout = 'dcid:geoId/' + r['STATE_FIPS_CODE'] + r[
                'COUNTY_CODE']
        row = {
            'variableMeasured': 'dcs:' + value[0],
            'observationAbout': observationAbout,
            'value': int(r['VALUE'].replace(',', '')),
        }
        if len(value) > 1:
            row['unit'] = 'dcs:' + value[1]
        writer.writerow(row)


if __name__ == '__main__':
    d = get_statvars('statvars')
    client = storage.Client()
    bucket = client.get_bucket('datcom-csv')
    blob = bucket.get_blob('usda/2017_cdqt_data.txt')
    s = blob.download_as_string().decode('utf-8')
    reader = csv.DictReader(io.StringIO(s), delimiter='\t')
    out = open('agriculture.csv', 'w', newline='')
    write_csv(reader, out, d)
