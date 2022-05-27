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
"""
Utility to generate a speculative version of the JSON config required to import data.
"""

import json
import os
from absl import app
from absl import flags

from .common_util import columns_from_zip_file, token_in_list_ignore_case, get_tokens_list_from_column_list
from .acs_spec_validator import find_columns_with_no_properties, find_missing_tokens
from .datacommons_api_wrappers.datacommons_wrappers import fetch_dcid_properties_enums

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
_FLAGS = flags.FLAGS

flags.DEFINE_string('generator_output', os.path.join(_SCRIPT_PATH, 'output'),
                    'Path to store the output files')
flags.DEFINE_boolean(
    'create_union_spec', False,
    'Produce union_spec.json which had combination of all previous specs')
flags.DEFINE_boolean(
    'guess_new_spec', False,
    'Produces a guessed spec from zip file and specs from the spec_dir folder')
flags.DEFINE_boolean('get_combined_property_list', False,
                     'Get list of properties available in previous specs')

flags.DEFINE_boolean('check_metadata', False,
                     'Parses the metadata files in zip rather than data files')

flags.DEFINE_list('expected_populations', ['Person'],
                  'List of expected population types')
flags.DEFINE_list('expected_properties', [], 'list of expected properties')


def get_spec_list() -> list:
    # data/scripts/us_census/acs5yr/subject_tables
    spec_dir = os.path.join(_SCRIPT_PATH, '..')

    spec_list = []
    # read all spec files in subject table folders
    for directory in sorted(os.listdir(spec_dir)):
        directory_path = os.path.join(spec_dir, directory)
        if os.path.isdir(directory_path):
            table_dir = os.path.join(spec_dir, directory)
            for filename in os.listdir(table_dir):
                if filename.endswith('_spec.json'):
                    spec_file = os.path.join(table_dir, filename)
                    with open(spec_file, 'r') as fp:
                        spec_list.append(json.load(fp))
    return spec_list


