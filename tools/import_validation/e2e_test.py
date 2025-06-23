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
"""End-to-end tests for the Import Validation framework."""

import unittest
import os
import json
import tempfile
import subprocess
import pandas as pd


class TestImportValidationE2E(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.test_dir.name, 'config.json')
        self.stats_path = os.path.join(self.test_dir.name, 'stats.csv')
        self.differ_path = os.path.join(self.test_dir.name, 'differ.csv')
        self.output_path = os.path.join(self.test_dir.name, 'output.csv')

        # Find the project root by looking for the .git directory
        current_path = os.path.abspath(os.path.dirname(__file__))
        while not os.path.isdir(os.path.join(current_path, '.git')):
            parent_path = os.path.dirname(current_path)
            if parent_path == current_path:  # Reached the filesystem root
                raise FileNotFoundError(
                    "Could not find project root (.git directory).")
            current_path = parent_path
        self.project_root = current_path

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
        self.assertIn("Found 2 unique place counts where 1 was expected.",
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


if __name__ == '__main__':
    unittest.main()
