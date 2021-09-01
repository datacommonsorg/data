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

import csv
import os
import pandas as pd
import unittest
from india.geo.districts import IndiaDistrictsMapper


class TestPreprocess(unittest.TestCase):

    def test_get_district_name_to_lgd_code_mapping(self):
        mapper = IndiaDistrictsMapper()
        district_lgd_code = mapper.get_district_name_to_lgd_code_mapping(
            "Karnataka", "bengaluru rural")
