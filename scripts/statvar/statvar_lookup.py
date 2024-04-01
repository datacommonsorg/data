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
"""Class to lookup StatVars using Property:Values.

To generate existing files, run the following command:
  python3 stat_var_processor.py --input_data=<path-to-csv> \
      --pv_map=<column-pv-map-file> \
      --output_path=<output-prefix>

This will generate the following outputs:
  <output-prefix>.mcf: MCF file with StatVar definitions.
  <output-prefix>.csv: CSV file with StatVarObservations.
  <output-prefix>.tmcf: MCF file mapping CSV columns to StatVar PVs.

For more details on configs and usage, please refer to the README.
"""

from collections import OrderedDict
import csv
import datetime
import glob
import itertools
import multiprocessing
import os
import re
import sys
import time
from typing import Union

from absl import app
from absl import flags
from absl import logging
import dateutil
from dateutil import parser
from dateutil.parser import parse
import pandas as pd
import process_http_server
import requests

# uncomment to run pprof
# os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
# from pypprof.net_http import start_pprof_server

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

import eval_functions
import file_util
import config_flags

from mcf_file_util import get_numeric_value
from mcf_file_util import load_mcf_nodes, write_mcf_nodes, add_namespace, strip_namespace
from mcf_filter import drop_existing_mcf_nodes
from mcf_diff import fingerprint_node, fingerprint_mcf_nodes, diff_mcf_node_pvs
from place_resolver import PlaceResolver
from json_to_csv import file_json_to_csv
from schema_generator import generate_schema_nodes

# imports from ../../util
from config_map import ConfigMap, read_py_dict_from_file
from counters import Counters, CounterOptions
from dc_api_wrapper import dc_api_is_defined_dcid
from download_util import download_file_from_url
from statvar_dcid_generator import get_statvar_dcid

_FLAGS = flags.FLAGS
