"""A simple script to download a full table in CSV form from https://data.epa.gov/efservice"""

import os
import pathlib
import ssl

import pandas as pd

from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_string('epa_table_name', '', 'Name of table to download')
flags.DEFINE_string('epa_output_path', 'tmp_data', 'Output directory')

_API_ROOT = 'https://data.epa.gov/efservice/'
_MAX_ROWS = 10000


def download(table_name, output_path):
    # Per https://stackoverflow.com/a/56230607
    ssl._create_default_https_context = ssl._create_unverified_context

    idx = 0
    out_file = os.path.join(output_path, table_name + '.csv')
    first_time = True
    while True:
        # Since 10K rows shouldn't consume too much memory, just use pandas.
        url = _API_ROOT + table_name + '/ROWS/' + str(idx) + ':' + str(
            idx + _MAX_ROWS - 1) + '/csv'
        df = pd.read_csv(url, dtype=str)
        print('Downloaded ' + str(len(df)) + ' rows from ' + url)
        if len(df) == 0:
            break
        if first_time:
            mode = 'w'
            header = True
            first_time = False
        else:
            mode = 'a'
            header = False
        df.to_csv(out_file, mode=mode, header=header, index=False)
        idx = idx + 10000


def main(_):
    assert FLAGS.epa_output_path
    assert FLAGS.epa_table_name
    pathlib.Path(FLAGS.epa_output_path).mkdir(exist_ok=True)
    download(FLAGS.epa_table_name, FLAGS.epa_output_path)


if __name__ == '__main__':
    app.run(main)