# create megaspec
def create_combined_spec(all_specs: list,
                         output_path: str = '../output/') -> dict:
    """Creates a union of all specs provided in the list.
    NOTE: XXXXX is placed at places where some manual resolution is required.
    
    Args:
      all_specs: List of specs whose union is to be computed.

    Returns:
      Dict object of the union spec.
  """
    output_path = os.path.expanduser(output_path)
    if not os.path.exists(output_path):
        os.makedirs(output_path, exist_ok=True)

    out_spec = {}
    out_spec['populationType'] = {}
    out_spec['measurement'] = {}
    out_spec['enumSpecializations'] = {}
    out_spec['pvs'] = {}
    out_spec['inferredSpec'] = {}
    out_spec['universePVs'] = []
    out_spec['ignoreColumns'] = []
    out_spec['ignoreTokens'] = []

    for cur_spec in all_specs:
        out_spec['populationType']['_DEFAULT'] = 'Person XXXXX'
        if 'populationType' in cur_spec:
            for population_token in cur_spec['populationType']:
                if not population_token.startswith('_'):
                    if population_token not in out_spec['populationType']:
                        out_spec['populationType'][population_token] = cur_spec[
                            'populationType'][population_token]
                    elif out_spec['populationType'][
                            population_token] != cur_spec['populationType'][
                                population_token]:
                        new_token = population_token + ' XXXXX'
                        temp_flag = True
                        i = 2
                        while new_token in out_spec['populationType']:
                            if out_spec['populationType'][
                                    new_token] == cur_spec['populationType'][
                                        population_token]:
                                temp_flag = False
                            new_token += str(i)
                            i += 1
                        if temp_flag:
                            out_spec['populationType'][new_token] = cur_spec[
                                'populationType'][population_token]

        out_spec['measurement']['_DEFAULT'] = {
            'measuredProperty': 'count XXXXX',
            'statType': 'measuredValue'
        }
        if 'measurement' in cur_spec:
            for measurement_token in cur_spec['measurement']:
                if not measurement_token.startswith('_'):
                    if measurement_token not in out_spec['measurement']:
                        out_spec['measurement'][measurement_token] = {}
                        out_spec['measurement'][measurement_token].update(
                            cur_spec['measurement'][measurement_token])
                    elif out_spec['measurement'][measurement_token] != cur_spec[
                            'measurement'][measurement_token]:
                        new_token = measurement_token + ' XXXXX'
                        temp_flag = True
                        i = 2
                        while new_token in out_spec['measurement']:
                            if out_spec['measurement'][new_token] == cur_spec[
                                    'measurement'][measurement_token]:
                                temp_flag = False
                            new_token += str(i)
                            i += 1
                        if temp_flag:
                            out_spec['measurement'][new_token] = cur_spec[
                                'measurement'][measurement_token]

        if 'enumSpecializations' in cur_spec:
            for enum_token in cur_spec['enumSpecializations']:
                if not enum_token.startswith('_'):
                    if enum_token not in out_spec['enumSpecializations']:
                        out_spec['enumSpecializations'][enum_token] = cur_spec[
                            'enumSpecializations'][enum_token]
                    elif out_spec['enumSpecializations'][enum_token] != cur_spec[
                            'enumSpecializations'][enum_token]:
                        print('Error:', enum_token,
                              'already assigned to enumSpecialization',
                              out_spec['enumSpecializations'][enum_token],
                              'new value:',
                              cur_spec['enumSpecializations'][enum_token])

        for property_name in cur_spec['pvs']:
            if property_name not in out_spec['pvs']:
                out_spec['pvs'][property_name] = {}
            for property_token in cur_spec['pvs'][property_name]:
                if property_token not in out_spec['pvs'][property_name]:
                    out_spec['pvs'][property_name][property_token] = cur_spec[
                        'pvs'][property_name][property_token]
                elif out_spec['pvs'][property_name][property_token] != cur_spec[
                        'pvs'][property_name][property_token]:
                    new_token = property_token + ' XXXXX'
                    temp_flag = True
                    i = 2
                    while new_token in out_spec['pvs'][property_name]:
                        if out_spec['pvs'][property_name][
                                new_token] == cur_spec['pvs'][property_name][
                                    property_token]:
                            temp_flag = False
                        new_token += str(i)
                        i += 1
                    if temp_flag:
                        out_spec['pvs'][property_name][new_token] = cur_spec[
                            'pvs'][property_name][property_token]

        if 'inferredSpec' in cur_spec:
            for property_name in cur_spec['inferredSpec']:
                if property_name not in out_spec['inferredSpec']:
                    out_spec['inferredSpec'][property_name] = {}
                    out_spec['inferredSpec'][property_name].update(
                        cur_spec['inferredSpec'][property_name])
                else:
                    cur_spec['inferredSpec'][property_name] = {}
                    for dependent_prop in cur_spec['inferredSpec'][
                            property_name]:
                        if dependent_prop not in out_spec['inferredSpec'][
                                property_name]:
                            out_spec['inferredSpec'][property_name][
                                dependent_prop] = cur_spec['inferredSpec'][
                                    property_name][dependent_prop]
                        elif out_spec['inferredSpec'][property_name][
                                dependent_prop] != cur_spec['inferredSpec'][
                                    property_name][dependent_prop]:
                            new_token = dependent_prop + ' XXXXX'
                            temp_flag = True
                            i = 2
                            while new_token in out_spec['inferredSpec'][
                                    property_name]:
                                if out_spec['inferredSpec'][property_name][
                                        new_token] == cur_spec['inferredSpec'][
                                            property_name][dependent_prop]:
                                    temp_flag = False
                                new_token += str(i)
                                i += 1
                            if temp_flag:
                                out_spec['inferredSpec'][property_name][
                                    new_token] = cur_spec['inferredSpec'][
                                        property_name][dependent_prop]

        # add universePVs
        if 'universePVs' in cur_spec:
            for cur_universe in cur_spec['universePVs']:
                if cur_universe not in out_spec['universePVs']:
                    out_spec['universePVs'].append(cur_universe)

        if 'ignoreColumns' in cur_spec:
            for column_name in cur_spec['ignoreColumns']:
                if column_name not in out_spec['ignoreColumns']:
                    out_spec['ignoreColumns'].append(column_name)

        if 'ignoreTokens' in cur_spec:
            for cur_token in cur_spec['ignoreTokens']:
                if cur_token not in out_spec['ignoreTokens']:
                    out_spec['ignoreTokens'].append(cur_token)

    union_spec_path = os.path.join(output_path, 'union_spec.json')
    with open(union_spec_path, 'w') as fp:
        json.dump(out_spec, fp, indent=2)

    return out_spec


