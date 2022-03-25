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

import os

from collections import OrderedDict


def get_pv_from_line(line: str):
    '''Returns a tuple of property, value from the line.'''
    pos = line.find(':')
    if pos < 0:
        return ('', line)
    prop = line[:pos].strip()
    value = line[pos + 1:].strip()
    return (prop, value)


def add_pv_to_node(prop: str, value: str, node: dict) -> dict:
    '''Add a propeorty: value to the node.
       If the property exisit, the value is added to the existing property with a comma.'''
    if node is None:
        node = {}
    if prop in node:
        if value != '' and value not in node[prop]:
            node[prop] = f'{node[prop]}, {value}'
    else:
        node[prop] = value
    return node


def add_mcf_node(pvs: dict, nodes: dict) -> dict:
    '''Add a node with propoerty values into the nodex dict
       If the node exists, the PVs are added to the existing node.'''
    if pvs is None or len(pvs) == 0:
        return
    dcid = pvs.get('dcid', '')
    dcid = pvs.get('Node', dcid)
    if dcid == '':
        print(f'WARNING: Ignoring node without a dcid: {pvs}')
    if dcid not in nodes:
        nodes[dcid] = {}
    node = nodes[dcid]
    for prop, value in pvs.items():
        add_pv_to_node(prop, value, node)
    return nodes


def load_mcf_nodes(filenames: str, nodes: dict = None) -> dict:
    '''Return a dict of nodes from the MCF file with the key as the dcid
     and a dict of propoerty:value for each node.
  '''
    files = filenames.split(',')
    if nodes is None:
        nodes = {}
    for file in files:
        with open(file, 'r') as input_f:
            pvs = {}
            for line in input_f:
                line = line.strip()
                if line == '':
                    add_mcf_node(pvs, nodes)
                    pvs = {}
                elif line[0] != '#':
                    prop, value = get_pv_from_line(line)
                    add_pv_to_node(prop, value, pvs)
    return nodes


_DEFAULT_NODE_PVS = OrderedDict({
    'Node': '',
    'typeOf': '',
    'subClassOf': '',
    'name': '',
    'description': '',
    'populationType': '',
    'measuredProperty': '',
    'statType': '',
})

def add_namespace(value, namespace: str = 'dcid') -> str:
   '''Returns the value with a namespace prefix for references.'''
   if isinstance(value, str):
       if value[0].isalpha() and value.find(':') < 0:
           return f'{namespace}:{value}'
   return f'{value}'

def get_prop_value_line(prop, value) -> str:
   '''Return a text line for a propoerty and value.'''
   if isinstance(value, list):
       value = ','.join([add_namespace(x) for x in value])
   else:
       value = add_namespace(value)
   return f'{prop}: {value}'
   

def write_mcf_nodes(node_dicts: list,
                    filename: str,
                    mode: str = 'w',
                    default_pvs: dict = _DEFAULT_NODE_PVS,
                    ignore_props=None,
                    header: str = None):
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
                props = list(nodes[dcid].keys())
                pvs = []
                # Add default properties in order.
                for prop in default_pvs:
                    value = node.get(prop, default_pvs[prop])
                    if value != '':
                        pvs.append(get_prop_value_line(prop, value))
                    if prop in props:
                        props.remove(prop)
                # Add remaining property values.
                for prop in props:
                    value = node.get(prop, '')
                    if value != '':
                        pvs.append(get_prop_value_line(prop, value))

                if len(pvs) > 0:
                    output_f.write('\n'.join(pvs))
                    output_f.write('\n\n')
