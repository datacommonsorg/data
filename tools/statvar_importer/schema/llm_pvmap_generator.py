# Copyright 2024 Google LLC
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
"""Utility to generate PV Map using LLMs.
This is used by data_annotator.py

To generate PV maps locally for a set of input strings, run the command:
  python llm_pvmap_generator.py \
      --llm_pvmap_input=<csv-file-with-strings-to-be-mapped> \
      --llm_pvmap_output=<csv-output-file> \
      --google_api_key=<GOOGLE_API_KEY>

  Add the following options arguments with additional LLM inputs
  for better quality suggestions:
      --llm_sample_pvmap=<sample-pvmap> \
      --llm_sample_statvars=<sample-statvars.mcf> \
      --llm_sample_data=<csv-data-file-with-input-strings> \
      --llm_data_context=<text-file> \

  Google API key can be obtained by following the steps in:
    https://ai.google.dev/gemini-api/docs/api-key
"""

import csv
import os
import sys

from absl import app
from absl import flags
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

_DEFAULT_LLM_PROMPT = os.path.join(_SCRIPT_DIR, 'llm_pvmap_prompt.txt')

_FLAGS = flags.FLAGS

flags.DEFINE_string('google_api_key', '', 'Google API key for generative AI')
flags.DEFINE_string('llm_pvmap_input', '',
                    'Input file with srings to be mapped to property values')
flags.DEFINE_string('llm_pvmap_output', '', 'Output file with generated pvmap')
flags.DEFINE_string('llm_model', 'gemini-2.0-flash', 'Model to use with LLM.')
flags.DEFINE_string('llm_sample_pvmap', 'sample_pvmap.csv',
                    'File with example property:value mappings.')
flags.DEFINE_string(
    'llm_sample_data', '',
    'File with sample CSV data with columns headers and strings to be mapped to PVs.'
)
flags.DEFINE_string('llm_sample_statvars', 'sample_statvars.mcf',
                    'MCF file with example statvars.')
flags.DEFINE_string('llm_data_context', '',
                    'Text file with description of the data strings.')
flags.DEFINE_string('llm_pvmap_prompt', _DEFAULT_LLM_PROMPT,
                    'Text file with the LLM prompt to generate PVMap.')
flags.DEFINE_string('llm_request', '',
                    'Output text file with copy prompt sent to LLM.')
flags.DEFINE_string('llm_response', '', 'Output text file with LLM response.')

import data_sampler
import file_util
import process_http_server
import config_flags
import schema_generator
import mcf_file_util
import property_value_mapper

from config_map import ConfigMap
from counters import Counters
from genai_helper import GenAIHelper, read_text_file, get_genai_helper_config_from_flags


