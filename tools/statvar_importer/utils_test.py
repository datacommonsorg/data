# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from utils import _capitalize_first_char


class UtilsTest(unittest.TestCase):

    def test_capitalize_first_char(self):
        self.assertEqual(_capitalize_first_char("hello"), "Hello")
        self.assertEqual(_capitalize_first_char("Hello"), "Hello")
        self.assertEqual(_capitalize_first_char(""), "")
        self.assertEqual(_capitalize_first_char("1hello"), "1hello")
        self.assertEqual(_capitalize_first_char(None), None)
        self.assertEqual(_capitalize_first_char(123), 123)
        self.assertEqual(_capitalize_first_char(" h"), " h")
        self.assertEqual(_capitalize_first_char("h"), "H")


if __name__ == '__main__':
    unittest.main()
