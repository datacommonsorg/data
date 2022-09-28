# Copyright 2022 Google LLC
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
import os
import unittest
from preprocess import map_names, GeoSadakLoader

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)


class TestPreprocess(unittest.TestCase):

    maxDiff = None

    def test_create_csv(self):
        expected_file = open(os.path.join(module_dir_, 'test/expected.csv'))
        expected_data = expected_file.read()
        expected_file.close()

        loader = GeoSadakLoader(
            source=os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'test/Gujarat.zip',
            ),
            state_name="Gujarat",
        )
        loader.load()
        loader.process()
        loader.save(os.path.join(module_dir_, "test/output.csv"))

        result_file = open(os.path.join(module_dir_, "test/output.csv"))
        result_data = result_file.read()
        result_file.close()

        os.remove(os.path.join(module_dir_, "test/output.csv"))
        self.assertEqual(u'{}'.format(expected_data), result_data)


if __name__ == '__main__':
    unittest.main()
