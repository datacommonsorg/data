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
''' Utility function to filter MCF nodes.'''

from absl import logging
from collections import OrderedDict
from itertools import islice

import datacommons as dc
import os
import requests_cache
import sys
import time
import urllib

from absl import app
from absl import flags

_FLAGS = flags.FLAGS

flags.DEFINE_string('input_mcf', '',
                    'Comma seperated list of MCF input files with nodes')
flags.DEFINE_string(
    'ignore_mcf', '',
    'Comma separated list of MCF files with nodes to be dropped from output')
flags.DEFINE_string('output_mcf', '', 'MCF output file with nodes')

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)

from mcf_file_util import load_mcf_nodes, add_namespace, strip_namespace, write_mcf_nodes
from mcf_diff import diff_mcf_node_pvs, add_counter, print_counters, get_diff_config


def drop_mcf_nodes(input_nodes: dict,
                   ignore_nodes: dict,
                   config: dict,
                   counters: dict = {}) -> dict:
    '''Function to filter MCF nodes removing any nodes in ignore_nodes.'''
    output_nodes = OrderedDict()
    logging.info(
        f'Filtering {len(input_nodes)} nodes with {len(ignore_nodes)} ignored nodes'
    )
    for dcid, pvs in input_nodes.items():
        # Check if dcid exists in ignore nodes and is equivalent.
        ignore_pvs = ignore_nodes.get(add_namespace(dcid), None)
        if ignore_pvs:
            # Compare if nodes have any difference in PVs.
            node_diff_counter = {}
            has_diff, diff_str = diff_mcf_node_pvs(node1=pvs,
                                                   node2=ignore_pvs,
                                                   config=config,
                                                   counters=node_diff_counter)
            if has_diff:
                logging.debug(
                    f'Diff in ignored Node: {dcid}, diff:\n{diff_str}\n')
                add_counter(counters, f'error-input-ignore-node-diff', 1)
            else:
                logging.debug(f'Ignored Node: {dcid},\n{pvs}\n')
                add_counter(counters, f'input-nodes-ignored', 1)
        else:
            output_nodes[dcid] = pvs
    return output_nodes


def filter_mcf_file(input_mcf_files: str,
                    ignore_mcf_files: str,
                    config: dict,
                    output_mcf: str,
                    counters: dict = {}) -> dict:
    '''Function to filter MCF nodes in input and write to the output file.'''
    # Load nodes from MCF files.
    input_nodes = load_mcf_nodes(input_mcf_files)
    ignore_nodes = load_mcf_nodes(ignore_mcf_files)
    add_counter(counters, 'input-nodes', len(input_nodes))
    add_counter(counters, 'ignore-nodes-loaded', len(input_nodes))

    # Remove any ignored nodes from input.
    output_nodes = drop_mcf_nodes(input_nodes, ignore_nodes, config, counters)

    # Remove any predefined nodes.
    if config.get('ignore_existing_nodes', False):
        existing_nodes = dc_api_get_node_property_values(
            list(output_nodes.keys()), config)
        add_counter(counters, 'existing-nodes-from-api', len(existing_nodes))
        output_nodes = drop_mcf_nodes(output_nodes, existing_nodes, config,
                                      counters)

    # Save the filtered nodes into an MCF file.
    if output_mcf:
        write_mcf_nodes([output_nodes], output_mcf)
        print(f'Wrote {len(output_nodes)} nodes to {output_mcf}')
    add_counter(counters, f'output-nodes', len(output_nodes))
    return counters


def main(_):
    counters = filter_mcf_file(_FLAGS.input_mcf, _FLAGS.ignore_mcf,
                               get_diff_config(), _FLAGS.output_mcf)
    print_counters(counters)


if __name__ == '__main__':
    app.run(main)
