"""Script to generate statvar names for UN statvars."""

import os
import re
import sys

from absl import app
from absl import flags
from absl import logging

import file_util
from mcf_file_util import add_namespace, strip_namespace, get_node_dcid
from mcf_file_util import load_mcf_nodes, write_mcf_nodes

from config_map import ConfigMap
from counters import Counters

flags.DEFINE_string('input_statvar_mcf', '', 'MCF files with statvar nodes.')
flags.DEFINE_string('output_statvar_mcf', '',
                    'Output MCF files for statvar with names.')
flags.DEFINE_string('input_schema_mcf', '',
                    'Schema file with names for propeorties.')
flags.DEFINE_integer('logging_level', logging.INFO, 'Logging level.')

_FLAGS = flags.FLAGS
"""Wrapper to generate statvar names for UN StatVars."""

_DEFAULT_IGNORE_PROP = {
    'Node': '',
    'dcid': '',
    'typeOf': '',
    'memberOf': '',
    'footnote': '',
    'description': '',
    'name': '',
    'populationType': '',
    'measuredProperty': 'value',
    'statType': 'measuredValue',
}


def to_sentence_case(text: str) -> str:
    """Returns a string in sentence case."""
    # convert camelCase
    sentence = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', ' ', text)

    # convert '_' to spaces
    sentence = re.sub(r'[_ ]+', ' ', sentence)
    sentence = sentence.strip()
    return sentence.capitalize()


class UNStatVarNameGenerator:

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
        self._schema_nodes = {}

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
        return name.strip('"').strip()

    def generate_statvar_name(self, pvs: dict) -> dict:
        """Adds a name to a statvar if it doesn't exist already."""
        name = pvs.get('name')
        if name:
            logging.debug(f'Using existing name for statvar:{name}')
            self._counters.add_counter(f'input-existing-name', 1)
            return pvs

        # Use the name from the schema if it already exists.
        dcid = get_node_dcid(pvs)
        name = self.get_schema_name(dcid)
        if name:
            pvs['name'] = '"' + name + '"'
            self._counters.add_counter(f'input-schema-name', 1)
            return pvs

        # Get the name from the populationType
        name_prefix = self.get_schema_name(pvs.get('populationType'))
        name_tokens = []
        # Collect names for constraint property:values
        for prop, value in pvs.items():
            pv_tokens = []
            prop = strip_namespace(prop)
            value = strip_namespace(value)
            ignore_val = strip_namespace(_DEFAULT_IGNORE_PROP.get(prop))
            if ignore_val is not None:
                if not ignore_val or ignore_val == value:
                    continue
            prop_name = self.get_schema_name(prop)
            if not prop_name:
                prop_name = to_sentence_case(prop)
                self._counters.add_counter('property-missing-name', 1)
            if prop_name:
                pv_tokens.append(prop_name)
            val_name = self.get_schema_name(value)
            if not val_name:
                val_name = to_sentence_case(value)
                self._counters.add_counter('value-missing-name', 1)
            if val_name:
                pv_tokens.append(val_name)
            if pv_tokens:
                name_tokens.append('='.join(pv_tokens))
        name_suffix = ', '.join(name_tokens)
        name = name_prefix
        if name_suffix:
            self._counters.add_counter(f'generated-statvar-name-contraints', 1)
            name = f'{name} [{name_suffix}]'
        pvs['name'] = f'"{name}"'
        self._counters.add_counter(f'generated-statvar-names', 1)


def generate_statvar_names(input_mcf: str, schema_mcf: str, output_mcf: str):
    """Generate names for statvars in input_mcf."""
    counters = Counters()
    config = {}
    sv_name_generator = UNStatVarNameGenerator(config, counters)
    sv_name_generator.load_schema_mcf(schema_mcf)

    statvar_nodes = load_mcf_nodes(input_mcf)
    logging.info(f'Generating statvar names for {len(statvar_nodes)}')
    for dcid, pvs in statvar_nodes.items():
        sv_name_generator.generate_statvar_name(pvs)

    if output_mcf:
        write_mcf_nodes(statvar_nodes, output_mcf)

    counters.print_counters()


def main(_):
    logging.set_verbosity(_FLAGS.logging_level)
    generate_statvar_names(_FLAGS.input_statvar_mcf, _FLAGS.input_schema_mcf,
                           _FLAGS.output_statvar_mcf)


if __name__ == '__main__':
    app.run(main)
