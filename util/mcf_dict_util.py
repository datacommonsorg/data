# Copyright 2020 Google LLC
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
"""Utility function to read, edit and write MCF files.
MCF files are read into dict like objects which can be easily modified and written back.
The format of dict would be as follows:
{
    'p1': {
        'value': '<value of the prop>',
        'namespace': '<namespace of the value>'
    },
    'p2': {
        'value': '<value of the prop>',
        'namespace': '<namespace of the value>',
        (present only when [X Y ..] like complex values are present)
        'complexValue': [
            'v1',
            'v2'
            ..
        ]
    }
    ...
}
Functions are provided to read or write single/multiple files.
When multiple files are read, a dict object is created with a list similar to
    above described dict like objects corresponding to each file.
Functions to edit mcf files include:
- Change property name.
- Change value of given property.
- Change namespace.
- Check existence of dcids in DC.
- Check existence of dcid in other set of nodes.
- Drop a list of nodes with given list dcid.

Caveats:
- Text values with ':' within them, eg: prop: "my value : with colon" 
    would not be easily accessible in dict form. It would be treated as multiple value.
- All comments are moved to the top of the node if sort_keys option is set with write to mcf.
- Currently cannot handle multiple instances of same property within a node.
- Incomplete handling of multiple values assigned to properties.
- Extra empty lines would be dropped
"""

import ast
import glob
import logging
import os
import re
import json
from sys import path
import requests
from typing import Dict, Optional, Union
from collections import OrderedDict

_MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
path.insert(1, os.path.join(_MODULE_DIR, '../'))

from dc_api_wrapper import dc_api_is_defined_dcid

PREFIX_LIST = ['dcs', 'dcid', 'l', 'schema']


def mcf_to_dict_list(mcf_str: str) -> list:
    """Converts MCF file string to a list of OrderedDict objects.

    Args:
        mcf_str: String read from MCF file.
        
    Returns:
        List of OrderedDict objects where each object represents a node in the MCF file.
    """
    # TODO preserve empty lines if required
    # split by \n\n
    nodes_str_list = mcf_str.split('\n\n')
    # each node
    node_list = []

    for node in nodes_str_list:
        node = node.strip()
        # check for comments
        node_str_list = node.split('\n')
        cur_node = OrderedDict()
        comment_ctr = 0
        is_first_prop = True
        # add each pv to ordered dict
        for pv_str in node_str_list:
            # TODO handle multiple occurrences of same property within a node
            pv_str = pv_str.strip()
            if pv_str.startswith('#'):
                cur_node[f'__comment{comment_ctr}'] = pv_str
                comment_ctr += 1
            elif is_first_prop:
                is_first_prop = False
                if pv_str and not pv_str.startswith('Node: '):
                    raise ValueError(
                        f'Missing "Node: <name>" in MCF node {node}')
            if pv_str and not pv_str.startswith('#'):
                # find p, prefix, v
                pv = pv_str.split(':')
                if pv_str.count(':') == 1:
                    p = pv[0].strip()
                    prefix = ''
                    v = pv[1].strip()
                elif pv_str.count(':') == 2:
                    p = pv[0].strip()
                    prefix = pv[1].strip()
                    v = pv[2].strip()
                else:
                    p = pv[0].strip()
                    prefix = pv[1].strip()
                    v = ':'.join(pv[2:]).strip()
                    # TODO detect colon within a str(for e.g. descriptionURL)
                    logging.warning(
                        "Warning - unexpected number of ':' found in %s",
                        pv_str)

                cur_node[p] = {}
                cur_node[p]['value'] = v
                if v.startswith('[') and v.endswith(']'):
                    cur_node[p]['complexValue'] = re.sub(' +', ' ',
                                                         v)[1:-1].split(' ')
                if v.count(':') > 0 and ',' in v:
                    # TODO better handling of multiple values
                    cur_node[p]['multiple_values'] = []
                    vals = v.split(',')
                    for cur_v in vals:
                        temp_dict = {}
                        if ':' in cur_v:
                            temp_dict['namespace'] = cur_v[:cur_v.
                                                           index(':')].strip()
                            temp_dict['value'] = cur_v[cur_v.index(':') +
                                                       1:].strip()
                        else:
                            temp_dict['namespace'] = ''
                            temp_dict['value'] = cur_v
                cur_node[p]['namespace'] = prefix
        node_list.append(cur_node)
    return node_list


