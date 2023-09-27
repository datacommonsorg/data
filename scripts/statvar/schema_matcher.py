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
"""Script to search for property and values in MCF files."""

import ast
import csv
import os
import sys

from absl import app
from absl import flags
from absl import logging
from collections import OrderedDict

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(os.path.join(os.path.dirname(_SCRIPT_DIR), 'statvar'))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

flags.DEFINE_string('input_file', '', 'Input file with queries to lookup.')
flags.DEFINE_list('input_query', [], 'Input queries to lookup.')
flags.DEFINE_string('output_csv', '',
                    'Output CSV with matching property, values.')
flags.DEFINE_string('schema_mcf', '/usr/local/google/dc/stat_vars/all_schema.mcf',
                    'Comma separated list of MCF files.')
flags.DEFINE_list('mcf_include_pv', [],
                  'List of property:values to include in the MCF.')
flags.DEFINE_string('config', '', 'Config dictionary.')
flags.DEFINE_float('min_match_fraction', 0.7,
                   'Minimum fraction of input string to match in results.')
flags.DEFINE_bool('debug', False, 'Enable debug messages.')

_FLAGS = flags.FLAGS

import file_util
import download_util
import process_http_server

from mcf_file_util import load_mcf_nodes, filter_mcf_nodes, strip_namespace
from ngram_matcher import NgramMatcher
from config_map import ConfigMap
from counters import Counters


_DEFAULT_CONFIG = {
    'match_props': ['dcid', 'name', 'description'],
    'max_results': 10,
    'min_match_fraction': 0.7,
}


class SchemaMatcher:
    '''Class to lookup schema nodes matching words to names and descriptions.'''

    def __init__(self, mcf_file: str, config: dict = {}, counters:Counters = None):
        self._counters = counters
        if self._counters is None:
          self._counters = Counters()
        self._config = ConfigMap(config_dict=_DEFAULT_CONFIG)
        if config:
            self._config.add_configs(config)
        self.schema_nodes = load_mcf_nodes(mcf_file, strip_namespaces=True)
        self._node_matcher = NgramMatcher(config=self._config.get_configs())
        self.add_nodes_to_matcher(self.schema_nodes,
                                  self._config.get('match_props'))
        # Map from a node to list of properties that can have the node as value.
        self._node_parent_prop = {}
        self._set_node_property_map()

    def add_nodes_to_matcher(
        self,
        nodes: dict,
        props: list = ['dcid', 'name', 'description', 'alternativeName'],
    ):
        '''Add the properties from the nodes to the ngram matcher for lookups.'''
        logging.info(f'Adding {props} for {len(nodes)} nodes into matcher.')
        self._counters.set_prefix('matcher-load-schema:')
        self._counters.add_counter('total', len(nodes))
        for dcid, node in nodes.items():
            # Add all the node PVs as key for lookup
            node_str = str(node)
            self._node_matcher.add_key_value(node_str, node)
            # Add selected property values for node lookup
            for prop in props:
                prop_value = node.get(prop)
                if prop_value:
                    self._node_matcher.add_key_value(
                        strip_namespace(prop_value), node)
            self._counters.add_counter('processed', 1)

    def lookup_pvs_for_query(self, query: str, types: list = []) -> dict:
        '''Returns the property:values that match the query string using the ngram matcher.'''
        pvs = {}
        nodes = self._node_matcher.lookup(query,
                                          num_results=self._config.get(
                                              'max_results', 10))
        logging.level_debug() and logging.debug(
            f'Got {len(nodes)} nodes for query: {query}, {nodes}')
        types_set = _get_set(types)
        for key, node in nodes:
            dcid = _get_dcid(node)
            if not self._node_is_type(dcid, types_set):
                # Ignore the result as it is not the required type.
                logging.level_debug() and logging.debug(
                    f'Ignoring {dcid}: {node} for {query} not of type: {types_set}'
                )
                continue
            prop = self._node_get_property(dcid)
            _add_pv(prop, dcid, pvs)
        logging.level_debug() and logging.debug(
            f'Got {len(pvs)} pvs for query: {query}, {pvs}')
        self._counters.add_counter('matcher-lookups', 1)
        if pvs:
          self._counters.add_counter('matcher-results', 1)
          self._counters.add_counter(f'matcher-results-pvs-{int(len(pvs)/2)}', 1)
        return pvs

    def _set_node_property_map(self):
        '''Sets the list of properties for each node.'''
        for dcid, node in self.schema_nodes.items():
            if self._node_is_type(dcid, 'Property'):
                range_includes = _get_set(node.get('rangeIncludes'))
                for r in range_includes:
                    self._node_parent_prop[strip_namespace(
                        r)] = strip_namespace(dcid)
                    logging.debug(f'Setting prop for {r} to {dcid}')

    def _node_get_property(self, dcid: str) -> str:
        '''Get the property for the node.
        If node is a property, return it else
        return the property that has rangeIncludes of the given node type.'''
        node_types = list(
            _get_set(self._node_get_property_value(dcid, 'typeOf')))
        node_types.extend(
            _get_set(self._node_get_property_value(dcid, 'subClassOf')))
        node_types.extend(self._node_get_types(dcid))
        if 'StatisticalVariable' in node_types:
          return 'variableMeasured'
        for parent in node_types:
            prop = self._node_parent_prop.get(parent)
            if prop:
                logging.level_debug() and logging.debug(
                    f'Got property {prop} for {dcid} type: {parent} for types: {node_types}'
                )
                return prop
        logging.level_debug() and logging.debug(
            f'No property for {dcid}, type: {node_types}')
        logging.debug(
            f'{dcid}: typeOf: {self._node_get_property_value(dcid, "typeOf")}, {self._node_get_types(dcid)}, {self.schema_nodes.get(dcid)}, {len(self.schema_nodes)}'
        )
        return ''

    def _node_get_property_value(self, dcid: str, prop: str) -> str:
        return strip_namespace(
            self.schema_nodes.get(strip_namespace(dcid), {}).get(prop))

    def _node_set_property_value(self, dcid: str, prop: str, value: str) -> str:
        '''Sets the property for a node.'''
        node = self.schema_nodes.get(dcid)
        if node:
            prop_values = _get_set(self._node_get_property_value(dcid, prop))
            prop_values.update(_get_set(value))
            node[prop] = prop_values
            return prop_values
        return None

    def _node_is_type(self, dcid: str, typeof: list) -> bool:
        '''Returns True if the node is one of the given types.'''
        types_set = _get_set(typeof)
        if not types_set:
            return True
        node_types = self._node_get_types(dcid)
        if node_types:
            common_types = node_types.intersection(_get_set(typeof))
            if common_types:
                return True
        return False

    def _node_get_types(self, dcid: str) -> set:
        '''Returns the set of classes the node is a type of.'''
        root_types = ['Class', 'Thing', 'Intangible', 'Enumeration', 'Property']
        parent_types = self._node_get_property_value(dcid, 'typeOf')
        if parent_types and isinstance(parent_types, set):
            # Parents already resolved. return it.
            return parent_types
        parent_types = _get_set(parent_types)
        parent_types.update(
            _get_set(self._node_get_property_value(dcid, 'subClassOf')))
        new_parents = _get_set(parent_types)
        while new_parents:
            next_parents = set()
            for parent in new_parents:
                parent_types.add(parent)
                node_parents = _get_set(
                    self._node_get_property_value(parent, 'typeOf'))
                node_parents.update(
                    _get_set(self._node_get_property_value(
                        parent, 'subClassOf')))
                for p in node_parents:
                    if p not in parent_types and p not in root_types:
                        next_parents.add(p)
            new_parents = next_parents
        self._node_set_property_value(dcid, 'typeOf', parent_types)
        logging.level_debug() and logging.debug(
            f'Got types: {dcid}: {parent_types}')
        return parent_types


