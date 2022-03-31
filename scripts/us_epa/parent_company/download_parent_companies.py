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
import ssl
import sys

import pandas as pd

from absl import app
from absl import flags

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../..'))
from us_epa.util import facilities_helper as fh

FLAGS = flags.FLAGS

flags.DEFINE_string('companies_table_name', '', 'Name of table to download')
flags.DEFINE_string('output_path', 'tmp_data', 'Output directory')

_API_ROOT = 'https://data.epa.gov/efservice/'
_MAX_ROWS = 10000


def main(_):
    assert FLAGS.output_path
    assert FLAGS.companies_table_name
    pathlib.Path(FLAGS.output_path).mkdir(exist_ok=True)
    fh.download(_API_ROOT, FLAGS.companies_table_name, _MAX_ROWS,
                FLAGS.output_path)


if __name__ == '__main__':
    app.run(main)
