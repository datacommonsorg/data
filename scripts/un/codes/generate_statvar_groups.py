"""Script to generate statvar groups for UN statvars."""

import itertools
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
sys.path.append(_DATA_DIR)
sys.path.append(os.path.join(_DATA_DIR, 'util'))
sys.path.append(os.path.join(_DATA_DIR, 'tools', 'statvar_importer'))

import file_util
from mcf_file_util import add_namespace, strip_namespace, get_node_dcid
from mcf_file_util import load_mcf_nodes, write_mcf_nodes, add_mcf_node

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
                    'Prefix for the statvar group.')
flags.DEFINE_list('statvar_property_order', ['populationType'],
                  'Statvar properties ordered by group heirarchy.')
flags.DEFINE_bool(
    'statvar_group_permutations', True,
    'Geneerate statvar groups for all permutations of properties.')
flags.DEFINE_integer('logging_level', logging.INFO, 'Logging level.')

_FLAGS = flags.FLAGS
"""Wrapper to generate statvar groups for UN StatVars."""

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


def get_default_statvar_group_config() -> dict:
    """Returns the default statvar group config."""
    return {
        'svg_root': _FLAGS.statvar_root,
        'svg_prefix': _FLAGS.statvar_group_prefix,
        'svg_properties': _FLAGS.statvar_property_order,
        'statvar_dcid_remove_prefix': _FLAGS.statvar_dcid_remove_prefix,
        'statvar_group_permutations': _FLAGS.statvar_group_permutations,
    }


def to_snake_case(text: str, delim: str = '_', upper: bool = True) -> str:
    """Returns a string in sentence case."""
    # convert camelCase
    sentence = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', delim, text)

    # convert '_' to spaces
    sentence = re.sub(r'[_ ]+', delim, sentence)
    sentence = sentence.strip()
    if upper:
        return sentence.upper()
    return sentence


def to_quoted(text: str) -> str:
    """Returns quoted string."""
    if not text:
        return text
    text = text.strip().strip('"').strip().replace('"', "'")
    if text:
        return '"' + text + '"'
    return ''


