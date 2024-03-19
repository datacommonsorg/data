# Copyright 2023 Google LLC
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
"""Class to resolve schema nodes using Property:Values."""

import os
import pprint
import sys
from typing import Union

from absl import app
from absl import flags
from absl import logging

# uncomment to run pprof
# os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
# from pypprof.net_http import start_pprof_server

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

import process_http_server

from mcf_file_util import load_mcf_nodes, write_mcf_nodes, add_namespace, strip_namespace, normalize_mcf_node
from mcf_diff import fingerprint_node, fingerprint_mcf_nodes, diff_mcf_node_pvs

# imports from ../../util
import file_util
from config_map import ConfigMap, read_py_dict_from_file
from counters import Counters, CounterOptions
from dc_api_wrapper import dc_api_is_defined_dcid
from download_util import download_file_from_url
from statvar_dcid_generator import get_statvar_dcid

_FLAGS = flags.FLAGS

flags.DEFINE_list('input_schema_mcf', [],
                  'List of schema MCF files to load for resolution.')
flags.DEFINE_list('resolve_mcf', [], 'MCF file with nodes to be resolved.')
flags.DEFINE_string(
    'resolve_output_path',
    '',
    'Output folder for resolved and unresolved files.',
)

_DEFAULT_CONFIG = {
    # List of properties to ignore when resolving a node.
    'resolve_ignore_props': [
        # StatVar properties to ignore
        'Node',
        'dcid',
        'name',
        'description',
        'provenance',
        'memberOf',
        'member',
        'relevantVariable',
    ],
    # List of properties to include when resolving PVs.
    'resolve_include_props': [],
    # Resolvable properties.
    # The property:value is assumed to be unique to a node.
    'resolve_props': ['dcid'],
}


class SchemaResolver:

    def __init__(self,
                 mcf_files: list,
                 config: dict = {},
                 counters: Counters = None):
        self._counters = counters
        if self._counters is None:
            self._counters = Counters()
        self._config = ConfigMap(config_dict=_DEFAULT_CONFIG)
        if config:
            self._config.add_configs(config)

        # Internal state
        # index of key to node pvs dict.
        self._index = {}
        # Dict of schema Nodes to resolve keyed by <dcid>
        self._schema_nodes = {}
        # Set of properties that don't have unique values across nodes
        self._non_unique_props = set()

        self.load_schema_mcf(mcf_files)

    def load_schema_mcf(self, schema_mcf_files: list):
        """Load nodes from schema MCF files and add to the index."""
        mcf_nodes = load_mcf_nodes(schema_mcf_files)
        for dcid, node in mcf_nodes.items():
            self.add_node(node)
        logging.info(
            f'Loaded {len(self._schema_nodes)} schema MCF nodes: {schema_mcf_files}'
        )

    def add_node(self, node: dict) -> bool:
        """Add a node with a dict of property:values to the index for lookup."""
        node_added = False
        dcid = get_node_dcid(node)
        schema_node = self._schema_nodes.get(dcid)
        if schema_node:
            logging.error(
                f'Cannot add additional PVs {node} for existing node: {schema_node}'
            )
            self._counters.add_counter(f'error-duplicate-node', 1)
            return node_added

        normalized_node = normalize_mcf_node(node, quantity_range_to_dcid=True)
        self._schema_nodes[dcid] = normalized_node

        # Add the node to the index for all keys
        index_keys = self.get_keys(normalized_node, False)
        for key in index_keys:
            key_prop = key[:key.find(':')]
            index_node = self._index.get(key)
            if index_node:
                logging.error(
                    f'Duplicate key {key} for node {node}, existing node: {index_node},'
                    f' dropping key_prop:{key_prop}')
                self._non_unique_props.add(key_prop)
                self._counters.add_counter(f'error-duplicate-keys-{key_prop}',
                                           1)
                continue
            self._index[key] = node
            self._counters.add_counter(f'index-keys-{key_prop}', 1)
            node_added = True
        if node_added:
            self._counters.add_counter('nodes_added', 1)
        return node_added

    def get_keys(self, node: dict, normalize_node: bool = True) -> list:
        """Returns a list of string keys for the node."""
        keys = []
        typeof = strip_namespace(node.get('typeOf', ''))
        dcid = add_namespace(get_node_dcid(node))
        if normalize_node:
            node = normalize_mcf_node(node, quantity_range_to_dcid=True)
        if typeof == 'StatisticalVariable':
            # Use fingerpring of all PVs in sorted order as key.
            fp = fingerprint_node(
                node,
                ignore_props=self._config.get('resolve_ignore_props'),
                compare_props=self._config.get('resolve_include_props'),
            )
            keys.append(fp)
        else:
            key_props = set(self._config.get('resolve_props', []))
            if '*' in key_props:
                key_props.update(node.keys())
            key_props = key_props.difference(self._non_unique_props)
            for prop in key_props:
                value = node.get(prop, '')
                if isinstance(value, str):
                    value = value.strip().strip('"')
                if value:
                    keys.append(f'{prop}:{value}')
        keys.append(dcid)
        return keys

    def resolve_node(self, node: dict) -> dict:
        keys = self.get_keys(node)
        for key in keys:
            resolved_node = self._index.get(key)
            if resolved_node:
                self._counters.add_counter('resolve-hits', 1)
                return resolved_node
        self._counters.add_counter('resolve-miss', 1)
        return {}