def columns_from_zip_list(zip_path_list: list,
                          check_metadata: bool = False) -> list:
    """Compiles a list of all unique column names that are present in a given zip file.

    Args:
      zip_path_list: List of zip files to be scanned.
      check_metadata: Boolean value to scan 'metadata' or 'data_overlay' files in the zip.

    Retuens:
      List of strings where each string is a unique column name present in the zip files.
  """
    all_columns = []
    for zip_path in zip_path_list:
        zip_path = os.path.expanduser(zip_path)
        all_columns.extend(
            columns_from_zip_file(zip_path, check_metadata=check_metadata))
    all_columns = list(set(all_columns))
    return all_columns


# go through megaspec creating output and discarded spec
def create_new_spec(all_columns: list,
                    union_spec: dict,
                    expected_populations: list = ('Person',),
                    expected_pvs: list = (),
                    output_path: str = '../output/',
                    delimiter: str = '!!') -> dict:
    """Creates a speculative JSON spec from expected populations, properties and union spec.
    NOTE: XXXXX is placed at places where it some manual resolution is required.
    
    Args:
      all_columns: List of strings where each string is a unique column name present in the zip files.
      union_spec: Spec version of union of previous specs.
      expected_populations: List of populations expected to be in the output spec.
      expected_pvs: List of properties expected to be in the output spec.
      output_path: Path to store the output spec and intermediate files.
      delimiter: delimiter seperating tokens within single column name string.

    Returns:
      Dict object of the union spec.
  """

    output_path = os.path.expanduser(output_path)
    if not os.path.exists(output_path):
        os.makedirs(output_path, exist_ok=True)

    all_tokens = get_tokens_list_from_column_list(all_columns, delimiter)

    out_spec = {}
    # assign expected_population[0] to default if present
    out_spec['populationType'] = {}
    out_spec['measurement'] = {}
    out_spec['enumSpecializations'] = {}
    out_spec['pvs'] = {}
    out_spec['inferredSpec'] = {}
    out_spec['universePVs'] = []
    out_spec['denominators'] = {}
    out_spec['ignoreColumns XXXXX'] = []
    out_spec['ignoreTokens XXXXX'] = []

    discarded_spec = {}
    discarded_spec['populationType'] = {}
    discarded_spec['measurement'] = {}
    discarded_spec['enumSpecializations'] = {}
    discarded_spec['pvs'] = {}
    discarded_spec['inferredSpec'] = {}
    discarded_spec['universePVs'] = []
    discarded_spec['denominators'] = {}
    discarded_spec['ignoreColumns'] = []
    discarded_spec['ignoreTokens'] = []

    for population_token in union_spec['populationType']:
        if population_token.startswith('_'):
            out_spec['populationType'][population_token] = union_spec[
                'populationType'][population_token]
        elif token_in_list_ignore_case(population_token, all_tokens):
            out_spec['populationType'][population_token] = union_spec[
                'populationType'][population_token]
        elif 'XXXXX' in population_token:
            if token_in_list_ignore_case(
                    population_token[:population_token.find('XXXXX') - 1],
                    all_tokens):
                out_spec['populationType'][population_token] = union_spec[
                    'populationType'][population_token]
        else:
            discarded_spec['populationType'][population_token] = union_spec[
                'populationType'][population_token]

    out_spec['populationType'] = {'_DEFAULT': expected_populations[0]}

    for i, new_population in enumerate(expected_populations):
        population_not_found = True
        for population_token in out_spec['populationType']:
            if out_spec['populationType'][population_token] == new_population:
                population_not_found = False
        if population_not_found:
            out_spec['populationType']['XXXXX' + str(i)] = new_population

    for measurement_token in union_spec['measurement']:
        if measurement_token.startswith('_'):
            out_spec['measurement'][measurement_token] = union_spec[
                'measurement'][measurement_token]
        elif token_in_list_ignore_case(measurement_token, all_tokens):
            out_spec['measurement'][measurement_token] = union_spec[
                'measurement'][measurement_token]
        elif measurement_token in all_columns:
            out_spec['measurement'][measurement_token] = union_spec[
                'measurement'][measurement_token]
        elif 'XXXXX' in measurement_token:
            if token_in_list_ignore_case(
                    measurement_token[:measurement_token.find('XXXXX') - 1],
                    all_tokens):
                out_spec['measurement'][measurement_token] = union_spec[
                    'measurement'][measurement_token]
        else:
            discarded_spec['measurement'][measurement_token] = union_spec[
                'measurement'][measurement_token]

    for enum_token in union_spec['enumSpecializations']:
        if token_in_list_ignore_case(enum_token, all_tokens):
            out_spec['enumSpecializations'][enum_token] = union_spec[
                'enumSpecializations'][enum_token]
        else:
            discarded_spec['enumSpecializations'][enum_token] = union_spec[
                'enumSpecializations'][enum_token]

    for prop in union_spec['pvs']:
        for property_token in union_spec['pvs'][prop]:
            if token_in_list_ignore_case(property_token, all_tokens):
                if prop not in out_spec['pvs']:
                    out_spec['pvs'][prop] = {}
                out_spec['pvs'][prop][property_token] = union_spec['pvs'][prop][
                    property_token]
            elif 'XXXXX' in property_token:
                if token_in_list_ignore_case(
                        property_token[:property_token.find('XXXXX') - 1],
                        all_tokens):
                    out_spec['pvs'][prop][property_token] = union_spec['pvs'][
                        prop][property_token]
            else:
                if prop not in discarded_spec['pvs']:
                    discarded_spec['pvs'][prop] = {}
                discarded_spec['pvs'][prop][property_token] = union_spec['pvs'][
                    prop][property_token]

    for prop in union_spec['inferredSpec']:
        if prop in out_spec['pvs']:
            out_spec['inferredSpec'].update(
                {prop: union_spec['inferredSpec'][prop]})
        else:
            discarded_spec['inferredSpec'].update(
                {prop: union_spec['inferredSpec'][prop]})

    for cur_universe in union_spec['universePVs']:
        population_flag = False
        for population_token in out_spec['populationType']:
            if out_spec['populationType'][population_token] == cur_universe[
                    'populationType']:
                population_flag = True

        property_flag = True
        cprops = cur_universe.get('constraintProperties', None)
        if cprops is not None:
            for property_name in cprops:
                if property_name not in out_spec['pvs']:
                    property_flag = False

        if property_flag and population_flag:
            out_spec['universePVs'].append(cur_universe)
        else:
            discarded_spec['universePVs'].append(cur_universe)

    # ignoreColumns
    for token_name in union_spec['ignoreColumns']:
        if token_in_list_ignore_case(token_name,
                                     all_tokens) or token_name in all_columns:
            if token_name not in out_spec['ignoreColumns XXXXX']:
                out_spec['ignoreColumns XXXXX'].append(token_name)
        else:
            discarded_spec['ignoreColumns'].append(token_name)

    # ignoreTokens
    for token_name in union_spec['ignoreTokens']:
        if token_in_list_ignore_case(token_name,
                                     all_tokens) or token_name in all_columns:
            if token_name not in out_spec['ignoreTokens XXXXX']:
                out_spec['ignoreTokens XXXXX'].append(token_name)
        else:
            discarded_spec['ignoreTokens'].append(token_name)

    dc_props = {}
    for population_dcid in expected_populations:
        dc_props[population_dcid] = fetch_dcid_properties_enums(population_dcid)

    # add missing properties from expected properties
    for property_name in expected_pvs:
        if property_name not in out_spec['pvs']:
            out_spec['pvs'][property_name] = {}
            # fetch values from dc if present
        for population_name in dc_props:
            if property_name in dc_props[population_name]:
                if dc_props[population_name][property_name]:
                    for i, enum_value in enumerate(
                            dc_props[population_name][property_name]):
                        out_spec['pvs'][property_name]['XXXXX' +
                                                       str(i)] = enum_value
            # TODO guess token if possible

    # print columns with no pv assignment
    columns_missing_pv = find_columns_with_no_properties(all_columns, out_spec)
    columns_missing_pv = list(set(columns_missing_pv))
    # print('---------------------')
    # print('columns missing pv')
    # print('---------------------')
    # print(columns_missing_pv)

    # missing tokens
    print('---------------------')
    print('missing tokens')
    print('---------------------')
    missing_tokens = find_missing_tokens(all_tokens, out_spec)
    print(json.dumps(missing_tokens, indent=2))

    # write to output files
    with open(os.path.join(output_path, 'generated_spec.json'), 'w') as fp:
        json.dump(out_spec, fp, indent=2)
    with open(os.path.join(output_path, 'discarded_spec_parts.json'),
              'w') as fp:
        json.dump(discarded_spec, fp, indent=2)

    # write missing reports to file
    with open(os.path.join(output_path, 'missing_report.json'), 'w') as fp:
        json.dump(
            {
                'columns_missing_pv': columns_missing_pv,
                'missing_tokens': missing_tokens
            },
            fp,
            indent=2)

    return out_spec


