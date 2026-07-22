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
"""Script and class to generate statvar groups for UN Statistical Variables.

Usage:
    python3 generate_statvar_groups.py \
        --input_statvar_mcf=statvars.mcf \
        --input_schema_mcf=schema.mcf \
        --output_statvar_group_mcf=statvar_groups.mcf
"""

import itertools
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
sys.path.append(_DATA_DIR)
sys.path.append(os.path.join(_DATA_DIR, 'util'))
sys.path.append(os.path.join(_DATA_DIR, 'tools', 'statvar_importer'))

import file_util
from mcf_file_util import (
    add_mcf_node,
    add_namespace,
    get_node_dcid,
    load_mcf_nodes,
    strip_namespace,
    write_mcf_nodes,
)

from config_map import ConfigMap
from counters import Counters

flags.DEFINE_string('input_statvar_mcf', '', 'MCF files with statvar nodes.')
flags.DEFINE_string('output_statvar_group_mcf', '',
                    'Output MCF files for statvar groups.')
flags.DEFINE_string('input_schema_mcf', '',
                    'Schema file with names for properties.')
flags.DEFINE_string('statvar_root', 'dc/g/Root', 'Root for the statvar group.')
flags.DEFINE_string('statvar_group_prefix', 'custom/g/undata',
                    'Prefix for the statvar group.')
flags.DEFINE_string('statvar_dcid_remove_prefix', '',
                    'Prefix pattern to remove from statvar DCIDs or names.')
flags.DEFINE_list('statvar_property_order', ['populationType'],
                  'Statvar properties ordered by group hierarchy.')
flags.DEFINE_bool(
    'statvar_group_permutations', True,
    'Generate statvar groups for all permutations of properties.')
flags.DEFINE_bool(
    'statvar_add_linked_member_of', True,
    'Add linkedMemberOf property to statvars to all its parent groups.')
flags.DEFINE_integer('logging_level', logging.INFO, 'Logging level.')

_FLAGS = flags.FLAGS

_DEFAULT_IGNORE_PROP = {
    'Node': '',
    'dcid': '',
    'typeOf': '',
    'memberOf': '',
    'footnote': '',
    'description': '',
    'name': '',
    'measuredProperty': 'value',
    'statType': 'measuredValue',
}

_RE_CAMEL = re.compile(r'(?<=[a-z0-9])(?=[A-Z])')
_RE_UNDERSCORE_SPACE = re.compile(r'[_ ]+')


def get_default_statvar_group_config() -> dict:
    """Returns the default statvar group configuration dictionary.

    Returns:
        Dictionary mapping configuration options to parsed command-line flags.

    Example:
        >>> cfg = get_default_statvar_group_config()
        >>> 'svg_root' in cfg
        True
    """
    return {
        'svg_root': _FLAGS.statvar_root,
        'svg_prefix': _FLAGS.statvar_group_prefix,
        'svg_properties': _FLAGS.statvar_property_order,
        'statvar_dcid_remove_prefix': _FLAGS.statvar_dcid_remove_prefix,
        'svg_dcid_remove_prefix': _FLAGS.statvar_dcid_remove_prefix,
        'statvar_group_permutations': _FLAGS.statvar_group_permutations,
        'statvar_add_linked_member_of': _FLAGS.statvar_add_linked_member_of,
    }


def to_snake_case(text: Union[str, None],
                  delim: str = '_',
                  upper: bool = True) -> str:
    """Converts camelCase or space-separated text to snake_case.

    Args:
        text: The source string to convert.
        delim: Delimiter to insert between words (default is '_').
        upper: If True, returns uppercase string; otherwise returns exactly
            as cased after substitution.

    Returns:
        The converted string, or empty string if input is None or empty.

    Example:
        >>> to_snake_case('camelCaseText')
        'CAMEL_CASE_TEXT'
        >>> to_snake_case('camelCaseText', upper=False)
        'camel_Case_Text'
    """
    if not text:
        return ''
    sentence = _RE_CAMEL.sub(delim, str(text))
    sentence = _RE_UNDERSCORE_SPACE.sub(delim, sentence).strip()
    if upper:
        return sentence.upper()
    return sentence


