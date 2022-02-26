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

import ast
import copy
import glob
import os
import re
import json
import requests
from typing import Dict, Optional, Union
from collections import OrderedDict

prefix_list = ['dcs', 'dcid', 'l', 'schema']


def request_post_json(url: str, data_: dict) -> dict:
  """Get JSON object version of reponse to POST request to given URL.

  Args:
    url: URL to make the POST request.
    data_: payload for the POST request

  Returns:
    JSON decoded response from the POST call.
      Empty dict is returned in case the call fails.
  """
  headers = {'Content-Type': 'application/json'}
  req = requests.post(url, data=json.dumps(data_), headers=headers)
  print(req.request.url)
  
  if req.status_code == requests.codes.ok:
    response_data = req.json()
  else:
    response_data = {'http_err_code': req.status_code}
    print('HTTP status code: ' + str(req.status_code))
  return response_data

def dc_check_existence(dcid_list: list, use_autopush: bool = True, max_items: int = 450) -> dict:
    data_ = {}
    ret_dict = {}
    if use_autopush:
        url_prefix = 'autopush.'
    else:
        url_prefix = ''
    
    chunk_size = max_items
    dcid_list_chunked = [dcid_list[i:i + chunk_size] for i in range(0, len(dcid_list), chunk_size)]
    for dcid_chunk in dcid_list_chunked:
      data_["dcids"] = dcid_chunk
      req = request_post_json(f'https://{url_prefix}api.datacommons.org/node/property-labels', data_)
      resp_dicts = req['payload']
      resp_dicts = ast.literal_eval(resp_dicts)
      for cur_dcid in resp_dicts:
        if not resp_dicts[cur_dcid]['inLabels'] and not resp_dicts[cur_dcid]['outLabels']:
          ret_dict[cur_dcid] = False
        else:
          ret_dict[cur_dcid] = True
    
    return ret_dict

def mcf_to_dict_list(mcf_str: str) -> list:
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
                    p = pv[0].strip()
                    prefix = pv[1].strip()
                    v = ':'.join(pv[1:]).strip()
                    # TODO detect colon within a str(for e.g. descriptionURL)
                    print(f"Warning - unexpected number of ':' found in {pv_str}")

                # TODO (optional) if not prefix
                    # if not complex value and p != 'dcid'
                        # prefix = 'dcs'
                cur_node[p] = {}
                cur_node[p]['value'] = v
                if v.startswith('[') and v.endswith(']'):
                    cur_node[p]['complexValue'] = re.sub(' +', ' ', v)[1:-1].split(' ')
                if v.count(':') > 0 and ',' in v:
                    cur_node[p]['multiple_values'] = []
                    vals = v.split(',')
                    for cur_v in vals:
                        temp_dict = {}
                        if ':' in cur_v:
                            temp_dict['prefix'] = cur_v[:cur_v.index(':')].strip()
                            temp_dict['value'] = cur_v[cur_v.index(':')+1:].strip()
                        else:
                            temp_dict['prefix'] = ''
                            temp_dict['value'] = cur_v
                cur_node[p]['namespace'] = prefix
        node_list.append(cur_node)
    return node_list

def mcf_file_to_dict_list(mcf_file_path: str) -> list:
    mcf_file_path = os.path.expanduser(mcf_file_path)
    # read the entire file
    with open(mcf_file_path, 'r') as fp:
        mcf_str = fp.read().strip()
    
    return mcf_to_dict_list(mcf_str)

# wrapper function to rename a list of properties
def mcf_dict_rename_prop(node_dict: Union[dict, OrderedDict], old_prop: str, new_prop: str) -> Union[dict, OrderedDict]:
    if old_prop in node_dict:
        new_tuples = [(new_prop, v) if k == old_prop else (k, v) for k, v in node_dict.items()]
        if type(node_dict) == type(OrderedDict()):
            return OrderedDict(new_tuples)
        else:
            return Dict(new_tuples)
    else:
        return node_dict

# wrapper function to rename value of a given property
def mcf_dict_rename_prop_value(node_dict: Union[dict, OrderedDict], prop: str, old_val: str, new_val: str) -> Union[dict, OrderedDict]:
    if prop in node_dict:
        for k, v in node_dict.items():
            if k == prop and v['value'] == old_val:
                v['value'] = new_val
    return node_dict

