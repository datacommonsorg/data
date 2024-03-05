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
"""Class to run the events pipeline stage to extract images form Earth Engine.
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

from counters import Counters
from pipeline_stage_runner import StageRunner, register_stage_runner


class EarthEngineRunner(StageRunner):
    '''Class to generate geoTif images from earth engine.'''

    def __init__(self,
                 config_dicts: list = [],
                 state: dict = {},
                 counters=None):
        configs = [earthengine_image.EE_DEFAULT_CONFIG]
        configs.extend(config_dicts)
        self.set_up('earthengine', configs, state, counters)

    def run(self,
            input_files: list = None,
            config_dict: dict = {},
            counters: Counters = None) -> list:
        '''Returns the list of geoTif images extracted from earth engine.
        If the stage's config:ee_wait_task is False,
        returns the list of earth engine tasks launched.
        '''
        logging.info(f'Processing earth engine config: {config_dict}')
        # Generate ee images
        ee_tasks = earthengine_image.ee_process(config_dict)
        if not ee_tasks:
            logging.info(
                f'No tasks or images returned for config:{config_dict}')
            return None
        # Return the list of output files.
        image_files = []
        for status in ee_tasks:
            output_file = status.get('output_file', '')
            if output_file:
                image_files.append(output_file)
        return image_files


# Register the EarthEngineRunner
register_stage_runner('earthengine', EarthEngineRunner)
