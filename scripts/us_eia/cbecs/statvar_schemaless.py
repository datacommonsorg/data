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
"""Script to convert statvars to schemaless or vice-versa.

Run it as follows:
  python3 statvar_schemaless.py --input_mcf=<input> --output_mcf=<output>

Copies over nodes from the input MCF to the output.
For statvar with references properties not yet defined in KG, the
property is commented and measuredProperty is set to the node dcid.
If --lower_case_mprop=True is set, then the mprp begins with a lower case.
If a previously commented property is now defined in KG,
the statvar is converted back into a normal StatVar.

To use autopush KG for reference checks, set '--use_autopush=True'.
To process only certain statvars, use '--regex=<REGEX>'.
Use --schema_mcf=<mcf_file1,mcf_file2> to pass in additional definitions
of nodes not yet in KG.

To allow references to new nodes in a schema_mcf file and not in KG,
use --schema_mcf=<file>
"""

import datacommons as dc
import datetime
import re
import sys
import time
import urllib

from absl import app
from absl import flags
from collections import OrderedDict

FLAGS = flags.FLAGS

flags.DEFINE_string('input_mcf', None, 'Input MCF file with statvars.')
flags.mark_flag_as_required('input_mcf')
flags.DEFINE_string('output_mcf', None, 'Output MCF file.')
flags.mark_flag_as_required('output_mcf')
flags.DEFINE_string(
    'regex', '',
    'Regular expression to select lines in input to be converted to schemaless.'
)
flags.DEFINE_bool('use_autopush', True, 'Use autopush for data commons API.')
flags.DEFINE_integer('debug_level', 0,
                     'Print debug messages at this level or lower.')
flags.DEFINE_integer('debug_lines', 100,
                     'Print counters once N inputs are processed.')
flags.DEFINE_bool(
    'lower_case_mprop', False,
    'Use a value starting with a lower case for measuredProperty')
flags.DEFINE_string(
    'schema_mcf', '',
    'Comma separated list of MCF files with additional schema definitions.')
flags.DEFINE_integer('max_api_retries', 3,
                     'Maximum number of retries for API calls.')
flags.DEFINE_integer('api_retry_interval', 10,
                     'Delay in secconds between API retries.')
flags.DEFINE_bool(
    'use_default_properties_only', False,
    'Comment out any non-default constraint property in a schemaless statvar.')
flags.DEFINE_integer('batch_nodes', 100, 'Number of nodes to batch up.')
flags.DEFINE_bool(
    'skip_upper_case_properties', True,
    'Skip any properties that start with an upper case. They are only used in schemaless statvars'
)

# Default properties in a StatVar.
_DEFAULT_PROPS = {
    'Node': '',
    'typeOf': 'dcs:StatisticalVariable',
    'measuredProperty': '@Node',
    'description': '',
    'statType': 'dcs:measuredValue',
    # 'populationType': 'schema:Thing',
    'keyString': '',
}

_KNOWN_DCIDS = {}

_SKIP_DCIDS = set({'Node', 'dcid'})

_CONFIG = {
    'max_api_retries': 3,
    'api_retry_interval': 10,
    'counter_display_interval': 10,
}

_COUNTERS = {}


def _add_counter(name: str, value: int, counters=_COUNTERS):
    '''Increment the counter by the given value.'''
    counters[name] = counters.get(name, 0) + value


def _print_counters(counters=_COUNTERS, interval=None):
    '''Display all counters at the given interval.'''
    if interval is not None:
        delay = time.perf_counter() - _print_counters._COUNTER_DISPLAY_TIME
        if delay < interval:
            return
    print('\nCounters:')
    for k in sorted(counters.keys()):
        print(f"\t{k:>40} = {counters[k]}")
    print('', flush=True)
    _print_counters._COUNTER_DISPLAY_TIME = time.perf_counter()


_print_counters._COUNTER_DISPLAY_TIME = 0


def _print_debug(debug_level: int, *args):
    if _CONFIG.get('debug_level', 0) >= debug_level:
        print("[", datetime.datetime.now(), "] ", *args, file=sys.stderr)


def _strip_namespace_prefix(text: str) -> str:
    '''Removes any namespace prefix seperated by ':', for example: dcid:'''
    return text[text.find(':') + 1:]


def _is_schema_element(entity: str) -> bool:
    '''Returns True if the entity refers to an entity likely in schema,
  i.e., it is a string.'''
    if not isinstance(entity, str):
        return False
    if entity == '':
        return False
    if not entity[0].isalpha():
        return False
    if ',' in entity:
        # Got a list of values. Lookup each recursively.
        entities = entity.split(',')
        has_schema_element = False
        for item in entities:
            if _is_schema_element(item):
                has_schema_element = True
        return has_schema_element
    if ' ' in entity:
        # Schema doesn't allow DCIDs with spaces.
        return False
    # Any string value beginning with an alphabet could be a schema node.
    return True


