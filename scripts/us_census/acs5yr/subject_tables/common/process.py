"""Process the data from Census ACS5Year Table S2201."""

import csv
import io
import json
import os
import requests
import zipfile
from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_string('output', None, 'Path to folder for output files')
flags.DEFINE_string('download_id', None, 'Download id for input data')
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

_IGNORED_VALUES = set(['**', '-', '***', '*****', 'N', '(X)', 'null'])


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
    with open(output, 'a') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        observation_date = filename.split('ACSST5Y')[1][:4]
        valid_columns = {}
        for row in reader:
            if row['GEO_ID'] == 'id':

                # Map feature names to stat vars
                for c in row:
                    sv = convert_column_to_stat_var(row[c], features)
                    if sv in stat_var_set:
                        valid_columns[c] = sv
                continue

            new_row = {
                'observationDate': observation_date,
                # TODO: Expand to support other prefixes?
                'observationAbout': 'dcid:geoId/' + row['GEO_ID'].split('US')[1]
            }
            for c in row:

                # We currently only support the stat vars in the list
                if c not in valid_columns:
                    continue
                sv = valid_columns[c]

                # Exclude missing values
                if row[c] in _IGNORED_VALUES:
                    continue

                # Exclude percentages
                if '.' in row[c]:
                    continue

                # Exclude suffix from median values
                if (row[c][-1] == '-' or row[c][-1] == '+'):
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
    f = open(FLAGS.features)
    features = json.load(f)
    f.close()
    f = open(FLAGS.stat_vars)
    stat_vars = f.read().splitlines()
    f.close()
    output_csv = os.path.join(FLAGS.output, 'output.csv')
    create_csv(output_csv, stat_vars)
    response = requests.get(
        f'https://data.census.gov/api/access/table/download?download_id={FLAGS.download_id}'
    )
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        for filename in zf.namelist():
            if 'data_with_overlays' in filename:
                print(filename)
                with zf.open(filename, 'r') as infile:
                    reader = csv.DictReader(io.TextIOWrapper(infile, 'utf-8'))
                    write_csv(filename, reader, output_csv, features, stat_vars)
    create_tmcf(os.path.join(FLAGS.output, 'output.tmcf'), features, stat_vars)


if __name__ == '__main__':
    flags.mark_flags_as_required(
        ['output', 'download_id', 'features', 'stat_vars'])
    app.run(main)