def _add_pv(prop: str, value: str, pvs: dict) -> dict:
    '''Add the property, value to the dict of pvs in the form:
    { 'p_<N>':  <prop>, 'v_<N>': <value>}.'''
    num_props = int(len(pvs) / 2)
    for index in range(1, num_props+1):
        p_key = f'p_{index}'
        p = pvs.get(p_key)
        if p:
            v = pvs.get(f'v_{index}')
            if p == prop and value in v:
                # Property already exists. Ignore it.
                return pvs
    # Add the new pv
    index = num_props + 1
    pvs[f'p_{index}'] = prop
    pvs[f'v_{index}'] = value
    return pvs


def _get_dcid(node: dict) -> str:
    dcid = node.get('dcid', node.get('Node'))
    if dcid and dcid[0] == '"':
        dcid = dcid[1:-1]
    return strip_namespace(dcid)


def _get_set(items: list) -> set:
    if items is None:
        return {}
    if isinstance(items, str):
        return set({strip_namespace(s.strip()) for s in items.split(',')})
    return set(items)


def search_pvs(mcf_file: str,
               config: dict,
               input_file: str,
               input_queries: list = [],
               output_file: str = None):
    '''Returns the matching property values for each input string.'''
    counters = Counters()
    matcher = SchemaMatcher(mcf_file, config, counters)
    if not input_queries:
        input_queries = list()
    # Load input queries.
    for file in file_util.file_get_matching(input_file):
        with file_util.FileIO(file) as query_file:
            for query in query_file:
                if query not in input_queries:
                    input_queries.append(query)

    # lookup PVs for each query
    logging.info(f'Looking up PVs for {len(input_queries)} queries...')
    counters.set_prefix('matcher-lookup:')
    counters.add_counter('total', len(input_queries))
    output_pvs = dict()
    max_pvs = 0
    for query in input_queries:
        pvs = matcher.lookup_pvs_for_query(query)
        if pvs:
            pvs['query'] = query
        else:
          pvs = { 'query': query}
        output_pvs[len(output_pvs)] = pvs
        max_pvs = int(len(pvs)/2)
        counters.add_counter('processed', 1)

    if output_file:
        columns = ['query']
        for index in range(1, max_pvs + 1):
          columns.append(f'p_{index}')
          columns.append(f'v_{index}')
        file_util.file_write_csv_dict(output_pvs, output_file, columns)
    else:
        for index, pvs in output_pvs.items():
            print(f'{pvs}')


def main(_):
    # Launch a web server if --http_port is set.
    if process_http_server.run_http_server(script=__file__, module=__name__):
        return

    if _FLAGS.debug:
        logging.set_verbosity(2)
    config = ConfigMap(filename=_FLAGS.config)
    config.set_config('min_match_fraction', _FLAGS.min_match_fraction)
    search_pvs(_FLAGS.schema_mcf, config.get_configs(), _FLAGS.input_file,
               _FLAGS.input_query, _FLAGS.output_csv)


if __name__ == '__main__':
    app.run(main)
