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
"""Utility function to read/write MCF nodes in files.

Uses a dictionary to process nodes of the form:
{
  '<dcid>': OrderedDict( [
                '<property>': '<value>'
                ...
                ])
}
where
  <dcid> is the node dcid with the namespace prefix: 'dcid:'
  <property> is a property name
  <value> is a string with a single value or a comma separated list of values.

  the property:values for a node are in the same order as in the input file.

  Comments in the file are also added as special properties:
  '# comment<N>' where N is the comment number within a node.

This can also be used as a commandline script to merge multiple MCF files into
a single MCF file with consolidated property:values for each node.

For example:
```
python3 mcf_file_util.py --input_mcf=test_data/*.mcf
--output_mcf=/tmp/output.mcf
```
"""

from collections import OrderedDict
import csv
import glob
import os
import re
import sys
from typing import Union
from absl import app
from absl import flags
from absl import logging

_FLAGS = flags.FLAGS

flags.DEFINE_string('input_mcf', '', 'List of MCF files to load.')
flags.DEFINE_string('output_mcf', '', 'output MCF nodes loaded into file.')
flags.DEFINE_bool(
    'append_values',
    True,
    'Append new values to existing properties. If False, new values overwrite'
    ' existing value.',
)
flags.DEFINE_bool('normalize', True, 'If True, values are normalized.')

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

import file_util

_DEFAULT_NODE_PVS = OrderedDict({
    'Node': '',
    'typeOf': '',
    'subClassOf': '',
    'name': '',
    'description': '',
    'populationType': '',
    'measuredProperty': '',
    'measurementQualifier': '',
    'statType': '',
    'measurementDenominator': '',
})


def add_namespace(value: Union[str, list], namespace: str = 'dcid') -> str:
    """Adds a namespace prefix to a string value, commonly used for DCIDs.

    This function checks if a value is a string and does not already have a
    namespace prefix (e.g., 'dcid:', 'dcs:'). If it's a simple string without a
    colon, it prepends the specified namespace. It can also handle comma-separated
    string values, applying the namespace to each part. It avoids adding a
    namespace to quoted strings or values that are not strings.

    Args:
        value: The string or list of strings to which the namespace will be added.
        namespace: The namespace prefix to add, defaulting to 'dcid'.

    Returns:
        The value with the namespace prefix. If the value already has a
        namespace, is a quoted string, or is not a string, it is returned
        unchanged. For lists, returns a comma-separated string with namespaces
        added to each element.

    Examples:
        >>> add_namespace('Count_Person')
        'dcid:Count_Person'
        >>> add_namespace('dcs:Count_Person')
        'dcs:Count_Person'
        >>> add_namespace('"My Name"')
        '"My Name"'
        >>> add_namespace(['Person', 'Animal'])
        'dcid:Person,dcid:Animal'
        >>> add_namespace('name,place')
        'dcid:name,dcid:place'
        >>> add_namespace(123)
        123
        >>> add_namespace(None)
        None
        >>> add_namespace('')
        ''
    """
    if isinstance(value, list):
        value_list = [add_namespace(v) for v in value]
        return ','.join(value_list)
    if value and isinstance(value, str):
        if value[0].isalpha() or value[0].isdigit():
            if ',' in value:
                value_list = get_value_list(value)
                return ','.join([add_namespace(v) for v in value_list])
            has_alpha = False
            for c in value:
                if c.isalpha() or c == '_' or c == '/':
                    has_alpha = True
                    break
            if has_alpha and value.find(':') < 0:
                return f'{namespace}:{value}'
    return value


def strip_namespace(value: str) -> str:
    """Removes a namespace prefix (e.g., 'dcid:', 'dcs:') from a string value.

    This function checks for a namespace, defined as a sequence of letters
    followed by a colon, at the beginning of the string. If found, it returns
    the string without this prefix. It is designed to ignore quoted strings,
    leaving them unchanged.

    Args:
        value: The string from which to strip the namespace.

    Returns:
        The string without the namespace prefix, or the original string if no
        namespace is found or if it's a quoted string.

    Examples:
        >>> strip_namespace('dcid:Count_Person')
        'Count_Person'
        >>> strip_namespace('dcs:Person')
        'Person'
        >>> strip_namespace('Count_Person')
        'Count_Person'
        >>> strip_namespace('"dcid:ignore"')
        '"dcid:ignore"'
        >>> strip_namespace(123)
        123
    """
    if value and isinstance(value, str):
        if '"' in value:
            # Do not modify quoted strings.
            return value
        pos = 0
        len_value = len(value)
        while pos < len_value:
            if not value[pos].isalpha():
                break
            pos += 1
        if pos < len_value and value[pos] == ':':
            return value[pos + 1:].strip()
    return value