# Class to generate PV Maps using LLMs.
class LLM_PVMapGenerator:

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

        # Initialize LLM
        self._genai_helper = GenAIHelper(self._config.get_configs(), counters)
        self._genai_helper.load_prompt(
            self._config.get('llm_pvmap_prompt', _DEFAULT_LLM_PROMPT))

        # Example pvmap
        self._sample_pv_map = {}
        self.load_sample_pvmap(self._config.get('sample_pvmap', ''))
        self._sample_statvars = {}
        self.load_sample_statvars(self._config.get('sample_statvars', ''))
        self._context_text = ''
        self.load_context(context_file=self._config.get('context', ''),
                          context=self._config.get('description', ''))
        self._sample_data = ''
        self.load_sample_data(self._config.get('sample_data', ''))

    def load_sample_pvmap(self, pvmap_file: str):
        """Load sample pvmap from a file."""
        pv_map = property_value_mapper.load_pv_map(pvmap_file)
        logging.info(f'Loaded {len(pv_map)} sample PVs from {pvmap_file}')
        self._sample_pv_map.update(pv_map)

    def add_sample_pvs(self, pv_map: dict):
        """Add sample PVs for LLM context."""
        self._sample_pv_map.update(pv_map)

    def load_sample_statvars(self, mcf_file: str):
        """Load example property:values from statvars."""
        mcf_file_util.load_mcf_nodes(mcf_file,
                                     self._sample_statvars,
                                     strip_namespaces=True)
        logging.info(
            f'Loaded {len(self._sample_statvars)} sample statvars from {mcf_file}'
        )

    def load_context(self, context_file: str = '', context: str = ''):
        self._context_text += context
        for file in file_util.file_get_matching(context_file):
            with file_util.FileIO(file) as input_file:
                file_text = input_file.read()
                logging.info(
                    f'Loaded {len(file_text)} bytes as context from {file}')
                self._context_text += file_text

    def load_sample_data(self, data_file: str):
        """Load sample rows from a CSV file."""
        sample_rows = []
        max_rows = self._config.get('sample_data_rows', 100)
        for file in file_util.file_get_matching(data_file):
            num_rows = file_util.file_estimate_num_rows(file)
            if num_rows > max_rows:
                file = data_sampler.sample_csv_file(file)
            with file_util.FileIO(file) as data_file:
                for line in data_file:
                    if len(sample_rows) < max_rows:
                        sample_rows.append(line.strip())
                    else:
                        break
            if len(sample_rows) >= max_rows:
                break
        self._sample_data = '\n'.join(sample_rows)
        logging.info(f'Loaded {len(sample_rows)} from {data_file}')

    # def load_schema_props(self, nodes: dict):
    #     """Load property nodes and save mapping from range to property."""
    #     for dcid, pvs in nodes.items():
    #       typeof = node.get('typeOf', '')
    #       if typeof != 'Property':
    #         continue
    #       ranges = node.get('rangeIncludes', '').split(',')
    #       for r in ranges:
    #         range_nodes = self._range_prop_map.get(r, {})

    # def load_sample_mcf(self, mcf_file: str):
    #     """Load example property:values from statvars."""
    #     nodes = mcf_file_util.load_mcf_nodes(mcf_file, strip_namespaces=True)
    #     for dcid, node in nodes.items():
    #       typeof = node.get('typeOf', '')
    #       if typeof == 'StatisticalVariable':
    #         mcf_file_util.add_mcf_node(node, self._sample_statvars)
    #       else:

    def generate_pvmap(self, input_pvmap: dict, prompt: str = '') -> dict:
        """Generate property:values for keys in the pvmap."""
        # Get sample PVs
        sample_pvs = get_pv_string_from_nodes(self._sample_pv_map, self._config)
        sample_pvs += get_sample_sv_name_pvs(self._sample_statvars,
                                             self._config)
        logging.info(f'Got sample pvs: {sample_pvs}')
        input_pv_str = get_pv_string_from_nodes(input_pvmap, self._config)
        logging.info(f'Got input pvmap: {input_pv_str}')

        # Set the pvmap prompt paramters per query.
        prompt_params = {
            'sample_pvs': sample_pvs,
            'sample_data': self._sample_data,
            'context': self._context_text,
            'input': input_pv_str,
        }

        # Query the LLM
        output_pvmap_str = self._genai_helper.generate_content(
            prompt, prompt_params)

        # Parse the response
        num_words = len(output_pvmap_str.split(' '))
        response_pvmap = get_nodes_from_pv_string(output_pvmap_str,
                                                  self._config)
        if self._config.get('llm_response_drop_extra_output', True):
            # Drop additional output maps that are not in the input.
            for key in list(response_pvmap.keys()):
                if key not in input_pvmap:
                    value = response_pvmap.pop(key)
                    logging.level_debug() and logging.debug(
                        f'Dropping extra output pv: {key}:{value}')
                    self._counters.add_counter('llm-response-pvmaps-dropped', 1)
        logging.info(f'LLM PVMap Response: {response_pvmap}')
        self._counters.add_counter('llm-response-tokens', num_words)
        self._counters.add_counter('llm-response-pvmaps', len(response_pvmap))
        return response_pvmap


# List of property values to be ignored for pv maps.
_IGNORE_NODES = {
    'typeOf:StatVarGroup',
}


def get_sv_pvs_string(node: dict,
                      ignore_props: dict = schema_generator.NAME_IGNORE_PROPS,
                      pv_separator: str = ':') -> str:
    """Returns a string of the form "name"->prop1:value1, prop2:value2, ..."""
    sv_name_pvs = []
    for prop, value in node.items():
        if not prop and not value:
            continue
        if prop in ignore_props:
            ignore_values = ignore_props[prop]
            if not ignore_values:
                continue
            if isinstance(ignore_values, str):
                ignore_values = ignore_values.split(',')
            if value in ignore_values:
                continue
        sv_name_pvs.append(f'{prop}{pv_separator}{value}')
    return ', '.join(sv_name_pvs)


