# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for focused read-only Spanner import queries."""

import unittest
from unittest import mock

from agents.common.import_support.read_import_records import read_import_records


class _Snapshot:

    def __init__(self, rows):
        self._rows = rows
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute_sql(self, sql, params, param_types):
        self.calls.append((sql, params, param_types))
        return self._rows


class _Client:

    def __init__(self, snapshot):
        self._snapshot = snapshot

    def instance(self, instance):
        del instance
        return self

    def database(self, database):
        del database
        return self

    def snapshot(self):
        return self._snapshot


class ReadImportRecordsTest(unittest.TestCase):

    def test_current_uses_one_bound_query_and_disables_metrics(self):
        row = tuple(range(11))
        snapshot = _Snapshot([row])
        client = _Client(snapshot)
        with mock.patch(
                'agents.common.import_support.read_import_records.spanner.Client',
                return_value=client) as client_factory:
            result = read_import_records('project', 'instance', 'database',
                                         'Import', 'current')

        client_factory.assert_called_once_with(project='project',
                                               disable_builtin_metrics=True)
        self.assertEqual(1, len(snapshot.calls))
        self.assertEqual({'import_name': 'Import'}, snapshot.calls[0][1])
        self.assertEqual('ImportStatus',
                         snapshot.calls[0][0].split(' FROM ')[1].split()[0])
        self.assertEqual(1, result['limit'])
        self.assertFalse(result['truncated'])

    def test_history_requests_limit_plus_one_and_reports_truncation(self):
        row = tuple(range(11))
        snapshot = _Snapshot([row, row])

        result = read_import_records('project',
                                     'instance',
                                     'database',
                                     'Import',
                                     'version_history',
                                     limit=1,
                                     client=_Client(snapshot))

        self.assertEqual(1, len(snapshot.calls))
        self.assertEqual(2, snapshot.calls[0][1]['limit'])
        self.assertEqual(1, len(result['rows']))
        self.assertTrue(result['truncated'])


if __name__ == '__main__':
    unittest.main()
