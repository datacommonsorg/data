#!/usr/bin/env python3

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
