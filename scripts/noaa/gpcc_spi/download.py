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

flags.DEFINE_string('download_dir', '/tmp/gpcc_spi', 'Output directory.')

flags.DEFINE_list('periods', None, (
    'Comma separated list of periods. '
    'A period is the duration in months for a particular SPI value.'
    'Possible values are 1, 2, 3, 6, 9, 12, 24, 36, 48, 60, and 72, defaults to\
        all.'))
DEFAULT_PERIODS = ['1', '3', '6', '9', '36', '72']

flags.DEFINE_string('distribution', 'pearson',
                    ('Distribution fucntion used to compute the SPI.'
                     'One of (pearson, gamma). Defaults to pearson.'))
DEFAULT_DISTRIBUTION = 'pearson'


def download_one(url, path: str):
    """Download a single spi nc file."""
    logging.info('Starting to download %s to %s', url, path)
    with urllib.request.urlopen(url) as source:
        with open(path, 'wb') as dest:
            shutil.copyfileobj(source, dest)
    logging.info('Finished downloading: %s', path)


def download_all(download_dir: str, distribution: str, periods: List[str]):
    """Download spi nc files for all periods."""
    os.makedirs(download_dir, exist_ok=True)

    periods = DEFAULT_PERIODS
    distribution = DEFAULT_DISTRIBUTION

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for period in periods:
            p = period if int(
                period
            ) >= 10 else f"0{int(period)}"  # url format is '01' instead '1'
            url = f'https://www.ncei.noaa.gov/pub/data/nidis/gpcc/spi-pearson/\
                gpcc-spi-{distribution}-{p}.nc'

            dest = os.path.join(download_dir, f'gpcc_spi_{distribution}_{p}.nc')
            futures.append(executor.submit(download_one, url, dest))

        for future in concurrent.futures.as_completed(futures):
            if future.exception():
                raise Exception(
                    "Part of the download failed. Please re-run or fix the\
                        script.")


def main(_):
    """Download all nc files."""
    download_all(FLAGS.download_dir, FLAGS.periods, FLAGS.distribution)


if __name__ == "__main__":
    app.run(main)
