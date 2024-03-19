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
"""Utility to generate tmcf files for US Census ACS 5 Year files."""

import json
import os
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
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

import schema_resolver
import process_http_server

from mcf_file_util import load_mcf_nodes, write_mcf_nodes, add_namespace, strip_namespace, normalize_mcf_node
from mcf_diff import fingerprint_node, fingerprint_mcf_nodes, diff_mcf_node_pvs

# imports from ../../util
import file_util
from config_map import ConfigMap, read_py_dict_from_file
from counters import Counters, CounterOptions
from dc_api_wrapper import dc_api_is_defined_dcid
from download_util import download_file_from_url
from statvar_dcid_generator import get_statvar_dcid

_FLAGS = flags.FLAGS

flags.DEFINE_list('acs_group_jsons', [],
                  'List of ACS group JSON files to process')
flags.DEFINE_string('acs_config', '', 'Config file')
flags.DEFINE_string('acs_schema_mcf', '', 'MCF file with existing Statvars')
flags.DEFINE_string('acs_output_dir', '',
                    'Directory for output tMCF and StatVar mcf')
flags.DEFINE_string('acs_output_statvars_mcf', '',
                    'Output StatVars MCF for new StatVars')

_DEFAULT_CONFIG = {
    'svobs_about_resolve_property': 'usCensusGeoId',
    'svobs_about_type': 'Place',
    'svobs_about_column': 'GEO_ID',
}