def dc_api_lookup(lookup_items: list, retry: int = 0) -> list:
    # Lookup property 'typeOf' for all dcids.
    # A missing 'typeOf' is assumed to indicate node is missing in schema.
    defined_items = []
    if lookup_items is not None and len(lookup_items) > 0:
        try:
            _print_debug(2, f'Looking up property for "{lookup_items}"')
            _add_counter('dc_api_lookups', 1)
            lookup_results = dc.get_property_values(lookup_items, prop='typeOf')
        except urllib.error.URLError:
            if retry > _CONFIG.get('max_api_retries', 3):
                _print_debug(0, f'Exceeded API retries for "{prop}"')
                raise RuntimeError
            else:
                delay = _CONFIG.get('api_retry_interval', 3)
                _print_debug(
                    0,
                    f'Retrying API for "{prop}" after delay of {delay} secs.')
                time.sleep(delay)
                return dc_api_lookup(lookup_items, retry + 1)
        # Update known dcids and return defined nodes.
        for item in lookup_items:
            if item in lookup_results and len(lookup_results[item]) > 0:
                _KNOWN_DCIDS[item] = True
                defined_items.append(item)
            else:
                _KNOWN_DCIDS[item] = False
    return defined_items


def dc_is_defined(entities: list, retry: int = 0) -> list:
    '''Returns the list of entities defined in DC.'''
    if len(_KNOWN_DCIDS) == 0:
        # Load known properties and values.
        for k, v in _DEFAULT_PROPS.items():
            _KNOWN_DCIDS[k] = True
            _KNOWN_DCIDS[_strip_namespace_prefix(v)] = True
        _print_debug(2, f'Added default props: {_KNOWN_DCIDS}')
    # Collect all items to be looked up.
    defined_items = []
    lookup_items = []
    for item in entities:
        # Allow any non-string values like int or quantity ranges.
        if not _is_schema_element(item):
            defined_items.append(item)
            continue
        for dcid in item.split(','):
            dcid = _strip_namespace_prefix(dcid)
            if not _is_schema_element(dcid):
                defined_items.append(item)
                continue
            if dcid in _KNOWN_DCIDS:
                if _KNOWN_DCIDS[dcid]:
                    defined_items.append(dcid)
            else:
                lookup_items.append(dcid)
    defined_items.extend(dc_api_lookup(lookup_items, retry))
    return defined_items


def dc_is_pv_valid(prop: str, value: str) -> bool:
    '''Returns true if the property and value are defined in KG.'''
    if prop in _SKIP_DCIDS:
        # value is a dcid. Allow it and save it for reference checks.
        _KNOWN_DCIDS[prop] = True
        _KNOWN_DCIDS[_strip_namespace_prefix(value)] = True
        return True
    if len(dc_is_defined([prop])) == 0:
        _print_debug(1, f'Missing property definition for {prop}: {value}.')
        return False
    if len(dc_is_defined([value])) == 0:
        _print_debug(1, f'Missing value definition for {prop}: {value}.')
        return False
    _print_debug(3, f'{prop}: {value} is defined.')
    return True


def drop_non_default_properties(pvs: OrderedDict, default_pv: dict):
    '''Comment out any non-default properties.
    Schemaless statvars can have all constraint properties omitted.
    '''
    props = list(pvs.keys())
    for prop in props:
        if len(prop) > 0 and prop[0] == '#':
            # Retain any commented properties.
            continue
        drop_pv = False
        if not prop in default_pv:
            # Comment any non-default property.
            _print_debug(1, f'Ignoring non-default property {prop}: {value}.')
            _add_counter(f'non_default_property_dropped', 1)
            _add_counter(f'non_default_property_dropped:{prop}', 1)
            drop_pv = True
        else:
            # Comment a default property that has a non-default value.
            value = _strip_namespace_prefix(pvs[prop])
            default_value = _strip_namespace_prefix(default_pv[prop])
            if default_value != '' and default_value[
                    0] != '@' and default_value != value:
                _add_counter(f'non_default_pv_dropped', 1)
                _add_counter(f'non_default_pv:{prop}:{value}', 1)
                _print_debug(1, f'Ignoring non-default value {prop}: {value}.')
                drop_pv = True
        if drop_pv:
            # Comment out the property in the node.
            value = pvs.pop(prop)
            pvs[f'# {prop}'] = value