class UNStatVarGroupGenerator:

    def __init__(
        self,
        config_dict: dict = {},
        counters: Counters = None,
    ):
        self._config = ConfigMap()
        self._config.update_config(config_dict)
        self._counters = counters
        if counters is None:
            self._counters = Counters()
        # dictionary of schema nodes keyed by dcid.
        self._schema_nodes = {}
        # dictionary of statvar groups created.
        self._statvar_groups = {}

    def load_schema_mcf(self, mcf: str) -> dict:
        """Loads schema nodes from MCF files."""
        load_mcf_nodes(mcf, nodes=self._schema_nodes)
        self._counters.add_counter('input-schema-nodes',
                                   len(self._schema_nodes))
        return self._schema_nodes

    def get_schema_node(self, dcid: str) -> dict:
        """Returns a schema node for the dcid."""
        if not dcid:
            return None
        node = self._schema_nodes.get(strip_namespace(dcid))
        if not node:
            node = self._schema_nodes.get(add_namespace(dcid))
        return node

    def get_schema_name(self, dcid: str) -> str:
        """Returns the name for the dcid fomr the schema."""
        node = self.get_schema_node(dcid)
        if not node:
            return ''
        name = node.get('alternateName')
        if not name:
            name = node.get('name', '')
        if not name:
            # convert the dcid to a name string
            remove_prefix = self._config.get('statvar_dcid_remove_prefix', '')
            name = re.sub(remove_prefix, '', dcid[dcid.find('/') + 1:])
            name = to_snake_case(name).capitalize()
        return name.strip('"').strip()

    def add_statvar_group(self, pvs: dict):
        """Add a statvar group to schema."""
        add_mcf_node(pvs, self._schema_nodes)
        add_mcf_node(pvs, self._statvar_groups)

    def get_statvar_groups(self) -> dict:
        """Returns the new statvar groups created."""
        return self._statvar_groups

    def get_statvar_group_node(self, dcid, name, parent) -> dict:
        return {
            'Node': add_namespace(dcid),
            'typeOf': 'dcid:StatVarGroup',
            'name': to_quoted(name),
            'specializationOf': add_namespace(parent),
        }

    def generate_prop_value_svg(self, pvs: dict, grp_props: list,
                                svg_parent: str, svg_prefix: str):
        """Generate statvar groups for the property values in the list."""
        strip_prefix = self._config.get('svg_dcid_remove_prefix', '')
        depth = 0
        for prop in grp_props:
            val = strip_namespace(pvs.get(prop, ''))
            if not val:
                continue
            # Create svg for the property
            prop_id = re.sub(strip_prefix, '', to_snake_case(prop))
            svg_dcid = svg_prefix + prop_id
            svg_name = self.get_schema_name(prop)
            self.add_statvar_group(
                self.get_statvar_group_node(svg_dcid, svg_name, svg_parent))
            depth += 1
            self._counters.add_counter(
                f'generated-statvar-groups-depth-{depth}', 1)
            svg_parent = svg_dcid
            svg_prefix = svg_dcid + self._config.get(
                'statvar_dcid_value_delimiter', '--')

            # Generate statvar group for value
            val_id = re.sub(strip_prefix, '', val)
            svg_dcid = svg_prefix + val_id
            svg_name = self.get_schema_name(val)
            self.add_statvar_group(
                self.get_statvar_group_node(svg_dcid, svg_name, svg_parent))
            depth += 1
            self._counters.add_counter(
                f'generated-statvar-groups-depth-{depth}', 1)
            svg_parent = svg_dcid
            svg_prefix = svg_dcid + self._config.get('statvar_dcid_delimiter',
                                                     '__')
        # Add the statvar to the leaf group.
        sv = {
            'Node': add_namespace(get_node_dcid(pvs)),
            'typeOf': 'StatisticalVariable',
            'memberOf': svg_parent,
        }
        self.add_statvar_group(sv)
        self._counters.add_counter(f'statvar-for-depth-{depth}', 1)

    def generate_groups_for_statvar(self, pvs: dict, svg_parent: str,
                                    svg_prefix: str):
        """Generates statvar groups for the hierarchy property:values in the statvar."""
        self._counters.add_counter('input-statvars', 1)
        # Get the properties for the group
        grp_props = dict()
        for prop, value in pvs.items():
            prop = strip_namespace(prop)
            value = strip_namespace(value)
            ignore_val = strip_namespace(_DEFAULT_IGNORE_PROP.get(prop))
            if ignore_val is not None:
                if not ignore_val or ignore_val == value:
                    continue
            grp_props.setdefault(prop, value)

        # Get an ordered list of properties to create statvar groups.
        # Also generate statvar for each set of properties.
        strip_prefix = self._config.get('svg_dcid_remove_prefix', '')
        for prop in self._config.get('svg_properties', ['populationType']):
            val = grp_props.pop(prop, None)
            if not val:
                continue
            val = re.sub(strip_prefix, '', to_snake_case(val))
            svg_dcid = svg_prefix + val
            svg_name = self.get_schema_name(val)
            self.add_statvar_group(
                self.get_statvar_group_node(svg_dcid, svg_name, svg_parent))
            self._counters.add_counter(f'generated-statvar-groups-{prop}', 1)
            svg_parent = svg_dcid
            svg_prefix = svg_dcid + self._config.get('statvar_dcid_delimiter',
                                                     '__')

        # Generate statvar group for all permutations of properties.
        props_perm = sorted(grp_props.keys())
        if self._config.get('statvar_group_permutations', False):
            props_perm = list(itertools.permutations(grp_props.keys()))
        for props_list in props_perm:
            self.generate_prop_value_svg(pvs, props_list, svg_parent,
                                         svg_prefix)

    def generate_statvar_groups(self, sv_nodes: dict):
        """Generate statvar groups for given statvar nodes."""
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

        # Make the top SVG a child of root
        if 'Root' not in svg_root and self._config.get(
                'generate_statvar_group_root', True):
            name = to_snake_case(svg_root[svg_root.find('/') + 1:], ' ', False)
            self.add_statvar_group(
                self.get_statvar_group_node(svg_root, name, 'dc/g/Root'))
            self._counters.add_counter(f'generated-statvar-groups-root', 1)


def generate_statvar_groups(input_mcf: str,
                            schema_mcf: str,
                            output_mcf: str,
                            config: dict = None):
    """Generate groups for statvars in input_mcf."""
    counters = Counters()
    sv_grp_generator = UNStatVarGroupGenerator(config, counters)
    sv_grp_generator.load_schema_mcf(schema_mcf)

    statvar_nodes = load_mcf_nodes(input_mcf)
    logging.info(f'Generating statvar groups for {len(statvar_nodes)} nodes')
    sv_grp_generator.generate_statvar_groups(statvar_nodes)

    sv_grps = sv_grp_generator.get_statvar_groups()
    if output_mcf and sv_grps:
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