def mcf_file_to_dict_list(mcf_file_path: str) -> list:
    """Convets MCF file to a list of OrderedDict objects.

    Args:
        mcf_file_path: Path of the MCF file.
        
    Returns:
        List of OrderedDict objects where each object represents a node in the MCF file.
    """
    mcf_file_path = os.path.expanduser(mcf_file_path)
    # read the entire file
    with open(mcf_file_path, 'r') as fp:
        mcf_str = fp.read().strip()

    return mcf_to_dict_list(mcf_str)


def mcf_dict_rename_prop(node_dict: Union[dict, OrderedDict], old_prop: str,
                         new_prop: str) -> Union[dict, OrderedDict]:
    """Helper function to rename a property of the Node.

    Args:
        node_dict: OrderedDict or Dict object representing a node in MCF file.
        old_prop: Name of the property to to be replaced.
        new_prop: New name of the property.
        
    Returns:
        OrderedDict or Dict object representing a node in the MCF file.
    """
    if old_prop in node_dict:
        new_tuples = [(new_prop, v) if k == old_prop else (k, v)
                      for k, v in node_dict.items()]
        if type(node_dict) == type(OrderedDict()):
            return OrderedDict(new_tuples)
        else:
            return Dict(new_tuples)
    else:
        return node_dict


def mcf_dict_rename_prop_value(node_dict: Union[dict, OrderedDict], prop: str,
                               old_val: str,
                               new_val: str) -> Union[dict, OrderedDict]:
    """Helper function to rename a value of a given property of the Node.

    Args:
        node_dict: OrderedDict or Dict object representing a node in MCF file.
        prop: Name of the property whose value needs to to be replaced.
        old_val: Name of the value to be replaced.
        new_val: New name of the value.
        
    Returns:
        OrderedDict or Dict object representing a node in the MCF file.
    """
    if prop in node_dict:
        for k, v in node_dict.items():
            if k == prop and v['value'] == old_val:
                v['value'] = new_val
    return node_dict


# wrapper function to rename namespace
def mcf_dict_rename_namespace(node_dict: Union[dict, OrderedDict], old_ns: str,
                              new_ns: str) -> Union[dict, OrderedDict]:
    """Helper function to rename namespace of the Node.

    Args:
        node_dict: OrderedDict or Dict object representing a node in MCF file.
        old_ns: Name of the namespace to be replaced.
        new_ns: New name of the namespace.
        
    Returns:
        OrderedDict or Dict object representing a node in the MCF file.
    """
    for k, v in node_dict.items():
        if not (k == 'Node' and v['namespace'] == 'dcid'):
            if v['namespace'] == old_ns:
                v['namespace'] = new_ns
    return node_dict


def get_dcid_node(node_dict: Union[dict, OrderedDict]) -> str:
    """Finds the dcid of the given Node.

    Args:
        node_dict: OrderedDict or Dict object representing a node in MCF file.
        
    Returns:
        The dcid of the given Node, empty String if no dcid is found
    """
    if 'Node' in node_dict and node_dict['Node']['namespace'] == 'dcid':
        return node_dict['Node']['value']
    elif 'dcid' in node_dict:
        return node_dict['dcid']['value']
    else:
        return ''


# get dcid list from list of dict
def get_dcids_node_list(node_list: list) -> list:
    """Fetches the list of dcids for given list of nodes.

    Args:
        node_list: List of OrderedDict or Dict objects representing a node in MCF file.
        
    Returns:
        The List dcids of the nodes present in the input list.
    """
    ret_list = []
    for node_dict in node_list:
        s = get_dcid_node(node_dict)
        if s:
            ret_list.append(s)
    return ret_list


