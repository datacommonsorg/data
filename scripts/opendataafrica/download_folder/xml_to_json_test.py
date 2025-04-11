import json
import os
import tempfile
import unittest
import pandas as pd
import xml.etree.ElementTree as ET
from io import StringIO
from unittest.mock import patch

import xml_to_json


class XMLToJsonConverterTest(unittest.TestCase):
    """This class has the method required to test the convert_xml_to_json function."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.input_xml_path = os.path.join(self.temp_dir, 'input.xml')
        self.output_json_path = os.path.join(self.temp_dir, 'output.json')

    def tearDown(self):
        os.remove(self.input_xml_path)
        os.remove(self.output_json_path)
        os.rmdir(self.temp_dir)

    def _create_xml_file(self, content):
        with open(self.input_xml_path, 'w') as f:
            f.write(content)

    def _read_json_file(self):
        with open(self.output_json_path, 'r') as f:
            return json.load(f)

    def test_xml_with_different_data_types(self):
        # Create an XML content string
        xml_content = """
        <data>
            <string>Hello</string>
            <integer>42</integer>
            <float>3.14</float>
            <boolean>true</boolean>
            <null/>
        </data>
        """
        # Create a temporary XML file
        self._create_xml_file(xml_content)

        # Define the expected JSON output
        expected_json = {
            "data": {
                "string": "Hello",
                "integer": "42",
                "float": "3.14",
                "boolean": "true",
                "null": None
            }
        }

        # Call the conversion function with the file paths
        xml_to_json.convert_xml_to_json(self.input_xml_path,
                                        self.output_json_path)

        # Read the generated JSON file
        actual_json = self._read_json_file()

        # Compare the actual JSON with the expected JSON
        self.assertEqual(actual_json, expected_json)


if __name__ == "__main__":
    unittest.main()