# wrapper function to rename namespace
def mcf_dict_rename_namespace(node_dict: Union[dict, OrderedDict], old_ns: str, new_ns: str) -> Union[dict, OrderedDict]:
    for k, v in node_dict.items():
        if not (k == 'Node' and v['namespace'] == 'dcid'):
            if v['namespace'] == old_ns:
                v['namespace'] = new_ns

def get_dcid_node(node_dict: Union[dict, OrderedDict]) -> str:
    if 'Node' in node_dict and node_dict['Node']['namespace'] == 'dcid':
            return node_dict['Node']['value']
    elif 'dcid' in node_dict:
        return node_dict['dcid']['value']
    else:
        return ''

# get dcid list from list of dict
def get_dcids_node_list(node_list: list) -> list:
    ret_list = []
    for node_dict in node_list:
        s = get_dcid_node(node_dict)
        if s:
            ret_list.append(s)
    return ret_list

# get dcid list subset of key values
def get_dcids_prop_list(node_list: list, prop_list: list) -> list:
    ret_list = []
    for node_dict in node_list:
        is_match = True
        for prop in prop_list:
            if prop not in node_dict:
                is_match = False
        if is_match:
            s = get_dcid_node(node_dict)
            if s:
                ret_list.append(s)
    return ret_list

# list dupe
def node_list_check_existence_dc(node_list: list) -> dict:
    dcid_list = get_dcids_node_list(node_list)
    return dc_check_existence(dcid_list)

def node_list_check_existence_node_list(node_list: list, master_list: list) -> dict:
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
def drop_nodes(node_list: list, dcid_list: list) -> dict:
    ret_list = []
    for node_dict in node_list:
        if not get_dcid_node(node_dict) in dcid_list:
            ret_list.append(node_dict)
    return ret_list

def add_path_exp_mcf_dicts(new_path: str, existing_dict:Optional[dict] = None, reopen: bool = False) -> dict:
    if not existing_dict:
        existing_dict = {}
    
    new_path = os.path.expanduser(new_path)
    # if is dir add **/*.mcf
    if os.path.isdir(new_path):
        new_path = os.path.join(new_path, '**/*.mcf')
    
    matching_files = glob.glob(new_path, recursive=True)
    for cur_file in matching_files:
        # set of files
        print(cur_file)
        if cur_file not in existing_dict or reopen:
            existing_dict[cur_file] = mcf_file_to_dict_list(cur_file)
    
    return existing_dict

def dict_list_to_mcf_str(dict_list:list, sort_keys: bool = False, regen_complex_vals: bool = False) -> str:
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
        # add comments till node
        prop_list = list(cur_node.keys())
        i = 0
        while prop_list[i].startswith('__comment'):
            ret_str += cur_node[prop_list[i]]
            cur_node.pop(prop_list[i], None)
            i += 1
        # Keep Node: first
        ret_str += f"{'Node'}: {cur_node['Node']['namespace']+':' if cur_node['Node']['namespace'] else ''}{cur_node['Node']['value']}"
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
                    cur_node[prop]['value'] = f"[{' '.join(cur_node[prop]['complexValue'])}]"
                ret_str += f"{prop}: {cur_node[prop]['namespace']+':' if cur_node[prop]['namespace'] else ''}{cur_node[prop]['value']}"
            ret_str += '\n'
        ret_str += '\n'
    return ret_str

def dict_list_to_mcf_file(dict_list:list, mcf_file_path: str, sort_keys=False, regen_complex_vals: bool = False):
    mcf_file_path = os.path.expanduser(mcf_file_path)
    if os.path.dirname(mcf_file_path):
        os.makedirs(os.path.dirname(mcf_file_path), exist_ok=True)
    with open(mcf_file_path, 'w') as fp:
        fp.write(dict_list_to_mcf_str(dict_list, sort_keys=sort_keys, regen_complex_vals=regen_complex_vals))

def write_to_files(file_dict: dict, sort_keys: bool = False, regen_complex_vals: bool = False):
    for cur_file in file_dict:
        dict_list_to_mcf_file(file_dict[cur_file], cur_file, sort_keys=sort_keys, regen_complex_vals=regen_complex_vals)