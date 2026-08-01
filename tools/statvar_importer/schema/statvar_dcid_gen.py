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
"""Utilities to generate statistical variable DCIDs from schema properties."""

import hashlib
import os
import re
import sys
from typing import Union

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
from mcf_file_util import (
    add_mcf_node,
    add_namespace,
    is_leaf_object,
    strip_namespace,
)

_RE_CAMEL_1 = re.compile(r'([a-z])([A-Z0-9])')
_RE_CAMEL_2 = re.compile(r'([A-Z])([A-Z][a-z])')
_RE_NON_ALNUM = re.compile(r'[^A-Za-z0-9_.-]+')
_RE_MULTI_UNDERSCORE = re.compile(r'_+')


def camel_to_snake(text: Union[str, None], delim: str = '_') -> str:
    """Converts a string from camelCase to snake_case.

    Args:
        text: The camelCase string to convert.
        delim: Delimiter to use between words (default is '_').

    Returns:
        The converted snake_case string in lowercase.

    Example:
        >>> camel_to_snake('camelCase')
        'camel_case'
    """
    if not text:
        return ''
    text = str(text)
    s1 = _RE_CAMEL_1.sub(r'\1' + delim + r'\2', text)
    s2 = _RE_CAMEL_2.sub(r'\1' + delim + r'\2', s1)
    return s2.lower()


def get_dcid_name(
    dcid: Union[str, None], schema_nodes: Union[dict, None]
) -> Union[str, None]:
    """Returns the human-readable name for a DCID from schema nodes if defined.

    Args:
        dcid: The DCID string to look up.
        schema_nodes: Dictionary of schema nodes containing properties.

    Returns:
        The name of the DCID if found, or stripped DCID if no name property is
        defined. Returns None if the DCID is not in the schema or invalid.

    Example:
        >>> get_dcid_name('dcid:Count', {'Count': {'name': '"Total Count"'}})
        'Total Count'
    """
    if not dcid or schema_nodes is None:
        return None
    dcid_str = str(dcid)
    node = schema_nodes.get(strip_namespace(dcid_str))
    if not node:
        node = schema_nodes.get(add_namespace(dcid_str))
    if not node or not isinstance(node, dict):
        return None
    name = node.get('name')
    if not name:
        name = strip_namespace(dcid_str)
    return str(name).strip().strip('"').strip()


def get_dcid_token(word: Union[str, None],
                   upper_case: bool = False,
                   remove_prefix: str = '') -> str:
    """Returns the word normalized into a token suitable for a DCID.

    Args:
        word: The raw string to normalize.
        upper_case: If True, converts camelCase to uppercase snake_case.
        remove_prefix: Optional prefix or regex pattern to remove from token.

    Returns:
        A normalized DCID token string with alphanumeric chars and underscores.

    Example:
        >>> get_dcid_token('helloWorld', upper_case=True)
        'HELLO_WORLD'
    """
    if not word:
        return ''
    # Convert any non-alphanumeric characters to '_'
    token = _RE_NON_ALNUM.sub('_', str(word).strip())
    token = _RE_MULTI_UNDERSCORE.sub('_', token).strip('_')

    if upper_case:
        # Convert camelCase to snake_case
        token = camel_to_snake(token).upper()
    if remove_prefix and token:
        try:
            token = re.sub(remove_prefix, '', token)
        except re.error as e:
            logging.warning(
                f'Invalid regex prefix "{remove_prefix}" in get_dcid_token: {e}'
            )
            if token.startswith(remove_prefix):
                token = token[len(remove_prefix):]
    if token:
        token = token.strip('_.-')
        if token and any(c.isalnum() for c in token):
            return token[0].upper() + token[1:]
    return ''


def parse_fixed_properties(
    dcid_props: Union[list[str], tuple[str, ...], None] = None
) -> dict[str, set[str]]:
    """Parses fixed property definitions and their ignored default values.

    Args:
        dcid_props: List of property strings, optionally containing '<>'
            to specify ignored values (e.g. 'statType<>measuredValue').

    Returns:
        A dictionary mapping property names to sets of ignored values.

    Example:
        >>> parse_fixed_properties(
        ...     ['statType<>measuredValue', 'populationType']
        ... )
        {'statType': {'measuredValue'}, 'populationType': {''}}
    """
    if not dcid_props:
        dcid_props = [
            'statType<>measuredValue',
            'measurementQualifier',
            'measuredProperty',
            'populationType',
        ]
    fixed_props = dict()
    for prop_spec in dcid_props:
        if not prop_spec or not isinstance(prop_spec, str):
            continue
        prop = prop_spec.strip()
        val = ''
        if '<>' in prop:
            prop, val = prop.split('<>', 1)
            prop = prop.strip()
            val = val.strip()
        if prop:
            fixed_props.setdefault(prop, set()).add(val)
    return fixed_props