def strip_value(value: str) -> str:
    """Strips leading/trailing whitespace from a string value, handling quoted strings.

    This function removes whitespace from the beginning and end of a string.
    If the string is enclosed in double quotes, it strips whitespace from within
    the quotes, preserving the quotes themselves.

    Args:
        value: The string to be stripped.

    Returns:
        The stripped string.

    Examples:
        >>> strip_value('  my value  ')
        'my value'
        >>> strip_value('"  quoted value  "')
        '"quoted value"'
        >>> strip_value('no extra space')
        'no extra space'
        >>> strip_value(123)
        123
    """
    if value and isinstance(value, str):
        value = value.strip()
        if value and value[0] == '"' and value[-1] == '"':
            value_str = value[1:-1]
            value_str = value_str.strip()
            value = '"' + value_str + '"'
    return value


def get_pv_from_line(line: str) -> (str, str):
    """Parses a line of text to extract a property and a value.

    This function splits a line at the first colon (':') to separate the
    property from the value. It strips leading/trailing whitespace from both
    the property and the value. If no colon is found, the entire line is
    treated as the value, and the property is returned as an empty string.

    Args:
        line: The input string, typically in a 'property: value' format.

    Returns:
        A tuple containing the property (string) and the value (string).

    Examples:
        >>> get_pv_from_line('name: "My Node"')
        ('name', '"My Node"')
        >>> get_pv_from_line('  typeOf : StatVar  ')
        ('typeOf', 'StatVar')
        >>> get_pv_from_line('description')
        ('', 'description')
        >>> get_pv_from_line(': a value')
        ('', 'a value')
    """
    pos = line.find(':')
    if pos < 0:
        return ('', line)
    prop = line[:pos].strip()
    value = line[pos + 1:].strip()
    return (prop, value)


def _merge_pv_values(existing_value: Union[str, list], new_value: str,
                     strip_namespaces: bool, normalize: bool) -> str:
    """Merges a new value with an existing property value.

    If the new value is the same as the existing one, the existing value is
    returned. Otherwise, the new value is added to the existing value, creating a
    comma-separated list if necessary.

    Args:
        existing_value: The current value of the property.
        new_value: The new value to be added.
        strip_namespaces: If True, namespace prefixes are removed from the values.
        normalize: If True, the merged list is normalized.

    Returns:
        The merged value.
    """
    if new_value is None or new_value == existing_value:
        return existing_value

    # If new value or existing value is a list, need to dedup and merge
    if (isinstance(existing_value, list) or ',' in str(existing_value) or
            isinstance(new_value, list) or ',' in str(new_value)):
        # Merge the lists
        unique_values = []
        for v in get_value_list(str(existing_value)):
            if v not in unique_values:
                unique_values.append(v)
        for v in get_value_list(str(new_value)):
            if v not in unique_values:
                unique_values.append(v)

        if '"' in str(existing_value) or '"' in str(new_value):
            unique_values = [
                get_quoted_value(v, is_quoted=True) for v in unique_values
            ]
        if strip_namespaces:
            unique_values = [strip_namespace(v) for v in unique_values]
        if normalize:
            return normalize_list(','.join(sorted(unique_values)))
        return ",".join(unique_values)
    else:
        # Existing and new values are not list, so can be appended.
        return f'{existing_value},{new_value}'