def main(argv):
    combined_spec_out = create_combined_spec(get_spec_list(),
                                             _FLAGS.generator_output)

    if _FLAGS.create_union_spec:
        print(json.dumps(combined_spec_out, indent=2))
    if _FLAGS.get_combined_property_list:
        print(
            json.dumps(sorted(list(combined_spec_out['pvs'].keys())), indent=2))
    if _FLAGS.guess_new_spec:
        if not _FLAGS.zip_list and not _FLAGS.column_list_path:
            print(
                'ERROR: zip file/s or column list required to guess the new spec'
            )
        else:
            if _FLAGS.column_list_path:
                all_columns = json.load(
                    open(os.path.expanduser(_FLAGS.column_list_path), 'r'))
                guess_spec = create_new_spec(all_columns, combined_spec_out,
                                             _FLAGS.expected_populations,
                                             _FLAGS.expected_properties,
                                             _FLAGS.generator_output,
                                             _FLAGS.delimiter)
                print(json.dumps(guess_spec, indent=2))
            if _FLAGS.zip_list:
                all_columns = columns_from_zip_list(_FLAGS.zip_list,
                                                    _FLAGS.check_metadata)
                guess_spec = create_new_spec(all_columns, combined_spec_out,
                                             _FLAGS.expected_populations,
                                             _FLAGS.expected_properties,
                                             _FLAGS.generator_output,
                                             _FLAGS.delimiter)
                print(json.dumps(guess_spec, indent=2))


if __name__ == '__main__':
    flags.mark_bool_flags_as_mutual_exclusive(
        ['create_union_spec', 'guess_new_spec', 'get_combined_property_list'],
        required=True)
    app.run(main)
