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
"""Class to run an LLM query."""

import os
import re
import sys
import time

from absl import app
from absl import flags
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(_SCRIPT_DIR))),
                 'util'))

_FLAGS = flags.FLAGS

flags.DEFINE_string('genai_api_key', '', 'Google API key for generative AI')
flags.DEFINE_string('genai_input', '', 'Input file with input query.')
flags.DEFINE_string('genai_input_params', '',
                    'File with dictionary if input parameters')
flags.DEFINE_string('genai_output', '',
                    'Output file with generated response text.')
flags.DEFINE_string('genai_model', 'gemini-2.0-flash', 'Model to use with LLM.')
flags.DEFINE_boolean('genai_dry_run', False,
                     'Do not query the LLM, but only log the input query.')
flags.DEFINE_string(
    'genai_request', '',
    'Text file where the LLM request text used is copied into.')
flags.DEFINE_string('genai_response', '', 'Text file with the LLM response')

import file_util
import process_http_server

from config_map import ConfigMap
from counters import Counters


# Class to query GenAI APIs using a given prompt.
class GenAIHelper:

    def __init__(
        self,
        config_dict: dict = {},
        counters: Counters = None,
    ):
        # Import modules needed for GenAi
        # This is not imported in import-executor that loads this module
        # due to statvar processor but doesn't invoke genai
        import google.generativeai as genai

        self._config = ConfigMap()
        self._config.update_config(config_dict)
        self._counters = counters
        if counters is None:
            self._counters = Counters()

        # Initialize GenAi Model
        google_key = self._config.get('google_api_key')
        genai.configure(api_key=google_key)
        model_name = self._config.get('llm_model', 'gemini-2.0-flash')
        self._genai_model = genai.GenerativeModel(model_name)
        self._genai_prompt = self._config.get('llm_prompt', '')
        self._prompt_params = {}
        self.load_prompt(self._config.get('llm_prompt_file', ''))

    def load_prompt(self, file: str = ''):
        """Load the LLM prompt from the file."""
        if file:
            self._genai_prompt = read_text_file(file)
            logging.info(
                f'Loaded LLM prompt of size: {len(self._genai_prompt)} from {file}'
            )
        self._prompt_params = self.load_prompt_params()

    def load_prompt_params(self, prompt: str = '') -> dict:
        """Load any prompt params from config."""
        prompt_params = {}
        if not prompt:
            prompt = self._genai_prompt
        # Get all parameters in the prompt with the format pattern: '{<param>}'
        for p in re.findall(r'\{[a-zA-Z0-9_]*\}', prompt):
            param = p[1:-1]
            prompt_params[param] = ''

        # Load any default parameters from config.
        for param in prompt_params:
            value = self._config.get(param, '')
            if not value:
                continue
            value_files = file_util.file_get_matching(value)
            if value_files:
                # Parameter value is a file reference. Load value from file.
                logging.info(f'Loading param: {param} from {value_files}')
                prompt_params[param] = read_text_file(value_files)
            else:
                # Use parameter value from config.
                logging.info(f'Using param: {param}:{value}')
                prompt_params[param] = value
        logging.level_debug() and logging.debug(
            f'Got prompt params: {prompt_params}')
        return prompt_params

    def generate_content(self,
                         prompt: str = '',
                         prompt_params: dict = None) -> str:
        """Generate content using the genai model."""
        if not prompt:
            prompt = self._genai_prompt
        if prompt_params is None:
            prompt_params = self.load_prompt_params(prompt)
        if prompt_params:
            # Add default params.
            for param, value in self._prompt_params.items():
                if param not in prompt_params:
                    prompt_params[param] = value
        if prompt_params:
            logging.info(
                f'Generating prompt with params: {list(prompt_params.keys())}')
            genai_prompt = prompt.format(**prompt_params)
        else:
            genai_prompt = prompt
        num_words = len(genai_prompt.split(' '))
        logging.info(
            f'Querying LLM with prompt having {num_words} tokens: {genai_prompt[:1000]}'
        )
        self._counters.add_counter('llm-query', 1)
        self._counters.add_counter('llm-input-tokens', num_words)

        # Query the LLM
        if self._config.get('llm_dry_run', False):
            logging.info(f'Generated LLM Query: {genai_prompt}')
            write_text_to_file(genai_prompt,
                               self._config.get('llm_request', ''))
            return read_text_file(self._config.get('llm_response'))

        time_start = time.perf_counter()
        response = self._genai_model.generate_content(genai_prompt)
        time_sec = time.perf_counter() - time_start
        self._counters.add_counter('llm-response-time', time_sec)
        if not response.text:
            logging.error(f'LLM lookup failed: {response}')
            self._counters.add_counter('llm-query-failures', time_sec)
            return ''
        num_words = len(response.text.split(' '))
        self._counters.add_counter('llm-response-tokens', num_words)
        logging.info(
            f'Got LLM response with {num_words} tokens in {time_sec} seconds')
        write_text_to_file(genai_prompt, self._config.get('llm_request', ''))
        write_text_to_file(str(response), self._config.get('llm_response', ''))
        return response.text


def write_text_to_file(text: str, file: str):
    """Save the text into the file."""
    if not file:
        return
    with file_util.FileIO(file, 'w') as output_file:
        output_file.write(text)
    logging.info(f'Saved {len(text)} bytes into {file}')


def read_text_file(file: str, ignore_header_comment: bool = True) -> str:
    """Read text from file."""
    text_files = file_util.file_get_matching(file)
    if not text_files:
        return ''
    lines = []
    with file_util.FileIO(text_files[0]) as fp:
        for line in fp:
            if ignore_header_comment:
                if not lines and line[0] == '#':
                    # ignore header comment
                    continue
            lines.append(line.strip())
    return '\n'.join(lines)


def generate_content(input_prompt: str,
                     input_file: str = '',
                     input_params_file: str = '',
                     output_file: str = '',
                     config_dict: dict = {},
                     counters: Counters = None) -> str:
    """Generate context from generative AI using the input prompt."""
    genai_helper = GenAIHelper(config_dict, counters)
    if input_file:
        genai_helper.load_prompt(input_file)
    params = {}
    if input_params_file:
        params = file_util.file_load_py_dict(input_params_file)
    logging.info(f'Querying LLM with prompt: {input_prompt}, {input_file}')
    resp = genai_helper.generate_content(prompt=input_prompt,
                                         prompt_params=params)
    if output_file:
        write_text_to_file(resp, output_file)
    else:
        logging.info(f'Got GenAI context: {resp}')
    return resp


def get_genai_helper_config_from_flags():
    """Return config fomr commandline flags."""
    return {
        'llm_model': _FLAGS.genai_model,
        'google_api_key': _FLAGS.genai_api_key,
        'llm_dry_run': _FLAGS.genai_dry_run,
        'llm_request': _FLAGS.genai_request,
        'llm_response': _FLAGS.genai_response,
    }


def main(_):
    # Launch a web server with a form for commandline args
    # if the command line flag --http_port is set.
    if process_http_server.run_http_server(script=__file__, module=__name__):
        return

    logging.set_verbosity(1)

    counters = Counters()
    config = ConfigMap(get_genai_helper_config_from_flags())
    generate_content('', _FLAGS.genai_input, _FLAGS.genai_input_params,
                     _FLAGS.genai_output, config.get_configs(), counters)


if __name__ == '__main__':
    app.run(main)
