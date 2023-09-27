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
"""Utilities to generate schema nodes."""

import os
import re
import sys

from absl import app
from absl import flags
from absl import logging


_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util')
)

flags.DEFINE_string(
    'input_nodes', '', 'MCF file with nodes to generate schema for.'
)
flags.DEFINE_string('schema_mcf', '', 'MCF file with nodes for existing schema')
flags.DEFINE_string('generated_mcf', '', 'MCF file for new schema nodes.')

_FLAGS = flags.FLAGS

import file_util
import process_http_server

from config_map import ConfigMap
from dc_api_wrapper import dc_api_get_node_property_values
from mcf_file_util import load_mcf_nodes, write_mcf_nodes
from mcf_file_util import add_namespace, strip_namespace, add_mcf_node

import config_flags

# Base schema with some basic properties
_BASE_SCHEMA = {
    'dcid:Thing': {
        'Node': 'dcid:Thing',
        'typeOf': 'dcid:Class',
    },
    'dcid:typeOf': {
        'Node': 'dcid:typeOf',
        'typeOf': 'dcs:Property',
    },
    'dcid:StatisticalVariable': {
        'Node': 'dcs:StatisticalVariable',
        'typeOf': 'dcid:Class',
    },
    'dcid:populationType': {
        'Node': 'dcid:populationType',
        'typeOf': 'dcs:Property',
        'rangeIncludes': 'dcs:Thing',
    },
    'dcid:measuredProperty': {
        'Node': 'dcid:measuredProperty',
        'typeOf': 'dcs:Property',
    },
    'dcid:count': {
        'Node': 'dcs:count',
        'typeOf': 'dcs:Property',
    },
    'dcid:statType': {
        'Node': 'dcid:statType',
        'typeOf': 'dcs:Property',
    },
    'dcid:measuredvalue': {
        'Node': 'dcs:measuredvalue',
        'typeOf': 'dcid:Property',
    },
    'dcid:memberOf': {
        'Node': 'dcs:memberOf',
        'typeOf': 'dcid:Property',
    },
    'dcid:measurementQualifier': {
        'Node': 'dcs:measurementQualifier',
        'typeOf': 'dcid:Property',
    },
    'dcid:measurementDenominator': {
        'Node': 'dcs:measurementDenominator',
        'typeOf': 'dcid:Property',
    },
    'dcid:measurementMethod': {
        'Node': 'dcs:measurementMethod',
        'typeOf': 'dcid:Property',
    },
    'dcid:name': {
        'Node': 'dcid:name',
        'typeOf': 'dcs:Property',
    },
    'dcid:description': {
        'Node': 'dcid:description',
        'typeOf': 'dcs:Property',
    },
    'dcid:dcid': {
        'Node': 'dcid:dcid',
        'typeOf': 'dcs:Property',
    },
    'dcid:Node': {
        'Node': 'dcid:Node',
        'typeOf': 'dcs:Class',
    },
    'dcid:QuantityRange': {
        'Node': 'dcid:QuantityRange',
        'typeOf': 'dcs:Class',
    },
    'dcid:Text': {
        'Node': 'dcid:Text',
        'typeOf': 'dcs:Class',
    },
    'dcid:Number': {
        'Node': 'dcid:Number',
        'typeOf': 'dcs:Class',
    },
}


def get_schema_nodes(
    nodes: dict, schema_nodes: dict = None, config: dict = None
) -> dict:
  """Returns a dictionary of schema nodes for all property/values in nodes.

  Args:
    nodes: dictionary of nodes with a dict of property: value for each node.
    schema_nodes: dictionary of property values for all schema references in
      nodes. keyed by dcid.
  """
  if schema_nodes is None:
    schema_nodes = dict()
  lookup_dcids = set()
  for dcid, pvs in nodes.items():
    for prop, value in pvs.items():
      if prop:
        if prop[0].isalnum():
          lookup_dcids.add(add_namespace(strip_namespace(prop)))
          if value and isinstance(value, str):
            if value[0] != '"' and value[0] != '[':
              # Value is not a string or range, must be a schema node.
              value_list = value.split(',')
              for val in value_list:
                if val and val[0] != '"' and val[0] != '[' and ' ' not in val:
                  lookup_dcids.add(add_namespace(strip_namespace(val)))
    add_mcf_node(pvs, schema_nodes)

  # Batch lookup all dcids not in schema.
  num_dcids = len(lookup_dcids)
  lookup_dcids = lookup_dcids.difference(_BASE_SCHEMA.keys())
  lookup_dcids = lookup_dcids.difference(nodes.keys())
  if not lookup_dcids:
    return schema_nodes
  if schema_nodes:
    lookup_dcids = lookup_dcids.difference(set(schema_nodes.keys()))
  logging.level_debug() and logging.debug(
      f'Looking up schema for {len(lookup_dcids)} out of'
      f' {num_dcids} dcids from {len(nodes)} nodes: {lookup_dcids}'
  )
  dcid_schema = dc_api_get_node_property_values(list(lookup_dcids), config)
  logging.info(
      f'Got schema for {len(dcid_schema.keys())} dcids out of'
      f' {len(lookup_dcids)}'
  )
  schema_nodes.update(dcid_schema)
  # Recursively fetch schema for new nodes.
  return get_schema_nodes(dcid_schema, schema_nodes, config)


