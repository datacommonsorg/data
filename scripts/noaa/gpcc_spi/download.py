# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""""Downloads GRCC  Global Standarized Precipitation Index (SPI) data.


Please see the data readme for release schedule.
https://www.ncei.noaa.gov/pub/data/nidis/gpcc/nidis_gpcc_readme_c20220520.txt
"""

from absl import app
from absl import flags
import concurrent.futures
import logging
import urllib
import urllib.request
import shutil
from typing import List
import os

FLAGS = flags.FLAGS

flags.DEFINE_string('output_dir', '/tmp/gpcc_spi', 'Output directory.')
flags.DEFINE_list('periods', None, (
    'Comma separated list of periods. A period is the duration in months for a particular SPI value.'
    'Possible values are 1, 2, 3, 6, 9, 12, 24, 36, 48, 60, and 72, defaults to all.'
))
flags.DEFINE_string('distribution', 'pearson',
                    ('Distribution fucntion used to compute the SPI.'
                     'One of (pearson, gamma). Defaults to pearson.'))


def download_one(url, path: str):
  logging.info('Starting to download %s to %s' % (url, path))
  with urllib.request.urlopen(url) as source:
    with open(path, 'wb') as dest:
      shutil.copyfileobj(source, dest)
  logging.info('Finished downloading: %s' % path)


def download_all(output_dir: str, periods: List[str], distribution: str):
  with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = []
    for period in periods:
      p = period if int(
          period) >= 10 else f"0{int(period)}"  # url format is '01' instead '1'
      url = f'https://www.ncei.noaa.gov/pub/data/nidis/gpcc/spi-pearson/gpcc-spi-{distribution}-{p}.nc'
      dest = os.path.join(output_dir, f'gpcc_spi_{distribution}_{p}.nc')
      futures.append(executor.submit(download_one, url, dest))

    for future in concurrent.futures.as_completed(futures):
      if future.exception():
        raise Exception(
            "Part of the download failed. Please re-run or fix the script.")


def main(_):
  os.makedirs(FLAGS.output_dir, exist_ok=True)

  periods = FLAGS.periods
  if not periods:
    periods = ['1', '2', '3', '6', '9', '12', '24', '36', '48', '60', '72']
  download_all(FLAGS.output_dir, periods, FLAGS.distribution)


if __name__ == "__main__":
  app.run(main)
