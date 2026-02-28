# Copyright 2025 Google LLC
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
"""Utilities for statvar imports"""

import os
import sys
import glob
import json
import re
import shlex
from typing import Union

from absl import app
from absl import flags
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_SCRIPT_DIR.split('/data/')[0], 'data')
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(os.path.join(_DATA_DIR, 'util'))

import file_util
from counters import Counters
from config_map import ConfigMap
from property_value_mapper import load_pv_map
from mcf_diff import diff_mcf_nodes

# Globals
_STATVAR_PROCESSOR_SCRIPT = os.path.join(_DATA_DIR, "tools", "statvar_importer",
                                         "stat_var_processor.py")
_AGENTIC_SCRIPT = os.path.join(_DATA_DIR, "tools", "agentic_import",
                               "pvmap_generator.py")

_FLAGS = flags.FLAGS

flags.DEFINE_string('statvar_processor_script', _STATVAR_PROCESSOR_SCRIPT,
                    'Statvar processor script')
flags.DEFINE_string(
    'statvar_processor_options', None,
    'Additional options for statvar processor, for eg: --gemini_model=gemini-2.5-pro'
)
flags.DEFINE_string('pvmap_generation_method', 'statvar',
                    'Method fof pv map generation.')

flags.DEFINE_string('gemini_cli', 'gemini', 'Gemini CLI command')

# Utilities to get import related files.


def get_file_realpath(file: str, cwd: str) -> str:
    """Returns the full path for the file."""
    if os.path.exists(file):
        return os.path.realpath(file)
    dir_file = os.path.join(cwd, file)
    if os.path.exists(dir_file):
        return os.path.realpath(dir_file)
    return file


def load_manifest_json(file: str) -> dict:
    """Parses a manifest.json file into a dict object."""
    if not file:
        return {}
    try:
        with open(file, 'r') as fp:
            manifest_json = json.loads(fp.read())
            return manifest_json
    except Exception as e:
        logging.error(f'Unable to load manifest {file}, error: {e}')
        return {}


def create_empty_file(file: str):
    """Create an empty file, deleting any existing ones."""
    with open(file, 'w'):
        return


# Get the import specific manifest from the json
def get_manifest_for_import(import_name: str,
                            manifest_json: dict = None) -> dict:
    """Returns the manifect dict for a specific import in the json."""
    if manifest_json is None:
        manifest_json = load_manifest_json(
            get_import_manifest_file(import_name))
    for data_import in manifest_json.get('import_specifications', []):
        name = data_import.get('import_name')
        if name == import_name:
            return data_import
    return {}


# Get the manifest.josn file for an import
def get_import_manifest_file(import_name: str,
                             root_dir: str = _DATA_DIR) -> str:
    """Returns the folder containing the manifest.json for the import name."""
    files = glob.glob(os.path.join(root_dir, '**'), recursive=True)
    for file in files:
        if file.endswith('manifest.json'):
            import_manifest = get_manifest_for_import(import_name,
                                                      load_manifest_json(file))
            if import_manifest:
                return file
    return None


def get_statvar_import_config(import_name: str,
                              manifest_file: str = None) -> dict:
    """Get the files for an import using stat_var_processor.

  Returns a dict with the files and config needed to run the statvar processor:
    metadata, pvmap, input_data, places, output, etc.
  """
    if not manifest_file:
        manifest_file = get_import_manifest_file(import_name)
        if not manifest_file:
            logging.fatal(f'Unable to get manifest for import {import_name}')
            return {}

    import_dir = os.path.realpath(
        os.path.dirname(manifest_file)) if manifest_file else ''
    manifest = get_manifest_for_import(import_name,
                                       load_manifest_json(manifest_file))

    # Get the statvar processor commandline arguments
    statvar_cmd_args = []
    for script in manifest.get('scripts', []):
        statvar_script = os.path.basename(_STATVAR_PROCESSOR_SCRIPT)
        if statvar_script in script:
            # Got the statvar processor script.
            # Get the command line arguments
            cmd = script.split(statvar_script, 1)[1]
            statvar_cmd_args = shlex.split(cmd)
            break
    import_settings = dict(manifest)
    for arg in statvar_cmd_args:
        if '=' in arg:
            param, value = arg.split('=', 1)
            param = param.strip('-')
            import_settings[param] = get_file_realpath(value, import_dir)

    # Get the config from the metadata
    config = ConfigMap(import_settings, import_settings.get('config_file'))
    config.set_config('manifest', manifest_file)
    config.set_config("statvar_processor_args", statvar_cmd_args)
    config.set_config("import_dir", os.path.dirname(manifest_file))
    return config.get_configs()