def resolve_dcid_names(pvs: dict,
                       schema_nodes: dict,
                       ignore_props: set[str],
                       use_value_names: bool = False,
                       counters: Counters = None) -> dict[str, str]:
    """Filters ignored properties and fetches missing node names via DC API.

    Args:
        pvs: Source property-value dictionary for the statistical variable.
        schema_nodes: Dictionary of loaded schema nodes to query and update.
        ignore_props: Set of property names to exclude from DCID generation.
        use_value_names: Whether to resolve human-readable names for DCIDs.
        counters: Optional `Counters` object to record lookup statistics.

    Returns:
        A filtered dictionary of property-value pairs to include in the DCID.
    """
    dcid_pvs = dict()
    lookup_dcids = set()
    for prop, value in pvs.items():
        if not prop or prop in ignore_props:
            continue
        dcid_pvs[prop] = value
        if use_value_names:
            if not get_dcid_name(prop, schema_nodes):
                lookup_dcids.add(prop)
            if value and is_leaf_object(value) and not get_dcid_name(
                value, schema_nodes
            ):
                lookup_dcids.add(value)

    if lookup_dcids:
        if counters:
            counters.add_counter('dc_api_lookup_name', len(lookup_dcids))
        try:
            node_names = dc_api_get_node_property_values(list(lookup_dcids))
            if node_names:
                for node_pvs in node_names.values():
                    if node_pvs:
                        add_mcf_node(node_pvs, schema_nodes)
        except Exception as e:
            logging.error(
                f'Failed fetching node names for DCIDs {lookup_dcids}: {e}'
            )
    return dcid_pvs


def strip_overlapping_prop_prefix(value_token: Union[str, None],
                                  prop: Union[str, None],
                                  upper_case: bool = False) -> str:
    """Removes property name prefix from a value token if overlapping.

    If `value_token` starts with the property name (in camelCase, snake_case,
    or uppercase) followed by a delimiter or capital letter, the common prefix
    is removed so that only the distinct value/code remains.

    Args:
        value_token: The normalized token representing the property value.
        prop: The property name string (e.g. 'measurementQualifier').
        upper_case: Whether tokens are being formatted in uppercase.

    Returns:
        The `value_token` with any overlapping property prefix removed.

    Example:
        >>> strip_overlapping_prop_prefix(
        ...     'MeasurementQualifier_Annual', 'measurementQualifier'
        ... )
        'Annual'
        >>> strip_overlapping_prop_prefix(
        ...     'UNIT_PERCENT', 'unit', upper_case=True
        ... )
        'PERCENT'
    """
    if not value_token or not prop:
        return value_token or ''

    val_str = str(value_token)
    prop_str = str(prop).strip()
    if not prop_str or len(val_str) <= len(prop_str):
        return val_str

    # Generate candidate prefixes representing the property string
    candidates = set()
    c_token = get_dcid_token(prop_str, upper_case=upper_case)
    if c_token:
        candidates.add(c_token)
    c_upper = get_dcid_token(prop_str, upper_case=True)
    if c_upper:
        candidates.add(c_upper)
    c_title = get_dcid_token(prop_str, upper_case=False)
    if c_title:
        candidates.add(c_title)

    snake = camel_to_snake(prop_str)
    if snake:
        candidates.add(snake)
        candidates.add(snake.upper())
        candidates.add(snake.replace('_', ''))
        candidates.add(snake.replace('_', '').upper())

    # Sort candidates by length descending to strip the longest matching prefix
    sorted_candidates = sorted(
        [c for c in candidates if c and len(val_str) > len(c)],
        key=len,
        reverse=True,
    )

    for cand in sorted_candidates:
        if val_str.lower().startswith(cand.lower()):
            idx = len(cand)
            next_char = val_str[idx]
            if (next_char in ('_', '-', '.', ':') or
                    next_char.isupper() or upper_case):
                remainder = val_str[idx:].lstrip('_.-:')
                if remainder:
                    if upper_case:
                        return remainder.upper()
                    return remainder[0].upper() + remainder[1:]
    return val_str