# get dcid list subset of key values
def get_dcids_prop_list(node_list: list, property_list: list) -> list:
    """Fetches the list of dcids for given list of nodes and all the listed properties.

    Args:
        node_list: List of OrderedDict or Dict objects representing a node in MCF file.
        prop_list: List of properties to filter the nodes.
        
    Returns:
        The List dcids of the nodes that have all the properties from the input list.
    """
    ret_list = []
    for node_dict in node_list:
        is_match = True
        for prop in property_list:
            if prop not in node_dict:
                is_match = False
        if is_match:
            s = get_dcid_node(node_dict)
            if s:
                ret_list.append(s)
    return ret_list


def node_list_check_existence_dc(node_list: list) -> dict:
    """Checks the existence of dcid of each node in DC.

    Args:
        node_list: List of OrderedDict or Dict objects representing a node in MCF file.
        
    Returns:
        Dict object with dcids as key values and boolean values signifying existence as values.
    """
    dcid_list = get_dcids_node_list(node_list)
    return dc_api_is_defined_dcid(dcid_list)


def node_list_check_existence_node_list(node_list: list,
                                        master_list: list) -> dict:
    """Checks the existence of dcid of each node in another list of nodes.

    Args:
        node_list: List of OrderedDict or Dict objects representing a node in MCF file.
        master_list: List of OrderedDict or Dict objects representing a node in MCF file to compare against.
        
    Returns:
        Dict object with dcids as key values and boolean values signifying existence as values.
    """
    ret_dict = {}
    dcid_list = get_dcids_node_list(node_list)
    master_dcid_list = get_dcids_node_list(master_list)
    for dcid in dcid_list:
        if dcid in master_dcid_list:
            ret_dict[dcid] = True
        else:
            ret_dict[dcid] = False
    return ret_dict


# drop dcid list
def drop_nodes(node_list: list, dcid_list: list) -> list:
    """Drops the node from list of nodes if it's dcid is present in the dcid list.

    Args:
        node_list: List of OrderedDict or Dict objects representing a node in MCF file.
        dcid_list: List of dcids to be dropped from the list.
        
    Returns:
        List of OrderedDict or Dict objects representing a node in MCF file after dropping.
    """
    ret_list = []
    for node_dict in node_list:
        if not get_dcid_node(node_dict) in dcid_list:
            ret_list.append(node_dict.copy())
    return ret_list


def load_mcf_dicts(new_path: str,
                   existing_dict: Optional[dict] = None,
                   reopen: bool = False) -> dict:
    """Opens a set of files specified by `new_path` expression to create a list of nodes for each file.

    Args:
        new_path: Glob like path to open a set of files and create a list of node for each file.
        existing_dict: (Optional) dict returned from previous call to add more files to same dict object.
        reopen: Boolean value to skip opening files already present in the dictionary to prevent overwrites.
        
    Returns:
        A dictionary with filenames as key and a list of OrderedDict objects where each object 
            represents a node in the MCF file as value.
    """
    if not existing_dict:
        existing_dict = {}

    new_path = os.path.expanduser(new_path)
    # if is dir add **/*.mcf
    if os.path.isdir(new_path):
        new_path = os.path.join(new_path, '**/*.mcf')

    matching_files = glob.glob(new_path, recursive=True)
    for cur_file in matching_files:
        # set of files
        logging.info('Reading file %s', cur_file)
        if cur_file not in existing_dict or reopen:
            existing_dict[cur_file] = mcf_file_to_dict_list(cur_file)

    return existing_dict