def get_import_test_data(import_name: str, import_config: dict = None) -> dict:
    """Gets the test data for a given import config."""
    if import_config is None:
        import_config = get_statvar_import_config(import_name)

    if import_config.get('test_data_input'):
        # Already has test data set in config
        return import_config

    import_dir = ''
    pvmap = import_config.get('pv_map')
    if pvmap:
        import_dir = os.path.dirname(pvmap)
    if not import_dir:
        import_dir = os.path.dirname(import_config.get('manifest'))
    import_config["import_dir"] = import_dir

    # Get the directory for test_data/ under the import
    test_data_dir = import_dir
    test_data_dirs = glob.glob(os.path.join(import_dir, 'test*data'))
    if test_data_dirs:
        test_data_dir = test_data_dirs[0]

    # Get input and outputs matching pvmap in test data.
    pvmap_basename = ''
    if pvmap:
        pvmap_basename = re.sub(r'[_-]*pv[_-]*map.*', '',
                                os.path.basename(pvmap))
    if not pvmap_basename:
        # Look for any file with 'input' in the name
        pvmap_basename = 'data'

    logging.debug(
        f'Looking for test_data files in {import_dir}, {test_data_dirs}, {pvmap_basename}'
    )
    test_data = glob.glob(os.path.join(test_data_dir,
                                       f'*{pvmap_basename}*.csv'))
    test_data_input = None
    test_data_output = None
    test_data_inputs = [
        file for file in test_data if os.path.isfile(file) and 'input' in file
    ]
    if test_data_inputs:
        test_data_input = test_data_inputs[0]
    test_data_outputs = [
        file for file in test_data if os.path.isfile(file) and 'output' in file
    ]
    if test_data_outputs:
        test_data_output = test_data_outputs[0]

    if test_data_input:
        import_config['test_data_input'] = os.path.realpath(test_data_input)
    if test_data_output:
        import_config['test_data_output'] = os.path.realpath(test_data_output)
    logging.info(
        f'Got test data for import: {import_name}, input: {test_data_input}, output: {test_data_output}'
    )

    return import_config


def generate_import_pvmap(import_name: str,
                          import_config: dict = None,
                          method: str = 'statvar',
                          output_dir: str = '') -> dict:
    """Generate pvmap for an import."""
    import_config = get_import_test_data(import_name, import_config)
    if 'test_data_input' not in import_config:
        logging.error(
            f'No test data for {import_name}, cannot generate pvmap for {import_config}'
        )
        return None

    # Create a tmp directory generated files.
    import_dir = import_config.get('import_dir')
    if not output_dir:
        output_dir = os.path.join('tmp', method)
    tmp_dir = os.path.join(import_dir, output_dir)
    os.makedirs(tmp_dir, exist_ok=True)

    run_dir = ''
    generate_pvmap_cmd = ''
    if method.startswith('stat'):
        # Generate pvmap using statvar processor
        pvmap = os.path.join(tmp_dir, 'statvar_pvmap.csv')
        create_empty_file(pvmap)
        output_path = os.path.join(tmp_dir, 'output')
        output_data_pvs = os.path.join(tmp_dir, f'{method}_data_pvs.csv')
        override_args = {
            'pv_map': pvmap,
            'input_data': import_config.get('test_data_input', ''),
            'output_path': output_path,
            'output_data_pvs': output_data_pvs,
        }
        generate_pvmap_cmd = get_statvar_processor_cmd(import_config,
                                                       override_args)
        import_config[f'{method}_generate_pvmap_cmd'] = generate_pvmap_cmd
        import_config[f'{method}_generated_pvmap'] = pvmap
        import_config[f'{method}_output_data_pvs'] = output_data_pvs
    elif method.startswith('agentic'):
        # Generate pvmap using agentic importer
        # Generate PV map and metadata
        input_data = import_config.get('test_data_input', '')
        output_path = os.path.join(tmp_dir, 'output')
        cmd_args = []
        cmd_args.append('python')
        cmd_args.append(_AGENTIC_SCRIPT)
        cmd_args.append('--skip_confirmation=True')
        cmd_args.append(f'--gemini_cli="{_FLAGS.gemini_cli}"')
        cmd_args.append(f'--input_data="{input_data}"')
        cmd_args.append(f'--output_path="{output_path}"')
        generate_pvmap_cmd = ' '.join(cmd_args)
        import_config[f'{method}_generate_pvmap_cmd'] = generate_pvmap_cmd
        import_config[f'{method}_generated_pvmap'] = output_path + '_pvmap.csv'
        run_dir = os.path.dirname(_AGENTIC_SCRIPT)
        run_dir = _DATA_DIR

    generate_pvmap_cmd = import_config.get(f'{method}_generate_pvmap_cmd')
    pvmap = import_config.get(f'{method}_generated_pvmap')
    logging.info(
        f'Generating {method} pvmap: {pvmap} with command: {generate_pvmap_cmd}'
    )
    cwd = os.getcwd()
    if run_dir:
        os.chdir(run_dir)
    os.system(generate_pvmap_cmd)
    os.chdir(cwd)
    return import_config