def add_pv_to_node(
    prop: str,
    value: Union[str, list],
    node: dict,
    append_value: bool = True,
    strip_namespaces: bool = False,
    normalize: bool = True,
) -> dict:
    """Adds a property-value (PV) pair to a node dictionary.

    This function manages the addition of a PV to a node, with options for how
    to handle existing properties. It can append new values to a comma-separated
    list, replace existing values, and optionally normalize values by stripping
    whitespace and handling namespaces.

    Args:
        prop: The property of the PV pair (e.g., "typeOf", "name").
        value: The value of the PV pair. Can be a single value or a list of values.
        node: The dictionary representing the node to which the PV will be added.
        append_value: If True, new values are appended to existing values, creating
            a comma-separated list if necessary. If False, the existing value is
            replaced.
        strip_namespaces: If True, namespace prefixes (e.g., "dcid:") are
            removed from the value before processing.
        normalize: If True, the value is normalized (e.g., whitespace stripped,
            lists sorted).

    Returns:
        The updated node dictionary.

    Examples:
        >>> node = {'name': 'Person'}
        >>> add_pv_to_node('name', 'Human', node)
        {'name': 'Human,Person'}
        >>> add_pv_to_node('name', 'Human', node, append_value=False)
        {'name': 'Human'}
        >>> add_pv_to_node('typeOf', 'dcid:Class', {}, strip_namespaces=True)
        {'typeOf': 'Class'}
    """
    if node is None:
        node = {}
    if value and isinstance(value, str):
        if strip_namespaces:
            value = strip_namespace(value)
    if isinstance(value, list):
        if strip_namespaces:
            value = [strip_namespace(v) for v in value]
        value = ",".join(value)

    if normalize:
        if value and isinstance(value, str):
            value = strip_value(value)
            if value and ',' in value:
                # Split the comma separated value into a list.
                value = normalize_list(value, False)
        # Allow empty value
        # if not value:
        #    return node

    # allow empty values
    # if not value:
    #    return node
    existing_value = node.get(prop)
    if existing_value is not None and prop != 'Node' and prop != 'dcid':
        if append_value:
            if isinstance(existing_value, list):
                existing_value = ','.join(existing_value)
            node[prop] = _merge_pv_values(existing_value, value,
                                          strip_namespaces, normalize)
        else:
            # Replace with new value
            node[prop] = value
    else:
        # Add a new property:value
        node[prop] = value
    return node


def add_comment_to_node(comment: str, node: dict) -> dict:
    """Add a comment to the node. The comments are preserved in the order read.

  Args:
    comment: a comment string
    node: dictionary to whcih comment is to be added as a key.

  Returns:
    dictionary with the comment added.

  Comments are added as a property with a '#' prefix and index suffix,
  for example, '# comment1', '# comment2'.
  """
    # Count the existing comments in the node.
    num_comments = 0
    for c, v in node.items():
        if not c or c[0] != '#':
            continue
        if v == comment:
            # skip existing comment
            return node
        num_comments += 1
    next_comment_index = num_comments + 1
    # Add the new comment with the next index.
    node[f'# comment{next_comment_index}'] = comment
    return node


def get_node_dcid(pvs: dict) -> str:
    """Returns the dcid of the node without the namespace prefix.

  Args:
    pvs: dictionary of property:value for the node.

  Returns:
    nodes dcid if one is set.
  dcid is taken from the following properties in order:
    'dcid'
    'Node'
  """
    if not pvs:
        return ''
    dcid = pvs.get('Node', '')
    dcid = pvs.get('dcid', dcid)
    dcid = dcid.strip(' "')
    return strip_namespace(dcid)


def add_mcf_node(
    pvs: dict,
    nodes: dict,
    strip_namespaces: bool = False,
    append_values: bool = True,
    normalize: bool = True,
) -> dict:
    """Add a node with property values into the nodes dict

  If the node exists, the PVs are added to the existing node.

  Args:
    pvs: dictionary of property: values of the new node to be added.
    nodes: dictionary of existing nodes with property:value dict for each node.
    strip_namespaces: if True, strip namespace from the dcid key and values.
    append_values: if True, append new value for an exsting property, else
      replace with new value.

  Returns
    nodes dictionary to which the new node is added.
  """
    if pvs is None or len(pvs) == 0:
        return None
    dcid = get_node_dcid(pvs)
    if dcid == '':
        logging.warning(f'Ignoring node without a dcid: {pvs}')
    if strip_namespaces:
        dcid = strip_namespace(dcid)
    else:
        dcid = add_namespace(dcid)
    if dcid not in nodes:
        nodes[dcid] = {}
    node = nodes[dcid]
    for prop, value in pvs.items():
        add_pv_to_node(prop, value, node, append_values, strip_namespaces,
                       normalize)
    logging.level_debug() and logging.log(
        2, f'Added node {dcid} with properties: {pvs.keys()}')
    return nodes


