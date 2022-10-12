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
"""Wrapper for

1. Download
2. Preprocess csv files.
3. Aggregate over places.
"""

import os

from .download import download_all
from .download import DEFAULT_DISTRIBUTION
from .download import DEFAULT_PERIODS

from .preprocess_gpcc_spi import preprocess_gpcc_spi
from .gpcc_spi_aggregation import run_gpcc_spi_aggregation
from .gpcc_spi_aggregation import DEFAULT_PLACE_AREA_RATIO_JSON_PATH

from absl import flags
from absl import app

FLAGS = flags.FLAGS

flags.DEFINE_string('process_dir', '/tmp/gpcc_spi', 'Directory ')


def run(process_dir):
    """Runs download, preprocess, and aggregation in series."""

    download_dir = os.path.join(process_dir, 'download')
    spi_nc_file_patterns = os.path.join(download_dir, 'gpcc_spi*.nc')

    preprocess_dir = os.path.join(process_dir, 'preprocessed')
    preprocessed_csv_pattern = os.path.join(preprocess_dir, '*.csv')

    aggregations_dir = os.path.join(process_dir, 'aggregations')

    download_all(download_dir, DEFAULT_DISTRIBUTION, DEFAULT_PERIODS)

    preprocess_gpcc_spi(spi_nc_file_patterns, preprocess_dir)

    run_gpcc_spi_aggregation(preprocessed_csv_pattern, aggregations_dir,
                             DEFAULT_PLACE_AREA_RATIO_JSON_PATH)


def main(_):
    """Entrypoint for running all gpcc spi related."""
    run(FLAGS.process_dir)


if __name__ == "__main__":
    app.run(main)
