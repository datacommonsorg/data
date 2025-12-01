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
"""Class to lookup/resolve schema nodes using property:values."""

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
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(_SCRIPT_DIR))),
                 'util'))

import process_http_server

from mcf_file_util import load_mcf_nodes, write_mcf_nodes
from mcf_file_util import add_namespace, strip_namespace, normalize_mcf_node
from mcf_diff import fingerprint_node

# imports from data/util
import file_util
from config_map import ConfigMap
from counters import Counters
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
        'alternateName',
        'description',
        'descriptionUrl',
        'provenance',
        'memberOf',
        'member',
        'relevantVariable',
        'keyString',
    ],
    # List of properties to include when resolving PVs.
    'resolve_include_props': [],
    # Resolvable properties.
    # The property:value is assumed to be unique to a node.
    'resolve_props': ['dcid'],
}


class SchemaResolver:
    """Class to lookup schema nodes using unique propety:values.
      It creates an index of propperty:value to node dcid for existing nodes.
      for properoties that have unique values.

      To resolve a node, it looks up the index of property:values to
      find any existing unique node with the property:value.

      This is similar to the the DC APi /resolve but doesn't use a predefined
      list of properties for the index.

    Usage:
         # Create a SchemaResolver loaded with MCF nodes.
         # This creates an index from unique property:value to the node.
         resolver = SchemaResolver('<mcf-files>')

         # Resolve a node with partial property:values.
         partial_node = { <prop1>: <value1> }
         full_node = resolver.resolve_node(partial_node)
         if not full_node:
           logging.error(f'Unable to resolve {partial_node}')

    """

    def __init__(self,
                 mcf_files: list = '',
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
        # These properties are ignored when adding new nodes to the index.
        self._non_unique_props = set()

        self.load_schema_mcf(mcf_files)

    def load_schema_mcf(self, schema_mcf_files: list):
        """Load nodes from schema MCF files and add to the index."""
        mcf_nodes = load_mcf_nodes(schema_mcf_files, {})
        if mcf_nodes:
            for dcid, node in mcf_nodes.items():
                self.add_node(node)
        logging.info(
            f'Loaded {len(self._schema_nodes)} schema MCF nodes: {schema_mcf_files}'
        )

    def add_node(self, node: dict) -> bool:
        """Returns True if a node with a dict of property:values is added to the index.
        All the property:values in the node are added to the index when there is no conflict.
        For property:values that are not unique, the property is removed fom index.

        Args:
          node: dictionary of property:values

        Returns:
          True/False depending on whether node was added to the index.
        """
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
        index_keys = self._get_keys(normalized_node, False)
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

    def resolve_node(self, node: dict) -> dict:
        """Returns the node with all property:values given a partial node
        with subset of properties.

        Args:
          node: dictionary with property:values in a node to be looked up

        Returns:
          dictionary with all property:values for the matching node or
          {} when there is no match
        """
        keys = self._get_keys(node)
        for key in keys:
            resolved_node = self._index.get(key)
            if resolved_node:
                prop = key[:key.find(':')]
                self._counters.add_counter(f'resolve-hits-{prop}', 1)
                return resolved_node
        self._counters.add_counter('resolve-miss', 1)
        return {}

    def get_node(self, dcid: str) -> dict:
        """Returns the property:values for the node with the given dcid."""
        return self._schema_nodes.get(strip_namespace(dcid))

    def get_nodes(self) -> dict:
        """Returns dictionary of all nodes loaded into the index keyed by dcid."""
        return self._schema_nodes

    def _get_keys(self, node: dict, normalize_node: bool = True) -> list:
        """Returns a list of string keys for the node property:values.
        It excludes properties in self._non_unique_props.
        """
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


def get_node_dcid(node: dict) -> str:
    """Returns the dcid without the namespace prefix for the node."""
    if not node:
        return ''
    dcid = node.get('dcid', node.get('Node', '')).strip()
    if dcid and dcid[0] == '"':
        # Strip quotes around dcid
        dcid = dcid.strip('"')
    return strip_namespace(dcid)


def resolve_nodes(
    schema_mcf: list,
    input_mcf: list,
    output_path: str = None,
) -> dict:
    """Resolve nodes in an MCF file with a subset of propeorty:values and
    return the node with all property:values.

    Args:
      schema_mcf: list of MCF files with full node definition
      input_mcf: list of MCF files with partial MCF nodes to be looked up.
      output_path: output MCF file to save resolved nodes.

    Returns:
      dictionary of resolved nodes.
    """
    resolver = SchemaResolver(schema_mcf)
    output_nodes = {}
    logging.info(f'Resolving nodes from {input_mcf}')
    for input_file in file_util.file_get_matching(input_mcf):
        input_nodes = load_mcf_nodes(input_file, {})
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
