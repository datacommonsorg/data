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
"""Script and class to generate statvar names for UN Statistical Variables.

Usage:
    python3 generate_statvar_name.py \
        --input_statvar_mcf=statvars.mcf \
        --input_schema_mcf=schema.mcf \
        --output_statvar_mcf=statvars_named.mcf
"""

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
    add_namespace,
    get_node_dcid,
    load_mcf_nodes,
    strip_namespace,
    write_mcf_nodes,
)

from config_map import ConfigMap
from counters import Counters

flags.DEFINE_string('input_statvar_mcf', '', 'MCF files with statvar nodes.')
flags.DEFINE_string('output_statvar_mcf', '',
                    'Output MCF files for statvar with names.')
flags.DEFINE_string('input_schema_mcf', '',
                    'Schema file with names for properties.')
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
    'populationType': '',
    'measuredProperty': 'value',
    'statType': 'measuredValue',
}

_RE_CAMEL = re.compile(r'(?<=[a-z0-9])(?=[A-Z])')
_RE_UNDERSCORE_SPACE = re.compile(r'[_ ]+')


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


def to_sentence_case(text: Union[str, None]) -> str:
    """Converts camelCase or underscore string into readable sentence case.

    Args:
        text: The string to normalize into sentence case.

    Returns:
        A sentence-cased string with words separated by single spaces and
        the first letter capitalized.

    Example:
        >>> to_sentence_case('measuredProperty_gender')
        'Measured property gender'
    """
    if not text:
        return ''
    sentence = _RE_CAMEL.sub(' ', str(text))
    sentence = _RE_UNDERSCORE_SPACE.sub(' ', sentence).strip()
    return sentence.capitalize()


class UNStatVarNameGenerator:
    """Class that resolves or generates descriptive names for StatVars."""

    def __init__(
        self,
        config_dict: Union[dict, None] = None,
        counters: Union[Counters, None] = None,
    ):
        """Initializes the UNStatVarNameGenerator.

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

    def load_schema_mcf(self, mcf: str) -> dict:
        """Loads schema nodes from an MCF file into local dictionary.

        Args:
            mcf: Path to the schema MCF file.

        Returns:
            Dictionary of loaded schema nodes keyed by DCID.

        Example:
            >>> gen = UNStatVarNameGenerator()
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
            >>> gen = UNStatVarNameGenerator()
            >>> gen.get_schema_node('PopulationPerson')
        """
        if not dcid or not isinstance(dcid, str):
            return None
        node = self._schema_nodes.get(strip_namespace(dcid))
        if not node:
            node = self._schema_nodes.get(add_namespace(dcid))
        return node

    def get_schema_name(self, dcid: Union[str, None]) -> str:
        """Returns the human-readable alternateName or name from schema.

        Args:
            dcid: The DCID string to look up.

        Returns:
            The name from schema if found, or empty string otherwise.

        Example:
            >>> gen = UNStatVarNameGenerator()
            >>> gen.get_schema_name('dcid:Person')
            'Person'
        """
        if not dcid or not isinstance(dcid, str):
            return ''
        node = self.get_schema_node(dcid)
        if not node or not isinstance(node, dict):
            return ''
        name = node.get('alternateName')
        if not name:
            name = node.get('name', '')
        return str(name).strip('"').strip()

    def generate_statvar_name(self, pvs: dict) -> dict:
        """Adds or resolves a descriptive 'name' property on a StatVar node.

        If the node already has a name or matches a schema name exact, that
        name is quoted and retained. Otherwise, builds a composite name using
        the populationType prefix followed by bracketed constraints.

        Args:
            pvs: Property-value dictionary representing the StatVar.

        Returns:
            The input `pvs` dictionary updated with a quoted 'name' property.

        Example:
            >>> gen = UNStatVarNameGenerator()
            >>> gen.generate_statvar_name({'populationType': 'Person', ...})
            {'populationType': 'Person', 'name': '"Person [Gender=Female]"'}
        """
        if not pvs or not isinstance(pvs, dict):
            return pvs or {}
        name = pvs.get('name')
        if name:
            logging.debug(f'Using existing name for statvar:{name}')
            self._counters.add_counter('input-existing-name', 1)
            pvs['name'] = to_quoted(name)
            return pvs

        # Use the name from the schema if it already exists exact.
        dcid = get_node_dcid(pvs)
        name = self.get_schema_name(dcid)
        if name:
            pvs['name'] = to_quoted(name)
            self._counters.add_counter('input-schema-name', 1)
            return pvs

        # Resolve prefix from populationType name or fallback sentence case
        pop_type = pvs.get('populationType')
        name_prefix = self.get_schema_name(pop_type)
        if not name_prefix and pop_type:
            name_prefix = to_sentence_case(strip_namespace(pop_type))

        name_tokens = []
        # Collect names for secondary constraint property-value pairs
        for prop, value in pvs.items():
            pv_tokens = []
            prop_id = strip_namespace(prop)
            val_id = strip_namespace(value)
            ignore_val = strip_namespace(_DEFAULT_IGNORE_PROP.get(prop_id))
            if ignore_val is not None and (not ignore_val or
                                           ignore_val == val_id):
                continue

            prop_name = self.get_schema_name(prop)
            if not prop_name:
                prop_name = to_sentence_case(prop_id)
                self._counters.add_counter('property-missing-name', 1)
            if prop_name:
                pv_tokens.append(prop_name)

            val_name = self.get_schema_name(value)
            if not val_name:
                val_name = to_sentence_case(val_id)
                self._counters.add_counter('value-missing-name', 1)
            if val_name:
                pv_tokens.append(val_name)

            if pv_tokens:
                name_tokens.append('='.join(pv_tokens))

        name_suffix = ', '.join(name_tokens)
        name = name_prefix
        if name_suffix:
            self._counters.add_counter('generated-statvar-name-constraints', 1)
            if name:
                name = f'{name} [{name_suffix}]'
            else:
                name = f'[{name_suffix}]'
        pvs['name'] = to_quoted(name)
        self._counters.add_counter('generated-statvar-names', 1)
        return pvs


def generate_statvar_names(input_mcf: str, schema_mcf: str, output_mcf: str):
    """Orchestrates loading, name generation, and writing output MCF files.

    Args:
        input_mcf: Path to input MCF file containing StatisticalVariable nodes.
        schema_mcf: Path to schema MCF file with alternateName/name definitions.
        output_mcf: Target file path to write StatVars with generated names.

    Example:
        >>> generate_statvar_names('in.mcf', 'schema.mcf', 'named.mcf')
    """
    counters = Counters()
    config = {}
    sv_name_generator = UNStatVarNameGenerator(config, counters)
    if schema_mcf and os.path.exists(schema_mcf):
        sv_name_generator.load_schema_mcf(schema_mcf)

    if not input_mcf or not os.path.exists(input_mcf):
        logging.warning(
            f'Input MCF file not found: {input_mcf}. Skipping generation.'
        )
        return

    statvar_nodes = load_mcf_nodes(input_mcf)
    logging.info(f'Generating statvar names for {len(statvar_nodes)}')
    for dcid, pvs in statvar_nodes.items():
        sv_name_generator.generate_statvar_name(pvs)

    if output_mcf and statvar_nodes:
        out_dir = os.path.dirname(output_mcf)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        write_mcf_nodes(statvar_nodes, output_mcf)

    counters.print_counters()


def main(_):
    logging.set_verbosity(_FLAGS.logging_level)
    generate_statvar_names(_FLAGS.input_statvar_mcf, _FLAGS.input_schema_mcf,
                           _FLAGS.output_statvar_mcf)


if __name__ == '__main__':
    app.run(main)