def to_quoted(text: Union[str, None]) -> str:
    """Wraps string in double quotes and normalizes internal quotes.

    Args:
        text: The raw string to quote.

    Returns:
        The string enclosed in double quotes with internal quotes replaced by
        single quotes, or empty string if input is None or empty.

    Example:
        >>> to_quoted('Hello "World"')
        '"Hello \'World\'"'
    """
    if not text:
        return ''
    s = str(text).strip()
    if s.startswith('"') and s.endswith('"') and len(s) >= 2:
        s = s[1:-1].strip()
    cleaned = s.replace('"', "'")
    if cleaned:
        return f'"{cleaned}"'
    return ''


def strip_prefix_safe(text: Union[str, None],
                      prefix_pattern: Union[str, None]) -> str:
    """Removes regex prefix pattern safely without raising exceptions.

    Args:
        text: The string to strip prefix from.
        prefix_pattern: Optional regular expression string pattern to remove.

    Returns:
        The string with the matching prefix removed.

    Example:
        >>> strip_prefix_safe('TEST_Population', 'TEST_')
        'Population'
    """
    if not text:
        return ''
    val_str = str(text)
    if not prefix_pattern:
        return val_str
    try:
        return re.sub(str(prefix_pattern), '', val_str)
    except re.error as e:
        logging.warning(
            f'Invalid regex prefix "{prefix_pattern}": {e}'
        )
        if val_str.startswith(str(prefix_pattern)):
            return val_str[len(str(prefix_pattern)):]
        return val_str


