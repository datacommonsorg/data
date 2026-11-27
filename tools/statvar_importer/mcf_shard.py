# Copyright 2025 Google LLC
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
"""Utilities to shard MCF files.

"""

import glob
import math
import os
import re
import sys

from absl import app
from absl import flags
from absl import logging
from collections import OrderedDict
from typing import Union

# Default output filename suffix per shard where
# shard_number is an integer and total_shards is the number of output shards.
_DEFAULT_SHARD_SUFFIX = '-{shard_number:%05d}-of-{total_shards:%05d}'

_FLAGS = flags.FLAGS

flags.DEFINE_string('mcf_shard_input', '', 'List of MCF files to load.')
flags.DEFINE_string('mcf_shard_output_prefix', '',
                    'output MCF nodes loaded into file.')
flags.DEFINE_integer('mcf_shard_output_count', 0, 'Number of output shards.')
flags.DEFINE_integer('mcf_shard_output_per_shard', 0,
                     'Number of nodes per output shard.')
flags.DEFINE_string(
    'mcf_shard_output_suffix', _DEFAULT_SHARD_SUFFIX,
    'Output suffix template for a shard with place holders for shard_number and total_shards.'
)

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

import file_util
import mcf_file_util


def write_sharded_mcf_nodes(nodes: dict,
                            output_prefix: str,
                            output_suffix: str = '',
                            output_shards_count: int = 0,
                            output_nodes_per_shard: int = 0) -> list:
    """Write nodes into sharded MCF files.

  Args:
    nodes: dictionary of PCF nodes keyed by dcid with value as dictionary of
      property:values in the node.
    output_prefix: output file path with prefix of file basename.
    output_suffix: template for sharded output filename suffix.
    output_shards_count: number of output shards to be written.
      If 0, the output count is determined dynamically.
    output_nodes_per_shard: number of nodes per output shard.
      If 0, it is determined dynamically.
      One of output_shards_count or output_nodes_per_shard is expected to be set.

  Returns:
    list of output files created.
  """
    if not nodes:
        return []

    num_nodes = len(nodes)
    if output_nodes_per_shard > 0:
        shards_count = math.ceil(num_nodes / output_nodes_per_shard)
        if output_shards_count > 0 and shards_count != output_shards_count:
            logging.error(
                f'Writing MCF nodes to {shards_count} shards instead of {output_shards_count}'
            )
        output_shards_count = shards_count

    logging.info(
        f'Writing {num_nodes} nodes to {shards_count} shards with {output_nodes_per_shard} nodes per shard.'
    )

    # Split nodes into shards by fingerprint of the key
    sharded_nodes = {}
    node_index = -1
    for key, node in nodes.items():
        node_index += 1
        # Get the shard for the node based on hash of the key
        if not key:
            key = mcf_file_util.get_node_dcid(node)
            if not key:
                key = node_index
        node_hash = hash(key)
        node_shard = node_hash % output_shards_count

        # Assign the node to the shard
        if node_shard not in sharded_nodes:
            sharded_nodes[node_shard] = OrderedDict()
        sharded_nodes[node_shard][key] = node

    # Write the sharded nodes to output files.
    if not output_suffix:
        output_suffix = _DEFAULT_SHARD_SUFFIX
    output_files = []
    for shard_number, nodes_in_shard in sharded_nodes.items():
        shard_filename = output_prefix + output_suffix.format(**{
            'shard_number': shard_number,
            'total_shards': output_shards_count
        })
        mcf_file_util.write_mcf_nodes([nodes_in_shard], shard_filename)
        output_files.append(shard_filename)
    return output_files


def main(_):
    if not _FLAGS.mcf_shard_input or not _FLAGS.mcf_shard_output_prefix:
        print(
            f'Please provide input and output MCF files with --mcf_shard_input and'
            f' --mcf_shard_output_prefix.')
        return
    nodes = mcf_file_util.load_mcf_nodes(_FLAGS.mcf_shard_input,
                                         strip_namespaces=False,
                                         append_values=True,
                                         normalize=False)
    outputs = write_sharded_mcf_nodes(nodes, _FLAGS.mcf_shard_output_prefix,
                                      _FLAGS.mcf_shard_output_suffix,
                                      _FLAGS.mcf_shard_output_count,
                                      _FLAGS.mcf_shard_output_per_shard)
    logging.info(
        f'Wrote {len(nodes)} nodes into {len(outputs)} shards in {_FLAGS.mcf_shard_output_prefix}*'
    )


if __name__ == '__main__':
    app.run(main)
