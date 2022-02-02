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

import os
from collections import OrderedDict

prefix_list = ['dcs', 'dcid', 'l', 'schema']

    # read mcf files
        # get list of files
        # file to list
        # update counters
    # add path
    # get list of files
    # get dict list
    # update dict list
    # check duplicates
    # remove duplicates
    # same dcid different statvar
    # different dcid same statvar

# TODO wrapper function to rename a list of properties
# if 'race' in cur_node:
    # cur_node = OrderedDict([('targetedRace', v) if k == 'race' else (k, v) for k, v in cur_node.items()])
# TODO wrapper function to rename value of a given property
# TODO wrapper function to rename namespace

def mcf_to_dict_list(mcf_str: str) -> list:
    # split by \n\n
    nodes_str_list = mcf_str.split('\n\n')
    # each node
    node_list = []
    dcid_list = []
    
    for node in nodes_str_list:
        node = node.strip()
        # check for comments
        node_str_list = node.split('\n')
        cur_node = OrderedDict()
        
        comment_ctr = 0
        is_first_prop = True
        # add each pv to ordered dict
        for pv_str in node_str_list:
            pv_str = pv_str.strip()
            if pv_str.startswith('#'):
                cur_node[f'__comment{comment_ctr}'] = pv_str
                comment_ctr += 1
            elif is_first_prop:
                is_first_prop = False
                if pv_str and not pv_str.startswith('Node: '):
                    raise ValueError(
                        'Each node must start with Node: <name>".')
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
                    # TODO detect colon within a str(for e.g. descriptionURL)
                    print(f"Warning - unexpected number of ':' found, {pv_str} will be ignored")
                # TODO (optional) if not prefix
                    # if not quantity range and p != 'dcid'
                        # prefix = 'dcs'
                cur_node[p] = {}
                cur_node[p]['value'] = v
                cur_node[p]['namespace'] = prefix
                
        node_list.append(cur_node)
        if 'dcid' in cur_node:
            dcid_list.append(cur_node['dcid']['value'])
        elif cur_node['Node']['namespace'] == 'dcid':
            dcid_list.append(cur_node['Node']['namespace'])
        else:
            dcid_list.append('')
    
    ret_dict = {}
    ret_dict['nodes'] = node_list
    ret_dict['dcid'] = dcid_list
    return ret_dict

def add_path(path: str, existing_dict = None) -> dict:
    if not existing_dict:
        existing_dict = {}
    # if is dir add **/*.mcf
    # get list of files
        # to list and store in dict
        # warn reopen
    return existing_dict

# TODO get dcid list from list of dict
# TODO get dcid list subset of key values
# TODO list dupe
# TODO de dupe

# TODO same dcid/node check

def mcf_file_to_dict_list(mcf_file_path: str) -> list:
    mcf_file_path = os.path.expanduser(mcf_file_path)
    # read all
    with open(mcf_file_path, 'r') as fp:
        mcf_str = fp.read().strip()
    
    return mcf_to_dict_list(mcf_str)

def dict_list_to_mcf(dict_list:list, sort_keys=False) -> str:
    ret_str = ''
    for _node in dict_list:
        cur_node = _node.copy()
        # TODO other validations if required
        if 'Node' not in cur_node:
            raise ValueError(
                'Each node must have Node: <name>".')
        # TODO preserve comments
        if '__comment' in cur_node:
            ret_str += cur_node['__comment']
        cur_node.pop('__comment', None)
        # TODO add comments till node
        # TODO add inline and end comments
        # Keep Node: first
        ret_str += f"{'Node'}: {cur_node['Node']['namespace']+':' if cur_node['Node']['namespace'] else ''}{cur_node['Node']['value']}"
        ret_str += '\n'
        cur_node.pop('Node', None)
        
        prop_list = list(cur_node.keys())
        # sort keys if flag raised
        if sort_keys:
            prop_list = sorted(prop_list)
        for prop in prop_list:
            ret_str += f"{prop}: {cur_node[prop]['namespace']+':' if cur_node[prop]['namespace'] else ''}{cur_node[prop]['value']}"
            ret_str += '\n'
        ret_str += '\n'
    return ret_str

def dict_list_to_mcf_file(dict_list:list, mcf_file_path: str, sort_keys=False):
    mcf_file_path = os.path.expanduser(mcf_file_path)
    if os.path.dirname(mcf_file_path):
        os.makedirs(os.path.dirname(mcf_file_path), exist_ok=True)
    with open(mcf_file_path, 'w') as fp:
        fp.write(dict_list_to_mcf(dict_list, sort_keys))

