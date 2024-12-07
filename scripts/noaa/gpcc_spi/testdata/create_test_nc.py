# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Create a trimmed version of SPI nc sources for testing purposes.

Usage (from repo root dir):
cd scripts/noaa/gpcc_spi
python create_test_nc.py
"""

from absl import app
import pandas as pd
import xarray
from pathlib import Path
import os


def create_test_nc(source_file):
    ds = xarray.open_dataset(source_file, engine='netcdf4')
    df = ds.to_dataframe()
    # Remove if spi value is missing
    df = df.dropna()

    montana_spi_1988 = df[(df.index.get_level_values(0) == 47.5) &
                          (df.index.get_level_values(1) == 249.5) &
                          (df.index.get_level_values(2) >= '1988-01-01') &
                          (df.index.get_level_values(2) <= '1988-12-31')]

    nevada_spi_1988 = df[(df.index.get_level_values(0) == 37.5) &
                         (df.index.get_level_values(1) == 242.5) &
                         (df.index.get_level_values(2) >= '1988-01-01') &
                         (df.index.get_level_values(2) <= '1988-12-31')]
    combined = pd.concat([
        nevada_spi_1988,
        montana_spi_1988,
    ])

    filename = Path(source_file).name
    combined.to_xarray().to_netcdf(os.path.join('testdata', filename),
                                   engine='netcdf4')


def main(_):
    source_files = [
        '/tmp/gpcc_spi/gpcc_spi_pearson_12.nc',
        '/tmp/gpcc_spi/gpcc_spi_pearson_72.nc'
    ]
    for source_file in source_files:
        create_test_nc(source_file)


if __name__ == "__main__":
    app.run(main)
