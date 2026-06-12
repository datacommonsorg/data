# Copyright 2026 Google LLC
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
"""Utilities to generate statvar dcid."""

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
_DATA_DIR = os.path.dirname(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(os.path.join(_DATA_DIR, 'util'))

from counters import Counters
from dc_api_wrapper import dc_api_get_node_property_values
from mcf_file_util import strip_namespace, add_namespace, add_mcf_node, is_leaf_object


def camel_to_snake(text: str, delim: str = '_') -> str:
    """Convert a string from camelCase to snake_case.

    Args:
      text: The camelCase string to convert.
      delim: Delimiter to use between words (default is '_').

    Returns:
      The converted snake_case string in lowercase.
    """
    s1 = re.sub(r'([a-z0-9])([A-Z])', r'\1' + delim + r'\2', text)
    s2 = re.sub(r'([a-zA-Z])([0-9])', r'\1' + delim + r'\2', s1)
    s3 = re.sub(r'([A-Z])([A-Z][a-z])', r'\1' + delim + r'\2', s2)
    return s3.lower()


def get_dcid_name(dcid: str, schema_nodes: dict) -> str:
    """Returns the name for a DCID if it exists in the schema.

    Args:
      dcid: The DCID string to look up.
      schema_nodes: Dictionary of schema nodes containing properties.

    Returns:
      The name of the DCID if found, or stripped DCID if no name property is
      defined. Returns None if the DCID is not in the schema.
    """
    node = schema_nodes.get(strip_namespace(dcid))
    if not node:
        node = schema_nodes.get(add_namespace(dcid))
    if not node:
        return None
    name = node.get('name')
    if not name:
        name = strip_namespace(dcid)
    return name.strip('"').strip()


def get_dcid_token(word: str,
                   upper_case: bool = False,
                   remove_prefix: str = '') -> str:
    """Returns the word normalized into a token suitable for a DCID.

    Args:
      word: The raw string to normalize.
      upper_case: If True, converts camelCase to uppercase snake_case.
      remove_prefix: Optional prefix string to remove from the token.

    Returns:
      A normalized DCID token string.
    """
    # Convert any non alphanumeric characters to '_'
    token = re.sub(r'[^A-Za-z0-9_.-]+', '_', word.strip())
    token = re.sub(r'_+', '_', token).strip('_')

    if upper_case:
        # Convert camelCase to snake case
        token = camel_to_snake(token).upper()
    if remove_prefix:
        token = token.removeprefix(remove_prefix)
    return token[0].upper() + token[1:]


def generate_dcid_for_statvar(pvs: dict,
                              config: dict,
                              schema_nodes: dict = None,
                              counters: Counters = None) -> str:
    """Returns the generated statistical variable DCID using the configuration.

    Args:
      pvs: Dictionary of property-value mappings representing the StatVar.
      config: Configuration dictionary defining DCID generation parameters.
      schema_nodes: Optional dictionary of loaded schema nodes.
      counters: Optional Counters object to track statistics.

    Returns:
      A generated DCID string for the StatVar.
    """

    if schema_nodes is None:
        schema_nodes = dict()

    # Get the order of properties for dcid with ignored values
    dcid_props = config.get('statvar_dcid_fixed_properties', [
        'statType<>measuredValue',
        'measurementQualifier',
        'measuredProperty',
        'populationType',
    ])
    fixed_props = dict()
    for prop in dcid_props:
        val = ''
        if '<>' in prop:
            prop, val = prop.split('<>', 1)
        fixed_props.setdefault(prop, set()).add(val)

    use_value_names = config.get('statvar_dcid_value_name', False)
    dcid_prefix = config.get('statvar_dcid_prefix', '')
    ignore_props = config.get('statvar_dcid_ignore_properties', [
        'description', 'name', 'nameWithLanguage', 'descriptionUrl',
        'alternateName', 'footnote', 'unCode', 'Node', 'typeOf'
    ])
    prop_delim = config.get('statvar_dcid_delimiter', '_')
    val_delim = config.get('statvar_dcid_value_delimiter', '')
    upper_case = config.get('statvar_dcid_upper_case', False)
    remove_prefix = config.get('statvar_dcid_remove_prefix', '')

    add_prop = False
    if val_delim:
        add_prop = True

    # Lookup names for values.
    lookup_dcids = set()
    dcid_pvs = dict()
    for prop, value in pvs.items():
        if prop not in ignore_props:
            dcid_pvs[prop] = value
            if use_value_names and not get_dcid_name(prop, schema_nodes):
                lookup_dcids.add(prop)
            if use_value_names and not is_leaf_object(
                    value) and not get_dcid_name(value, schema_nodes):
                lookup_dcids.add(value)

    if lookup_dcids:
        if counters:
            counters.add_counter('dc_api_lookup_name', len(lookup_dcids))
        node_names = dc_api_get_node_property_values(list(lookup_dcids))
        for pvs in node_names.values():
            add_mcf_node(pvs, schema_nodes)

    ordered_props = []
    # Add properties from template followed by constraint props
    for prop, val in fixed_props.items():
        prop_val = dcid_pvs.get(prop)
        if prop_val:
            if val and prop_val in val:
                dcid_pvs.pop(prop)
            else:
                ordered_props.append(prop)
    for prop in sorted(dcid_pvs.keys()):
        if prop not in ordered_props:
            ordered_props.append(prop)

    # Get ordered list of dcid tokens
    dcid_tokens = []
    for prop in ordered_props:
        prop_value = dcid_pvs.pop(prop, None)
        if prop_value:
            value_name = prop_value
            if use_value_names:
                value_name = get_dcid_name(prop_value, schema_nodes)
            value_name = get_dcid_token(value_name, upper_case, remove_prefix)
            if val_delim and prop not in fixed_props:
                prop_name = get_dcid_token(prop, upper_case, remove_prefix)
                value_name = prop_name + val_delim + value_name
            if upper_case:
                value_name = value_name.upper()
            dcid_tokens.append(value_name)
    dcid = prop_delim.join(dcid_tokens)
    if dcid_prefix:
        dcid = dcid_prefix + dcid
    return dcid
