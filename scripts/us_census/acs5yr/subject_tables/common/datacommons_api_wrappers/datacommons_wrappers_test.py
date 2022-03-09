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

import unittest
from DC_wrappers import *


class TestDCWrappers(unittest.TestCase):

    def test_dc_check_existence(self):
        ret = dc_check_existence(['Count_Person', 'Person', 'node1'])
        self.assertEqual(ret, {
            'Count_Person': True,
            'Person': True,
            'node1': False
        })


if __name__ == '__main__':
    unittest.main()
