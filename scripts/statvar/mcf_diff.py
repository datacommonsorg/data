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
''' Utility functions to compare MCF nodes.
Normalizes MCF nodes and generates diffs.

To compare two MCF files through command line, run the following:
  python3 mcf_diff.py --mcf1=<MCF file> --mcf2=<MCF file>
'''

import difflib
import logging
import os
import pprint
import sys

from absl import app
from absl import flags

_FLAGS = flags.FLAGS

flags.DEFINE_string('mcf1', '', 'MCF file with nodes')
flags.DEFINE_string('mcf2', '', 'MCF file with nodes')
flags.DEFINE_list(
    'ignore_property',
    [
        'description',
        'provenance',
        'memberOf',
        'name',
        'constraintProperties',
        'keyString',  # 'Node'
    ],
    'List of properties to be ignored in diffs.')
flags.DEFINE_bool(
    'ignore_dcid', False,
    'If set, ignores the dcid for nodes and instead uses fingerprint.')
flags.DEFINE_list(
    'ignore_nodes_with_pvs', [],
    'Ignore nodes containing any of the PVs in the comma separated list.')
flags.DEFINE_list('compare_dcids', [],
                  'List of dcids to be compared. Others are ignored.')
flags.DEFINE_bool('ignore_existing_nodes', False,
                  'Drop input MCF nodes that exist in the DataCommons API.')
flags.DEFINE_integer('dc_api_batch_size', 100,
                     'Number of dcids to lookup in a call to each API.')
flags.DEFINE_bool('show_diff_nodes_only', True, 'Output nodes with diff only.')
flags.DEFINE_string(
    'loglevel', 'DEBUG',
    'Level for logging messages. One of {DEBUG, INFO, WARNING, ERROR}')

# Allows the following module imports to work when running as a script
# relative to data/scripts/
#sys.path.append(os.path.sep.join([
#     '..' for x in filter(lambda x: x == os.path.sep,
#                              os.path.abspath(__file__).split('scripts/')[1])
#                              ]))

from mcf_file_util import load_mcf_nodes, normalize_mcf_node, normalize_pv, node_dict_to_text, get_node_dcid, strip_namespace


def add_counter(counters: dict, name: str, value: int = 1):
    '''Add a counter to the dict.'''
    counters[name] = counters.get(name, 0) + value


def print_counters(counters: dict):
    '''Print the counters.'''
    pp = pprint.PrettyPrinter(indent=4, stream=sys.stderr)
    pp.pprint(counters)


def get_diff_config() -> dict:
    '''Returns the config for MCF diff from flags.'''
    #logging.basicConfig(level=_FLAGS.loglevel.upper())
    logging.basicConfig(level='DEBUG',
                        handlers=[logging.StreamHandler(sys.stderr)])
    return {
        'ignore_dcid': _FLAGS.ignore_dcid,
        'ignore_property': _FLAGS.ignore_property,
        'compare_dcids': _FLAGS.compare_dcids,
        'ignore_existing_nodes': _FLAGS.ignore_existing_nodes,
        'dc_api_batch_size': _FLAGS.dc_api_batch_size,
        'show_diff_nodes_only': _FLAGS.show_diff_nodes_only,
        'ignore_nodes_with_pvs': _FLAGS.ignore_nodes_with_pvs,
    }


def diff_mcf_node_pvs(node1: dict,
                      node2: dict,
                      config: dict,
                      counters: dict = None) -> (bool, str):
    '''Compare PVs in two nodes and report differences in the counter.
    returns the lines with diff marked with '<' or '>' in the beginning.
    Returns a tuple of bool set to Trus if there is a diff and the diff string.'''
    if counters is None:
        counters = {}
    diff_lines = []
    dcid1 = get_node_dcid(node1)
    dcid2 = get_node_dcid(node2)

    # Remove any properties to be ignored.
    ignore_props = config.get('ignore_property', [])
    for p in ignore_props:
        if p in node1:
            node1.pop(p)
        if p in node2:
            node2.pop(p)

    # Normalize nodes and diff line by line.
    node1_str = node_dict_to_text(normalize_mcf_node(node1)).split('\n')
    node2_str = node_dict_to_text(normalize_mcf_node(node2)).split('\n')
    logging.debug(
        f'DEBUG: Comparing nodes:\n{node1_str}, \nNode2:{node2_str}\n')
    diff = difflib.ndiff(node1_str, node2_str)

    # Generate a diff string.
    diff_str = []
    has_diff = False
    for d in diff:
        diff_str.append(d)
        if d[0] == ' ':
            add_counter(counters, f'PVs matched', 1)
        elif d[0] == '-':
            has_diff = True
            add_counter(counters, f'missing pvs in mcf1', 1)
        elif d[0] == '+':
            has_diff = True
            add_counter(counters, f'missing pvs in mcf2', 1)
    if has_diff:
        if len(node1) > 0:
            if len(node2) > 0:
                add_counter(counters, f'nodes with diff', 1)
            else:
                add_counter(counters, f'nodes missing in mcf2', 1)
        else:
            add_counter(counters, f'nodes missing in mcf1', 1)
    else:
        add_counter(counters, f'nodes matched', 1)
    return has_diff, '\n'.join(diff_str)