def update_mcf_nodes(
    nodes: dict,
    output_nodes: dict,
    strip_namespaces: bool = False,
    append_values: bool = True,
    normalize: bool = True,
) -> dict:
    """Returns output_nodes with Property:values from nodes added.

  Args:
    nodes: dictionary of MCF nodes in the form:
      { <dcid>: { <prop> : <value> ...} ... }
    output_nodes: Nodes to be updated
    strip_namespaces: if True, strip namespace from the dcid key and values.
    append_values: if True, append new value for an exsting property, else
      replace with new value.
    normalize: if True, values are normalized.

  Returns:
    dictionary of output_nodes updated with property:values from nodes.
  """
    index = 0
    for key, node in nodes.items():
        # Set the node dcid if not present.
        dcid = get_node_dcid(node)
        if not dcid:
            dcid = key
            if not key:
                dcid = str(index)
            node['Node'] = add_namespace(dcid)
        # Add PVs from node to output_nodes
        add_mcf_node(node, output_nodes, strip_namespaces, append_values,
                     normalize)
    return output_nodes


def load_mcf_nodes(
    filenames: Union[str, list],
    nodes: dict = None,
    strip_namespaces: bool = False,
    append_values: bool = True,
    normalize: bool = True,
) -> dict:
    """Return a dict of nodes from the MCF file with the key as the dcid

  and a dict of property:value for each node.

  Args:
    filenames: command seperated string or a list of MCF filenames
    nodes: dictonary to which new nodes are added. If a node with dcid exists,
      the new properties are added to the existing node.
    strip_namespace: if True, strips namespace from the value for node
      properties as well as the dcid key for the nodes dict.
    append_values: if True, appends new values for existing properties into a
      comma seperated list, else replaces existing value.

  Returns:
    dictionary with dcid as the key and a values as a dict of property:values
      {
        '<dcid1>': {
          '<prop1>': '<value1>',
          '<prop2>': '<value2>'
          ...
        },
        '<dcid2>': {
          ...
        },
        ...
      }
  """
    if not filenames:
        return nodes
    # Load files in order of input
    files = []
    if isinstance(filenames, str):
        filenames = filenames.split(',')
    for file in filenames:
        files.extend(file_util.file_get_matching(file))
    if nodes is None:
        nodes = _get_new_node(normalize)
    for file in files:
        if not file:
            continue
        num_nodes = 0
        num_props = 0
        if file.endswith('.csv'):
            # Load nodes from CSV
            file_nodes = file_util.file_load_csv_dict(file)
            for key, pvs in file_nodes.items():
                if 'Node' not in pvs:
                    pvs['Node'] = key
                num_props += len(pvs)
                add_mcf_node(pvs, nodes, strip_namespaces, append_values,
                             normalize)
            num_nodes = len(file_nodes)
        else:
            # Load nodes from MCF file.
            with file_util.FileIO(file, 'r', errors='ignore') as input_f:
                pvs = _get_new_node(normalize)
                for line in input_f:
                    # Strip leading trailing whitespaces
                    line = re.sub(r'\s+$', '', re.sub(r'^\s+', '', line))
                    if line and line[0] == '"' and line[-1] == '"':
                        line = line[1:-1]
                    if line == '""':
                        # MCFs downloaded from sheets have "" for empty lines.
                        line = ''
                    if line.count('""') > 1:
                        # MCFs from sheets have quotes escaped as '""<text>""'
                        line = line.replace('""', '"')
                    if line == '':
                        if pvs:
                            add_mcf_node(pvs, nodes, strip_namespaces,
                                         append_values, normalize)
                            num_nodes += 1
                            pvs = _get_new_node(normalize)
                    elif line[0] == '#':
                        add_comment_to_node(line, pvs)
                    else:
                        prop, value = get_pv_from_line(line)
                        if strip_namespaces:
                            value = strip_namespace(value)
                        add_pv_to_node(prop, value, pvs, append_values,
                                       strip_namespace, normalize)
                        num_props += 1
                if pvs:
                    add_mcf_node(pvs, nodes, strip_namespaces, append_values,
                                 normalize)
                    num_nodes += 1
        logging.info(
            f'Loaded {num_nodes} nodes with {num_props} properties from file {file}'
        )
    return nodes


