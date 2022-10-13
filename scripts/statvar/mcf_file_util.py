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
''' Utility function to read/write MCFs in files.'''

import csv
import glob
import logging
import os

from collections import OrderedDict


def add_namespace(value, namespace: str = 'dcid') -> str:
    '''Returns the value with a namespace prefix for references.'''
    if value and isinstance(value, str):
        if value[0].isalpha() and value.find(':') < 0:
            return f'{namespace}:{value}'
    return value


def strip_namespace(value: str) -> str:
    '''Returns the value without the namespace prefix.'''
    if value and isinstance(value, str):
        return value[value.find(':') + 1:].strip()
    return value


def get_pv_from_line(line: str):
    '''Returns a tuple of property, value from the line.
    '''
    pos = line.find(':')
    if pos < 0:
        return ('', line)
    prop = line[:pos].strip()
    value = line[pos + 1:].strip()
    return (prop, value)


def add_pv_to_node(prop: str, value: str, node: dict) -> dict:
    '''Add a property: value to the node.
       If the property exists, the value is added to the existing property with a comma.'''
    if node is None:
        node = {}
    if prop in node:
        if value != '' and value not in node[prop]:
            node[prop] = f'{node[prop]}, {value}'
    else:
        node[prop] = value
    return node


def add_comment_to_node(line: str, node: dict) -> dict:
    '''Add a comment to the node. The comments are preserved in the order read.'''
    comments = [c for c in node.keys() if c and c[0] == '#']
    next_comment_index = len(comments) + 1
    node[f'# comment{next_comment_index}'] = line


def get_node_dcid(pvs: dict) -> str:
    '''Returns the dcid of the node without the namespace prefix.'''
    if not pvs:
        return None
    dcid = pvs.get('Node', '')
    dcid = pvs.get('dcid', dcid)
    dcid = dcid.strip()
    if dcid and dcid[0] == '"':
        dcid = dcid[1:-1]
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
            with open(file, 'r') as input_f:
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


def get_prop_value_line(prop, value) -> str:
    '''Return a text line for a property and value.'''
    if isinstance(value, list):
        value = ','.join([add_namespace(x) for x in value])
    else:
        value = add_namespace(value)
    return f'{prop}: {value}'


def normalize_value(val) -> str:
    '''Normalize a property value adding a standard namespace prefix 'dcid:'.'''
    if val:
        if isinstance(val, str):
            # TODO: handle a mix of quoted strings and dcids.
            if val[0] == '"':
                if ',' in val:
                    # Sort comma separated text values.
                    value_list = [
                        '"{}"'.format(v.strip()) for v in list(
                            csv.reader([val],
                                       delimiter=',',
                                       quotechar='"',
                                       skipinitialspace=True))[0]
                    ]
                    values = sorted(value_list)
                    return ','.join(values)
                else:
                    return val
            elif ',' in val:
                # Sort comma separated dcids.
                values = sorted(
                    [add_namespace(strip_namespace(x)) for x in val.split(',')])
                return ','.join(values)
            else:
                return add_namespace(strip_namespace(val))
        if isinstance(val, list):
            # Sort a list of values normalizing the namespace prefix.
            values = sorted([normalize_value(x) for x in val])
            return ','.join(values)
    return val


def normalize_pv(prop: str, value: str) -> str:
    '''Returns a normalized property:value string.'''
    return ':'.join([prop.strip(), normalize_value(value)])


def normalize_mcf_node(node: dict) -> dict:
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
        if p and p[0] == '#':
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
            pvs.append(get_prop_value_line(prop, value))
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
            pvs.append(get_prop_value_line(prop, value))
    return '\n'.join(pvs)


def write_mcf_nodes(node_dicts: list,
                    filename: str,
                    mode: str = 'w',
                    default_pvs: dict = _DEFAULT_NODE_PVS,
                    ignore_props=None,
                    header: str = None,
                    config: dict = None):
    '''Write the nodes to an MCF file.'''
    if ignore_props is None:
        ignore_props = []
    with open(filename, mode) as output_f:
        if header is not None:
            output_f.write(header)
            output_f.write('\n')
        for nodes in node_dicts:
            for dcid in nodes.keys():
                node = nodes[dcid]
                pvs = node_dict_to_text(node, default_pvs)
                if len(pvs) > 0:
                    output_f.write(pvs)
                    output_f.write('\n\n')