def diff_mcf_nodes(nodes1: dict,
                   nodes2: dict,
                   config: dict = {},
                   counters: dict = None) -> str:
    '''Compare nodes across two dicts and report differences as a dict of counters.'''
    if counters is None:
        counters = {}
    diff_str = []
    for dcid1 in nodes1.keys():
        if dcid1 not in nodes2:
            add_counter(
                counters,
                f'dcid missing in nodes2:dcid={dcid1}, PVs={nodes1[dcid1]}', 1)
            add_counter(counters, f'dcid missing in nodes2', 1)

    # Compare PVs across all nodes.
    all_dcids = set(list(nodes1.keys()))
    all_dcids.update(list(nodes2.keys()))
    for dcid in all_dcids:
        (has_diff, node_diff) = diff_mcf_node_pvs(nodes1.get(dcid, {}),
                                                  nodes2.get(dcid, {}), config,
                                                  counters)
        if not config.get('show_diff_nodes_only', False) or has_diff:
            diff_str.append(node_diff)
            diff_str.append('\n')

    dcids1 = set(nodes1.keys())
    dcids2 = set(nodes2.keys())
    diff = dcids2.difference(dcids1)
    for dcid2 in diff:
        add_counter(
            counters,
            f'dcid missing in nodes1:dcid={dcid2}, PVs={nodes2[dcid2]}', 1)
        add_counter(counters, f'dcid missing in nodes1', 1)
    return ('\n'.join(diff_str))


def fingerprint_node(pvs: dict, ignore_props: set = {}) -> str:
    '''Returns a fingerprint of all PVs in the node.
    The fingerprint is a concatenated set of PVs sorted by the property.'''
    fp = []
    for p in sorted(pvs.keys()):
        if p not in ignore_props:
            fp.append(f'{p}:{pvs[p]}')
    return ';'.join(fp)


def fingerprint_mcf_nodes(nodes: dict, ignore_props: list = []) -> dict:
    '''Return a set of nodes with fingerprint as the key.'''
    fp_nodes = {}
    fp_ignore_props = set(['dcid', 'Node', 'value'])
    fp_ignore_props.update(ignore_props)
    for node, pvs in nodes.items():
        # Generate the fingerprint for the node with non-ignored PVs.
        fp_nodes[fingerprint_node(pvs, fp_ignore_props)] = nodes[node]
    return fp_nodes


def filter_nodes(nodes: dict, config: dict = {}) -> dict:
    '''Filter dictionary of Nodes to a subset of allowed dcids.'''
    allow_dcids = config.get('compare_dcids', None)
    # Normalize ignored PVs.
    ignored_pvs = set()
    ignored_pvs_list = config.get('ignore_nodes_with_pvs', None)
    if ignored_pvs_list:
        for pv in ignored_pvs_list:
            if isinstance(pv, str) and ':' in pv:
                prop, value = pv.split(':', 1)
                ignored_pvs.add(normalize_pv(prop, value))
    filtered_nodes = {}
    for k, v in nodes.items():
        # Drop nodes with dcid not in allowed list.
        if allow_dcids and strip_namespace(k) in allow_dcids:
            logging.debug(f'Dropping dcid not in compare_dcids: {k}, {v}')
            continue
        # Drop nodes containing any ignored property value.
        drop_node = False
        for prop, value in v.items():
            if prop and prop[0] != '#':
                if normalize_pv(prop, value) in ignored_pvs:
                    logging.debug(
                        f'Dropping dcid with ignored pv {prop}:{value}: {k}, {v}'
                    )
                    drop_node = True
                    break
        if not drop_node:
            filtered_nodes[k] = v
    return filtered_nodes


def diff_mcf_files(file1: str,
                   file2: str,
                   config: dict = {},
                   counters: dict = None) -> str:
    '''Compares MCF nodes in two files and returns the diffs.'''
    nodes1 = filter_nodes(load_mcf_nodes(file1), config)
    nodes2 = filter_nodes(load_mcf_nodes(file2), config)
    if config.get('ignore_dcid', False):
        # Generate a fingerprint of all nodes instead of dcid.
        ignore_props = config.get('ignore_property', [])
        nodes1 = fingerprint_mcf_nodes(nodes1, ignore_props)
        nodes2 = fingerprint_mcf_nodes(nodes2, ignore_props)

    logging.info(
        f'Comparing {len(nodes1)} nodes from {file1} with {len(nodes2)} nodes from {file2}'
    )
    return diff_mcf_nodes(nodes1, nodes2, config, counters)


def main(_):
    diff_counters = diff_mcf_files(_FLAGS.mcf1, _FLAGS.mcf2, get_diff_config())
    print_counters(diff_counters)


if __name__ == '__main__':
    app.run(main)