def filter_mcf_nodes(
    nodes: dict,
    allow_dcids: list = None,
    allow_nodes_with_pv: list = None,
    ignore_nodes_with_pv: list = None,
) -> dict:
    """Filter dictionary of Nodes to a subset of allowed dcids.

  Args:
    nodes: dictionary of nodes keyed by dcid.
    allow_dcids: list of dcids to be returned.
    allow_nodes_with_pv: list of properties nodes with any of the properties in
      the list are returned.
    ignore_nodes_with_pv: list of properties to be ignored. nodes with any of
      the properties in the list are dropped.

  Returns:
    dictionary with the filtered nodes.
  """
    # Normalize ignored PVs.
    ignored_pvs = set()
    ignored_pvs = _pv_list_to_dict(ignore_nodes_with_pv)
    compared_pvs = _pv_list_to_dict(allow_nodes_with_pv)
    filtered_nodes = {}
    for k, v in nodes.items():
        # Drop nodes with dcid not in allowed list.
        if allow_dcids and strip_namespace(k) in allow_dcids:
            logging.log(2, f'Dropping dcid not in compare_dcid: {k}, {v}')
            continue
        # Drop nodes containing any ignored property value.
        drop_node = False
        for prop, value in v.items():
            if prop and prop[0] != '#':
                if _is_pv_in_dict(prop, value, ignored_pvs):
                    logging.log(
                        2,
                        f'Dropping dcid with ignored pv {prop}:{value}: {k}, {v}'
                    )
                    drop_node = True
                    break
                if compared_pvs and not _is_pv_in_dict(prop, value,
                                                       compared_pvs):
                    logging.log(
                        2,
                        f'Dropping dcid without any compared pv {prop}:{value}: {k}, {v}',
                    )
                    drop_node = True
                    break
        if not drop_node:
            filtered_nodes[k] = v
    return filtered_nodes


def get_numeric_value(value: str,
                      decimal_char: str = '.',
                      separator_chars: str = ' ,$%') -> Union[int, float, None]:
    """Returns the float value from string or None.

  Args:
    value: string to be converted into a number. It can have comma separted
      digits with decimal points, for eg: NN,NNN.NNN
    decimal_char: character used for decimal place seperator, default: '.'
    seperator_char: seperator characters for 1000s or 100s for example:
      NNN,NNN,NNN

  Returns:
    number as a float or int if the value is a number, None otherwise
  """
    if isinstance(value, int) or isinstance(value, float):
        return value
    if value and isinstance(value, str):
        try:
            # Strip separator characters from the numeric string
            normalized_value = value.strip()
            if (normalized_value[0].isdigit() or normalized_value[0] == '.' or
                    normalized_value[0] == '-' or normalized_value[0] == '+'):
                # Input looks like a number. Remove allowed extra characters.
                normalized_value = ''.join(
                    [c for c in normalized_value if c not in separator_chars])
                # Replace decimal characters with period '.'
                if decimal_char != '.':
                    normalized_value = '.'.join(
                        normalized_value.split(decimal_char))
                if value.count('.') > 1:
                    # Period may be used instead of commas. Remove it.
                    normalized_value = normalized_value.replace('.', '')
            if normalized_value.count('.') == 1:
                float_val = float(normalized_value)
                # Convert to int if there are no decimal values
                int_val = int(float_val)
                if int_val == float_val:
                    return int_val
                return float_val
            return int(normalized_value)
        except ValueError:
            # Value is not a number. Ignore it.
            return None
    return None


