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
''' Utility function to read/write MCF nodes in files.

Uses a dictionary to process nodes of the form:
{
  '<dcid>': OrderedDict( [
                '<property>': '<value>'
                ...
                ])
}
where
  <dcid> is the node dcid with the namespace prefix: 'dcid:'
  <property> is a property name
  <value> is a string with a single value or a comma seperated list of values.

  the property:values for a node are in the same order as in the input file.

  Comments in the file are also added as special properties:
  '# comment<N>' where N is the comment number within a node.

This can also be used as a commandline script to merge multiple MCF files into
a single MCF file with consolidated property:values for each node.

For example:
```
python3 mcf_file_util.py --input_mcf=test_data/*.mcf --output_mcf=/tmp/output.mcf
```
'''

import csv
import glob
import os
import re
import sys

from collections import OrderedDict
from absl import app
from absl import flags
from absl import logging
from typing import Union

_FLAGS = flags.FLAGS

flags.DEFINE_string('input_mcf', '', 'List of MCF files to load.')
flags.DEFINE_string('output_mcf', '', 'output MCF nodes loaded into file.')

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

import file_util

_DEFAULT_NODE_PVS = OrderedDict({
    'Node': '',
    'typeOf': '',
    'subClassOf': '',
    'name': '',
    'description': '',
    'populationType': '',
    'measuredProperty': '',
    'measurementQualifier': '',
    'statType': '',
    'measurementDenominator': '',
})


def add_namespace(value: str, namespace: str = 'dcid') -> str:
    '''Returns the value with a namespace prefix for references.
    Args:
      value: string to which namespace is to be added.
    Returns:
      value with the namespace prefix if the value is not a quoted string
      and doesn't have a namespace already.
      O/w return the value as is.

    Any sequence of letters followed by a ':' is treated as a namespace.
    Quoted strings are assumed to start with '"' and won't get a namespace.
    '''
    if value and isinstance(value, str):
        if value[0].isalpha() and value.find(':') < 0:
            return f'{namespace}:{value}'
    return value


def strip_namespace(value: str) -> str:
    '''Returns the value without the namespace prefix.
    Args:
      value: string from which the namespace prefix is to be removed.
    Returns:
      value without the namespace prefix if there was a namespace

    Any sequence of letters followed by a ':' is treated as a namespace.
    Quoted strings are assumed to start with '"' and won't be filtered.
    '''
    if value and isinstance(value, str):
        pos = 0
        len_value = len(value)
        while (pos < len_value):
            if not value[pos].isalpha():
                break
            pos += 1
        if pos < len_value and value[pos] == ':':
            return value[pos + 1:].strip()
    return value


def get_pv_from_line(line: str) -> (str, str):
    '''Returns a tuple of (property, value) from the line.
    Args:
      line: a string form an input file of the form <prop>:<value>.
    Returns:
      tuple: (property: str, value: str)
      removing leading/trailing whitespaces from the propety and value.
      quoted values will have the quote preserved.
      In case of a missing ':', the line is returned as value with empty property.
    '''
    pos = line.find(':')
    if pos < 0:
        return ('', line)
    prop = line[:pos].strip()
    value = line[pos + 1:].strip()
    return (prop, value)


def add_pv_to_node(prop: str, value: str, node: dict) -> dict:
    '''Add a property:value to the node dictionary.
       If the property exists, the value is added to the existing property with a comma.
    Args:
      prop: Property string
      value: Value string
      node: dictionary to which the property is to be added.
    Returns:
      dictionary of property values.
    '''
    if node is None:
        node = {}
    if prop in node:
        # Property already exists. Add value to a list if not present.
        if value and value not in node[prop]:
            node[prop] = f'{node[prop]},{value}'
    else:
        # Add a new property:value
        node[prop] = value
    return node


