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
"""Unit tests for the Import Validation framework."""

import unittest
import os
import sys
import json
import tempfile
import subprocess
import pandas as pd


class ImportValidationTest(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.test_dir.name, 'config.json')
        self.stats_path = os.path.join(self.test_dir.name, 'stats.csv')
        self.differ_path = os.path.join(self.test_dir.name, 'differ.csv')
        self.output_path = os.path.join(self.test_dir.name, 'output.csv')

        # Find the project root using the canonical git command
        result = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                                capture_output=True,
                                text=True,
                                check=True)
        self.project_root = result.stdout.strip()

        # Create an empty differ output file, as it is required
        pd.DataFrame({'DELETED': []}).to_csv(self.differ_path, index=False)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_e2e_successful_run(self):
        """Tests a successful end-to-end run of the script."""
        # 1. Create sample data that should pass validation
        with open(self.config_path, 'w') as f:
            json.dump(
                {
                    "rules": [{
                        "rule_id": "num_places_consistent",
                        "validator": "NUM_PLACES_CONSISTENT",
                        "scope": {
                            "data_source": "stats"
                        },
                        "params": {}
                    }]
                }, f)
        pd.DataFrame({
            'StatVar': ['sv1', 'sv2'],
            'NumPlaces': [10, 10]  # Consistent
        }).to_csv(self.stats_path, index=False)

        # 2. Run the script
        result = subprocess.run([
            'python3', '-m', 'tools.import_validation.runner',
            f'--validation_config={self.config_path}',
            f'--stats_summary={self.stats_path}',
            f'--differ_output={self.differ_path}',
            f'--validation_output={self.output_path}'
        ],
                                capture_output=True,
                                text=True,
                                cwd=self.project_root)

        # 3. Assert success
        self.assertEqual(result.returncode, 0,
                         f"Script failed with stderr: {result.stderr}")
        output_df = pd.read_csv(self.output_path)
        self.assertEqual(len(output_df), 1)
        self.assertEqual(output_df.iloc[0]['Status'], 'PASSED')

    def test_e2e_failed_run(self):
        """Tests a failed end-to-end run of the script."""
        # 1. Create sample data that should fail validation
        with open(self.config_path, 'w') as f:
            json.dump(
                {
                    "rules": [{
                        "rule_id": "num_places_consistent",
                        "validator": "NUM_PLACES_CONSISTENT",
                        "scope": {
                            "data_source": "stats"
                        },
                        "params": {}
                    }]
                }, f)
        pd.DataFrame({
            'StatVar': ['sv1', 'sv2'],
            'NumPlaces': [10, 20]  # Inconsistent
        }).to_csv(self.stats_path, index=False)

        # 2. Run the script
        result = subprocess.run([
            'python3', '-m', 'tools.import_validation.runner',
            f'--validation_config={self.config_path}',
            f'--stats_summary={self.stats_path}',
            f'--differ_output={self.differ_path}',
            f'--validation_output={self.output_path}'
        ],
                                capture_output=True,
                                text=True,
                                cwd=self.project_root)

        # 3. Assert failure
        self.assertEqual(result.returncode, 1,
                         "Script should have failed but didn't")
        self.assertIn(
            "The number of places is not consistent across all StatVars.",
            result.stderr)

    def test_e2e_missing_flag_fails(self):
        """Tests that the script fails when a required flag is missing."""
        # Run the script without the required --stats_summary flag
        result = subprocess.run([
            'python3', '-m', 'tools.import_validation.runner',
            f'--validation_config={self.config_path}',
            f'--differ_output={self.differ_path}',
            f'--validation_output={self.output_path}'
        ],
                                capture_output=True,
                                text=True,
                                cwd=self.project_root)

        # Assert that the script exits with an error
        self.assertNotEqual(result.returncode, 0,
                            "Script should have failed due to missing flag")
        self.assertIn("Flag --stats_summary must have a value other than None",
                      result.stderr)

    def test_e2e_variables_filtering(self):
        """Tests that the runner correctly applies the 'variables' filter."""
        # 1. Create a config that filters for a specific StatVar
        with open(self.config_path, 'w') as f:
            json.dump(
                {
                    "rules": [{
                        "rule_id": "num_places_consistent_filtered",
                        "validator": "NUM_PLACES_CONSISTENT",
                        "scope": {
                            "data_source": "stats",
                            "variables": {
                                "dcids": ["sv1", "sv2"]
                            }
                        },
                        "params": {}
                    }]
                }, f)
        # 2. Create data where the filtered StatVars pass, but the unfiltered
        #    ones would fail.
        pd.DataFrame({
            'StatVar': ['sv1', 'sv2', 'sv3', 'sv4'],
            'NumPlaces': [10, 10, 20, 30]  # Consistent for sv1/sv2
        }).to_csv(self.stats_path, index=False)

        # 3. Run the script
        result = subprocess.run([
            'python3', '-m', 'tools.import_validation.runner',
            f'--validation_config={self.config_path}',
            f'--stats_summary={self.stats_path}',
            f'--differ_output={self.differ_path}',
            f'--validation_output={self.output_path}'
        ],
                                capture_output=True,
                                text=True,
                                cwd=self.project_root)

        # 4. Assert success, because the failing StatVars were filtered out
        self.assertEqual(result.returncode, 0,
                         f"Script failed with stderr: {result.stderr}")
        output_df = pd.read_csv(self.output_path)
        self.assertEqual(len(output_df), 1)
        self.assertEqual(output_df.iloc[0]['Status'], 'PASSED')

    def test_e2e_sql_validator_fails(self):
        """Tests that the SQL_VALIDATOR works in an end-to-end run."""
        # 1. Create a config using the SQL_VALIDATOR
        with open(self.config_path, 'w') as f:
            json.dump(
                {
                    "rules": [{
                        "rule_id": "sql_max_value_check",
                        "validator": "SQL_VALIDATOR",
                        "params": {
                            "query": "SELECT StatVar, MaxValue FROM stats",
                            "condition": "MaxValue <= 100"
                        }
                    }]
                }, f)
        # 2. Create data that will fail the SQL condition
        pd.DataFrame({
            'StatVar': ['sv1', 'sv2'],
            'MaxValue': [99, 101]
        }).to_csv(self.stats_path, index=False)

        # 3. Run the script
        result = subprocess.run([
            'python3', '-m', 'tools.import_validation.runner',
            f'--validation_config={self.config_path}',
            f'--stats_summary={self.stats_path}',
            f'--differ_output={self.differ_path}',
            f'--validation_output={self.output_path}'
        ],
                                capture_output=True,
                                text=True,
                                cwd=self.project_root)

        # 4. Assert failure and check the output
        self.assertEqual(result.returncode, 1,
                         "Script should have failed but didn't")
        output_df = pd.read_csv(self.output_path)
        self.assertEqual(len(output_df), 1)
        self.assertEqual(output_df.iloc[0]['Status'], 'FAILED')
        self.assertIn('sv2', output_df.iloc[0]['Details'])


if __name__ == '__main__':
    unittest.main()
