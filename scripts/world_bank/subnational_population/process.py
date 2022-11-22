# Copyright 2022 Google LLC
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
'''Script to process flood insurance claims data from US FEMA's
National Flood Insurance Program using the generic stat-var_processor.'''

import os
import sys
import pandas as pd

from absl import app
from absl import flags

_SCRIPTS_DIR = os.path.join(
    os.path.abspath(__file__).split('scripts')[0], 'scripts')
sys.path.append(_SCRIPTS_DIR)
sys.path.append(os.path.join(_SCRIPTS_DIR, "statvar"))

from stat_var_processor import StatVarDataProcessor, process
from mcf_file_util import strip_namespace

_FLAGS = flags.FLAGS
default_input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "input_files")
default_output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "output")
pv = ['pvmap.py','observationAbout:countrystatecode.json']

# flags.DEFINE_string("input_path", default_input_path, "Import Data File's Path")
# flags.DEFINE_string("output_path", default_output_path, "Output Data File's Path")
# flags.DEFINE_list("pv_map", pv, "pv map Files")

def process_data():
    process(input_data=default_input_path,
            output_path=default_output_path,
            pv_map_files=pv)


def main(_):
    process_data()


if __name__ == '__main__':
    app.run(main)