def add_comment_to_node(comment: str, node: dict) -> dict:
    '''Add a comment to the node. The comments are preserved in the order read.
    Args:
      comment: a comment string
      node: dictionary to whcih comment is to be added as a key.
    Returns:
      dictionary with the comment added.

    Comments are added as a property with a '#' prefix and index suffix,
    for example, '# comment1', '# comment2'.
    '''
    # Count the existing comments in the node.
    comments = [c for c in node.keys() if c and c[0] == '#']
    next_comment_index = len(comments) + 1
    # Add the new comment with the next index.
    node[f'# comment{next_comment_index}'] = comment
    return node


def get_node_dcid(pvs: dict) -> str:
    '''Returns the dcid of the node without the namespace prefix.
    Args:
      pvs: dictionary of property:value for the node.
    Returns:
      nodes dcid if one is set.
    dcid is taken from the following properties in order:
      'dcid'
      'Node'
    '''
    if not pvs:
        return ''
    dcid = pvs.get('Node', '')
    dcid = pvs.get('dcid', dcid)
    dcid = dcid.strip(' "')
    return strip_namespace(dcid)


def add_mcf_node(pvs: dict, nodes: dict) -> dict:
    '''Add a node with property values into the nodes dict
       If the node exists, the PVs are added to the existing node.'''
    if pvs is None or len(pvs) == 0:
        return
    dcid = add_namespace(get_node_dcid(pvs))
    if dcid == '':
        logging.warning(f'Ignoring node without a dcid: {pvs}')
    if dcid not in nodes:
        nodes[dcid] = {}
    node = nodes[dcid]
    for prop, value in pvs.items():
        add_pv_to_node(prop, value, node)
    return nodes


def load_mcf_nodes(filenames: str, nodes: dict = None) -> dict:
    '''Return a dict of nodes from the MCF file with the key as the dcid
     and a dict of property:value for each node.
    '''
    files = []
    file_names = filenames.split(',')
    for file in file_names:
        files.extend(glob.glob(file))
    if nodes is None:
        nodes = {}
    for file in files:
        if file:
            num_nodes = 0
            num_props = 0
            with file_util.FileIO(file, 'r') as input_f:
                pvs = {}
                for line in input_f:
                    line = line.strip()
                    if line == '':
                        add_mcf_node(pvs, nodes)
                        num_nodes += 1
                        pvs = {}
                    elif line[0] == '#':
                        add_comment_to_node(line, pvs)
                    else:
                        prop, value = get_pv_from_line(line)
                        add_pv_to_node(prop, value, pvs)
                        num_props += 1
                if pvs:
                    add_mcf_node(pvs, nodes)
                    num_nodes += 1
                logging.info(
                    f'Loaded {num_nodes} nodes with {num_props} properties from file {file}'
                )
    return nodes


def _pv_list_to_dict(pv_list: list) -> dict:
    '''Convert a list of property:value into a set of PVs.'''
    pvs = set()
    if pv_list:
        for pv in pv_list:
            if isinstance(pv, str):
                if ':' in pv:
                    prop, value = pv.split(':', 1)
                else:
                    prop, value = pv, ''
                prop = prop.strip()
                value = normalize_value(value)
                if prop not in pvs:
                    pvs[prop] = set()
                pvs[prop].add(value)
    return pvs


def _is_pv_in_dict(prop: str, value: str, pvs: dict) -> bool:
    '''Returns true if the property:value or propert is in the pvs dict.'''
    if not prop:
        return False
    prop = prop.strip()
    if value:
        value = normalize_value(value)
    if prop in pvs:
        if value and value in pvs[prop]:
            return True
        if '' in pvs[prop]:
            return True
    return False


