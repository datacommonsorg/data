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
""" Utility function to filter MCF nodes.

Can be used through command line to filter a set of MCF file.

For example, to filter MCF file and remove nodes that already exist in the DC API:
  python3 mcf_filter.py --input_mcf=<mcf-file> --ignore_existing_nodes \
       --output_mcf=<output-mcf>

To remove nodes defined in another MCF file:
  python3 mcf_filter.py --input_mcf=<mcf-file> --ignore_mcf=<mcf-file> \
       --output_mcf=<output-mcf>
"""

from collections import OrderedDict
from itertools import islice
import os
import sys
import time
import urllib

from absl import app
from absl import flags
from absl import logging
import datacommons as dc

_FLAGS = flags.FLAGS

flags.DEFINE_string(
    'ignore_mcf',
    '',
    'Comma separated list of MCF files with nodes to be dropped from output',
)
flags.DEFINE_list('ignore_dcids', [], 'List of dcids to be ignored')
flags.DEFINE_bool('ignore_existing_nodes', True,
                  'Drop nodes that are defined in DC API.')

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

from counters import Counters
from dc_api_wrapper import dc_api_get_node_property_values
from mcf_file_util import load_mcf_nodes, write_mcf_nodes
from mcf_file_util import add_namespace, strip_namespace
from mcf_file_util import check_nodes_can_merge
from mcf_diff import diff_mcf_node_pvs, get_diff_config


def drop_mcf_nodes(
    input_nodes: dict,
    ignore_nodes: dict,
    config: dict = {},
    counters: Counters = None,
) -> dict:
    """Function to filter MCF nodes removing any nodes in ignore_nodes.

  Args:
    input_nodes: dictionary of MCF nodes keyed by dcid.
    ignore_nodes: dictionary of MCF nodes that are  removed from input_nodes.
    config: config options for diff
    counters (output): dictionary with counts of number of nodes dropped or
      returned.

  Returns:
    A dictionary of node property:values keyed by dcid from input_nodes that
    are not dropped.
  """
    if not counters:
        counters = Counters()
    output_nodes = OrderedDict()
    logging.info(
        f'Filtering {len(input_nodes)} nodes with {len(ignore_nodes)} ignored'
        ' nodes')
    for dcid, pvs in input_nodes.items():
        # Check if dcid exists in ignore nodes and is equivalent.
        ignore_pvs = ignore_nodes.get(add_namespace(dcid), None)
        if ignore_pvs:
            # Compare if nodes have any difference in PVs.
            has_diff, diff_str, added, deleted, modified = diff_mcf_node_pvs(
                node_1=pvs, node_2=ignore_pvs, config=config, counters=counters)
            if has_diff:
                logging.warning(
                    f'Diff in ignored Node: {dcid}, diff:\n{diff_str}\n')
                if config.get('output_nodes_with_additions',
                              False) and (deleted or modified):
                    output_nodes[dcid] = pvs
                    counters.add_counter(f'input-nodes-with-additions', 1)
                else:
                    counters.add_counter(f'error-input-ignore-node-diff', 1,
                                         dcid)
            else:
                logging.debug(f'Ignored Node: {dcid},\n{pvs}\n')
                counters.add_counter(f'input-nodes-ignored', 1)
            # Check if nodes can be merged.
            if not check_nodes_can_merge(ignore_pvs, pvs):
                logging.error(
                    f'Node has conflicting properties:{dcid}: {ignore_pvs}, {pvs}'
                )
                counters.add_counter(f'error-node-merge-conflict', 1, dcid)
        else:
            output_nodes[dcid] = pvs
    return output_nodes


def drop_existing_mcf_nodes(input_nodes: dict,
                            config: dict = {},
                            counters: Counters = None) -> dict:
    """Function to drop existing MCF nodes and return new nodes.

  Args:
    input_nodes: dictionary of MCF nodes keyed by dcid to be filtered
    config: config options for diff
    counters (output): dictionary with counts of number of nodes dropped or
      returned.

  Returns:
    A dictionary of node property:values keyed by dcid from input_nodes that
    are not dropped.
  """
    if not counters:
        counters = Counters()
    # Get the property-values from DC API for all nodes
    dcids = [strip_namespace(dcid) for dcid in list(input_nodes.keys()) if dcid]
    existing_nodes = dc_api_get_node_property_values(dcids, config)
    counters.add_counter('existing-nodes-from-api', len(existing_nodes))
    return drop_mcf_nodes(input_nodes, existing_nodes, config, counters)


def filter_mcf_file(
    input_mcf_files: str,
    ignore_mcf_files: str,
    config: dict,
    output_mcf: str,
    counters: Counters = None,
) -> dict:
    """Function to filter MCF nodes in input and write to the output file.

  Args:
    input_mcf_files: Comma seeprated list of input MCF files.
    ignore_mcf_files: Comma seperated list of MCF files with nodes to be
      dropped.
    config: dictionary with configuration parameters:
      ignore_existing_nodes: If set to True, nodes defined in DC API are
        dropped.
    output_mcf_file: MCF file to write nodes from input that are not dropped.
    counters (output): Returns the counts of nodes processed, dropped.

  Returns:
    A dictionary of nodes with property:values keyed by dcid from input
    that are not dropped.
  """
    # Load nodes from MCF files.
    if not counters:
        counters = Counters()
    input_nodes = load_mcf_nodes(input_mcf_files)
    ignore_nodes = load_mcf_nodes(ignore_mcf_files)
    counters.add_counter('input-nodes', len(input_nodes))
    counters.add_counter('ignore-nodes-loaded', len(input_nodes))

    # Remove any ignored nodes from input.
    output_nodes = drop_mcf_nodes(input_nodes, ignore_nodes, config, counters)

    # Remove any predefined nodes.
    if config.get('ignore_existing_nodes', False):
        output_nodes = drop_existing_mcf_nodes(output_nodes, config, counters)

    # Save the filtered nodes into an MCF file.
    if output_mcf:
        write_mcf_nodes([output_nodes], output_mcf)
        logging.info(f'Wrote {len(output_nodes)} nodes to {output_mcf}')
    counters.add_counter(f'output-nodes', len(output_nodes))
    counters.print_counters()
    return output_nodes


def main(_):
    config = get_diff_config()
    config['ignore_existing_nodes'] = _FLAGS.ignore_existing_nodes
    filter_mcf_file(_FLAGS.input_mcf, _FLAGS.ignore_mcf, config,
                    _FLAGS.output_mcf)


if __name__ == '__main__':
    app.run(main)