def get_schema(dcid: str, schema: dict = {}) -> bool:
  """Returns True if dcid is defined in schema."""
  node = schema.get(strip_namespace(dcid))
  if not node:
    node = schema.get(add_namespace(dcid), {})
  if not node:
    node = _BASE_SCHEMA.get(add_namespace(dcid), {})
  return node


def get_dcid(node: dict) -> str:
  return node.get('dcid', node.get('Node'))


def get_prop(node: dict, prop: str) -> str:
  return strip_namespace(node.get(prop, ''))


def is_numeric(value) -> bool:
  try:
    n = float(value)
    return True
  except ValueError:
    return False


def get_value_type(value: str, prop: str, schema: dict) -> str:
  """Returns the type of the value."""
  if not value:
    return ''
  if isinstance(value, str):
    value = value.split(',')[0]
  if is_numeric(value):
    return 'Number'
  if not value or not isinstance(value, str):
    return ''
  if value[0] == '"':
    return 'Text'
  if value[0] == '[':
    return 'QuantityRange'
  # Check if value is an existing schema node.
  value_node = get_schema(value, schema)
  if value_node:
    return get_prop(value_node, 'typeOf')
  # Value doesn't exist in schema.
  # Use property's range if it exists.
  property_node = get_schema(prop, schema)
  if property_node:
    range_type = get_prop(property_node, 'rangeIncludes').split(',')[0]
    if range_type:
      return range_type
  return ''


def generate_new_property_node(
    prop: str, parent_node: dict, schema: dict
) -> dict:
  """Returns a node for the new property."""
  prop = strip_namespace(prop)
  if not prop:
    return {}
  if get_schema(prop):
    # Don't extend base schema
    logging.debug(f'Skipping existing property: {prop}')
    return {}
  if prop[0] == '#' or prop[0].isupper():
    logging.debug(f'Skipping invalid property: {prop}')
    return {}
  domain_node = get_dcid(parent_node)
  if get_prop(parent_node, 'typeOf') == 'StatisticalVariable':
    domain_node = get_prop(parent_node, 'populationType')
  value_type = get_value_type(get_prop(parent_node, prop), prop, schema)
  property_node = get_schema(prop, schema)
  new_node = {}
  if domain_node and domain_node not in get_prop(
      property_node, 'domainIncludes'
  ):
    new_node['domainIncludes'] = add_namespace(domain_node)
  if not value_type:
    value_type = prop[0].upper() + prop[1:] + 'Enum'
  if value_type and value_type not in get_prop(property_node, 'rangeIncludes'):
    new_node['rangeIncludes'] = add_namespace(value_type)
  if new_node:
    new_node['Node'] = add_namespace(prop)
    new_node['typeOf'] = 'dcs:Property'
    new_node['name'] = f'"{prop}"'
  logging.level_debug() and logging.debug(
      f'Generated new property node: {new_node}'
  )
  return new_node


def generate_new_value_node(value: str, prop: str, schema: dict) -> list[dict]:
  """Returns a list of schema nodes for the new value and its enum type."""
  value = strip_namespace(value)
  if not value:
    return []
  if get_schema(value):
    # Don't extend base schema
    logging.debug(f'Skipping exsiting value node: {value}')
    return []
  value_type = get_schema(value, schema)
  if value_type:
    # value is a known type in schema
    logging.debug(f'Skipping exsiting value type node: {value_type}')
    return []
  if value[0].islower():
    # Value is another prperty. Return a new property node.
    return [generate_new_property_node(value, {}, schema)]
  new_nodes = []
  value_type = get_value_type(value, prop, schema)
  if value_type == 'QuantityRange':
    logging.debug(f'Ignoring QuantityRange for {value}')
    return []
  if not get_schema(value_type, _BASE_SCHEMA):
    # Generate a new enumeration node for the type of the value
    if not value_type:
      value_type = prop[0].upper() + prop[1:] + 'Enum'
    value_type_node = get_schema(value_type, schema)
    if not value_type_node:
      new_value_type_node = {
          'Node': add_namespace(value_type),
          'name': f'"{value_type}"',
          'typeOf': 'schema:Class',
          'subClassOf': 'dcs:Enumeration',
      }
      new_nodes.append(new_value_type_node)
  # Generate a new node for the value
  new_node = {}
  new_node['Node'] = add_namespace(value)
  new_node['typeOf'] = add_namespace(value_type)
  new_node['name'] = '"' + _camel_case_to_space(strip_namespace(value)) + '"'
  new_nodes.append(new_node)
  logging.level_debug() and logging.debug(
      f'Generated new value node: {new_nodes}'
  )
  return new_nodes