def filter_mcf_nodes(nodes: dict,
                     allow_dcids: list = None,
                     allow_nodes_with_pv: list = None,
                     ignore_nodes_with_pv: list = None) -> dict:
    '''Filter dictionary of Nodes to a subset of allowed dcids.'''
    # Normalize ignored PVs.
    ignored_pvs = set()
    ignored_pvs = _pv_list_to_dict(ignore_nodes_with_pv)
    compared_pvs = _pv_list_to_dict(allow_nodes_with_pv)
    filtered_nodes = {}
    for k, v in nodes.items():
        # Drop nodes with dcid not in allowed list.
        if allow_dcids and strip_namespace(k) in allow_dcids:
            logging.debug(f'Dropping dcid not in compare_dcid: {k}, {v}')
            continue
        # Drop nodes containing any ignored property value.
        drop_node = False
        for prop, value in v.items():
            if prop and prop[0] != '#':
                if _is_pv_in_dict(prop, value, ignored_pvs):
                    logging.debug(
                        f'Dropping dcid with ignored pv {prop}:{value}: {k}, {v}'
                    )
                    drop_node = True
                    break
                if compared_pvs and not _is_pv_in_dict(prop, value,
                                                       compared_pvs):
                    logging.debug(
                        f'Dropping dcid without any compared pv {prop}:{value}: {k}, {v}'
                    )
                    drop_node = True
                    break
        if not drop_node:
            filtered_nodes[k] = v
    return filtered_nodes


def _get_prop_value_line(prop, value) -> str:
    '''Return a text line for a property and value.'''
    if isinstance(value, list):
        value = ','.join([add_namespace(x) for x in value])
    else:
        value = add_namespace(value)
    return f'{prop}: {value}'


def get_numeric_value(value: str,
                      decimal_char: str = '.',
                      separator_chars: str = ' ,') -> Union[int, float, None]:
    '''Returns the float value from string or None.'''
    if isinstance(value, int) or isinstance(value, float):
        return value
    if value and isinstance(value, str):
        try:
            normalized_value = value
            if (value[0].isdigit() or value[0] == '.' or value[0] == '-' or
                    value[0] == '+'):
                # Input looks like a number. Remove allowed extra characters.
                normalized_value = ''.join(
                    [c for c in normalized_value if c not in separator_chars])
                # Replace decimal characters with period '.'
                if decimal_char != '.':
                    normalized_value = '.'.join(
                        normalized_value.split(decimal_char))
                if value.count('.') > 1:
                    # Period may be used instead of commas. Remove it.
                    normalized_value = normalized_value.replace('.', '')
            if normalized_value.count('.') == 1:
                return float(normalized_value)
            return int(normalized_value)
        except ValueError:
            # Value is not a number. Ignore it.
            return None
    return None


def normalize_list(val: str) -> str:
    '''Normalize a comma separated list sorting items.'''
    if ',' in val:
        # Sort comma separated text values.
        value_list = [
            '"{}"'.format(v.strip()) for v in list(
                csv.reader(
                    [val], delimiter=',', quotechar='"', skipinitialspace=True))
            [0]
        ]
        values = sorted(value_list)
        return ','.join(values)
    else:
        return val


def normalize_range(val: str) -> str:
    '''Normalize a quantity range into [<N> <M> Unit].'''
    # Extract start, end and unit for the quantity range
    quantity_pat = r'\[ *(?P<unit1>[A-Z][A-Za-z0-9_/]*)? *(?P<start>[0-9\.]+|-)? *(?P<end>[0-9\.]+|-)? *(?P<unit2>[A-Z][A-Za-z0-9_]*)? *\]'
    matches = re.search(quantity_pat, val)
    if not matches:
        return val

    match_dict = matches.groupdict()
    if not match_dict:
        return val

    logging.debug(f'Matched range: {match_dict}')

    start = match_dict.get('start', '')
    end = match_dict.get('end', '')
    unit = match_dict.get('unit1', '')
    unit2 = match_dict.get('unit2', unit)
    if unit2:
        unit = unit2
    return f'[{start} {end} {unit}]'


