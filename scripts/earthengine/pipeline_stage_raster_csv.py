# Copyright 2023 Google LLC
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
"""Class to run the events pipeline stage to generate CSVs
with place typs supported by DataCOmmons, such as S2Cells
from inputs such as geoTif or CSVs downloaded form external sources with lat/lng.
"""

import os
import sys

from absl import logging

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPTS_DIR)
sys.path.append(os.path.dirname(_SCRIPTS_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPTS_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPTS_DIR)), 'util'))

import earthengine_image
import file_util
import raster_to_csv

from config_map import ConfigMap
from counters import Counters
from pipeline_stage_runner import StageRunner, register_stage_runner


class RasterCSVRunner(StageRunner):
    '''Class to generate CSV per input geoTif or CSV with lat/long.'''

    def __init__(self,
                 config_dicts: list = [],
                 state: dict = {},
                 counters=None):
        self.set_up('raster_csv', config_dicts, state, counters)

    def run(self,
            input_files: list = None,
            config_dict: dict = {},
            counters: Counters = None) -> list:
        '''Returns the csv files with data per geo point generated
        from the input files.
        The input geoTif files are converted to data per-s2 cell grid.
        Input csvs with lat,longs are also converted to data per grid point.
        '''
        output_files = []

        for filename in file_util.file_get_matching(input_files):
            output_filename = self.get_output_filename(input_filename=filename)
            if self.should_skip_existing_output(output_filename):
                logging.info(
                    f'Skip processing {filename} for existing file: {output_filename}'
                )
                continue
            filebase, ext = os.path.splitext(filename)
            input_geotif = ''
            input_csv = ''
            if ext == '.csv':
                # Use CSV as input. It is assumed to have a date column.
                input_csv = filename
            else:
                input_geotif = filename
                # Get date from geoTif filename as bands may not have the
                # date.
                output_date = earthengine_image.get_date_from_filename(
                    filename, self.get_config('time_period', 'P1D',
                                              config_dict))
                if output_date:
                    self.set_config('output_date', output_date)
            config = self.get_configs()
            config.update(config_dict)
            raster_to_csv.process(input_geotif, input_csv, output_filename,
                                  ConfigMap(config_dict=config), self.counters)
            output_files.append(output_filename)
        return output_files


# Register the RasterCSVRunner
register_stage_runner('raster_csv', RasterCSVRunner)
