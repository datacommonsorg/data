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
"""Utility to generate StatVar names using LLM.

To generate names for statvars in an MCF file, run the command:
  python llm_statvar_name_generator.py \
      --llm_statvar_input=<input-mcf-file> \
      --llm_statvar_output=<output-mcf-file> \
      --llm_api_key=<GOOGLE-API-key>

  To use LLMs, get a Google API Key following the steps in:
    https://ai.google.dev/gemini-api/docs/api-key
"""

import csv
import os
import sys
import tempfile

from absl import app
from absl import flags
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

_DEFAULT_LLM_NAME_PROMPT = os.path.join(_SCRIPT_DIR,
                                        'llm_statvar_name_prompt.txt')
_FLAGS = flags.FLAGS

flags.DEFINE_string('llm_api_key', '', 'Google API key for generative AI')
flags.DEFINE_string('llm_statvar_input', '',
                    'Input MCF file with statvars with names to be added.')
flags.DEFINE_string(
    'llm_sample_statvar_names', '',
    'MCF file with example statvars with names and descriptions.')
flags.DEFINE_string('llm_statvar_output', '',
                    'Output MCF file for statvars with names.')
flags.DEFINE_string('llm_statvar_name_prompt', _DEFAULT_LLM_NAME_PROMPT,
                    'Text file with the LLM prompt to generate StatVar names.')
flags.DEFINE_string('llm_statvar_name_context', '',
                    'Text file with the context to generate StatVar names.')
flags.DEFINE_string('llm_name_request', '',
                    'Output text file with copy prompt sent to LLM.')
flags.DEFINE_string('llm_name_response', '',
                    'Output text file with LLM response.')

import file_util
import process_http_server
import config_flags
import mcf_file_util

from config_map import ConfigMap
from counters import Counters
from genai_helper import GenAIHelper, read_text_file, write_text_to_file, get_genai_helper_config_from_flags


# Class to generate PV Maps using LLMs.
class LLM_StatVarNameGenerator:

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
            self._config.get('llm_name_prompt', _DEFAULT_LLM_NAME_PROMPT))

        # Example pvmap
        self._sample_statvars = {}
        self.load_sample_statvars(self._config.get('sample_statvars', ''))
        self._context_text = ''
        self.load_context(context_file=self._config.get('context', ''),
                          context=self._config.get('description', ''))

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

    def generate_names(self, nodes: dict, prompt: str = '') -> dict:
        """Generate names for each node in nodes."""
        # Get sample statvars as text
        sample_statvars = get_nodes_as_text(self._sample_statvars)
        # Generate names in batches
        batch_size = self._config.get('llm_statvar_name_batch_size', 20)
        remaining_dcids = list(nodes.keys())
        output_nodes = {}
        num_batches = 0
        while len(remaining_dcids) > 0:

            # Get a batch of nodes to process.
            batch_dcids = remaining_dcids[:batch_size]
            selected_svs = {}
            for dcid in batch_dcids:
                selected_svs[dcid] = nodes[dcid]

            # Set the prompt parameters for name generation.
            input_statvars = get_nodes_as_text(selected_svs)
            prompt_params = {
                'sample_statvars': sample_statvars,
                'context': self._context_text,
                'input_statvars': input_statvars,
            }

            # Query the LLM for names
            self._counters.add_counter('llm-name-queries', 1)
            self._counters.add_counter('llm-name-query-nodes',
                                       len(selected_svs))
            output_statvars = self._genai_helper.generate_content(
                prompt, prompt_params)
            if output_statvars:
                batch_output_nodes = get_nodes_from_text(output_statvars)
                self._counters.add_counter('llm-name-query-responses',
                                           len(batch_output_nodes))
                output_nodes.update(batch_output_nodes)
            num_batches += 1
            remaining_dcids = remaining_dcids[batch_size:]

        logging.info(
            f'Generated names for {len(nodes)} statvars in {num_batches} batches'
        )
        # Update the iput nodes with the generated names from output.
        for dcid, node in output_nodes.items():
            input_node = nodes.get(dcid)
            if not input_node:
                logging.error(f'Got {dcid} not in input')
                continue
            for prop in ['name', 'description']:
                new_value = node.get(prop, '')
                if new_value:
                    old_value = input_node.get(prop, '')
                    if old_value != new_value:
                        input_node[prop] = new_value
                        logging.level_debug() and logging.debug(
                            f'Updated {prop} from {old_value} to {new_value}')
                        self._counters.add_counter(
                            f'llm-statvar-generated-{prop}', 1)

        return nodes


def get_nodes_as_text(nodes: dict) -> str:
    """Returns a text string with all nodes as MCFs."""
    if not nodes:
        return ''
    mcf_file = tempfile.NamedTemporaryFile(delete=False,
                                           suffix='-nodes.mcf').name
    mcf_file_util.write_mcf_nodes(nodes, mcf_file)
    logging.level_debug() and logging.debug(
        f'Using tempfile {mcf_file} for statvar MCF.')
    return read_text_file(mcf_file)


def get_nodes_from_text(mcf: str) -> dict:
    """Returns the nodes parsed from the text string."""
    mcf_file = tempfile.NamedTemporaryFile(delete=False,
                                           suffix='-nodes.mcf').name
    write_text_to_file(mcf, mcf_file)
    return mcf_file_util.load_mcf_nodes(mcf_file)


def get_name_config_from_flags() -> dict:
    config = get_genai_helper_config_from_flags()
    config.update({
        'google_api_key': _FLAGS.llm_api_key,
        'sample_statvars': _FLAGS.llm_sample_statvar_names,
        'context': _FLAGS.llm_statvar_name_context,
        'llm_name_prompt': _FLAGS.llm_statvar_name_prompt,
        'llm_request': _FLAGS.llm_name_request,
        'llm_response': _FLAGS.llm_name_response,
    })
    return config


def llm_generate_names(nodes: dict,
                       output_file: str,
                       config: ConfigMap = None,
                       counters: Counters = None) -> dict:
    """Returns the nodes with LLM generated names."""
    if config is None:
        config = ConfigMap()
    if counters is None:
        counters = Counters()
    logging.info(f'Generating names for {len(nodes)} nodes')
    llm_name_generator = LLM_StatVarNameGenerator(config.get_configs(),
                                                  counters)
    output_nodes = llm_name_generator.generate_names(nodes)
    if output_nodes:
        if output_file:
            mcf_file_util.write_mcf_nodes(output_nodes, output_file)
    return output_nodes


def main(_):
    # Launch a web server with a form for commandline args
    # if the command line flag --http_port is set.
    if process_http_server.run_http_server(script=__file__, module=__name__):
        return

    logging.set_verbosity(1)

    counters = Counters()
    config = ConfigMap(get_name_config_from_flags())
    input_nodes = mcf_file_util.load_mcf_nodes(_FLAGS.llm_statvar_input)
    llm_generate_names(input_nodes, _FLAGS.llm_statvar_output, config, counters)


if __name__ == '__main__':
    app.run(main)
