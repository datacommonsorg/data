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
"""Temporary test file to reproduce and fix bugs."""

import unittest
import os
import sys
import json
import tempfile
import subprocess
import pandas as pd


class BugReproductionTest(unittest.TestCase):

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

        # Create a dummy stats file, as it is often required
        pd.DataFrame({'StatVar': ['sv1'], 'Value': [1]}).to_csv(self.stats_path,
                                                               index=False)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_empty_differ_file_runs_validation(self):
        """
    Tests that a differ file with only headers (empty DataFrame) still runs
    the validation and fails it if the condition is not met.
    """
        # 1. Create a config that checks for deleted count
        with open(self.config_path, 'w') as f:
            json.dump(
                {
                    "rules": [{
                        "rule_id": "check_deleted_count",
                        "validator": "DELETED_COUNT",
                        "scope": {
                            "data_source": "differ"
                        },
                        "params": {
                            "threshold": -1
                        } # Fail if deleted count is not > -1
                    }]
                }, f)
        # 2. Create a differ file with only headers
        pd.DataFrame({
            'DELETED': []
        }).to_csv(self.differ_path, index=False)

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

        # 4. Assert that the validation PASSED, because the check ran and 0 > -1
        self.assertEqual(
            result.returncode, 0,
            "Script should have passed because the check should have run and passed."
        )
        output_df = pd.read_csv(self.output_path)
        self.assertEqual(len(output_df), 1)
        self.assertEqual(output_df.iloc[0]['Status'], 'PASSED')

    def test_missing_differ_file_does_not_throw_exception(self):
        """
    Tests that a missing differ file does not cause the runner to throw an
    exception when a differ-based rule is present.
    """
        # 1. Create a config that requires the 'differ' data source
        with open(self.config_path, 'w') as f:
            json.dump(
                {
                    "rules": [{
                        "rule_id": "check_deleted_count",
                        "validator": "DELETED_COUNT",
                        "scope": {
                            "data_source": "differ"
                        },
                        "params": {
                            "threshold": 10
                        }
                    }]
                }, f)

        # 2. Run the script without the --differ_output flag
        result = subprocess.run([
            'python3', '-m', 'tools.import_validation.runner',
            f'--validation_config={self.config_path}',
            f'--stats_summary={self.stats_path}',
            f'--validation_output={self.output_path}'
        ],
                                capture_output=True,
                                text=True,
                                cwd=self.project_root)

        # 3. Assert that the script does not exit with a fatal error
        # It should pass because an empty (missing) differ file has 0 deleted
        # points, which is within the threshold of 10.
        self.assertEqual(
            result.returncode, 0,
            f"Script should not have thrown an exception. Stderr: {result.stderr}"
        )
        output_df = pd.read_csv(self.output_path)
        self.assertEqual(len(output_df), 1)
        self.assertEqual(output_df.iloc[0]['Status'], 'PASSED')


if __name__ == '__main__':
    unittest.main()
