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

import csv
import math
import glob
import xarray
from datetime import datetime
import numpy as np
import os
import sys
from pathlib import Path
from typing import Optional

from absl import flags
from absl import app

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../util/'))  # for recon util

FLAGS = flags.FLAGS

flags.DEFINE_string('in_pattern', '/tmp/gpcc_spi/*.nc',
                    'Input NetCDF4 file(s).')
flags.DEFINE_string('output_dir', '/tmp/gpcc_spi/out',
                    'The directory where the output mcf will be generated in.')


def to_one_degree_grid_place(latlon):
  """Latlng data to grid format.

  Change longitude from 0 ~ 360 scale to -180 ~ 180 scale.
  Change coordinate from middle of the grid to north west point of the grid.
  """
  return f'grid_1/{math.floor(latlon[0])}_{math.floor((latlon[1]+180)%360 - 180)}'


def nc_to_df(nc_path, period, spi_col):
  """Read a netcdf and parse to df."""
  ds = xarray.open_dataset(nc_path, engine='netcdf4')
  df = ds.to_dataframe()
  # Remove if spi value is missing
  df = df.dropna()
  # By default, SPI data has a multi index of ('lat', 'lon', 'time')
  df = df.reset_index()
  # Rename the spi col from "spi_01" for example to spi.
  # This is so that data for all accumulation periods have a standard SPI column
  # for the tmcf to express.
  df.rename(columns={spi_col: "spi"}, inplace=True)
  df['variable'] = f"dcs:standardizedPrecipitationIndex_Atmosphere_{int(period)}MonthPeriod"
  df['place'] = df[['lat', 'lon']].apply(to_one_degree_grid_place, axis=1)
  df = df.drop('lat', axis=1)
  df = df.drop('lon', axis=1)
  return df


def process_one(in_file, output_dir: Optional[str] = None, write: bool = True):
  print("processing file:  ", in_file, " ", datetime.now().strftime("%H:%M:%S"))
  path = Path(in_file)
  period = int(path.stem.split('_')[-1])
  spi_col = f"spi_{path.stem.split('_')[-1]}"

  output_path = os.path.join(output_dir, path.with_suffix('.csv').name)

  df = nc_to_df(in_file, period, spi_col)
  if write:
    df.to_csv(
        path_or_buf=output_path,
        columns=['time', 'spi', 'variable', 'place'],
        index=False)
    return output_path
  else:
    return df
  print("finished writing csv: ", datetime.now().strftime("%H:%M:%S"))


def process_main(in_pattern, output_dir: str):
  for file in sorted(glob.glob(in_pattern)):
    process_one(file, output_dir)


def main(_):
  process_main(FLAGS.in_pattern, FLAGS.output_dir)


if __name__ == "__main__":
  app.run(main)
