# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import json
import pandas as pd
# from india.geo.states import IndiaDistrictsMapper

# UTILS_PATH = 'india_wris/utils/'
UTILS_PATH = '../utils/'
data = pd.read_csv('data.csv')

json_file_path = "../util/pollutants.json"

with open(json_file_path, 'r') as j:
     pollutants = json.loads(j.read())
