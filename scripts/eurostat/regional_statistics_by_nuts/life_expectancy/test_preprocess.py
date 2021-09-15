# Copyright 2020 Google LLC
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
from parameterized import parameterized
import generate_mcf


class PreprocessTest(unittest.TestCase):
    @parameterized.expand([('singlevalue', '80Years', '[Years 80]'),
                           ('interval', '40To50Years', '[Years 40 50]'),
                           ('upperlimit', 'Upto1Years', '[Years - 1]'),
                           ('lowerlimit', '85OrMoreYears', '[Years 85 -]')])
    def test_convert_range(self, name, str_in, expected):
        self.assertEqual(generate_mcf.convert_range(str_in), expected)


if __name__ == '__main__':
    unittest.main()