def run_statvar_processor_test_data(import_name: str,
                                    import_config: dict = None,
                                    override_config: dict = {},
                                    output_dir: str = '') -> dict:
    """Run the statvar processor for an import on the test data."""
    import_config = get_import_test_data(import_name, import_config)

    # Create a tmp directory generated files.
    import_dir = import_config.get('import_dir')
    if not output_dir:
        output_dir = os.path.join('tmp', 'test_data')
    tmp_dir = os.path.join(import_dir, output_dir)
    os.makedirs(tmp_dir, exist_ok=True)

    # Generate the statvar command with test_data input
    output_path = os.path.join(tmp_dir, 'output')
    output_data_pvs = os.path.join(tmp_dir, 'test_data_pvs.csv')
    test_override_args = {
        'input_data': import_config.get('test_data_input', ''),
        'output_path': output_path,
        'output_data_pvs': output_data_pvs,
        'genai_model': import_config.get('genai_model', '')
    }
    if override_config:
        test_override_args.update(override_config)
    statvar_test_cmd = get_statvar_processor_cmd(import_config,
                                                 test_override_args)
    import_config['test_output_data_pvs'] = output_data_pvs
    import_config['test_output'] = output_dir

    # Run the command from import dir
    # as statvar processor may have args with local paths.
    cwd = os.getcwd()
    os.chdir(import_dir)
    logging.info(f'Generating test output with command: {statvar_test_cmd}')
    os.system(statvar_test_cmd)
    os.chdir(cwd)
    return import_config


def get_statvar_processor_cmd(import_config: dict,
                              override_config: dict = {}) -> str:
    """Returns the statvar processor command using the configs.
    Uses the override configs if present, else the import_config.
    """
    statvar_cmd_args = []
    statvar_cmd_args.append('python')
    statvar_cmd_args.append(_FLAGS.statvar_processor_script)
    for arg in import_config.get('statvar_processor_args', []):
        param = ''
        if '=' in arg:
            param = arg.split('=')[0]
        if param not in override_config:
            statvar_cmd_args.append(arg)
    for param, value in override_config.items():
        if not param:
            continue
        if not param.startswith('--'):
            param = '--' + param
        statvar_cmd_args.append(f'{param}="{value}"')
    if _FLAGS.statvar_processor_options:
        # Add additional arguments.
        statvar_cmd_args.append(_FLAGS.statvar_processor_options)
    return ' '.join(statvar_cmd_args)


def load_pvmap_file(file: str, drop_ignored_props: bool = True) -> dict:
    """Load pvmap from file and drop ignored properties."""
    pvmap = load_pv_map(file)
    output_pvmap = {}
    for key, pvs in pvmap.items():
        if drop_ignored_props and key.startswith('#'):
            continue
        if not pvs:
            continue
        output_pvs = {}
        for p, v in pvs.items():
            if drop_ignored_props and p in ['#Column', 'DataType']:
                continue
            if drop_ignored_props and p.startswith('#'):
                if not (p.startswith('#Eval') or p.startswith('#Regex') or
                        p.startswith('#Filter') or p.startswith('#Multiply') or
                        p.startswith('#ignore') or p.startswith('#Format')):
                    # Drop any comments
                    continue
            output_pvs[p] = v
        if output_pvs:
            output_pvs['dcid'] = key
            output_pvmap[key] = output_pvs
    return output_pvmap


def get_pvmap_diff(pvmap_file1: str,
                   pvmap_file2: str,
                   diff_output: str = '',
                   config: dict = {},
                   counters: Counters = None) -> str:
    """Compare two pvmaps."""
    if counters is None:
        counters = Counters()
    pvmap1 = load_pvmap_file(pvmap_file1)
    pvmap2 = load_pvmap_file(pvmap_file2)
    counters.add_counter(f'nodes-input1-{pvmap_file1}', len(pvmap1))
    counters.add_counter(f'nodes-inpit2-{pvmap_file2}', len(pvmap2))
    pvmap_diff_str = diff_mcf_nodes(pvmap1,
                                    pvmap2,
                                    config=config,
                                    counters=counters)
    logging.info(f'Got pvmap diff: {pvmap_diff_str}')
    logging.info(f'Pvmap diff counters:')
    counters.print_counters()
    if diff_output:
        with open(diff_output, 'w') as fp:
            fp.write(pvmap_diff_str)
        counters_file = diff_output.replace('.diff', '') + '-counters.csv'
        file_util.file_write_csv_dict(counters.get_counters(), counters_file)
