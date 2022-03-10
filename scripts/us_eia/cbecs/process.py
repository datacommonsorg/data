# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''
Generate statvars for commercial buildings data set.
'''

import csv
import os
import re
import sys
import datetime
import time

from absl import app
from absl import flags
from inspect import getframeinfo, stack


# Allows the following module imports to work when running as a script
# module_dir_ is the path to where this code is running from.
_MODULE_DIR = os.path.dirname(__file__)
sys.path.append(os.path.join(_MODULE_DIR))
sys.path.append(os.path.join(_MODULE_DIR,
                             '../../../util/'))  # for statvar_dcid_generator

from statvar_dcid_generator import get_statvar_dcid
from config import PROPERTY_MAP
from stat_var_group import add_stat_var_groups

FLAGS = flags.FLAGS

flags.DEFINE_list('csv_data_files', [],
                  'csv files from UNData Energy datasets to process')
flags.DEFINE_string('output_path', 'tmp_data_dir/un_energy_output',
                    'Data set name used as file name for mcf and tmcf')
flags.DEFINE_integer('skip_rows', 0,
                     'Number of rows to skip at the start of the csv file.')
flags.DEFINE_integer('header_rows', 1,
                     'Number of rows to process as header per csv file.')
flags.DEFINE_integer('num_rows', -1,
                     'Number of rows to process per file. -1 for all.')
flags.DEFINE_integer('debug_level', 0, 'Print debug messages at this level or lower.')
flags.DEFINE_integer('debug_lines', 10, 'Print error logs every N lines')
flags.DEFINE_boolean('emit_all_properties', False,
                     'Emit all properties including non-existing ones.')
flags.DEFINE_boolean('drop_duplicate_svobs', True,
                     'Drop statvars with duplicate observations.')
flags.DEFINE_boolean(
    'schemaless_statvars', True,
    'Generate schemaless statvars with popType set to the statvar itself.')
flags.DEFINE_string('svg_root', 'eia/g/Root',
                    'Generate statvar groups under this root statvar.')
flags.DEFINE_string('svg_prefix', '',
                    'Generate statvar groups under this root statvar.')

_DEFAULT_STAT_VAR_PV = {
    'typeOf': 'dcs:StatisticalVariable',
    'measurementQualifier': 'Annual',
    'statType': 'dcs:measuredValue',
    'observationAbout': 'dcid:country/USA',
    'populationType': 'CommercialBuilding',
    'measuredProperty': 'count',
}

_OBSERVATION_PROPS = [
    'observationAbout',
    'observationDate',
    'value',
    'variableMeasured',
    'unit',
    'Input',
]

_OBSERVATION_COLUMNS = _OBSERVATION_PROPS + ['Scale', 'Node']

_DEFAULT_STAT_VAR_GROUP_PV = {
    'typeOf': 'dcs:StatVarGroup',
}

_DCID_IGNORE_PROPS = [
  'typeOf',
  'name',
  'description',
  'statType',
  'measurementQualifier',
  'measuredProperty',
  'populationType',
] + _OBSERVATION_COLUMNS

_DEFAULT_SVG_IGNORE_PROPS = _OBSERVATION_COLUMNS + [
    'Node',
    #'typeOf',
    #'measuredProperty',
    #'statType',
    'measurementDenominator',
    'measurementQualifier',
    'description',
    'name',
    'dcid',
    'scalingFactor',
]

_TEMPLATE_MCF = """
Node: E:DataSet->E0
typeOf: dcs:StatVarObservation
observationAbout: C:DataSet->observationAbout
observationDate: C:DataSet->observationDate
variableMeasured: C:DataSet->variableMeasured
value: C:DataSet->value
unit: C:DataSet->unit
"""

# Global configs saved when processing a file.
_CONFIG = {}


def _set_config(settings: dict):
    '''Set the config valus from the dict.'''
    _CONFIG.update(settings)


def _get_config_value(option: str, default='', config=_CONFIG):
    '''Returns the valud in the config with a default value if not set.'''
    return config.get(option, default)


def _set_config_value(option: str, value, config=_CONFIG):
    '''Set the config value overwriting any previous value.'''
    config[option] = value


# Global counters for debugging
_COUNTERS = {}


def _add_counter(name: str, value: int, counters=_COUNTERS):
    '''Increment the counter by the given value.'''
    counters[name] = counters.get(name, 0) + value


def _add_error_counter(counter_name: str, error_msg: str, counters=_COUNTERS):
    _print_debug(2, "Error: ", counter_name, error_msg)
    if counters is not None:
        _add_counter(counter_name, 1, counters)
        debug_lines = 1
        if 'debug_lines' in counters:
            debug_lines = counters['debug_lines']
        if counters.get(counter_name, 0) % debug_lines == 0:
            print("ERROR: ", counter_name, ": ", error_msg, file=sys.stderr)


def _print_counters(counters: dict, steps=None):
    row_key = 'inputs_processed'
    if steps is None or counters.get(row_key, 0) % steps == 0:
        print('\nSTATS:')
        for k in sorted(counters):
            print(f"\t{k:>30} = {counters[k]}")
        if 'inputs_processed' in counters:
            start_ts = counters['time_start']
            end_ts = time.perf_counter()
            print(
                'Processing rate: {:.2f}'.format(counters['inputs_processed'] /
                                                 (end_ts - start_ts)),
                'rows/sec')
        print('', flush=True)


def _print_debug(debug_level: int, *args):
    if _CONFIG.get('debug_level', 0) >= debug_level:
        caller = getframeinfo(stack()[1][0])
        print(
            f'[{datetime.datetime.now()}:{os.path.basename(caller.filename)}:{caller.lineno}]',
            *args,
            file=sys.stderr)


def get_camelcase_alnum_string(input_string: str) -> str:
    '''Returns a capitalized string with only alphabets or numbers.
    Example: "Abc-def(HG-123)" -> "AbcDefHG"
    '''
    # strip out paranthesis
    paranthesis_pos = input_string.find('(')
    if paranthesis_pos > 0:
        input_string = input_string[:paranthesis_pos]
    # replace any non-alpha characters with space
    clean_str = [s if s.isalnum() else ' ' for s in input_string]
    joined_str = ''.join(clean_str)
    # split by space and capitalise first letter, preserving any other capitals
    return ''.join(
        [w[0].upper() + w[1:] for w in joined_str.split(' ') if len(w) > 0])


def get_paranthesis_str(text: str) -> str:
    '''Returns the string within paranthesis.'''
    paranthesis_pos = text.find('(')
    if paranthesis_pos > 0:
        return get_camelcase_alnum_string(text[paranthesis_pos +
                                               1:text.rfind(')')])
    return ''


def get_dict_value(text: str, maps: dict) -> dict:
    '''Returns a property for the text from the maps.'''
    if text in maps:
        return maps[text]
    pvs = []
    prop = get_value_string(get_camelcase_alnum_string(text))
    unit = get_paranthesis_str(text)
    found_pv = False
    if prop in maps:
        pvs.append(maps[prop])
        found_pv = True
    if unit in maps:
        pvs.append(maps[unit])
        found_pv = True
    if not found_pv:
        _print_debug(1, f'ERROR: Missing value in map for {text}')
        pvs.append({prop: '@VALUE'})
    pvs.append({'@SOURCE': [text]})
    return merge_property_value_maps(pvs)


def invert_dict(pvs: dict) -> dict:
    '''Invert a dictionary to value: key.'''
    new_pvs = {}
    for k, v in pvs.items():
        if '@' in v:
            new_pvs[v] = k
        else:
            new_pvs[k] = v
    return new_pvs


def get_properties(headers: list, maps: dict) -> dict:
    '''Returns the dictionary of property values for a series of texts.'''
    pvs_list = []
    for header in headers:
        if header != '':
            pvs_list.append(get_dict_value(header, maps))
    return merge_property_value_maps(pvs_list)


def add_column_headers(row: list, headers: list) -> list:
    '''Add a row to list of header rows.
       If there are empty columns in the row, repeat previous column
       to expand horizontally merged cells.
       Add the row to the list of headers.

       Args:
        row: A new list of columns for a row.
        headers: List of column headers.
          number of columns in row and headers are assumed to match.
    '''
    expanded_row = []
    last_col = ''
    for col in row:
        if col != '':
            expanded_row.append(col)
            last_col = col
        else:
            expanded_row.append(last_col)
    headers.append(expanded_row)
    return headers


def get_column_properties(headers: list, maps: dict) -> dict:
    '''Returns the list of all PVs for each column in the header.'''
    if headers is None or len(headers) == 0:
        return []
    columns = [[] for x in range(len(headers[0]))]
    for row in headers:
        for i in range(len(row)):
            columns[i].append(row[i])

    col_props = []
    for i in range(len(columns)):
        # columns[i].reverse()
        col_props.append(get_properties(get_value_string(columns[i]), maps))
    return col_props


def is_section_header(row: list) -> bool:
    '''Returns true if the row is a section header, i.e, all columns
       except the first are empty.
    '''
    return ''.join(row[1:]) == ''


def get_value_string(text):
    '''Converts value to a quantity range or int value.'''
    value = text
    if isinstance(value, str):
        value = value.replace(',', '').strip()
        if value.find('To') > 0:
            value = value.replace('To', ' ')
        if value.startswith('FewerThan'):
            value = value.replace('FewerThan', '- ')
        if value.startswith('Before'):
            value = value.replace('Before', '- ')
        if value.endswith('OrMore'):
            value = value.replace('OrMore', ' -')
        if value.startswith('Over'):
            value = value.replace('Over', '') + ' -'
        _print_debug(2, f'Changed {text} to {value}')
    return value

def get_alnum_string(text: str) -> str:
    '''Returns a string with just alphanumeric characters.'''
    alnum_str = ''.join([c if c.isalnum() or c == '-' else '' for c in text])
    return alnum_str[0].upper() + alnum_str[1:]

def get_stat_var_dcid(pvs: dict) -> dict:
    '''Returns a dcid for the statvar property values.
       Sorts all properties alphabetically and returns the contactenated string
       of property and values.
    '''
    # Only using value causes dup statvars and multiple properties have same value
    # dcid = get_statvar_dcid(pvs, ignore_props=_OBSERVATION_COLUMNS)
    _DEFAULT_DCID_PROPS = [ 'statType', 'measurementQualifier', 'measuredProperty', 'populationType']
    _IGNORE_VALUES = ['measuredValue']
    tokens = []
    for p in _DEFAULT_DCID_PROPS:
        if p in pvs:
            value = strip_namespace(pvs[p])
            if value != '' and value not in _IGNORE_VALUES:
                tokens.append(get_alnum_string(value.replace('Value', '')))
    # Add remaining propertes in alphabetical order with P_V
    for p, v in pvs.items():
        if p not in _DCID_IGNORE_PROPS:
            tokens.append(p)
            tokens.append(strip_namespace(get_alnum_string(v)))
    dcid = '_'.join(tokens)    
    dcid = dcid.replace(' ', '_')
    return dcid


def replace_value_in_dict(sv: dict, value: str, new_value: str):
    '''Replace any value in the dict with the replacement.'''
    for p in sv.keys():
        v = sv[p]
        if isinstance(v, str) and value in v:
            v1 = v.replace('{' + value + '}',
                           new_value).replace(value, new_value)
            sv[p] = v1
            _print_debug(2, f'Replaced [{p}]:{v} with {v1}')
            return True
    return False


def merge_property_value_maps(pv_list: list) -> dict:
    '''Merge a set of dictionaries with property and values resolving references in order.'''
    sv = {'@SOURCE': []}
    if pv_list is None or len(pv_list) == 0:
        return sv
    sv.update(pv_list[0])
    for pvs in pv_list[1:]:
        # Lookup each key in PV and resolve in sv.
        for k, v in pvs.items():
            value_resolved = False
            new_val = get_value_string(v)
            if k == '@SOURCE':
                # Merge source texts form different columns.
                sv['@SOURCE'].extend(v)
                value_resolved = True
            elif k.startswith('@'):
                value_resolved = replace_value_in_dict(sv, k, new_val)
            elif isinstance(v, str) and v.startswith('@'):
                replace_val = get_value_string(k)
                value_resolved = replace_value_in_dict(sv, v, replace_val)
            if not value_resolved:
                sv[k] = new_val
    # resolve any remaining values within the SV
    for k in list(sv.keys()):
        item_resolved = False
        v = sv[k]
        new_val = get_value_string(v)
        if k.startswith('@'):
            item_resolved = replace_value_in_dict(sv, k, new_val)
    #    elif isinstance(v, str) and v.startswith('@'):
    #        replace_val = get_value_string(k)
    #        item_resolved = replace_value_in_dict(sv, v, replace_val)
    #    #if item_resolved:
    #    #  sv.pop(k)
    _print_debug(2, f"Merged dicts: {pv_list} into {sv}")
    return sv


def get_stat_var_pvs(pvs: dict, ignore_props: dict) -> dict:
    '''Resolve statvar value references and return statvar with a dcid.'''
    sv = {}
    for k, v in pvs.items():
        if '@' in k or k in ignore_props:
            # Skip references.
            continue
        if isinstance(v, str):
            if '{@' in v:
                try:
                    new_v = v.format(**pvs)
                    sv[k] = new_v
                except KeyError:
                    _print_debug(1, f"Dropping {k}:{v} without value")
            elif not '@' in v and v != '':
                sv[k] = v
        else:
            sv[k] = v
    if 'Node' not in sv:
        dcid = get_stat_var_dcid(sv)
        sv['Node'] = dcid
        pvs['Node'] = dcid
    if 'description' not in sv:
        sv['description'] = '"' + get_statvar_description(sv) + '"'
    return sv


def get_sv_obs(pvs: dict, value: str, date: str) -> dict:
    '''Retruns the pvs for the statvar obvervation.'''
    svobs = {}
    for p in _OBSERVATION_PROPS:
        if p in pvs:
            svobs[p] = pvs[p]
    value_num = float(value)
    if 'Scale' in pvs:
        value_num *= pvs['Scale']
    svobs['value'] = value_num
    svobs['variableMeasured'] = pvs['Node']
    if 'observationAbout' not in svobs:
        svobs['observationAbout'] = 'country/USA'
    if 'observationDate' not in svobs:
        svobs['observationDate'] = date
    return svobs


def get_prop_value_str(value):
    '''Returns the formatted property value text with namespace prefix.'''
    if not isinstance(value, str):
        return value
    if len(value) > 0 and value.find(' ') < 0 and value.find(':') < 0:
        if value[0].isalpha():
            return 'dcid:' + value
    return value


def strip_namespace(value: str) -> str:
    '''Removes any namespace prefix for the value.'''
    if isinstance(value, str) and len(value) > 0 and value[0].isalpha():
        return value[value.find(':') + 1:]
    return value


def get_quantity_string(value: str) -> str:
    '''Returns a description string for a quantity range.'''
    quantity_re = r'\[\s*(?P<start>[0-9-]+)\s+(?P<end>[0-9-]*)?\s*(?P<unit>\w+)\s*\]'
    matches = re.search(quantity_re, value)
    if not matches:
        return value
    start = matches.group('start')
    end = matches.group('end')
    unit = matches.group('unit')
    if start == '-':
        return f'{end} {unit} or less'
    if end == '-':
        return f'{start} {unit} or more'
    if end == '':
        return f'{start} {unit}'
    return f'{start} to {end} {unit}'


def get_space_seperated_string(text: str) -> str:
    '''Converts "CamelCase" to space separated string "camel case"'''
    chars = [' ' + x.lower() if x.isupper() else x for x in text]
    return ''.join(chars).replace('  ', ' ').strip()


def get_statvar_description(sv: dict) -> str:
    '''Returns the description string for a statvar.
    Uses the standard phrases for common PVs and
    adds a comma seperated list for remaining domains specific property values.
    '''
    _DESCRIPTION_STRINGS = {
        'count': 'number',
        'medianValue': 'Median',
        'meanValue': 'Mean',
        'measuredValue': 'Total',
    }
    value = []
    props_added = []
    for p in ['statType', 'measuredProperty']:
        pv = strip_namespace(sv.get(p, ''))
        if pv in _DESCRIPTION_STRINGS:
            value.append(_DESCRIPTION_STRINGS[pv])
        elif pv != '':
            value.append(get_space_seperated_string(pv))
    value.append('of')
    value.append(
        get_space_seperated_string(strip_namespace(sv.get('populationType',
                                                          ''))))
    ignore_props = set(_OBSERVATION_COLUMNS + list(_DEFAULT_STAT_VAR_PV.keys()))
    props = set(sv.keys()) - ignore_props
    cprops = []
    for p in props:
        if p in ignore_props:
            continue
        v = strip_namespace(str(sv[p]))
        if v.startswith('['):
            v = get_quantity_string(v)
        if v == 'True':
            if p.startswith('has'):
                p = p.replace('has', 'with')
            v = ''
        p = get_space_seperated_string(p)
        v = get_space_seperated_string(v)
        if p != '' or v != '':
            if len(cprops) > 0:
                cprops[-1] += ','
        if p != '':
            cprops.append(p)
        if v != '':
            cprops.append(v)
    if len(cprops) > 0 and not cprops[0].startswith('with'):
        value.append('with')
    desc = ' '.join(value + cprops)
    return desc[0].upper() + desc[1:]


def get_stat_var_mcf(sv: dict, config: dict, default_props: dict) -> str:
    '''Returns the MCF for the StatVar node.
       Properties with lower case first letter are only written.
    '''
    _print_debug(2, {}, f'Generating MCF for {sv}')
    sv_mcf = []
    sv_mcf.append('Node: ' + get_prop_value_str(sv['Node']))
    sv_ignored = []
    schemaless = config.get('schemaless_statvars', False)
    sv_props = list(sv.keys())
    if 'Node' in sv_props:
        sv_props.remove('Node')
    if default_props is not None:
        for p in default_props:
            if p in _OBSERVATION_COLUMNS:
                continue
            if p not in sv_props:
                sv[p] = default_props[p]
                sv_mcf.append(p + ': ' + get_prop_value_str(default_props[p]))
            else:
                sv_mcf.append(p + ': ' + get_prop_value_str(sv[p]))
                sv_props.remove(p)
    for p in sorted(sv_props):
        if p in _OBSERVATION_COLUMNS or p in default_props:
            continue
        if schemaless and p == 'measuredProperty':
            sv_mcf.append(p + ': ' + sv['Node'])
            sv_ignored.append('# ' + p + ': ' + get_prop_value_str(sv[p]))
            continue
        elif p[0].isupper():
            # Properties in prod begin with lower case.
            # Property starting with upper case indicates an unresolved PV
            # to be used for schemaless import.
            sv_ignored.append('# ' + p + ': ' + get_prop_value_str(sv[p]))
            continue
        if isinstance(sv[p], list):
            sv_mcf.append(p + ': ' +
                          ','.join([get_prop_value_str(x) for x in sv[p]]))
        else:
            sv_mcf.append(p + ': ' + get_prop_value_str(sv[p]))
    return '\n'.join(sv_mcf + sv_ignored)


def write_stat_var_mcf(sv_map: dict, filename: str, config: dict,
                       default_props: dict, counters: dict):
    '''Write statvars to a file.'''
    _print_debug(0, f"Writing {len(sv_map)} stat-vars to {filename}.mcf")
    with open(filename + '.mcf', 'w') as f_mcf:
        for node in sv_map.keys():
            f_mcf.write('\n\n')
            f_mcf.write(get_stat_var_mcf(sv_map[node], config, default_props))
    _add_counter('output_stat_vars', len(sv_map), counters)


def write_statvar_obs_csv(sv_obs: list, filename: str, counters: dict):
    '''Write ststvar observations to a csv fle.'''
    _print_debug(
        0,
        f"Writing {len(sv_obs)} stat-var-obs to {filename}.csv and {filename}.tmcf"
    )
    with open(filename + '.csv', 'w', newline='') as f_out_csv:
        csv_writer = csv.DictWriter(f_out_csv,
                                    fieldnames=_OBSERVATION_PROPS,
                                    extrasaction='ignore',
                                    lineterminator='\n')
        csv_writer.writeheader()
        for key, data_row in sv_obs.items():
            csv_writer.writerow(data_row)
        _add_counter('output_stat_var_obs', len(sv_obs), counters)

    with open(filename + '.tmcf', 'w', newline='') as f_out_tmcf:
        f_out_tmcf.write(_TEMPLATE_MCF)


def get_year_from_filename(filename: str) -> str:
    '''Get the year from the filename.'''
    year_match = re.search(r'\b[0-9]{4}\b', filename)
    if year_match:
        return year_match.group(0)
    return ''


def preprocess_row(row_text: list) -> list:
    '''Do any pre-processing on the row such as string replacements.'''
    # Remove any columns with 'Unnamed:' that is a sideeffect of pandas.
    row = ['' if x.startswith('Unnamed') else x.replace('- ', '') for x in row_text]
    return row


def _is_number(value):
    '''Returns True if the input is a number, else False.'''
    if isinstance(value, str):
        # Check if the string value is a number.
        try:
            float(value)
            return True
        except ValueError:
            return False
    if isinstance(value, int) or isinstance(value, float):
        return True
    return False


def process_header_row(row: list, config: dict, context: dict,
                       counters: dict) -> bool:
    '''Process row as a header.
       Returns true if the row is a header, else false.
    '''
    # Header rows are assumed to precede data rows.
    # Check if any data_row has been processed.
    data_rows = counters.get('data_rows', 0)
    _print_debug(2, f'Checking: {data_rows} for {row}"')
    if data_rows == 0:
        # Check if there are multiple columns with data.
        num_data = 0
        for data in row:
            if data != '' and _is_number(data):
                num_data += 1
        _print_debug(2, f'Checking row with {num_data} data as header: {row}"')
        if num_data < _get_config_value('min_data_columns', 1):
            _print_debug(
                2, f'Processing row with {num_data} data as header: {row}"')
            return True
    return False


def add_sv_map(sv: dict, sv_map: dict, counters: dict) -> bool:
    '''Add a statvar to the map of statvars.'''
    dcid = sv['Node']
    if dcid in sv_map:
        # Node with same dcid exists. Check if properties match as well.
        if sv_map[dcid] != sv:
            _add_error_counter(
                'error_mismatch_sv_dcid',
                f'Duplicate dcid for StatVars: {sv_map[dcid]} and {sv}',
                counters)
        return False
    sv_map[dcid] = sv
    return True


def add_svobs(svobs: dict, sv_obs_map, counters: dict) -> bool:
    '''Add a Statvar observation to the map.
    Drops duplicate svobs with a warning.
    '''
    obs_key = svobs['variableMeasured'] + svobs['observationAbout'] + svobs[
        'observationDate'] + svobs.get('unit', '-')
    if obs_key in sv_obs_map:
        if svobs['value'] != sv_obs_map[obs_key]['value']:
            _add_error_counter(
                'error_duplicate_stat_var_obs',
                f"Duplicate StatVarObs: {sv_obs_map[obs_key]} == {svobs}",
                counters)
            # Collect duplicate observations
            if 'DuplicateInput' not in sv_obs_map[obs_key]:
                 sv_obs_map[obs_key]['DuplicateInput'] = []
            sv_obs_map[obs_key]['DuplicateInput'].append(svobs)
        else:
            _add_counter('ignored_duplicate_observations', 1, counters)
            _print_debug(
                2, f'Duplicate svobs in source: {sv_obs_map[obs_key]}, {svobs}')
        return False
    sv_obs_map[obs_key] = svobs
    return True

def remove_duplicate_svobs(svobs_map: dict, sv_map: dict, counters: dict):
    '''Remove any statvars with duplicate observations.     
    '''
    # Collect StatVars with dups.
    dup_sv = set()
    for svobs_key in list(svobs_map.keys()):
        svobs = svobs_map[svobs_key]
        if len(svobs.get('DuplicateInput', [])) > 0:
           # Drop stat var obs with dups.
           dup_sv.add(svobs['variableMeasured'])
           _add_error_counter('error_dropped_duplicate_svobs',
           f'Dropping duplicate svobs: {svobs}', counters) 
           svobs_map.pop(svobs_key)
    # Drop Statvars with dups.
    for sv in dup_sv:
        sv_map.pop(sv)
        _add_error_counter('error_dropped_stat_vars_with_dup_svobs',
           f'Dropping statvar with dups: {sv}', counters) 
        

def process_csv(csv_files: list, output_path: str, config: dict,
                counters: dict):
    '''Process a CSV file with data.
       Args:
         filename: Name of the csv file with data to process.
         config:  Configuration and settings for data processing.
         stat_vars: Dictionary of statvars to whcih new statvars for data will be added.
         stat_var_obs: List of stat var observations where each items is a dict.
    '''
    _set_config(config)
    context = {}
    _COUNTERS = counters
    # header_rows = _get_config_value('header_rows', 1)
    stat_vars_map = {}
    stat_var_obs = {}
    num_rows = config.get('num_rows', -1)
    counters['time_start'] = time.perf_counter()
    for filename in csv_files:
        with open(filename, 'r', encoding='UTF8') as f:
            _print_debug(0, f'Processing {filename}...')
            _add_counter('input_files_processed', 1, counters)
            csv_reader = csv.reader(f)
            skip_rows = _get_config_value('skip_rows', 0)
            counters['line'] = 0
            counters['data_rows'] = 0
            counters['header_rows'] = 0
            counters['file'] = filename
            year = get_year_from_filename(filename)
            _set_config_value('year', year)
            headers = []
            column_properties = []
            section_property = {}
            for row in csv_reader:
                _add_counter('line', 1, counters)
                input_ref = f"{filename}:{counters['line']}"
                if num_rows >= 0 and counters['line'] > num_rows:
                    break
                if skip_rows > 0:
                    skip_rows -= 1
                    continue
                _add_counter('inputs_processed', 1, counters)
                row = preprocess_row(row)
                if process_header_row(row, config, context, counters):
                    _print_debug(
                        1, f"Processing header:{input_ref}: {row}")
                    _add_counter('header_rows', 1, counters)
                    add_column_headers(row, headers)
                    continue
                if len(headers) > 0 and len(column_properties) == 0:
                    # Processing first non-header row.
                    # Consolidate header properties per column.
                    column_properties = get_column_properties(
                        headers, PROPERTY_MAP)
                    _print_debug(1, f"Generated header columns {headers}\n",
                                 f"Header PVs: {column_properties}")
                _print_debug(2, f"Processing row:{input_ref}: {row}")
                row_props = get_properties([get_value_string(row[0])],
                                           PROPERTY_MAP)
                if is_section_header(row):
                    section_property = row_props
                    _add_counter('section_header_rows', 1, counters)
                    continue
                _add_counter('data_rows', 1, counters)
                row_props = merge_property_value_maps(
                    [section_property, invert_dict(row_props)])
                for column_number in range(1, len(row) - 1):
                    input_ref = f"{filename}:{counters['line']}:{column_number}"
                    _print_debug(
                        2, f"Processing col: {input_ref}: {row[column_number]}")
                    value = get_value_string(row[column_number])
                    if _is_number(value):
                        stat_var = {}
                        stat_var.update(_DEFAULT_STAT_VAR_PV)
                        col_props = {}
                        if column_number < len(column_properties):
                            col_props = column_properties[column_number]
                        stat_var.update(row_props)
                        stat_var.update(col_props)
                        # stat_var['@SOURCE'].extend(row_props['@SOURCE'])
                        _print_debug(1, f"Generated stat-var {stat_var}")
                        stat_var_pvs = get_stat_var_pvs(stat_var,
                                                        _OBSERVATION_PROPS)
                        if add_sv_map(stat_var_pvs, stat_vars_map, counters):
                            _add_counter('stat_vars', 1, counters)
                        svobs = get_sv_obs(stat_var, value, year)
                        svobs['Input'] = input_ref
                        if add_svobs(svobs, stat_var_obs, counters):
                            _add_counter('stat_vars_obs', 1, counters)
        _print_counters(counters, steps=10)

    if config.get('drop_duplicate_svobs', False):
        remove_duplicate_svobs(stat_var_obs, stat_vars_map, counters)

    stat_var_groups = {}
    svg_root = config.get('svg_root', '')
    svg_prefix = config.get('svg_prefix', '')
    stat_var_groups = {}
    if svg_root != '' and svg_prefix != '':
        add_stat_var_groups(svg_root,
                            svg_prefix,
                            stat_vars_map,
                            stat_var_groups,
                            ignore_props=_DEFAULT_SVG_IGNORE_PROPS,
                            ignore_default_pvs=_DEFAULT_STAT_VAR_PV)
        _print_debug(
            1,
            f'Generated {len(stat_var_groups)} for {len(stat_vars_map)} statvars'
        )
        _add_counter('stat_var_groups', len(stat_var_groups), counters)
        write_stat_var_mcf(stat_var_groups, output_path + '.svg', config,
                           _DEFAULT_STAT_VAR_GROUP_PV, counters)
    write_stat_var_mcf(stat_vars_map, output_path, config, _DEFAULT_STAT_VAR_PV,
                       counters)
    write_statvar_obs_csv(stat_var_obs, output_path, counters)

    counters['time_end'] = time.perf_counter()
    counters['total_time_secs'] = counters['time_end'] - counters['time_start']
    _print_counters(counters)


def main(_):
    csv_data_files = FLAGS.csv_data_files
    if len(csv_data_files) > 0 and FLAGS.output_path != '':
        process_csv(
            csv_data_files, FLAGS.output_path, {
                'skip_rows': FLAGS.skip_rows,
                'header_rows': FLAGS.header_rows,
                'num_rows': FLAGS.num_rows,
                'debug': FLAGS.debug_level,
                'emit_all_properties': FLAGS.emit_all_properties,
                'schemaless_statvars': FLAGS.schemaless_statvars,
                'svg_root': FLAGS.svg_root,
                'svg_prefix': FLAGS.svg_prefix,
                'drop_duplicate_svobs': FLAGS.drop_duplicate_svobs,
            }, {
                'debug_lines': FLAGS.debug_lines,
            })
    else:
        print(f'Please specify files to process with --csv_data_files=<,>')


if __name__ == '__main__':
    app.run(main)
