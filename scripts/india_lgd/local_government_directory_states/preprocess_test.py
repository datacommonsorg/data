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

import filecmp
import os
import json
import tempfile
import unittest
from india_lgd.local_government_directory_states.preprocess import LocalGovermentDirectoryStatesDataLoader

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)


class TestPreprocess(unittest.TestCase):
    def test_create_csv(self):
        lgd_csv = os.path.join(os.path.dirname(__file__),
                               "./test_data/lgd_allStateofIndia_export.csv")
        wikidata_csv = os.path.join(
            os.path.dirname(__file__),
            "./test_data/wikidata_india_states_and_ut_export.csv")
        clean_csv = os.path.join(os.path.dirname(__file__),
                                 "./test_data/clean_csv.csv")

        expected_csv = os.path.join(os.path.dirname(__file__),
                                    "./test_data/expected_csv.csv")

        loader = LocalGovermentDirectoryStatesDataLoader(
            lgd_csv, wikidata_csv, clean_csv)
        loader.process()
        loader.save()

        result_file = open(clean_csv)
        result_data = result_file.read()
        result_file.close()

        expected_file = open(expected_csv)
        expected_data = expected_file.read()
        expected_file.close()

        os.remove(clean_csv)
        self.assertEqual(expected_data, result_data)


if __name__ == '__main__':
    unittest.main()
