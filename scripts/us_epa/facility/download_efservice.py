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

flags.DEFINE_string('epa_table_name', '', 'Name of table to download')
flags.DEFINE_string('epa_output_path', 'tmp_data', 'Output directory')

_API_ROOT = 'https://data.epa.gov/efservice/'
_MAX_ROWS = 10000


def main(_):
    assert FLAGS.epa_output_path
    assert FLAGS.epa_table_name
    pathlib.Path(FLAGS.epa_output_path).mkdir(exist_ok=True)
    fh.download(_API_ROOT, FLAGS.epa_table_name, _MAX_ROWS,
                FLAGS.epa_output_path)


if __name__ == '__main__':
    app.run(main)
