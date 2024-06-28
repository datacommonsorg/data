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
"""Class to run the events pipeline stage to generate events from CSV.
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

import process_events

from config_map import ConfigMap
from counters import Counters
from pipeline_stage_runner import StageRunner, register_stage_runner


class EventsRunner(StageRunner):
    '''Class to generate Events and StatvarObservations using GeoEventsProcessor.'''

    def __init__(self,
                 config_dicts: list = [],
                 state: dict = {},
                 counters=None):
        configs = [process_events.get_default_config()]
        configs.extend(config_dicts)
        self.set_up('events', configs, state, counters)

    def run(self,
            input_files: list = None,
            config_dict: dict = {},
            counters: Counters = None) -> list:
        '''Process data for places into events.'''
        config = ConfigMap(config_dict=config_dict)
        output_path = self.get_output_dir(config_dict)
        return process_events.process(csv_files=input_files,
                                      output_path=output_path,
                                      config=config)


# Register the EventsRunner
register_stage_runner('events', EventsRunner)
