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
"""Script to get pvmap generation quality."""

import os
import sys
import glob
import shlex

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
from mcf_diff import diff_mcf_nodes

import statvar_imports_utils as sv_utils

# Globals
_FLAGS = flags.FLAGS

flags.DEFINE_string(
    'statvar_import_name', '',
    'StatVarProcessor based import to evaluate with a manifest.json.')
flags.DEFINE_string('pvmap_generation_method', 'statvar',
                    'Method fof pv map generation.')


def main(_):
    # uncomment to run pprof
    # start_pprof_server(port=8123)

    # Launch a web server with a form for commandline args
    # if the command line flag --http_port is set.
    process_http_server.run_http_server(http_port=_FLAGS.http_port,
                                        script=__file__,
                                        module=config_flags)
    process_import(import_name=_FLAGS.statvar_import_name,
                   pvmap_generation_method=_FLAGS.pvmap_generation_method)


if __name__ == '__main__':
    app.run(main)
