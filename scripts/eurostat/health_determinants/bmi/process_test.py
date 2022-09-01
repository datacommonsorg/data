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

import os
import sys

_COMMON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(1, _COMMON_PATH)
from process import EuroStatBMI
from common.unitest_common_methods import CommonTestClass


class BMITestInit:

    def __init__(self):
        MODULE_DIR = os.path.dirname(__file__)
        test_input_files_directory = os.path.join(MODULE_DIR, "test_files",
                                                  "input_files")
        self.ip_test_files = os.listdir(test_input_files_directory)
        self.ip_test_files = [
            test_input_files_directory + os.sep + file
            for file in self.ip_test_files
        ]
        self.expected_files_directory = os.path.join(MODULE_DIR, "test_files",
                                                     "expected_files")
        self.import_class = EuroStatBMI


class BMITest(CommonTestClass.CommonTestCases):
    klass = BMITestInit
