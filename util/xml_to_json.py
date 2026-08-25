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
import sys
from absl import app
from absl import logging
import xmltodict


def convert_xml_to_json(input_xml_path: str, output_json_path: str) -> None:
    """Converts an XML file to a JSON file.

    Args:
        input_xml_path: The path to the input XML file.
        output_json_path: The path to the output JSON file.

    Raises:
        FileNotFoundError: If the input XML file is not found.
        Exception: If an error occurs during XML parsing or file writing.
    """
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


def main(argv: list[str]) -> None:
    """Entry point for CLI execution."""
    if len(argv) < 3:
        logging.fatal(
            "Usage: python xml_to_json.py <input_xml_file> <output_json_file>")
        sys.exit(1)
    input_xml_file = argv[1]
    output_json_file = argv[2]
    logging.info(
        f"Started with convert_xml_to_json with xml path {input_xml_file} and output path {output_json_file}"
    )
    convert_xml_to_json(input_xml_file, output_json_file)


if __name__ == "__main__":
    app.run(main)