def generate_schema_nodes(
    nodes: dict,
    schema: dict = None,
    new_schema_mcf: str = None,
    config: dict = {},
    new_nodes: dict = None,
) -> dict:
  """Returns a dictionary with new schema nodes.

  Args:
    nodes: dictionary of nodes with 'dcid:<dcid>' as the key and value as {
      <prop>: <value> }
    schema: dictionary of existing schema nodes, such as statvars. Any property,
      value not defined in schema is looked up in the DC API and added to the
      schema as nodes.
    new_schema_mcf: MCF file with new schema nodes to be reused and added to the
      output. Can be the output from a previous run with edits that carried to
      the output.
    new_nodes: dictionary of new nodes keyed by dcid. Additional new nodes are
      added to this dict.
    config: dictionary of config parameters such as DC API root, batch size,
      etc. if config.'generate_provisional_schema' is set, 'isProvisional: True'
      is added to all generated nodes.

  Returns:
    Dictionary of new nodes: { 'dcid:<dcid>' : { <prop1> : <value1>, <rop2> :
    vlaue> } }
  """
  if isinstance(schema, str):
    # Load the schema from MCF file.
    schema = load_mcf_nodes(schema)
  schema = get_schema_nodes(nodes, schema, config)
  new_schema = load_mcf_nodes(new_schema_mcf, new_nodes)
  schema = get_schema_nodes(new_schema, schema, config)

  # Look for new PVs not defined in schema.
  num_new_props = 0
  num_new_values = 0
  for dcid, pvs in nodes.items():
    if not dcid or dcid[0] == '#':
      continue
    for prop, value in pvs.items():
      if not prop or not prop[0].isalnum():
        continue
      new_prop_node = generate_new_property_node(prop, pvs, schema)
      if new_prop_node:
        if not get_schema(prop, schema) and config.get(
            'generate_provisional_schema', True
        ):
          new_prop_node['isProvisional'] = 'dcs:True'
        add_mcf_node(new_prop_node, new_schema)
        add_mcf_node(new_prop_node, schema)
        num_new_props += 1

      if value and isinstance(value, str) and value[0] == '"':
        continue
      new_value_nodes = []
      values = value.split(',')
      for value in values:
        value = value.strip()
        new_value_nodes.extend(generate_new_value_node(value, prop, schema))

      for value_node in new_value_nodes:
        if not value_node:
          continue
        if not get_schema(get_dcid(value_node), schema) and config.get(
            'generate_provisional_schema', True
        ):
          value_node['isProvisional'] = 'dcs:True'
        add_mcf_node(value_node, new_schema)
        add_mcf_node(value_node, schema)
        num_new_values += 1
      logging.level_debug() and logging.debug(
          f'For node: {dcid}:{pvs}, generated prop: {new_prop_node}, value:'
          f' {new_value_nodes}'
      )
  logging.info(
      f'Generated {len(new_schema)} new nodes with {num_new_props} new'
      f' properties and {num_new_values} new values.'
  )
  return new_schema


def generate_new_schema_mcf(
    input_mcf: str, schema_mcf: str, output_mcf: str, config: dict
):
  input_nodes = load_mcf_nodes(input_mcf)
  schema_nodes = load_mcf_nodes(schema_mcf)
  logging.info(
      f'Loaded {len(input_nodes)} input nodes, {len(schema_nodes)} schema nodes'
  )
  new_value_nodes = generate_schema_nodes(
      input_nodes, schema_nodes, output_mcf, config
  )
  if new_value_nodes and output_mcf:
    logging.info(f'Writing {len(new_value_nodes)} new nodes into {output_mcf}')
    write_mcf_nodes(new_value_nodes, output_mcf)


def _camel_case_to_space(name: str) -> str:
  """Convert the name in CamelCase to space separated words 'Camel Case'"""
  if not name:
    return name
  # Find positions of capital preceded by non-capital letter
  split_pos = [0]
  split_pos.extend([m.start() + 1 for m in re.finditer('[^A-Z][A-Z0-9]', name)])
  split_pos.append(len(name))
  # Insert space at split positions.
  return ' '.join(
      [name[start:end] for start, end in zip(split_pos, split_pos[1:])]
  )


def main(_):
  # Launch a web server with a form for commandline args
  # if the command line flag --http_port is set.
  if process_http_server.run_http_server(script=__file__, module=__name__):
    return

  config = config_flags.get_config_from_flags(_FLAGS.config)
  generate_new_schema_mcf(
      _FLAGS.input_nodes,
      _FLAGS.schema_mcf,
      _FLAGS.generated_mcf,
      config.get_configs(),
  )


if __name__ == '__main__':
  app.run(main)