# Pick a diverse sample of property values
def get_sample_sv_name_pvs(nodes: dict, config: dict = None) -> str:
    """Returns a sample of "name -> property:value" for the statvars."""
    pvs_seen = {}
    props_seen = {}
    if config is None:
        config = ConfigMap()
    max_rows_per_prop = config.get('max_examples_per_property', sys.maxsize)
    max_rows_per_sv = config.get('max_examples_per_statvar', sys.maxsize)
    sample_size = config.get('num_pv_examples', 1000)
    pv_separator = config.get('pv_separator', ':')
    name_pv_separator = config.get('name_pv_separator', ' --> ')
    ignore_props = config.get('statvar_name_ignore_props',
                              schema_generator.NAME_IGNORE_PROPS)
    samples = []
    dcids = list(nodes.keys())
    while (len(samples) < sample_size and len(dcids) > 0):
        # Generate name to property:value mapping for statvar.
        dcid = dcids.pop()
        node = nodes[dcid]
        sv_name = schema_generator.generate_statvar_name(node, config)
        sv_pvs = get_sv_pvs_string(node, ignore_props, pv_separator)
        if sv_name:
            # Check if statvar has any unique property or value.
            select_sv = True
            for pv in sv_pvs.split(','):
                if not pv or not ':' in pv:
                    continue
                prop, value = pv.split(':', 1)
                if pv in _IGNORE_NODES:
                    select_sv = False
                    break
                if pvs_seen.get(pv, 0) > max_rows_per_sv:
                    # There are enough samples for the property:value.
                    select_sv = False
                    break
                if props_seen.get(prop, 0) > max_rows_per_prop:
                    # There are enough samples for property.
                    select_sv = False
                    break
            if select_sv:
                # Add selected PV and update counts for property:values.
                samples.append(f'{sv_name}{name_pv_separator}{sv_pvs}')
                for prop, value in node.items():
                    props_seen[prop] = props_seen.get(prop, 0) + 1
                    pv = f'{prop}:{value}'
                    pvs_seen[pv] = pvs_seen.get(pv, 0) + 1
    logging.info(f'Got {len(samples)} PV samples from {len(nodes)} nodes')
    return '\n'.join(samples)


def get_pv_string_from_nodes(pvmap: dict, config: ConfigMap = None) -> str:
    """Returns a string of key -> property:value from the pvmap."""
    if config is None:
        config = ConfigMap()
    pv_separator = config.get('pv_separator', ':')
    name_pv_separator = config.get('name_pv_separator', ' --> ')
    pv_map_str = []
    for key, pvs in pvmap.items():
        if not key:
            continue
        pv_str = get_sv_pvs_string(pvs,
                                   ignore_props={},
                                   pv_separator=pv_separator)
        pv_map_str.append(f'{key}{name_pv_separator}{pv_str}')
    return '\n'.join(pv_map_str)


def get_nodes_from_pv_string(sv_name_pvs: str,
                             config: ConfigMap = None) -> dict:
    """Returns a dictionary of nodes with property:values from the name--> p:v, strings."""
    if config is None:
        config = ConfigMap()
    pv_separator = config.get('pv_separator', ':')
    name_pv_separator = config.get('name_pv_separator', ' --> ')

    nodes = {}
    for line in sv_name_pvs.split('\n'):
        if not line:
            continue
        line = line.strip()
        if not line or not name_pv_separator in line:
            continue
        key, sv_name_pvs = line.split(name_pv_separator, 1)
        node = nodes.get(key, {})
        for prop_value in sv_name_pvs.split(','):
            if pv_separator in prop_value:
                prop, value = prop_value.split(pv_separator, 1)
                mcf_file_util.add_pv_to_node(prop.strip(), value.strip(), node)
        nodes[key] = node
    return nodes


def get_llm_config_from_flags() -> dict:
    config = get_genai_helper_config_from_flags()
    config.update({
        'google_api_key': _FLAGS.google_api_key,
        'sample_pvmap': _FLAGS.llm_sample_pvmap,
        'sample_statvars': _FLAGS.llm_sample_statvars,
        'sample_data': _FLAGS.llm_sample_data,
        'context': _FLAGS.llm_data_context,
        'llm_pvmap_prompt': _FLAGS.llm_pvmap_prompt,
        'llm_request': _FLAGS.llm_request,
        'llm_response': _FLAGS.llm_response,
    })
    return config


def llm_generate_pvmap(pvmap: dict,
                       output_file: str,
                       config: ConfigMap = None,
                       counters: Counters = None) -> dict:
    """Returns the LLM generated PV map for input strings in pvmap."""
    if config is None:
        config = ConfigMap()
    if counters is None:
        counters = Counters()
    logging.debug(f'Generating pvmap for: {pvmap}')
    llm_pvmap_generator = LLM_PVMapGenerator(config.get_configs(), counters)
    output_pvmap = llm_pvmap_generator.generate_pvmap(pvmap)
    if output_pvmap:
        if output_file:
            property_value_mapper.write_pv_map(output_pvmap, output_file)
    return output_pvmap


def main(_):
    # Launch a web server with a form for commandline args
    # if the command line flag --http_port is set.
    if process_http_server.run_http_server(script=__file__, module=__name__):
        return

    logging.set_verbosity(1)

    counters = Counters()
    config = ConfigMap(get_llm_config_from_flags())
    input_pvmap = property_value_mapper.load_pv_map(_FLAGS.llm_pvmap_input)
    llm_generate_pvmap(input_pvmap, _FLAGS.llm_pvmap_output, config, counters)


if __name__ == '__main__':
    app.run(main)