class UNStatVarGroupGenerator:
    """Generator class that builds StatVarGroup hierarchy from StatVars."""

    def __init__(
        self,
        config_dict: Union[dict, None] = None,
        counters: Union[Counters, None] = None,
    ):
        """Initializes the UNStatVarGroupGenerator.

        Args:
            config_dict: Optional configuration map overriding defaults.
            counters: Optional `Counters` tracker object for reporting stats.
        """
        self._config = ConfigMap()
        if config_dict and isinstance(config_dict, dict):
            self._config.update_config(config_dict)
        self._counters = counters
        if self._counters is None:
            self._counters = Counters()
        self._schema_nodes = {}
        self._statvar_groups = {}

    def load_schema_mcf(self, mcf: str) -> dict:
        """Loads schema nodes from an MCF file into local dictionary.

        Args:
            mcf: Path to the schema MCF file.

        Returns:
            Dictionary of loaded schema nodes keyed by DCID.

        Example:
            >>> gen = UNStatVarGroupGenerator()
            >>> nodes = gen.load_schema_mcf('sample_schema.mcf')
        """
        if not mcf or not os.path.exists(mcf):
            return self._schema_nodes
        load_mcf_nodes(mcf, nodes=self._schema_nodes)
        self._counters.add_counter('input-schema-nodes',
                                   len(self._schema_nodes))
        return self._schema_nodes

    def get_schema_node(self, dcid: Union[str, None]) -> Union[dict, None]:
        """Looks up a schema node dictionary by DCID.

        Args:
            dcid: The DCID string of the schema node (with or without 'dcid:').

        Returns:
            The schema node dictionary if found, or None otherwise.

        Example:
            >>> gen = UNStatVarGroupGenerator()
            >>> gen.get_schema_node('PopulationPerson')
        """
        if not dcid or not isinstance(dcid, str):
            return None
        node = self._schema_nodes.get(strip_namespace(dcid))
        if not node:
            node = self._schema_nodes.get(add_namespace(dcid))
        return node

    def get_schema_name(self, dcid: Union[str, None]) -> str:
        """Returns the human-readable alternateName or name for a schema DCID.

        Args:
            dcid: The DCID string to look up.

        Returns:
            The name from schema if found, or a snake_case formatted fallback
            derived from the DCID.

        Example:
            >>> gen = UNStatVarGroupGenerator()
            >>> gen.get_schema_name('dcid:CountPerson')
            'Count person'
        """
        if not dcid or not isinstance(dcid, str):
            return ''
        node = self._schema_node_name_lookup(dcid)
        if node:
            return node
        # Convert DCID to a readable sentence fallback when not in schema
        clean_id = strip_namespace(dcid)
        remove_prefix = self._config.get('statvar_dcid_remove_prefix', '')
        name = strip_prefix_safe(clean_id[clean_id.rfind('/') + 1:],
                                 remove_prefix)
        name = to_snake_case(name, delim=' ', upper=False).capitalize()
        return name.strip('"').strip()

    def _schema_node_name_lookup(self, dcid: str) -> str:
        """Helper to extract alternateName or name from schema node dict."""
        node = self.get_schema_node(dcid)
        if not node or not isinstance(node, dict):
            return ''
        name = node.get('alternateName')
        if not name:
            name = node.get('name', '')
        return str(name).strip('"').strip()

    def add_statvar_group(self, pvs: dict):
        """Adds a StatVarGroup node to local dictionaries.

        Args:
            pvs: Property-value dictionary representing the StatVarGroup node.

        Example:
            >>> gen = UNStatVarGroupGenerator()
            >>> gen.add_statvar_group({'Node': 'dcid:svg_test', ...})
        """
        if not pvs or not isinstance(pvs, dict):
            return
        add_mcf_node(pvs, self._schema_nodes)
        add_mcf_node(pvs, self._statvar_groups)

    def get_statvar_groups(self) -> dict:
        """Returns the dictionary of generated StatVarGroup nodes.

        Returns:
            Dictionary mapping StatVarGroup DCIDs to their property-value maps.

        Example:
            >>> gen = UNStatVarGroupGenerator()
            >>> grps = gen.get_statvar_groups()
        """
        return self._statvar_groups

    def get_statvar_group_node(self,
                               dcid: str,
                               name: str,
                               parent: str) -> dict:
        """Constructs a standard StatVarGroup node dictionary.

        Args:
            dcid: The unique DCID for the new StatVarGroup.
            name: Human-readable display name for the group.
            parent: DCID of the parent node this group specializes.

        Returns:
            A property-value dictionary representing the StatVarGroup node.

        Example:
            >>> gen = UNStatVarGroupGenerator()
            >>> gen.get_statvar_group_node('svg_1', 'Group 1', 'dc/g/Root')
            {'Node': 'dcid:svg_1', 'typeOf': 'dcid:StatVarGroup', ...}
        """
        return {
            'Node': add_namespace(str(dcid) if dcid else ''),
            'typeOf': 'dcid:StatVarGroup',
            'name': to_quoted(str(name) if name else ''),
            'specializationOf': add_namespace(str(parent) if parent else ''),
        }

    def generate_prop_value_svg(self,
                                pvs: dict,
                                grp_props: list,
                                svg_parent: str,
                                svg_prefix: str) -> list[str]:
        """Generates nested hierarchy groups for property-value sequences.

        For each property in `grp_props`, creates a parent group for the
        property itself and a child group for its specific value in `pvs`.

        Args:
            pvs: Property-value dictionary of the StatVar being processed.
            grp_props: Ordered list of property strings to build groups for.
            svg_parent: Starting parent DCID for the first group node.
            svg_prefix: Starting DCID prefix for generated group nodes.

        Returns:
            List of generated StatVarGroup DCIDs corresponding to the sequence.
        """
        if not pvs or not grp_props:
            return []
        svg_grps = []
        strip_prefix = self._config.get(
            'svg_dcid_remove_prefix',
            self._config.get('statvar_dcid_remove_prefix', '')
        )
        val_delim = self._config.get('statvar_dcid_value_delimiter', '--')
        prop_delim = self._config.get('statvar_dcid_delimiter', '__')
        depth = 0

        for prop in grp_props:
            val = strip_namespace(pvs.get(prop, ''))
            if not val:
                continue
            # Create group node representing the property itself
            prop_id = strip_prefix_safe(to_snake_case(prop), strip_prefix)
            svg_dcid = svg_prefix + prop_id
            svg_name = self.get_schema_name(prop)
            self.add_statvar_group(
                self.get_statvar_group_node(svg_dcid, svg_name, svg_parent)
            )
            depth += 1
            self._counters.add_counter(
                f'generated-statvar-groups-depth-{depth}', 1
            )
            svg_parent = svg_dcid
            svg_prefix = svg_dcid + val_delim

            # Create group node representing the specific property value
            val_id = strip_prefix_safe(to_snake_case(val), strip_prefix)
            svg_dcid = svg_prefix + val_id
            svg_name = self.get_schema_name(val)
            self.add_statvar_group(
                self.get_statvar_group_node(svg_dcid, svg_name, svg_parent)
            )
            svg_grps.append(svg_dcid)
            depth += 1
            self._counters.add_counter(
                f'generated-statvar-groups-depth-{depth}', 1
            )
            svg_parent = svg_dcid
            svg_prefix = svg_dcid + prop_delim

        self._counters.add_counter(f'statvar-for-depth-{depth}', 1)
        return svg_grps

    def generate_groups_for_statvar(self,
                                    pvs: dict,
                                    svg_parent: str,
                                    svg_prefix: str):
        """Generates StatVarGroups for all hierarchy levels of a StatVar.

        Args:
            pvs: Property-value dictionary representing the StatVar.
            svg_parent: Root or parent DCID where the hierarchy begins.
            svg_prefix: Namespace prefix string for generated group DCIDs.

        Example:
            >>> gen = UNStatVarGroupGenerator()
            >>> gen.generate_groups_for_statvar(pvs, 'dc/g/Root', 'custom/g/')
        """
        if not pvs or not isinstance(pvs, dict):
            return
        self._counters.add_counter('input-statvars', 1)
        grp_props = dict()
        for prop, value in pvs.items():
            prop = strip_namespace(prop)
            value = strip_namespace(value)
            ignore_val = strip_namespace(_DEFAULT_IGNORE_PROP.get(prop))
            if (ignore_val is not None and
                    (not ignore_val or ignore_val == value)):
                continue
            grp_props.setdefault(prop, value)

        leaf_svg = []
        linked_svgs = set()
        strip_prefix = self._config.get(
            'svg_dcid_remove_prefix',
            self._config.get('statvar_dcid_remove_prefix', '')
        )
        prop_delim = self._config.get('statvar_dcid_delimiter', '__')

        # Build initial hierarchy groups from explicitly configured properties
        for prop in self._config.get('svg_properties', ['populationType']):
            val = grp_props.pop(prop, None)
            if not val:
                continue
            val_id = strip_prefix_safe(to_snake_case(val), strip_prefix)
            svg_dcid = svg_prefix + val_id
            svg_name = self.get_schema_name(val)
            self.add_statvar_group(
                self.get_statvar_group_node(svg_dcid, svg_name, svg_parent)
            )
            linked_svgs.add(add_namespace(svg_dcid))
            self._counters.add_counter(f'generated-statvar-groups-{prop}', 1)
            svg_parent = svg_dcid
            svg_prefix = svg_dcid + prop_delim

        if not grp_props:
            leaf_svg.append(svg_parent)
            linked_svgs.add(svg_parent)

        # Generate groups across property permutations for remaining props
        props_perm = [sorted(list(grp_props.keys()))]
        if self._config.get('statvar_group_permutations', False):
            props_perm = list(itertools.permutations(props_perm[0]))
        for props_list in props_perm:
            parent_svgs = self.generate_prop_value_svg(
                pvs, props_list, svg_parent, svg_prefix
            )
            if parent_svgs:
                leaf_svg.append(parent_svgs[-1])
                linked_svgs.update(parent_svgs)

        # Create updated StatVar node linking to the generated parent groups
        sv = {
            'Node': add_namespace(get_node_dcid(pvs)),
            'typeOf': 'StatisticalVariable',
        }
        if leaf_svg:
            sv['memberOf'] = ','.join(
                [add_namespace(dcid) for dcid in leaf_svg]
            )
        if linked_svgs and self._config.get('statvar_add_linked_member_of',
                                            False):
            sv['linkedMemberOf'] = ','.join(
                [add_namespace(dcid) for dcid in sorted(linked_svgs)]
            )
        self.add_statvar_group(sv)

    def generate_statvar_groups(self, sv_nodes: dict):
        """Processes a dictionary of StatVar nodes to build all group nodes.

        Args:
            sv_nodes: Mapping of StatVar DCIDs to their property-value dicts.

        Example:
            >>> gen = UNStatVarGroupGenerator()
            >>> gen.generate_statvar_groups({'sv1': {'typeOf': ...}})
        """
        if not sv_nodes or not isinstance(sv_nodes, dict):
            return
        svg_prefix = self._config.get('svg_prefix', 'dc/g/')
        svg_root = self._config.get('svg_root', 'dc/g/Root')
        self._counters.add_counter('total', len(sv_nodes))

        for dcid, pvs in sv_nodes.items():
            self._counters.add_counter('processed', 1)
            typ = strip_namespace(pvs.get('typeOf', ''))
            if typ and typ != 'StatisticalVariable':
                self._counters.add_counter('input-non-statvar-ignored', 1)
                continue
            self.generate_groups_for_statvar(pvs, svg_root, svg_prefix)

        # Attach the top-level StatVarGroup node to the root node if needed
        if 'Root' not in svg_root and self._config.get(
                'generate_statvar_group_root', True):
            name = to_snake_case(
                svg_root[svg_root.rfind('/') + 1:], ' ', False
            )
            self.add_statvar_group(
                self.get_statvar_group_node(svg_root, name, 'dc/g/Root')
            )
            self._counters.add_counter('generated-statvar-groups-root', 1)


