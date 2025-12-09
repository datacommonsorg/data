# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
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

import pandas as pd
import requests

from absl import app
from absl import flags
from absl import logging

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../..'))
from us_epa.util import facilities_helper as fh

FLAGS = flags.FLAGS

flags.DEFINE_string('companies_table_name', '', 'Name of table to download')
flags.DEFINE_string('output_path', 'tmp_data', 'Output directory')

_API_ROOT = 'https://data.epa.gov/efservice/'
_MAX_ROWS = 10000


def main(_):
    logging.info("Starting download process for EPA parent companies.")

    assert FLAGS.output_path, "Output path must be specified."
    assert FLAGS.companies_table_name, "Company table name must be specified."

    pathlib.Path(FLAGS.output_path).mkdir(exist_ok=True)

    try:
        fh.download(_API_ROOT, FLAGS.companies_table_name, _MAX_ROWS,
                    FLAGS.output_path)
        logging.info(
            f"Successfully completed download for table: {FLAGS.companies_table_name}"
        )

    except pd.errors.EmptyDataError:
        logging.info(
            f"Detected end of data for table '{FLAGS.companies_table_name}'. Pagination completed gracefully."
        )

    except requests.exceptions.RequestException as e:
        logging.fatal(
            f"Network or HTTP error during download for {FLAGS.companies_table_name}: {e}"
        )
        raise RuntimeError(f"Network or HTTP error: {e}")  # Added RuntimeError
        sys.exit(1)

    except Exception as e:
        logging.fatal(
            f"An unexpected error occurred during download for {FLAGS.companies_table_name}: {e}"
        )
        raise RuntimeError(
            f"Unexpected error during download: {e}")  # Added RuntimeError
        sys.exit(1)


if __name__ == '__main__':
    app.run(main)