def get_pv_from_line(line: str):
    '''Returns a tuple of property, value from the line.'''
    pos = line.find(':')
    if pos < 0:
        return ('', line)
    prop = line[:pos].strip()
    value = line[pos + 1:].strip()
    return (prop, value)


def add_property_value(pv, prop, value):
    '''Adds the property value to the PV dict.'''
    if prop not in pv:
        pv[prop] = value
        return

    # Overwrite an existing value only if it is not the default.
    old_value = pv[prop]
    if prop == 'measuredProperty':
        # Add a non-dcid value.
        old_value = old_value.lower()
        dcid = _strip_namespace_prefix(pv['Node'])
        value = _strip_namespace_prefix(value)
        if value.lower() != dcid.lower():
            pv[prop] = f'dcid:{value}'
        return

    # Add value if it is not the default.
    if prop in _DEFAULT_PROPS:
        default_value = _DEFAULT_PROPS[prop]
        if default_value != '' and default_value == value:
            # Skip default value.
            return
    _print_debug(2, f'Overwriting PV {prop}:{old_value} -> {value}')
    pv[prop] = value


def _drop_pv(prop: str, value: str, reg_ex) -> bool:
    '''Returns True if the Property:value is to be dropped.'''
    if prop in _SKIP_DCIDS:
        return False
    if (reg_ex != '' and re.search(reg_ex, f'{prop}: {value}')):
        return True

    if _CONFIG.get('skip_upper_case_properties', False):
        if isinstance(prop, str) and len(prop) > 0 and prop[0].isupper():
            # Skip properties begining with an upper case.
            return True
    if not dc_is_pv_valid(prop, value):
        return True
    return False


def process_node(lines: list, reg_ex) -> list:
    '''Returns the lines for the node based on the input lines.'''
    pv = {}
    output_pv = OrderedDict()
    is_pv_dropped = False
    for line in lines:
        if line == '':
            continue
        if line[0] == '#':
            # If line was a commented property: value, restore it.
            # It will be commented again if it is still not defined.
            (prop, value) = get_pv_from_line(line[1:])
            if prop == '' or not prop[0].islower():
                output_pv[line] = ''
                continue
        else:
            (prop, value) = get_pv_from_line(line)
        if prop != '':
            pv[prop] = value
            if _drop_pv(prop, value, reg_ex):
                is_pv_dropped = True
                add_property_value(output_pv, f'# {prop}', value)
                _add_counter('properties_dropped', 1)
                _add_counter(f'property_dropped:{prop}', 1)
            else:
                add_property_value(output_pv, prop, value)
    if is_pv_dropped:
        # Convert to schemaless
        if 'Node' in output_pv:
            # Set the measuredProperty to the Node dcid
            # and comment the existing measuredProperty value.
            dcid = output_pv['Node']
            _print_debug(2, f'Converting {dcid} to schemaless')
            if _CONFIG['lower_case_mprop']:
                # Some checks require measuredProperty to start with lower case.
                dcid = _strip_namespace_prefix(dcid)
                dcid = 'dcid:' + dcid[0].lower() + dcid[1:]
            mprop = output_pv.get('measuredProperty', '')
            if mprop != dcid:
                if mprop != '':
                    output_pv['# measuredProperty'] = mprop
                output_pv['measuredProperty'] = dcid
            if _CONFIG.get('use_default_properties_only'):
                drop_non_default_properties(output_pv, _DEFAULT_PROPS)
            _add_counter('statvars_converted_to_schemaless', 1)

    if output_pv.get('typeOf', '') == _DEFAULT_PROPS['typeOf']:
        # Add any missing default statvar properties.
        for p, v in _DEFAULT_PROPS.items():
            if p not in output_pv:
                new_value = v
                if len(new_value) > 0 and new_value[0] == '@':
                    prop = new_value[1:]
                    new_value = pv.get(prop, '')
                if new_value != '':
                    output_pv[p] = new_value
                    _add_counter('default_properties_added', 1)
                    _add_counter(f'default_property_added_{p}', 1)

    # Convert the Property:Value dictionary to sequence of lines.
    output_lines = []
    for prop, value in output_pv.items():
        sep = ': '
        if value == '':
            sep = ''
        output_lines.append(f'{prop}{sep}{value}')
    _print_debug(2, f'Generated node {output_lines}')
    return output_lines