def order_dcid_properties(
    dcid_pvs: dict[str, str], fixed_props: dict[str, set[str]]
) -> list[str]:
    """Orders DCID properties, dropping fixed properties with ignored values.

    Fixed properties from the configuration are ordered first in their defined
    sequence, unless value matches an ignored default (e.g. measuredValue).
    All remaining properties are appended in alphabetical order.

    Args:
        dcid_pvs: Filtered property-value dictionary (modified in-place if
            ignored values are popped).
        fixed_props: Mapping of fixed property names to sets of ignored values.

    Returns:
        Ordered list of property names to be tokenized into the DCID.
    """
    ordered_props = []
    for prop, ignored_vals in fixed_props.items():
        prop_val = dcid_pvs.get(prop)
        if prop_val:
            if ignored_vals and prop_val in ignored_vals:
                dcid_pvs.pop(prop, None)
            else:
                ordered_props.append(prop)
    for prop in sorted(dcid_pvs.keys()):
        if prop not in ordered_props:
            ordered_props.append(prop)
    return ordered_props


def _tokenize_dcid(
    ordered_props: list[str],
    dcid_pvs: dict[str, str],
    fixed_props: dict[str, set[str]],
    use_value_names: bool,
    config: dict,
    schema_nodes: dict,
) -> tuple[str, list[tuple[str, str]], list[tuple[str, str]]]:
    """Helper to tokenize properties into fixed and constraint token pairs."""
    dcid_prefix = config.get('statvar_dcid_prefix', '')
    prop_delim = config.get('statvar_dcid_delimiter', '_')
    fixed_prop_delim = config.get('statvar_dcid_fixed_delimiter', '_')
    val_delim = config.get('statvar_dcid_value_delimiter', '')
    upper_case = config.get('statvar_dcid_upper_case', False)
    remove_prefix = config.get('statvar_dcid_remove_prefix', '')

    fixed_pairs = []
    prop_pairs = []
    dcid_fixed_tokens = []
    dcid_prop_tokens = []

    for prop in ordered_props:
        prop_value = dcid_pvs.get(prop)
        if not prop_value:
            continue
        value_name = prop_value
        if use_value_names:
            value_name = get_dcid_name(prop_value, schema_nodes) or prop_value
        value_name = get_dcid_token(value_name, upper_case, remove_prefix)
        value_name = strip_overlapping_prop_prefix(
            value_name, prop, upper_case=upper_case
        )
        if val_delim and prop not in fixed_props:
            prop_name = get_dcid_token(prop, upper_case)
            value_name = prop_name + val_delim + value_name
        if upper_case:
            value_name = value_name.upper()
        if prop in fixed_props:
            fixed_pairs.append((prop, value_name))
            dcid_fixed_tokens.append(value_name)
        else:
            prop_pairs.append((prop, value_name))
            dcid_prop_tokens.append(value_name)

    prop_token = prop_delim.join(dcid_prop_tokens)
    if prop_token:
        dcid_fixed_tokens.append(prop_token)
    dcid = fixed_prop_delim.join(dcid_fixed_tokens)
    if dcid_prefix:
        dcid = dcid_prefix + dcid
    return dcid, fixed_pairs, prop_pairs