def get_quoted_value(value: str, is_quoted: bool = None) -> str:
    """Returns a quoted string if there are spaces and special characters.

  Args:
    value: string value to be quoted if necessary.
    is_quoted: if True, returns values as quotes strings.

  Returns:
    value with optional double quotes.
  """
    if not value or not isinstance(value, str):
        return value

    value = value.strip('"')
    value = value.strip()
    if value.startswith('[') and value.endswith(']'):
        return normalize_range(value)
    if ' ' in value or ',' in value or is_quoted:
        if value[0] != '"':
            return '"' + value + '"'
    return value


def get_value_list(value: str) -> list:
    """Returns the value as a list

  Args:
    value: string with a single value or comma seperated list of values

  Returns:
    value as a list.
  """
    if isinstance(value, list):
        return value
    value_list = []
    # Read the string as a comma separated line.
    is_quoted = '"' in value
    try:
        if is_quoted and "," in value:
            # Read the string as a quoted comma separated line.
            row = list(
                csv.reader([value],
                           delimiter=',',
                           quotechar='"',
                           skipinitialspace=True))[0]
        else:
            # Without " quotes, the line can be split on commas.
            # Avoiding csv reader calls for performance.
            row = value.split(',')
        for v in row:
            val_normalized = get_quoted_value(v, is_quoted=is_quoted)
            value_list.append(val_normalized)
    except csv.Error:
        logging.error(
            f'Too large value {len(value)}, failed to convert to list')
        value_list = [value]
    return value_list


def normalize_list(value: str, sort: bool = True) -> str:
    """Normalize a comma separated list of sorting strings.

  Args:
    value: string value to be normalized. Can be a comma separated list or a
      sequence of characters.
    sort: if True, lists are sorted alphabetically.

  Returns:
    string that is a normalized version of value with duplicates removed.
  """
    if ',' in value:
        has_quotes = False
        if '"' in value:
            if value[0] == '"' and value[-1] == '"':
                if '{' in value or '[' in value:
                    # Retain dict value strings such as geoJsonCoordinates  as is.
                    return value
            # Sort comma separated text values.
            value_list = get_value_list(value)
            has_quotes = True
        else:
            value_list = value.split(',')
        values = []
        if sort:
            value_list = sorted(value_list)
        for v in value_list:
            if v not in values:
                normalized_v = normalize_value(
                    v,
                    quantity_range_to_dcid=False,
                    maybe_list=False,
                    is_quoted=has_quotes,
                )
                normalized_v = str(normalized_v)
                values.append(normalized_v)
        return ','.join(values)
    else:
        return value


def normalize_range(value: str, quantity_range_to_dcid: bool = False) -> str:
    """Normalize a quantity range into [<N> <M> Unit].

  Args:
    value: quantity or quantity range as a string.
    quantity_range_to_dcid: if True, converts quantity range to a dcid [ <start>
      <end> <unit>] is converted to dcid:Unit<start>To<end> if False, the
      quantity range is returned with unit at the end.

  Retruns:
    string with quantity range of the form '[<start> <end> <unit>]'
    or dcid:UnitStartToEnd if quantity_range_to_dcid is True.
  """
    # Check if value is a quantity range
    quantity_pat = (
        r'\[ *(?P<unit1>[A-Z][A-Za-z0-9_/]*)? *(?P<start>[0-9\.]+|-)?'
        r' *(?P<end>[0-9\.]+|-)? *(?P<unit2>[A-Z][A-Za-z0-9_]*)? *\]')
    matches = re.search(quantity_pat, value)
    if not matches:
        return value

    match_dict = matches.groupdict()
    if not match_dict:
        return value

    logging.log(2, f'Matched range: {match_dict}')

    # Value is a quantity range. Get the start, end and unit.
    start = match_dict.get('start', '')
    end = match_dict.get('end', '')
    unit = match_dict.get('unit1', '')
    unit2 = match_dict.get('unit2', unit)
    if unit2:
        unit = unit2
    normalized_range = ''
    if quantity_range_to_dcid:
        # Normalize quantity range to a dcid
        if unit:
            normalized_range += unit
        if start and start != '-':
            if end:
                if end != '-':
                    normalized_range += f'{start}To{end}'
                else:
                    normalized_range += f'{start}Onwards'
            else:
                normalized_range += f'{start}'
        else:
            normalized_range += f'Upto{end}'
        return add_namespace(normalized_range)
    normalized_range = '['
    if start:
        normalized_range += start + ' '
    if end:
        normalized_range += end + ' '
    if unit:
        normalized_range += unit
    normalized_range += ']'
    return normalized_range