def generate_statvar_groups(input_mcf: str,
                            schema_mcf: str,
                            output_mcf: str,
                            config: Union[dict, None] = None):
    """Orchestrates loading, group generation, and writing output MCF files.

    Args:
        input_mcf: Path to input MCF file containing StatisticalVariable nodes.
        schema_mcf: Path to schema MCF file with alternateName/name definitions.
        output_mcf: Target file path to write generated StatVarGroup nodes.
        config: Optional dictionary overriding default generator options.

    Example:
        >>> generate_statvar_groups('in.mcf', 'schema.mcf', 'groups.mcf')
    """
    counters = Counters()
    sv_grp_generator = UNStatVarGroupGenerator(config, counters)
    if schema_mcf and os.path.exists(schema_mcf):
        sv_grp_generator.load_schema_mcf(schema_mcf)

    if not input_mcf or not os.path.exists(input_mcf):
        logging.warning(
            f'Input MCF file not found: {input_mcf}. Skipping generation.'
        )
        return

    statvar_nodes = load_mcf_nodes(input_mcf)
    logging.info(f'Generating statvar groups for {len(statvar_nodes)} nodes')
    sv_grp_generator.generate_statvar_groups(statvar_nodes)

    sv_grps = sv_grp_generator.get_statvar_groups()
    if output_mcf and sv_grps:
        out_dir = os.path.dirname(output_mcf)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        write_mcf_nodes(sv_grps, output_mcf)
    counters.add_counter('output-nodes', len(sv_grps))
    counters.print_counters()


def main(_):
    logging.set_verbosity(_FLAGS.logging_level)
    generate_statvar_groups(_FLAGS.input_statvar_mcf, _FLAGS.input_schema_mcf,
                            _FLAGS.output_statvar_group_mcf,
                            get_default_statvar_group_config())


if __name__ == '__main__':
    app.run(main)
