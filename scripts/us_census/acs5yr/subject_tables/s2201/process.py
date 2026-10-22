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
"""Process the data from Census ACS5Year Table S2201."""

import csv
import io
import json
import os
import requests
import sys
import zipfile
from absl import app
from absl import flags
from absl import logging

_CODEDIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.join(_CODEDIR, '..', 'common'))
from resolve_geo_id import convert_to_place_dcid

FLAGS = flags.FLAGS
flags.DEFINE_string('output', None, 'Path to folder for output files')
flags.DEFINE_string('download_id', None, 'Download id for input data')
flags.DEFINE_string(
    'input_zip', None,
    'Path to local zip file containing downloaded Census data (e.g. S2201.zip)')
flags.DEFINE_string('features', None, 'JSON of feature maps')
flags.DEFINE_string('stat_vars', None, 'Path to list of supported stat_vars')

_TMCF_TEMPLATE = """
Node: E:Subject_Table->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{stat_var}
measurementMethod: dcs:CensusACS5yrSurvey
observationDate: C:Subject_Table->observationDate
observationAbout: C:Subject_Table->observationAbout
value: C:Subject_Table->{stat_var}{unit}
"""

_UNIT_TEMPLATE = """
unit: dcs:{unit}"""

_IGNORED_VALUES = set([
    '**', '-', '***', '*****', 'N', '(X)', 'null', '-222222222', '-333333333',
    '-555555555', '-666666666', '-888888888', '-999999999'
])


def convert_column_to_stat_var(column, features):
    """Converts input CSV column name to Statistical Variable DCID."""
    s = column.split('!!')
    sv = []
    base = False
    for p in s:

        # Set base SV for special cases
        if not base and 'base' in features:
            if p in features['base']:
                sv = [features['base'][p]] + sv
                base = True

        # Skip implied properties
        if 'implied_properties' in features and p in features[
                'implied_properties']:
            dependent = False
            for feature in features['implied_properties'][p]:
                if feature in s:
                    dependent = True
                    break
            if dependent:
                continue

        if 'properties' in features and p in features['properties']:

            # Add inferred properties
            if 'inferred_properties' in features and p in features[
                    'inferred_properties'] and features['inferred_properties'][
                        p] not in s:
                sv.append(
                    features['properties'][features['inferred_properties'][p]])

            # Add current property
            sv.append(features['properties'][p])

    # Set default base SV
    if not base and 'base' in features and '_DEFAULT' in features['base']:
        sv = [features['base']['_DEFAULT']] + sv

    # Prefix MOE SVs
    if 'Margin of Error' in s:
        sv = ['MarginOfError'] + sv
    return '_'.join(sv)


def create_csv(output, stat_vars):
    """Creates output CSV file."""
    fieldnames = ['observationDate', 'observationAbout'] + stat_vars
    with open(output, 'w') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()