def normalize_value(
    value,
    quantity_range_to_dcid: bool = False,
    maybe_list: bool = True,
    is_quoted: bool = False,
) -> str:
    """Normalize a property value adding a standard namespace prefix 'dcid:'.

  Args:
    value: string as a value of a property to be normalized.
    quantity_range_to_dcid: if True, convert quantity range to a dcid.
    maybe_list: if True, values with ',' are converted to a normalized list.

  Returns:
    normalized value with namespace 'dcid' for dcid values
    sorted list for comma separated values.
  """
    if value:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return ''
            if value[0] == '"' and value[-1] == '"' and len(value) > 100:
                # Retain very long strings, such as geoJsonCoordinates, as is.
                return value
            if ',' in value and maybe_list:
                return normalize_list(value)
            if value[0] == '[':
                return normalize_range(value, quantity_range_to_dcid)
            # Check if string is a numeric value.
            number = get_numeric_value(value)
            if number:
                return normalize_value(number)
            if ' ' in value or ',' in value or is_quoted:
                return get_quoted_value(value, is_quoted)
            # Normalize string with a standardized namespace prefix.
            if '__' in value:
                # For concatenated sequence of dcids, keep them sorted.
                values = strip_namespace(value).split('__')
                value = '__'.join(sorted(values))
            return add_namespace(strip_namespace(value))
        elif isinstance(value, float):
            # Return a fixed precision float string.
            return f'{value}'
        elif isinstance(value, list):
            # Sort a list of values normalizing the namespace prefix.
            values = sorted([
                normalize_value(x, quantity_range_to_dcid, is_quoted=is_quoted)
                for x in value
            ])
            return ','.join(values)
    return value


def normalize_pv(prop: str, value: str) -> str:
    """Returns a normalized property:value string.

  Args:
    prop: property name as a string
    value: property value as a string

  Returns:
    string of the form '<prop>:<value>' where value is normalized.
  """
    return ':'.join([prop.strip(), normalize_value(value)])


def normalize_mcf_node(
    node: dict,
    ignore_comments: bool = True,
    quantity_range_to_dcid: bool = False,
) -> dict:
    """Returns a normalized MCF node with all PVs in alphabetical order,

  a common namespace of 'dcid' and comma separated lists also sorted.

  Args:
    node: a dictionary with property:value
    ignore_comments: if True, properties that start with '#' are dropped.
    quantity_range_to_dcid: if True, quantity rane is converted to dcid.

  Returns:
    dictionary with normalized property:values.
  """
    normal_node = OrderedDict({})
    props = list(node.keys())
    # Add the nodes dcid.
    dcid = get_node_dcid(node)
    if dcid:
        normal_node['Node'] = add_namespace(dcid)
    for p in ['Node', 'dcid']:
        if p in props:
            props.remove(p)

    # Add remaining properties in alphabetical order.
    for p in sorted(props):
        if p and p[0] == '#' and ignore_comments:
            # Ignore comments
            continue
        value = node[p]
        if not value:
            continue
        normal_node[p] = normalize_value(value, quantity_range_to_dcid)
    logging.log(3, f'Normalized {node} to {normal_node}')
    return normal_node


def node_dict_to_text(node: dict, default_pvs: dict = _DEFAULT_NODE_PVS) -> str:
    """Convert a dictionary node of PVs into text.

  Args:
    node: dictionary of property: values.
    default_pvs: dictionary with default property:values. These properties are
      added to the node if not present.

  Returns:
    node as a text string with a property:value per line
  """
    props = list(node.keys())
    pvs = []
    # Add any initial comments
    for prop in node.keys():
        if prop and prop[0] != '#':
            break
        pvs.append(node[prop])
        props.remove(prop)

    # Add default properties in order.
    for prop, default_value in default_pvs.items():
        value = node.get(prop, default_value)
        if value != '':
            pvs.append(_get_prop_value_line(prop, value))
        if prop in props:
            props.remove(prop)
    # Add remaining property values.
    for prop in props:
        if prop and prop[0] == '#':
            # Add comment as is in the same order.
            if prop.startswith('# comment'):
                pvs.append(f'{node[prop]}')
            else:
                pvs.append(f'{prop}{node[prop]}')
            continue
        value = node.get(prop, '')
        if value != '':
            pvs.append(_get_prop_value_line(prop, value))
    return '\n'.join(pvs)