def apply_cumulative_property_dropping(
    fixed_pairs: list[tuple[str, str]],
    prop_pairs: list[tuple[str, str]],
    max_len: int,
    config: dict,
) -> str:
    """Drops secondary constraints incrementally to stay within max_len.

    Retains core fixed properties and as many secondary constraint properties
    as can fit within `max_len`. Omitted properties are deterministically
    hashed and appended as a short hash suffix to preserve uniqueness.

    Args:
        fixed_pairs: List of (property, token) tuples for core properties.
        prop_pairs: List of (property, token) tuples for secondary constraints.
        max_len: Maximum allowed character length for the DCID string.
        config: Configuration dictionary with delimiters and prefix settings.

    Returns:
        The truncated DCID string ending with a deterministic hash suffix.
    """
    dcid_prefix = config.get('statvar_dcid_prefix', '')
    prop_delim = config.get('statvar_dcid_delimiter', '_')
    fixed_prop_delim = config.get('statvar_dcid_fixed_delimiter', '_')
    hash_len = config.get('statvar_dcid_hash_length', 8)

    all_tokens = [t for _, t in fixed_pairs + prop_pairs]
    full_str = fixed_prop_delim.join(all_tokens)
    full_hash = hashlib.md5(full_str.encode('utf-8')).hexdigest()[:hash_len]
    full_hash = full_hash.upper()

    retained_fixed = []
    retained_props = []
    omitted = False

    for prop, token in fixed_pairs:
        test_fixed = retained_fixed + [token]
        test_str = fixed_prop_delim.join(test_fixed)
        if dcid_prefix:
            test_str = dcid_prefix + test_str
        if len(test_str) + len(fixed_prop_delim) + hash_len <= max_len:
            retained_fixed.append(token)
        else:
            omitted = True
            break

    if not omitted:
        for prop, token in prop_pairs:
            test_props = retained_props + [token]
            prop_token = prop_delim.join(test_props)
            test_fixed = retained_fixed + [prop_token]
            test_str = fixed_prop_delim.join(test_fixed)
            if dcid_prefix:
                test_str = dcid_prefix + test_str
            if len(test_str) + len(fixed_prop_delim) + hash_len <= max_len:
                retained_props.append(token)
            else:
                omitted = True
                break

    final_fixed = list(retained_fixed)
    if retained_props:
        final_fixed.append(prop_delim.join(retained_props))
    if omitted or not final_fixed:
        final_fixed.append(full_hash)

    dcid = fixed_prop_delim.join(final_fixed)
    if dcid_prefix:
        dcid = dcid_prefix + dcid
    if len(dcid) > max_len:
        budget = max(0, max_len - hash_len - 1)
        clean_prefix = dcid[:budget].rstrip('_.-:/') if budget > 0 else ''
        if clean_prefix:
            return f"{clean_prefix}_{full_hash}"
        return full_hash[:max_len]
    return dcid


def generate_dcid_for_statvar(pvs: Union[dict, None],
                              config: Union[dict, None] = None,
                              schema_nodes: Union[dict, None] = None,
                              counters: Union[Counters, None] = None) -> str:
    """Generates a statistical variable DCID from property-value mappings.

    Args:
        pvs: Dictionary of property-value mappings representing the StatVar.
        config: Configuration dictionary defining DCID generation parameters.
        schema_nodes: Optional dictionary of loaded schema nodes.
        counters: Optional `Counters` object to track statistics.

    Returns:
        A generated DCID string for the StatVar.

    Example:
        >>> generate_dcid_for_statvar(
        ...     {'statType': 'measuredValue', 'measuredProperty': 'count',
        ...      'populationType': 'Person'},
        ...     {}
        ... )
        'Count_Person'
    """
    if not pvs or not isinstance(pvs, dict):
        return ''
    if config is None or not isinstance(config, dict):
        config = {}
    if schema_nodes is None or not isinstance(schema_nodes, dict):
        schema_nodes = {}

    # Parse fixed properties and their default/ignored values from config
    fixed_props = parse_fixed_properties(
        config.get('statvar_dcid_fixed_properties')
    )

    use_value_names = config.get('statvar_dcid_value_name', False)
    ignore_props = set(
        config.get('statvar_dcid_ignore_properties', [
            'description', 'name', 'nameWithLanguage', 'descriptionUrl',
            'alternateName', 'footnote', 'unCode', 'Node', 'typeOf'
        ])
    )

    # Filter ignored properties and resolve missing DCID names via DC API
    dcid_pvs = resolve_dcid_names(
        pvs, schema_nodes, ignore_props, use_value_names, counters
    )

    # Order fixed properties first followed by sorted constraint properties
    ordered_props = order_dcid_properties(dcid_pvs, fixed_props)

    # Tokenize each property value into standardized DCID components
    dcid, fixed_pairs, prop_pairs = _tokenize_dcid(
        ordered_props, dcid_pvs, fixed_props, use_value_names, config,
        schema_nodes
    )

    max_len = config.get('statvar_dcid_max_length', 255)
    if max_len > 0 and len(dcid) > max_len:
        # Fallback Strategy #3: Retry with raw codes instead of long value names
        if use_value_names:
            if counters:
                counters.add_counter('statvar_dcid_fallback_raw_codes', 1)
            dcid, fixed_pairs, prop_pairs = _tokenize_dcid(
                ordered_props, dcid_pvs, fixed_props, False, config,
                schema_nodes
            )
        # Fallback Strategy #4: Cumulative prioritized property dropping + hash
        if len(dcid) > max_len:
            if counters:
                counters.add_counter('statvar_dcid_truncated_with_hash', 1)
            dcid = apply_cumulative_property_dropping(
                fixed_pairs, prop_pairs, max_len, config
            )

    return dcid
