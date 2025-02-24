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

from genericpath import exists
import math
import glob
import xarray
from datetime import datetime
import logging
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

flags.DEFINE_string('gpcc_spi_input_pattern', '/tmp/gpcc_spi/*.nc',
                    'Input NetCDF4 file(s).')
flags.DEFINE_string('gpcc_spi_preprocessed_dir', '/tmp/gpcc_spi/out',
                    'The directory where the output mcf will be generated in.')
DEFAULT_START_DATE = '1900-01-01'
flags.DEFINE_string('start_date', DEFAULT_START_DATE,
                    'Dash separated start date. Defaults to "1900-01-01"')
DEFAULT_END_DATE = datetime.today().strftime('%Y-%m-%d')
flags.DEFINE_string('end_date', DEFAULT_END_DATE,
                    'Dash separated start date. Defaults to the running date.')


def to_one_degree_grid_place(latlon):
    """Latlng data to grid format.

  Change longitude from 0 ~ 360 scale to -180 ~ 180 scale.
  Change coordinate from middle of the grid to north west point of the grid.
  """
    return f'grid_1/{math.floor(latlon[0])}_{math.floor((latlon[1]+180)%360 - 180)}'


def nc_to_df(nc_path, period, spi_col, start_date, end_date):
    """Read a netcdf and parse to df."""
    ds = xarray.open_dataset(nc_path, engine='netcdf4')
    df = ds.to_dataframe()
    df = df[(df.index.get_level_values('time') >= start_date) &
            (df.index.get_level_values('time') <= end_date)]

    # Remove if spi value is missing
    df = df.dropna()
    # By default, SPI data has a multi index of ('lat', 'lon', 'time')
    df = df.reset_index()
    # Rename the spi col from "spi_01" for example to spi.
    # This is so that data for all accumulation periods have a standard SPI column
    # for the tmcf to express.
    df.rename(columns={spi_col: "spi"}, inplace=True)
    df['variable'] = f'dcs:StandardizedPrecipitationIndex_Atmosphere_{int(period)}MonthPeriod'
    df['period'] = f'"[{int(period)} dcs:Monthly]"'
    df['place'] = df[['lat', 'lon']].apply(to_one_degree_grid_place, axis=1)
    df = df.drop('lat', axis=1)
    df = df.drop('lon', axis=1)
    return df


def preprocess_one(start_date,
                   end_date,
                   in_file: str,
                   preprocessed_dir: Optional[str] = None,
                   write: bool = True):
    """Create a single csv file from a single input nc file."""
    logging.info('processing file:  %s: %s', in_file,
                 datetime.now().strftime('%H:%M:%S'))
    path = Path(in_file)
    period = int(path.stem.split('_')[-1])
    spi_col = f"spi_{path.stem.split('_')[-1]}"

    df = nc_to_df(in_file, period, spi_col, start_date, end_date)
    if not write:
        return df

    output_path = os.path.join(preprocessed_dir, path.with_suffix('.csv').name)
    df.to_csv(path_or_buf=output_path,
              columns=['time', 'spi', 'variable', 'period', 'place'],
              index=False,
              quotechar="'")  # This writes double quote as is.
    logging.info('finished writing csv: %s',
                 datetime.now().strftime('%H:%M:%S'))
    return output_path


def preprocess_gpcc_spi(start_date, end_date, in_pattern,
                        preprocessed_dir: str):
    """Run preprocess for all input patterns."""
    os.makedirs(preprocessed_dir, exist_ok=True)

    for file in sorted(glob.glob(in_pattern)):
        preprocess_one(start_date, end_date, file, preprocessed_dir)


def main(_):
    """Run pre-preocess spis with flags."""
    preprocess_gpcc_spi(FLAGS.start_date, FLAGS.end_date,
                        FLAGS.gpcc_spi_input_pattern,
                        FLAGS.gpcc_spi_preprocessed_dir)


if __name__ == "__main__":
    app.run(main)
