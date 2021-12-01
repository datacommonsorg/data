# Copyright 2021 Google LLC
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
Module to generate a column map to their corresponding statistical variable defintions.
"""
import os
import io
import sys
import logging
import json
import re
import csv
from zipfile import ZipFile
from collections import OrderedDict
import pandas as pd

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH,
                             '../common'))  # for statvar_dcid_generator
from generate_col_map import GenerateColMapBase


def process_zip_file(zip_file_path,
                     spec_path,
                     write_output=True,
                     output_dir_path='./',
                     delimiter='!!',
                     header_row=1):
    """Given a zip file of datasets in csv format, the function builds a column map for each year
  Args:
    zip_file_path: input zip file with data files in csv format, file naming expected to be consistent with data.census.gov
    spec_path: File path where the JSON specification to be used for generating the column map is present
    write_output: Boolean to allow saving the generated column map to an out_dir_path. (default = False)
    output_dir_path: File path to the directory where column map is to be saved (default=./)
    delimiter: specify the string delimiter used in the column names. (default=!!, for subject tables)
    header_row: specify the index of the row where the column names are found in the csv files (default=1, for subject tables)
  Returns:
    A dictionary mapping each year with the corresponding column_map from generate_stat_var_map()
    Example:
      "2016": {
        "Total Civilian population": {
          "populationType": "Person",
          "statType": "measuredValue",
          "measuredProperty": "Count Person"
          "armedForceStatus": "Civilian"
        },
        "<column-name-2>": {}, .....,
      }
  """
    f = open(spec_path, 'r')
    spec_dict = json.load(f)
    f.close()

    column_map = {}
    counter_dict = {}

    with ZipFile(zip_file_path) as zf:
        for filename in zf.namelist():
            if 'data_with_overlays' in filename:
                df = pd.read_csv(zf.open(filename, 'r'),
                                 header=header_row,
                                 low_memory=False)
                year = filename.split(f'ACSST5Y')[1][:4]
                column_map[year] = generate_stat_var_map(
                    spec_dict, df.columns.tolist(), delimiter)

    ## save the column_map
    if write_output:
        f = open(f'{output_dir_path}/column_map.json', 'w')
        json.dump(column_map, f, indent=4)
        f.close()
    return column_map


def generate_stat_var_map(spec_dict, column_list, delimiter='!!'):
    """Wrapper function for generateColMapBase class to generate column map.

  Args:
    specDict: A dictionary containing specifications for the different properties of the statistical variable.
    columnList: A list of column names for which the column map needs to be generated. This is typically the column header in the dataset.

  Returns:
    A dictionary mapping each column to their respective stat_var node definitions.
    Example: {
      "Total Civilian population": {
        "populationType": "Person",
        "statType": "measuredValue",
        "measuredProperty": "Count Person"
        "armedForceStatus": "Civilian"
      },
      "<column-name-2>": {}, .....,
    }
  """
    col_map_obj = GenerateColMapBase(spec_dict=spec_dict,
                                     column_list=column_list,
                                     delimiter=delimiter)
    return col_map_obj._generate_stat_vars_from_spec()
