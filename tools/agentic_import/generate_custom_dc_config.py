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

import csv
import os
from typing import Dict, List

import jinja2
from absl import app
from absl import flags
from absl import logging

FLAGS = flags.FLAGS

flags.DEFINE_string('input_csv', None, 'Path to input CSV file (required)')
flags.mark_flag_as_required('input_csv')

flags.DEFINE_string('output_config', None,
                    'Path to output config.json file (required)')
flags.mark_flag_as_required('output_config')


class ConfigGenerator:
    """Generates Data Commons custom import config from CSV output."""

    # Path to the config template relative to this script
    TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'templates',
                                 'custom_dc_data_config.j2')

    # Required columns in the CSV (StatVarObservation mandatory properties)
    REQUIRED_COLUMNS = {
        'observationAbout',  # place DCID
        'observationDate',  # time period
        'variableMeasured',  # StatVar DCID
        'value'  # measured value
    }

    # Optional columns in the CSV (StatVarObservation optional properties)
    OPTIONAL_COLUMNS = {
        'observationPeriod',  # P1Y=yearly, P1M=monthly
        'unit',  # Percent, USD
        'scalingFactor',  # 100 for percentages, 1000000 for millions
        'measurementMethod'  # CensusACS5yrSurvey, EstimateMethod
    }

    # Mapping from CSV column names to Data Commons standard names
    CSV_TO_DC_MAPPINGS = {
        'variableMeasured': 'variable',
        'observationAbout': 'entity',
        'observationDate': 'date',
        'value': 'value',
        'unit': 'unit',
        'scalingFactor': 'scalingFactor',
        'measurementMethod': 'measurementMethod',
        'observationPeriod': 'observationPeriod'
    }

    def __init__(self, input_csv_path: str, output_config_path: str):
        self._input_csv_path = os.path.abspath(input_csv_path)
        self._output_config_path = os.path.abspath(output_config_path)

    def validate_input_file(self) -> None:
        """Validates that input CSV file exists and is readable."""
        if not os.path.exists(self._input_csv_path):
            raise FileNotFoundError(
                f"Input CSV file not found: {self._input_csv_path}")

        if not os.path.isfile(self._input_csv_path):
            raise ValueError(
                f"Input path is not a file: {self._input_csv_path}")

        if not os.access(self._input_csv_path, os.R_OK):
            raise PermissionError(
                f"Cannot read input CSV file: {self._input_csv_path}")

    def validate_output_path(self) -> None:
        """Validates that output directory exists and is writable."""
        output_dir = os.path.dirname(self._output_config_path)

        if output_dir and not os.path.exists(output_dir):
            raise FileNotFoundError(
                f"Output directory does not exist: {output_dir}")

        if output_dir and not os.access(output_dir, os.W_OK):
            raise PermissionError(
                f"Cannot write to output directory: {output_dir}")

    def read_csv_headers(self) -> List[str]:
        """Reads and returns the CSV headers."""
        try:
            with open(self._input_csv_path, 'r', encoding='utf-8') as file:
                # Read first line to get headers
                first_line = file.readline().strip()
                if not first_line:
                    raise ValueError("CSV file is empty")

                # Use csv.reader to properly handle quoted headers
                csv_reader = csv.reader([first_line])
                headers = next(csv_reader)

                if not headers:
                    raise ValueError("CSV file has no headers")

                return [header.strip() for header in headers]

        except Exception as e:
            raise ValueError("Error reading CSV headers") from e

    def validate_required_columns(self, headers: List[str]) -> None:
        """Validates that all required columns are present in the CSV."""
        header_set = set(headers)
        missing_required = self.REQUIRED_COLUMNS - header_set

        if missing_required:
            raise ValueError(
                f"Missing required columns: {sorted(missing_required)}")

        logging.info(
            f"All required columns found: {sorted(self.REQUIRED_COLUMNS)}")

    def build_column_mappings(self, headers: List[str]) -> Dict[str, str]:
        """Builds column mappings for template (DC standard name → CSV column name)."""
        header_set = set(headers)
        column_mappings = {}

        # Add required columns (we know they're present from validation)
        for csv_col in self.REQUIRED_COLUMNS:
            if csv_col in header_set:
                dc_standard_name = self.CSV_TO_DC_MAPPINGS[csv_col]
                column_mappings[dc_standard_name] = csv_col

        # Add optional columns if present
        for csv_col in self.OPTIONAL_COLUMNS:
            if csv_col in header_set:
                dc_standard_name = self.CSV_TO_DC_MAPPINGS[csv_col]
                column_mappings[dc_standard_name] = csv_col
                logging.info(f"Found optional column: {csv_col}")

        # Log unexpected columns (not in our known set)
        all_known_columns = self.REQUIRED_COLUMNS | self.OPTIONAL_COLUMNS
        unexpected_columns = header_set - all_known_columns
        if unexpected_columns:
            logging.warning(
                f"Unexpected columns found (will be ignored): {sorted(unexpected_columns)}"
            )

        return column_mappings

    def generate_config(self, column_mappings: Dict[str, str]) -> str:
        """Generates the complete configuration using the template."""
        # Set up Jinja2 environment with template directory
        template_dir = os.path.dirname(self.TEMPLATE_PATH)
        template_filename = os.path.basename(self.TEMPLATE_PATH)

        env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                                 trim_blocks=True,
                                 lstrip_blocks=True,
                                 comment_start_string='{#',
                                 comment_end_string='#}')

        # Load the template
        template = env.get_template(template_filename)

        # Extract filename from input CSV path (without directory)
        output_filename = os.path.basename(self._input_csv_path)

        # Render template with context
        config_content = template.render(output_filename=output_filename,
                                         column_mappings=column_mappings)

        return config_content

    def write_config_file(self, config_content: str) -> None:
        """Writes the configuration content to the output file."""
        try:
            with open(self._output_config_path, 'w', encoding='utf-8') as file:
                file.write(config_content)

            logging.info(
                f"Configuration written to: {self._output_config_path}")

        except Exception as e:
            raise ValueError("Error writing config file") from e

    def run(self) -> None:
        """Main execution method."""
        logging.info(f"Processing CSV file: {self._input_csv_path}")
        logging.info(f"Output config file: {self._output_config_path}")
        logging.info(f"Using template: {self.TEMPLATE_PATH}")

        # Validate inputs
        self.validate_input_file()
        self.validate_output_path()

        # Read and analyze CSV
        headers = self.read_csv_headers()
        logging.info(f"CSV headers found: {headers}")

        # Validate required columns
        self.validate_required_columns(headers)

        # Create column mappings for template
        column_mappings = self.build_column_mappings(headers)
        logging.info(f"Column mappings for template: {column_mappings}")

        # Generate config using template
        config_content = self.generate_config(column_mappings)
        self.write_config_file(config_content)

        logging.info("Configuration generation completed successfully!")


def main(argv):
    """Main entry point."""
    if len(argv) > 1:
        raise app.UsageError('Too many command-line arguments.')

    generator = ConfigGenerator(FLAGS.input_csv, FLAGS.output_config)
    generator.run()


if __name__ == '__main__':
    app.run(main)
