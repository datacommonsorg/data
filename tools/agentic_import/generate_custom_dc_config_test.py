#!/usr/bin/env python3

# Copyright 2025 Google LLC
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

import json
import os
import shutil
import tempfile
import unittest

from generate_custom_dc_config import ConfigGenerator


class TestConfigGenerator(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.csv_file = os.path.join(self.temp_dir, "test.csv")
        self.config_file = os.path.join(self.temp_dir, "config.json")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def create_test_csv(self, content):
        with open(self.csv_file, 'w') as f:
            f.write(content)

    def test_required_columns_only(self):
        csv_content = "observationAbout,observationDate,variableMeasured,value\ngeoId/06,2020,Count_Person,39538223"
        self.create_test_csv(csv_content)

        generator = ConfigGenerator(self.csv_file, self.config_file)
        generator.run()

        with open(self.config_file, 'r') as f:
            config = json.load(f)

        self.assertIn("test.csv", config["inputFiles"])
        column_mappings = config["inputFiles"]["test.csv"]["columnMappings"]

        expected_mappings = {
            "entity": "observationAbout",
            "date": "observationDate",
            "variable": "variableMeasured",
            "value": "value"
        }
        self.assertEqual(column_mappings, expected_mappings)

    def test_with_optional_columns(self):
        csv_content = "observationAbout,observationDate,variableMeasured,value,unit,scalingFactor\ngeoId/06,2020,Count_Person,39538223,Person,1"
        self.create_test_csv(csv_content)

        generator = ConfigGenerator(self.csv_file, self.config_file)
        generator.run()

        with open(self.config_file, 'r') as f:
            config = json.load(f)

        column_mappings = config["inputFiles"]["test.csv"]["columnMappings"]

        self.assertIn("unit", column_mappings)
        self.assertIn("scalingFactor", column_mappings)
        self.assertEqual(column_mappings["unit"], "unit")
        self.assertEqual(column_mappings["scalingFactor"], "scalingFactor")

    def test_missing_required_columns(self):
        csv_content = "observationAbout,observationDate\ngeoId/06,2020"
        self.create_test_csv(csv_content)

        generator = ConfigGenerator(self.csv_file, self.config_file)

        with self.assertRaises(ValueError) as context:
            generator.run()

        self.assertIn("Missing required columns", str(context.exception))

    def test_file_not_found(self):
        non_existent_file = os.path.join(self.temp_dir, "nonexistent.csv")

        generator = ConfigGenerator(non_existent_file, self.config_file)

        with self.assertRaises(FileNotFoundError):
            generator.run()


if __name__ == '__main__':
    unittest.main()
