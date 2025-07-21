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
"""Tests for the ReportGenerator."""

import unittest
import os
import tempfile
import pandas as pd
import json

from tools.import_validation.report_generator import ReportGenerator
from tools.import_validation.result import ValidationResult, ValidationStatus


class TestReportGenerator(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.output_path = os.path.join(self.test_dir.name, 'output.csv')

    def tearDown(self):
        self.test_dir.cleanup()

    def test_generate_detailed_report(self):
        # 1. Create some sample validation results
        results = [
            ValidationResult(ValidationStatus.PASSED,
                             'Test 1',
                             details={
                                 'rows_processed': 10,
                                 'rows_succeeded': 10,
                                 'rows_failed': 0
                             }),
            ValidationResult(ValidationStatus.FAILED,
                             'Test 2',
                             'Something failed',
                             details={
                                 'rows_processed': 5,
                                 'rows_succeeded': 0,
                                 'rows_failed': 5
                             },
                             validation_params={'threshold': 42})
        ]

        # 2. Generate the report
        report_generator = ReportGenerator(results)
        report_generator.generate_detailed_report(self.output_path)

        # 3. Read the output file and verify its contents
        self.assertTrue(os.path.exists(self.output_path))
        output_df = pd.read_csv(self.output_path)

        self.assertEqual(len(output_df), 2)
        self.assertEqual(output_df.iloc[0]['ValidationName'], 'Test 1')
        self.assertEqual(output_df.iloc[0]['Status'], 'PASSED')
        self.assertEqual(output_df.iloc[1]['ValidationName'], 'Test 2')
        self.assertEqual(output_df.iloc[1]['Status'], 'FAILED')
        self.assertEqual(output_df.iloc[1]['Message'], 'Something failed')

        # Verify the details of the second result
        details = json.loads(output_df.iloc[1]['Details'])
        self.assertEqual(details['rows_processed'], 5)
        self.assertEqual(details['rows_succeeded'], 0)
        self.assertEqual(details['rows_failed'], 5)

        self.assertIn('ValidationParams', output_df.columns)
        self.assertEqual(output_df.iloc[1]['ValidationParams'],
                         '{"threshold": 42}')

    def test_generate_summary_report_placeholder(self):
        report_generator = ReportGenerator([])
        summary = report_generator.generate_summary_report()
        self.assertIn("not yet implemented", summary)


if __name__ == '__main__':
    unittest.main()