def get_node_dcid(node: dict) -> str:
    """Returns the dcid without the namespace prefix for the node."""
    if not node:
        return ''
    dcid = node.get('dcid', node.get('Node', '')).strip()
    if dcid and dcid[0] == '"':
        # Strip quotes around dcid
        dcid = dcid[1:-1]
    return strip_namespace(dcid)


def resolve_nodes(
    schema_mcf: list,
    input_mcf: list,
    output_path: str = None,
) -> dict:
    resolver = SchemaResolver(schema_mcf)
    output_nodes = {}
    logging.info(f'Resolving nodes from {input_mcf}')
    for input_file in file_util.file_get_matching(input_mcf):
        input_nodes = load_mcf_nodes(input_file)
        logging.info(f'Resolving {len(input_nodes)} nodes from input_file')
        resolved_nodes = {}
        unresolved_nodes = {}
        for key, node in input_nodes.items():
            resolved_node = resolver.resolve_node(node)
            if resolved_node:
                dcid = get_node_dcid(resolved_node)
                resolved_nodes[dcid] = resolved_node
                resolved_node[
                    '#ResolvedNode: '] = f'original={key},resolved={dcid}'
                logging.info(f'Resolved {node} to {resolved_node}')
            else:
                dcid = get_node_dcid(node)
                if not dcid:
                    dcid = get_statvar_dcid(node)
                    node['Node'] = add_namespace(dcid)
                unresolved_nodes[dcid] = node
                logging.info(f'Unable to resolve node {node}')
        if output_path:
            basename = os.path.basename(input_file)
            output = os.path.join(output_path, basename)
            if resolved_nodes:
                write_mcf_nodes(
                    resolved_nodes,
                    file_util.file_get_name(output,
                                            suffix='_resolved',
                                            file_ext='.mcf'),
                )
                output_nodes.update(resolved_nodes)
            if unresolved_nodes:
                write_mcf_nodes(
                    unresolved_nodes,
                    file_util.file_get_name(output,
                                            suffix='_unresolved',
                                            file_ext='.mcf'),
                )
                output_nodes.update(unresolved_nodes)
        else:
            print(f'Resolved {len(resolved_nodes)} out of {len(input_nodes)}')
            pprint.pprint(resolved_nodes)
            print(
                f'Unresolved {len(unresolved_nodes)} out of {len(input_nodes)}')
            pprint.pprint(unresolved_nodes)
    return output_nodes


def main(_):
    # Launch a web server if --http_port is set.
    if process_http_server.run_http_server(script=__file__, module=__name__):
        return

    # if _FLAGS.debug:
    #  logging.set_verbosity(2)

    resolve_nodes(
        _FLAGS.input_schema_mcf,
        _FLAGS.resolve_mcf,
        _FLAGS.resolve_output_path,
    )


if __name__ == '__main__':
    app.run(main)
