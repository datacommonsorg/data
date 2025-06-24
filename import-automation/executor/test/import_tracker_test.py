
# Copyright 2023 Google LLC
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
"""
Tests for import_tracker.py.
"""

import unittest

from app.import_tracker import ImportTracker, ImportStatus

class ImportTrackerTest(unittest.TestCase):
    """
    Tests for the ImportTracker class.
    """

    def test_to_json(self):
        """
        Tests that the to_json method returns a valid JSON string.
        """
        tracker = ImportTracker(import_name='test_import',
                                status=ImportStatus.STARTED,
                                message='Import started.')
        json_string = tracker.to_json()
        self.assertEqual(
            '{"import_name": "test_import", "status": 1, "message": "Import started."}',
            json_string)

    def test_from_json(self):
        """
        Tests that the from_json method returns a valid ImportTracker object.
        """
        json_string = '{"import_name": "test_import", "status": 1, "message": "Import started."}'
        tracker = ImportTracker.from_json(json_string)
        self.assertEqual('test_import', tracker.import_name)
        self.assertEqual(ImportStatus.STARTED, tracker.status)
        self.assertEqual('Import started.', tracker.message)