class USCensusACSProcessor:
    """Class to process US Census ACS files."""

    def __init__(self, config: dict = {}, counters: Counters = None):
        self._counters = counters
        if self._counters is None:
            self._counters = Counters()
        self._config = ConfigMap(config_dict=_DEFAULT_CONFIG)
        if config:
            self._config.add_configs(config)

        # Initialize statvar resolver
        self._statvar_resolver = schema_resolver.SchemaResolver(
            mcf_files=self._config.get('existing_statvar_mcf'),
            config=self._config.get_configs(),
            counters=self._counters,
        )

        # Dictionary of new statvars.
        self._new_statvars = {}

    def process_table_group(self, group_json: dict):
        """Process a dictionary of groups in a table.

    Resolves the SV property:values for each group into an existing Statvar
    or generates a new StatVar.
    Generates a tMCF Node for each group with the additional property:values for
    svobs.
    """
        if not group_json:
            return

        tmcf_nodes = {}
        tmcf_place_node = ''
        num_existing_svs = 0
        num_new_svs = 0
        indicator = list(group_json.keys())[-1]
        group = indicator[:indicator.find('_')]
        self._counters.add_counter('input-group-jsons', 1, group)
        self._counters.add_counter('input-group-nodes', len(group_json), group)
        for indicator, group_pvs in group_json.items():
            group = indicator[:indicator.find('_')]
            unique_id = _get_unique_id(indicator)
            statvar_pvs = group_pvs.get('sv')
            if not statvar_pvs:
                logging.error(
                    f'Ignoring group without sv: {indicator}:{group_pvs}')
                self._counters.add_counter(f'error-groups-without-sv', 1,
                                           indicator)
                continue

            sv_node = self._statvar_resolver.resolve_node(statvar_pvs)
            if not sv_node:
                sv_node = statvar_pvs
            statvar_dcid = schema_resolver.get_node_dcid(sv_node)
            if not statvar_dcid:
                # This is a new StatVar. Generate a dcid.
                try:
                    statvar_dcid = get_statvar_dcid(sv_node)
                except TypeError as e:
                    logging.error(
                        f'Exception when processing {indicator}:{group_pvs}: {e}'
                    )
                    self._counters.add_counter('error-group-dcid', 1, indicator)
                    continue
                sv_node['Node'] = add_namespace(statvar_dcid)
                sv_node['#usCensusUniqueId: '] = indicator
                self._new_statvars[statvar_dcid] = sv_node
                self._counters.add_counter('new-statvars', 1, statvar_dcid)
                num_new_svs += 1
            else:
                self._counters.add_counter('existing-statvars', 1, statvar_dcid)
                num_existing_svs += 1

            if not tmcf_place_node and self._config.get(
                    'svobs_about_resolve_property'):
                # Add tMCF node for the place
                tmcf_node_index = len(tmcf_nodes)
                tmcf_place_node = {
                    'Node':
                        f'E:{group}->E{tmcf_node_index}',
                    'typeOf':
                        add_namespace(
                            self._config.get('svobs_about_type', 'Place')),
                    # Add resolved place property
                    self._config.get('svobs_about_resolve_property'):
                        self._config.get('svobs_about_column', 'GEO_ID'),
                }
                tmcf_nodes[tmcf_node_index] = tmcf_place_node

            # Add a tMCF node for the group column value
            tmcf_node_index = len(tmcf_nodes)
            tmcf = {
                'Node': f'E:{group}->E{tmcf_node_index}',
                'typeOf': 'dcs:StatVarObservation',
            }
            tmcf['variableMeasured'] = add_namespace(statvar_dcid)
            tmcf['value'] = f'C:{group}->{unique_id}'
            # Add any fixed PVs for SVObs such as mMethod, unit.
            for prop, value in group_pvs.get('svobs', {}).items():
                tmcf[prop] = value
            tmcf['#usCensusUniqueId: '] = unique_id
            tmcf_nodes[tmcf_node_index] = tmcf

        # Emit the tMCF
        output_dir = self._config.get('acs_output_dir', '.')
        tmcf_file = os.path.join(output_dir, f'{group}.tmcf')
        write_mcf_nodes(tmcf_nodes, tmcf_file)
        self._counters.add_counter('output-tmcf-files', 1, tmcf_file)
        self._counters.add_counter('output-tmcf-nodes', len(tmcf_nodes), group)
        logging.info(
            f'Generated group {group} tMCF: {tmcf_file} with {num_new_svs} new and'
            f' {num_existing_svs} existing StatVars')

    def process_group_mappings(self, group_files: str):
        """Generate tMCF and Svs for the groups JSOn files."""
        for group_json_file in file_util.file_get_matching(group_files):
            logging.info(f'Processing group mapping file: {group_json_file}')
            group_json_dict = {}
            with file_util.FileIO(group_json_file) as json_file:
                group_json_dict = json.loads(json_file.read())

            self.process_table_group(group_json_dict)
            self._counters.add_counter('input-group-jsons', 1)

        if self._new_statvars:
            sv_mcf_file = self._config.get('acs_output_statvars_mcf')
            if not sv_mcf_file:
                sv_mcf_file = os.path.join(
                    self._config.get('acs_output_dir', '.'),
                    'acs_stat_vars.mcf')
            write_mcf_nodes(self._new_statvars, sv_mcf_file)
            logging.info(
                f'Wrote {len(self._new_statvars)} StatVars into {sv_mcf_file}')


def _get_unique_id(indicator: str) -> str:
    """Returns the unique ID for the indicator to match the table column.

  Moves the Estimate or MarginOfError suffix to match the table column header
  For example: 'B01001_003E' -> 'B01001_E003'
  """
    unique_id = indicator
    sv_type = indicator[-1]
    if sv_type == 'E' or sv_type == 'M':
        # Move the type code to follow '_'
        unique_id = indicator[:-1].replace('_', f'_{sv_type}')
    return unique_id


def main(_):
    # Launch a web server if --http_port is set.
    if process_http_server.run_http_server(script=__file__, module=__name__):
        return

    # if _FLAGS.debug:
    #  logging.set_verbosity(2)

    config = _DEFAULT_CONFIG
    config['acs_output_dir'] = _FLAGS.acs_output_dir
    config['existing_statvar_mcf'] = _FLAGS.acs_schema_mcf
    config_map = ConfigMap(config_dict=config, filename=_FLAGS.acs_config)
    acs_processor = USCensusACSProcessor(config_map.get_configs())
    acs_processor.process_group_mappings(_FLAGS.acs_group_jsons)


if __name__ == '__main__':
    app.run(main)
