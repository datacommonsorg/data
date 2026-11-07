# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
This Python Script Load the datasets, cleans it
and generates cleaned CSV, MCF, TMCF file.
Before running this module, run download_input_files.py script, it downloads
required input files, creates necessary folders for processing.
Folder information
input_files - downloaded files (from nces naep website) are placed here
output_files - output files (mcf, tmcf and csv are written here)
"""

import os
import sys
import pandas as pd
import csv

from absl import app
from absl import flags
from absl import logging

# from ca_config import denominator_ignore_prop

MODULE_DIR = os.path.dirname(__file__)
sys.path.insert(1, MODULE_DIR + '/../../statvar')
#pylint:disable=wrong-import-position
#pylint:disable=import-error
#pylint:disable=wildcard-import
from stat_var_processor import StatVarDataProcessor, process, StatVarsMap

#pylint:enable=import-error
#pylint:disable=wildcard-import

# pylint:disable=too-few-public-methods

_FLAGS = flags.FLAGS


class Subnational(StatVarDataProcessor):
    """
    This is a subClass that inherits proeprties from StatVarDataProcessor.
    """
    # Defining path for the process.
    input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "input_files")
    global unmapped_path
    _output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "output_files")
    if not os.path.exists(_output_path):
        os.mkdir(_output_path)

    unmapped_path = os.path.join(_output_path, "unmmaped_place.txt")

    def preprocess_row(self, row: list, row_index) -> list:
        '''Modify the contents of the row and return new values.
        Can add additional columns or change values of a column.
        To ignore the row, return an empty list.'''
        # Assigning Place name to a variable.
        place_value = row[3]
        # To handle header of the file
        if place_value == "Country Name":
            return row
        pvs = self._pv_mapper.get_pvs_for_key(place_value, 'observationAbout')
        # To filter out the Place which do not have mapping dcid and writing it
        # to a file. These dcids are manually mapped if exist.
        if pvs is None:
            with open(unmapped_path, 'a') as file:
                file.write(row[3])
                file.write('\n')
            return None
        else:
            return row


if __name__ == '__main__':
    _input_files = [
        f'{MODULE_DIR}/input_files/P_Data_Extract_From_Subnational_Population_Data.csv'
    ]
    _output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "output_files/subnational")
    # config.py has common properties for every StatVar.
    _conf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "config.json")
    # The pv_map has Each column mapped to the desired property.
    # countrystatecode.json has the dcid mapping.
    _pv_map = [
        f'{MODULE_DIR}/pvmap.py',
        f'observationAbout:{MODULE_DIR}/countrystatecode.json',
    ]

    process(data_processor_class=Subnational,
            input_data=_input_files,
            output_path=_output_path,
            config_file=_conf_path,
            pv_map_files=_pv_map)

# pylint:enable=too-few-public-methods