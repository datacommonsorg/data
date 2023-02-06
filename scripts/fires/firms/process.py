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
"""Script to process NASA firms data.
The daily fires data set is downloaded as a csv with location of fires from
https://firms.modaps.eosdis.nasa.gov/api/.
These fire points are converted to S2Cells of level 13.
"""

import ast
import os
import sys
import pandas as pd

from absl import app
from absl import flags
from absl import logging
from io import StringIO

flags.DEFINE_string('config_path',
                    'gs://datcom-import-cache/fires/firms/firms_config.py',
                    'Path to JSON file with configurations.')

_FLAGS = flags.FLAGS

# Allow imports from other folders.
_SCRIPTS_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(_SCRIPTS_DIR)
sys.path.append(os.path.dirname(_SCRIPTS_DIR))

from earthengine import raster_to_csv as r2csv
from util import download_util
from util.config_map import ConfigMap


def _download_fires_csv(urls: list, output_csv: str):
    '''Download FIRMS fires CSV data and save it into output_csv file.
  Doenloads CSV rows from each url and writes all of them into a single file.

  Args:
    url: URL to download the fires data from.
       The URL download may be throttled, so, the download is retried a few times.
    output_csv: filename t save the downloaded data as csv.

  Returns:
    The file with downloaded csv data.
  '''
    dfs = []
    for url in urls:
        # Download CSV from one url.
        csv_data = ''
        for retry in range(10):
            csv_data = download_util.request_url(url=url,
                                                 method='GET',
                                                 output='text',
                                                 timeout=120,
                                                 retries=3,
                                                 retry_secs=300)
            if not csv_data or ',' not in csv_data:
                logging.debug(f'Failed to download csv data. retrying.')
                time.sleep(100)
            else:
                break
            logging.debug(f'Got {len(csv_data)} bytes from {url}')
        # Load CSV data downloaded into a DataFrame.
        dfs.append(pd.read_csv(StringIO(csv_data), dtype=str))
    # Merge all CSV rows downloaded from all URLs and save into the output file.
    df = pd.concat(dfs)
    df.to_csv(output_csv, index=False)
    logging.info(f'Downloaded FIRMS data from {url} into {output_csv}')


def process_fires_data(config_path: str):
    config = ConfigMap(config_dict=r2csv._DEFAULT_CONFIG,
                       config_string=download_util.request_url(config_path))
    if config.get('debug', False):
        logging.set_verbosity(2)

    urls = config.get('url', '')
    csv_input_data = config.get('csv_data', 'nasa_firms_input_data.csv')
    if urls:
        _download_fires_csv(urls, csv_input_data)

    # Process the CSV data into S2 cells.
    r2csv.process(input_geotiff='',
                  input_csv=csv_input_data,
                  output_csv=config.get('output_csv',
                                        'fires_s2_cell_areas.csv'),
                  config=config)


def main(_):
    process_fires_data(_FLAGS.config_path)


if __name__ == '__main__':
    app.run(main)