def write_mcf_nodes(
    node_dicts: list,
    filename: str,
    mode: str = 'w',
    default_pvs: dict = _DEFAULT_NODE_PVS,
    header: str = None,
    ignore_comments: bool = True,
    sort: bool = False,
):
    """Write the nodes to an MCF file.

  Args:
    node_dicts: dictionary of nodes keyed by dcid and each node as a dictionary
      of property:value.
    filename: output MCF file to be written
    mode: if 'a', nodes are appended to existing file. else file is overwritten
      with the nodes.
    default_pvs: dictionary of default property:value to be added to all nodes.
    header: string written as a comment at the begining of the file.
    ignore_comments: if True, drop comments that begin with '#' in the property.
    sort: if True, nodes in the output file are sorted by dcid. the properties
      in the node are also sorted.
  """
    if not node_dicts:
        return
    if isinstance(node_dicts, dict):
        # Caller has a single dict of nodes. Create a list of dicts for it.
        node_dicts = [node_dicts]
    if filename.endswith('.csv'):
        # Write PVs as a csv
        node_dict = node_dicts[0]
        for d in node_dicts[1:]:
            node_dict.update(d)
        file_util.file_write_csv_dict(node_dict, filename)
        return
    with file_util.FileIO(filename, mode) as output_f:
        if header is not None:
            output_f.write(header)
            output_f.write('\n')
        for nodes in node_dicts:
            node_keys = list(nodes.keys())
            if sort:
                node_keys = sorted(node_keys)
            for dcid in node_keys:
                node = nodes[dcid]
                if sort:
                    node = normalize_mcf_node(node, ignore_comments)
                pvs = node_dict_to_text(node, default_pvs)
                if len(pvs) > 0:
                    output_f.write(pvs)
                    output_f.write('\n\n')


def _get_prop_value_line(prop, value) -> str:
    """Return a text line for a property and value."""
    if isinstance(value, list):
        value = ','.join([add_namespace(x) for x in value])
    else:
        value = add_namespace(value)
    return f'{prop}: {value}'


def _pv_list_to_dict(pv_list: list) -> dict:
    """Convert a list of property:value into a set of PVs."""
    pvs = set()
    if not pv_list:
        return pvs

    for pv in pv_list:
        if isinstance(pv, str):
            if ':' in pv:
                prop, value = pv.split(':', 1)
            else:
                prop, value = pv, ''
            prop = prop.strip()
            value = normalize_value(value)
            if prop not in pvs:
                pvs[prop] = set()
            pvs[prop].add(value)
    return pvs


def _is_pv_in_dict(prop: str, value: str, pvs: dict) -> bool:
    """Returns true if the property:value or propert is in the pvs dict."""
    if not prop:
        return False
    prop = prop.strip()
    if value:
        value = normalize_value(value)
    if prop in pvs:
        if value and value in pvs[prop]:
            return True
        if '' in pvs[prop]:
            return True
    return False


def _get_new_node(normalize: bool = True) -> dict:
    """Returns OrderedDict if normalize is true, else a dict."""
    if normalize:
        return OrderedDict()
    return dict()


def main(_):
    if not _FLAGS.input_mcf or not _FLAGS.output_mcf:
        print(f'Please provide input and output MCF files with --input_mcf and'
              f' --output_mcf.')
        return
    nodes = load_mcf_nodes(_FLAGS.input_mcf,
                           append_values=_FLAGS.append_values,
                           normalize=_FLAGS.normalize)
    write_mcf_nodes([nodes], _FLAGS.output_mcf)
    logging.info(f'{len(nodes)} MCF nodes from {_FLAGS.input_mcf} written to'
                 f' {_FLAGS.output_mcf}')


if __name__ == '__main__':
    app.run(main)
