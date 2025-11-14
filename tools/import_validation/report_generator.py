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
"""Module for the ReportGenerator class."""

import csv
import json
from result import ValidationResult


class ReportGenerator:
    """Generates reports from a list of validation results."""

    def __init__(self, results: list[ValidationResult]):
        self.results = results

    def generate_report(self, output_path: str):
        """Writes the validation results to a file.

    The output format is determined by the file extension of the output_path.
    Supported formats are .csv and .json.

    Args:
        output_path: The path to the output file.
    """
        if not self.results:
            return

        if output_path.endswith('.csv'):
            self._generate_csv_report(output_path)
        elif output_path.endswith('.json'):
            self._generate_json_report(output_path)
        else:
            raise ValueError(
                f"Unsupported file format for output path: {output_path}. "
                "Supported formats are .csv and .json.")

    def _generate_csv_report(self, output_path: str):
        """Writes the detailed validation results to a CSV file.

    Args:
        output_path: The path to the output CSV file.
    """
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "ValidationName", "Status", "Message", "Details",
                "ValidationParams"
            ])
            for result in self.results:
                details_str = json.dumps(result.details,
                                         default=str) if result.details else ''
                params_str = json.dumps(
                    result.validation_params,
                    default=str) if result.validation_params else ''
                writer.writerow([
                    result.name,
                    result.status.value,
                    result.message,
                    details_str,
                    params_str,
                ])

    def _generate_json_report(self, output_path: str):
        """Writes the detailed validation results to a JSON file.

    Args:
        output_path: The path to the output JSON file.
    """
        report_data = []
        for result in self.results:
            report_data.append({
                'validation_name': result.name,
                'status': result.status.value,
                'message': result.message,
                'details': result.details,
                'validation_params': result.validation_params,
            })

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)

    def generate_summary_report(self) -> str:
        """Generates a human-readable summary report string."""
        # Placeholder for summary report generation
        return "Summary report not yet implemented."