def dict_list_to_mcf_str(node_list: list,
                         sort_keys: bool = False,
                         regen_complex_vals: bool = False) -> str:
    """Creates a string (which could be written to a file) from list of Dict like object representation of nodes.

    Args:
        node_list: List of OrderedDict or Dict objects representing a node in MCF file.
        sort_keys: Boolean value to sort the properties before appending the node to the string.
                    NOTE: This keeps Node on the top and all inline comments would be moved around.
        regen_complex_vals: Boolean value to regenrate the value string of the property from the list 
                                of complex value representation.
        
    Returns:
        String representation of the list of nodes.
    """
    ret_str = ''
    for _node in node_list:
        cur_node = _node.copy()

        is_comment_block = True
        for prop in cur_node:
            if not prop.startswith('__comment'):
                is_comment_block = False
        # TODO other validations if required
        if not is_comment_block:
            if 'Node' not in cur_node:
                raise ValueError('Each node must have Node: <name>".')

        # preserve comments
        if '__comment' in cur_node:
            ret_str += cur_node['__comment']
        cur_node.pop('__comment', None)
        # add comments till node
        prop_list = list(cur_node.keys())
        i = 0
        while i < len(prop_list) and prop_list[i].startswith('__comment'):
            ret_str += cur_node[prop_list[i]]
            ret_str += '\n'
            cur_node.pop(prop_list[i], None)
            i += 1

        if not is_comment_block:
            # Keep Node: first
            namespace = cur_node['Node'].get('namespace', '')
            if namespace:
                namespace += ':'
            ret_str += f"Node: {namespace}{cur_node['Node']['value']}"
            ret_str += '\n'
            cur_node.pop('Node', None)

        prop_list = list(cur_node.keys())
        # sort keys if flag raised
        if sort_keys:
            prop_list = sorted(prop_list)
        for prop in prop_list:
            if prop.startswith('__comment'):
                ret_str += cur_node[prop]
            else:
                if 'complexValue' in cur_node[prop] and regen_complex_vals:
                    cur_node[prop][
                        'value'] = f"[{' '.join(cur_node[prop]['complexValue'])}]"
                ret_str += f"{prop}: {cur_node[prop]['namespace']+':' if cur_node[prop]['namespace'] else ''}{cur_node[prop]['value']}"
            ret_str += '\n'
        ret_str += '\n'
    # return ''.join(ret_str.rsplit('\n', 1))
    return ret_str


def dict_list_to_mcf_file(dict_list: list,
                          mcf_file_path: str,
                          sort_keys=False,
                          regen_complex_values: bool = False):
    """Write list of Dict like object representation of nodes to an MCF file.

    Args:
        dict_list: List of OrderedDict or Dict objects representing a node in MCF file.
        mcf_file_path: Path of the output MCF file.
        sort_keys: Boolean value to sort the properties before appending the node to the string.
                    NOTE: This keeps Node on the top and all inline comments would be moved around.
        regen_complex_vals: Boolean value to regenrate the value string of the property from the list 
                                of complex value representation.
    """
    mcf_file_path = os.path.expanduser(mcf_file_path)
    if os.path.dirname(mcf_file_path):
        os.makedirs(os.path.dirname(mcf_file_path), exist_ok=True)
    logging.info('Writing file %s', mcf_file_path)
    with open(mcf_file_path, 'w') as fp:
        fp.write(
            dict_list_to_mcf_str(dict_list,
                                 sort_keys=sort_keys,
                                 regen_complex_vals=regen_complex_values))


def write_to_files(file_dict: dict,
                   sort_keys: bool = False,
                   regen_complex_vals: bool = False):
    """Write a set of list of Dict like object representation of nodes to an MCF file.

    Args:
        file_dict: Dict with output filename as the key and list of OrderedDict 
                        or Dict objects representing a node in MCF file as value.
        sort_keys: Boolean value to sort the properties before appending the node to the string.
                    NOTE: This keeps Node on the top and all inline comments would be moved around.
        regen_complex_vals: Boolean value to regenrate the value string of the property from the list 
                                of complex value representation.
    """
    for cur_file in file_dict:
        dict_list_to_mcf_file(file_dict[cur_file],
                              cur_file,
                              sort_keys=sort_keys,
                              regen_complex_values=regen_complex_vals)