def process_lines(node_lines: list, reg_ex, output_f):
    '''Process a node definition with a sequence of PVs.'''
    _print_debug(2, f'Processing node: {node_lines}')
    _add_counter('output_nodes', 1)
    if re.search(reg_ex, '\n'.join(node_lines)):
        # Process lines that match the regex pattern.
        new_lines = process_node(node_lines, reg_ex)
        output_f.write('\n'.join(new_lines))
        output_f.write('\n')
        _add_counter('input_nodes_matching_regex', 1)
        _add_counter('output_lines', len(new_lines) + 1)
    else:
        # Copy over original lines for nodes not matching the regex pattern.
        output_f.write('\n'.join(node_lines))
        output_f.write('\n')
        _add_counter('output_lines', len(node_lines) + 1)
    output_f.write('\n')


def process_node_lines(node_lines: list, reg_ex, output_f):
    '''Process a set of nodes as MCF lines in a batch.'''
    # Collect all PVs to lookup in a batch.
    prefetch_lookups = set()
    for node in node_lines:
        for line in node:
            (prop, value) = get_pv_from_line(line)
            if prop in _SKIP_DCIDS:
                # value is a dcid. Allow it and save it for reference checks.
                _KNOWN_DCIDS[prop] = True
                _KNOWN_DCIDS[_strip_namespace_prefix(value)] = True
                continue
            if _CONFIG.get('skip_upper_case_properties', False):
                if isinstance(prop,
                              str) and len(prop) > 0 and prop[0].isupper():
                    # Skip properties begining with an upper case.
                    continue
            prefetch_lookups.add(prop)
            prefetch_lookups.add(value)
    dc_is_defined(list(prefetch_lookups))
    # Process all lines for each node.
    for node in node_lines:
        process_lines(node, reg_ex, output_f)


def process(input_mcf: str, output_mcf: str, regex: str):
    '''Copies over the nodes form input MCF to the output MCF.'''
    num_lines = 0
    num_nodes = 0
    num_matches = 0
    #reg_ex = re.compile(regex)
    reg_ex = regex
    with open(input_mcf, 'r') as input_f:
        with open(output_mcf, 'w') as output_f:
            node_lines = []
            nodes_list = []
            for line in input_f:
                line = line.strip()
                num_lines += 1
                _add_counter('input_lines', 1)
                _print_debug(2, f'Processing {input_mcf}:{num_lines}:{line}')
                if line == '':
                    if len(node_lines) > 0:
                        num_nodes += 1
                        _add_counter('input_nodes', 1)
                        nodes_list.append(node_lines)
                        if len(nodes_list) >= _CONFIG.get('batch_nodes'):
                            process_node_lines(nodes_list, reg_ex, output_f)
                            nodes_list = []
                        node_lines = []
                    _print_counters(
                        interval=_CONFIG.get('counter_display_interval', 10))
                else:
                    node_lines.append(line)
            if len(node_lines) > 0:
                _add_counter('input_nodes', 1)
                nodes_list.append(node_lines)
                process_node_lines(nodes_list, reg_ex, output_f)
                nodes_list = []
    _print_counters()
    print(f'Copied over {num_nodes} nodes from {input_mcf} into {output_mcf}')


def load_schema_nodes(filenames: str):
    '''Load dcids from schema mcf files.'''
    files = filenames.split(',')
    for file in files:
        with open(file, 'r') as input_f:
            for line in input_f:
                line = line.strip()
                if 'Node:' in line or 'dcid:' in line:
                    dcid = ':'.join(line.split(':')[1:]).strip()
                    dcid = _strip_namespace_prefix(dcid)
                    _KNOWN_DCIDS[dcid] = True
                    _KNOWN_DCIDS[dcid[0].lower() + dcid[1:]] = True
                    _add_counter('loaded_dcid', 1)
                    _print_debug(3, f'Adding {dcid} to known references.')


def main(_) -> None:
    _CONFIG['debug_level'] = FLAGS.debug_level
    _CONFIG['lower_case_mprop'] = FLAGS.lower_case_mprop
    _CONFIG['debug_lines'] = FLAGS.debug_lines
    _CONFIG['max_api_retries'] = FLAGS.max_api_retries
    _CONFIG['api_retry_interval'] = FLAGS.api_retry_interval
    _CONFIG['use_default_properties_only'] = FLAGS.use_default_properties_only
    _CONFIG['batch_nodes'] = FLAGS.batch_nodes
    if FLAGS.use_autopush:
        server = 'http://autopush.api.datacommons.org'
        _print_debug(1, f'Setting API server to {server}')
        dc.utils._API_ROOT = server
    if FLAGS.schema_mcf != '':
        load_schema_nodes(FLAGS.schema_mcf)
    process(FLAGS.input_mcf, FLAGS.output_mcf, FLAGS.regex)


if __name__ == '__main__':
    app.run(main)