def write_csv(filename, reader, output, features, stat_vars):
    """Reads input_file and writes cleaned CSV to output."""
    if 'ACSST5Y' not in filename:
        return
    fieldnames = ['observationDate', 'observationAbout'] + stat_vars
    stat_var_set = set(stat_vars)
    if reader.fieldnames:
        reader.fieldnames = [
            name.strip('\ufeff" ') for name in reader.fieldnames
        ]
    with open(output, 'a') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        observation_date = filename.split('ACSST5Y')[1][:4]
        valid_columns = {}
        for row in reader:
            geo_id = row.get('GEO_ID')
            if not geo_id:
                continue

            if geo_id in ('Geography', 'id'):

                # Map feature names to stat vars
                for c in row:
                    if 'Percent' in row[c] or 'PERCENT' in row[c]:
                        continue
                    # In 2010-2014 S2201 tables, columns _002-_015 and _018-_021
                    # reported percentages without "Percent" in the header; only
                    # _001, _016, and _017 reported counts/median income.
                    if int(observation_date) < 2015 and not c.endswith(
                        ('_001E', '_001M', '_016E', '_016M', '_017E', '_017M')):
                        continue

                    sv = convert_column_to_stat_var(row[c], features)
                    if sv in stat_var_set:
                        valid_columns[c] = sv
                continue
            else:
                for c in row:
                    if row[c] and ',' in row[c]:
                        row[c] = str(row[c]).replace(',', '')

            if 'US' not in geo_id:
                continue
            place_dcid = convert_to_place_dcid(geo_id)
            if not place_dcid:
                continue

            new_row = {
                'observationDate': observation_date,
                'observationAbout': f'dcid:{place_dcid}'
            }
            for c in row:

                # We currently only support the stat vars in the list
                if c not in valid_columns:
                    continue
                sv = valid_columns[c]

                # Exclude missing values
                if row[c] in _IGNORED_VALUES:
                    continue

                # Strip trailing '.0' added by pandas float64 coercion on integer columns
                if row[c].endswith('.0'):
                    row[c] = row[c][:-2]

                # Exclude percentages
                if '.' in row[c]:
                    continue

                # Exclude suffix from median values
                if row[c] and (row[c][-1] == '-' or row[c][-1] == '+'):
                    new_row[sv] = row[c][:-1]
                else:
                    new_row[sv] = row[c]
            writer.writerow(new_row)


def create_tmcf(output, features, stat_vars):
    """Writes tMCF to output."""
    with open(output, 'w') as f_out:
        for i in range(len(stat_vars)):
            unit = ''
            if stat_vars[i] in features['units']:
                unit = _UNIT_TEMPLATE.format(
                    unit=features['units'][stat_vars[i]])
            f_out.write(
                _TMCF_TEMPLATE.format(index=i, stat_var=stat_vars[i],
                                      unit=unit))


def main(argv):
    if not FLAGS.input_zip and not FLAGS.download_id:
        default_zip = os.path.join(_CODEDIR, 'input_data', 'S2201.zip')
        if os.path.exists(default_zip):
            FLAGS.input_zip = default_zip
        else:
            raise ValueError(
                'Must provide either --input_zip or --download_id.')

    os.makedirs(FLAGS.output, exist_ok=True)

    with open(FLAGS.features) as f:
        features = json.load(f)
    with open(FLAGS.stat_vars) as f:
        stat_vars = f.read().splitlines()

    output_csv = os.path.join(FLAGS.output, 'output.csv')
    create_csv(output_csv, stat_vars)

    if FLAGS.input_zip:
        logging.info('Reading local archive: %s', FLAGS.input_zip)
        zf_context = zipfile.ZipFile(FLAGS.input_zip, 'r')
    else:
        logging.info('Downloading with download_id: %s', FLAGS.download_id)
        response = requests.get(
            f'https://data.census.gov/api/access/table/download?download_id={FLAGS.download_id}',
            timeout=60)
        response.raise_for_status()
        zf_context = zipfile.ZipFile(io.BytesIO(response.content))

    with zf_context as zf:
        # Sort files chronologically / deterministically
        for filename in sorted(zf.namelist()):
            base = os.path.basename(filename).lower()
            # Support both -Data.csv and data_with_overlays...csv
            if base.endswith('.csv') and 'acsst5y' in base and (
                    '-data.csv' in base or 'data_with_overlays' in base):
                logging.info('Processing file: %s', filename)
                with zf.open(filename, 'r') as infile:
                    reader = csv.DictReader(
                        io.TextIOWrapper(infile, 'utf-8-sig'))
                    write_csv(filename, reader, output_csv, features, stat_vars)

    create_tmcf(os.path.join(FLAGS.output, 'output.tmcf'), features, stat_vars)
    logging.info('Processing complete! Outputs written to %s', FLAGS.output)


if __name__ == '__main__':
    flags.mark_flags_as_required(['output', 'features', 'stat_vars'])
    app.run(main)
