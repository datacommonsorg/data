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
import os
import sys
from google.cloud import storage

from absl import app
from absl import flags
from absl import logging

_FLAGS = flags.FLAGS

flags.DEFINE_string(
    'input', 'gs://datcom-csv/usda/2017_cdqt_data.txt',
    'Input TXT file from https://www.nass.usda.gov/AgCensus/index.php')
flags.DEFINE_string('output', 'agriculture.csv', 'Output CSV file')

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.join(_SCRIPT_DIR.split('/scripts')[0], 'util'))

import file_util

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


def main(_):
    d = get_statvars('statvars')
    logging.info(
        f'Processing input: {_FLAGS.input} to generate {_FLAGS.output}')
    with file_util.FileIO(_FLAGS.input, 'r') as input_f:
        reader = csv.DictReader(input_f, delimiter='\t')
        with file_util.FileIO(_FLAGS.output, 'w', newline='') as out_f:
            write_csv(reader, out_f, d)


if __name__ == '__main__':
    app.run(main)
