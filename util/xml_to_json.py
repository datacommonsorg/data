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
from absl import app
from absl import flags
import xmltodict
from absl import logging
import sys


def convert_xml_to_json(input_xml_path: str, output_json_path: str) -> None:
    """Converts an XML file to a JSON file.

    Args:
        input_xml_path: The path to the input XML file.
        output_json_path: The path to the output JSON file.
    """
    try:
        with open(input_xml_path, 'r') as xml_file:
            xml_data = xml_file.read()

        if xml_data:
            data_dict = xmltodict.parse(xml_data)
            json_data = json.dumps(data_dict, indent=4)
            with open(output_json_path, 'w') as json_file:
                json_file.write(json_data)
        else:
            with open(output_json_path, 'w') as json_file:
                json_file.write('{}')
    except FileNotFoundError:
        logging.fatal(f"Error: Input XML file not found at '{input_xml_path}'")
    except Exception as e:
        logging.fatal(f"An error occurred during conversion: {e}")


"""calling this script from a bash script where we are passing tese 2 parameter"""
input_xml_file = sys.argv[1]
output_json_file = sys.argv[2]
convert_xml_to_json(input_xml_file, sys.argv[2])
