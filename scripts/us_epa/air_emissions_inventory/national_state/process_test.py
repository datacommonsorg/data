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
Script to automate the testing for EuroStat BMI (Body Mass Index) process script.
"""
import os
import sys

_COMMON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '...'))
sys.path.insert(1, _COMMON_PATH)
# pylint: disable=wrong-import-position
from process import USAirPollutionEmissionTrendsNationalAndState
from common.unitest_common_methods import CommonTestClass
# pylint: enable=wrong-import-position


class USAirPollutionEmissionTrendsNationalAndStateTest(
        CommonTestClass.CommonTestCases):
    _import_class = USAirPollutionEmissionTrendsNationalAndState
    _test_module_directory = os.path.dirname(__file__)