def normalize_value(val) -> str:
    '''Normalize a property value adding a standard namespace prefix 'dcid:'.'''
    if val:
        if isinstance(val, str):
            val = val.strip()
            # TODO: handle a mix of quoted strings and dcids.
            if val[0] == '"':
                return normalize_list(val)
            elif ',' in val:
                # Sort comma separated dcids.
                values = sorted([normalize_value(x) for x in val.split(',')])
                return ','.join(values)
            elif val[0] == '[':
                return normalize_range(val)
            else:
                # Check if string is a numeric value.
                number = get_numeric_value(val)
                if number:
                    return normalize_value(number)
                # Normalize string with a standardized namespace prefix.
                return add_namespace(strip_namespace(val))
        elif isinstance(val, float):
            # Return a fixed precision float string.
            return f'{val}'
        elif isinstance(val, list):
            # Sort a list of values normalizing the namespace prefix.
            values = sorted([normalize_value(x) for x in val])
            return ','.join(values)
    return val


def normalize_pv(prop: str, value: str) -> str:
    '''Returns a normalized property:value string.'''
    return ':'.join([prop.strip(), normalize_value(value)])


def normalize_mcf_node(node: dict, ignore_comments: bool = True) -> dict:
    '''Returns a normalized MCF node with all PVs in alphabetical order,
    a common namespace of 'dcid' and comma separated lists also sorted.
    '''
    normal_node = OrderedDict({})
    props = list(node.keys())
    # Add the nodes dcid.
    dcid = get_node_dcid(node)
    if dcid:
        normal_node['Node'] = add_namespace(dcid)
    for p in ['Node', 'dcid']:
        if p in props:
            props.remove(p)

    # Add remaining properties in alphabetical order.
    for p in sorted(props):
        if p and p[0] == '#' and ignore_comments:
            # Ignore comments
            continue
        value = node[p]
        if not value:
            continue
        normal_node[p] = normalize_value(value)
    logging.log(2, f'Normalized {node} to {normal_node}')
    return normal_node


def node_dict_to_text(node: dict, default_pvs: dict = _DEFAULT_NODE_PVS) -> str:
    '''Convert a dictionary node of PVs into text.'''
    props = list(node.keys())
    pvs = []
    # Add any initial comments
    for prop in node.keys():
        if prop and prop[0] != '#':
            break
        pvs.append(node[prop])
        props.remove(prop)

    # Add default properties in order.
    for prop, default_value in default_pvs.items():
        value = node.get(prop, default_value)
        if value != '':
            pvs.append(_get_prop_value_line(prop, value))
        if prop in props:
            props.remove(prop)
    # Add remaining property values.
    for prop in props:
        if prop and prop[0] == '#':
            # Add comment as is in the same order.
            pvs.append(f'{prop}{node[prop]}')
            continue
        value = node.get(prop, '')
        if value != '':
            pvs.append(_get_prop_value_line(prop, value))
    return '\n'.join(pvs)


def write_mcf_nodes(node_dicts: list,
                    filename: str,
                    mode: str = 'w',
                    default_pvs: dict = _DEFAULT_NODE_PVS,
                    header: str = None,
                    ignore_comments: bool = True,
                    sort: bool = False):
    '''Write the nodes to an MCF file.'''
    if isinstance(node_dicts, dict):
        # Caller has a single dict of nodes. Create a list of dicts for it.
        node_dicts = [node_dicts]
    with file_util.FileIO(filename, mode) as output_f:
        if header is not None:
            output_f.write(header)
            output_f.write('\n')
        for nodes in node_dicts:
            node_keys = list(nodes.keys())
            if sort:
                node_keys = sorted(node_keys)
            for dcid in node_keys:
                node = nodes[dcid]
                if sort:
                    node = normalize_mcf_node(node, ignore_comments)
                pvs = node_dict_to_text(node, default_pvs)
                if len(pvs) > 0:
                    output_f.write(pvs)
                    output_f.write('\n\n')


def main(_):
    if not _FLAGS.input_mcf or not _FLAGS.output_mcf:
        print(
            f'Please provide input and output MCF files with --input_mcf and --output_mcf.'
        )
        return
    nodes = load_mcf_nodes(_FLAGS.input_mcf)
    write_mcf_nodes([nodes], _FLAGS.output_mcf)
    logging.info(
        f'{len(nodes)} MCF nodes from {_FLAGS.input_mcf} written to {_FLAGS.output_mcf}'
    )


if __name__ == '__main__':
    app.run(main)
