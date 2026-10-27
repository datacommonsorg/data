# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""A simple script to download a full table in CSV form from https://data.epa.gov/efservice"""

import os
import pathlib
import sys

from absl import app
from absl import flags

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_PATH, '../../..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
from scripts.us_epa.util import facilities_helper as fh

FLAGS = flags.FLAGS

flags.DEFINE_string('companies_table_name', 'V_PARENT_COMPANY_INFO',
                    'Name of table to download')
flags.DEFINE_string('output_path', 'input_files', 'Output directory')

_API_ROOT = 'https://data.epa.gov/efservice/'
_MAX_ROWS = 10000


def main(_):
    if not FLAGS.output_path:
        raise ValueError('output_path must be provided.')
    if not FLAGS.companies_table_name:
        raise ValueError('companies_table_name must be provided.')
    pathlib.Path(FLAGS.output_path).mkdir(parents=True, exist_ok=True)
    fh.download(_API_ROOT, FLAGS.companies_table_name, _MAX_ROWS,
                FLAGS.output_path)


if __name__ == '__main__':
    app.run(main)
