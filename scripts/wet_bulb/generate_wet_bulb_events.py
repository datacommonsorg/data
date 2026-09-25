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
"""Script to generate WetBulb events using the events pipeline.

The events pipeline is setup with the following stages:
  1. earthengine:
     It uses the NASA/GSFC/MERRA/slv/2 data set from EarthEngine to get regions
     with high wetbulb temperature as a geoTif per day.

  2. raster_csv
     The geoTif is converted into a CSV with each pixel with regions with high
     wet bulb temperature converted into an S2 cell of level 10
     using the raster_to_csv.py utilities.

  3. events
     The resulting CSV with s2 cells is aggregated into events using
     the process_events.py. Neighbouring s2 cells with high wet-bulb temperatures
     are collated into a single event.
     s2 cells with web bulb temperature over successive days are also
     added into the same event.

     Once the regions with wet bulb temperature collated into events,
     the process_events.py utilities also generate a CSV with
     StatVar Observations for Area_WetBulbTemperatureEvent and
     Count_WetBulbTemperatureEvent for each events s2 cells at level 10, and places it is
     contained in, such as AdministrativeArea, Country, Continent and Earth.

  The generated files including the geoTif, CSVs with S2 cells and events are saved
  in GCS.

  The script runs once a month to update wetbulb events for the current year.
"""

import os
import re
import sys
import time

from absl import app
from absl import flags
from absl import logging

_SCRIPTS_DIR = os.path.dirname(__file__)
sys.path.append(_SCRIPTS_DIR)
sys.path.append(os.path.dirname(_SCRIPTS_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPTS_DIR)))
sys.path.append(os.path.join(os.path.dirname(_SCRIPTS_DIR), 'earthengine'))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPTS_DIR)), 'util'))

flags.DEFINE_string(
    'wet_bulb_pipeline_config',
    os.path.join(_SCRIPTS_DIR, 'wet_bulb_events_pipeline_config.py'),
    'Config for the pipeline as a py dictionary of json')

flags.DEFINE_list(
    'wet_bulb_pipeline_stages', [],
    'List of stages in the wetbulb events pipeline config to be run.')

_FLAGS = flags.FLAGS

import file_util

from config_map import ConfigMap
from events_pipeline import EventPipeline


def main(_):
    config = ConfigMap(filename=_FLAGS.wet_bulb_pipeline_config)
    if _FLAGS.start_date:
        config.get('defaults', {})['start_date'] = _FLAGS.start_date
    pipeline = EventPipeline(config=config)
    pipeline.run(run_stages=_FLAGS.wet_bulb_pipeline_stages)


if __name__ == '__main__':
    app.run(main)
