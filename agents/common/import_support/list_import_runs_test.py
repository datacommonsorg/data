# Copyright 2026 Google LLC
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
"""Tests for bounded Workflow execution listing."""

from datetime import datetime
from datetime import timezone
from types import SimpleNamespace
import unittest

from google.cloud.workflows import executions_v1

from agents.common.import_support.list_import_runs import list_workflow_execution_records
from agents.common.import_support.list_import_runs import select_runs


class _ExecutionClient:

    def __init__(self, executions):
        self._executions = executions
        self.request = None

    def list_executions(self, request):
        self.request = request
        page = SimpleNamespace(executions=self._executions)
        return SimpleNamespace(pages=[page])


class ListImportRunsTest(unittest.TestCase):

    def test_lists_full_view_and_filters_exact_identity(self):
        execution = SimpleNamespace(
            name='projects/p/locations/l/workflows/w/executions/one',
            create_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end_time=datetime(2026, 1, 1, 1, tzinfo=timezone.utc),
            duration='',
            state=executions_v1.Execution.State.SUCCEEDED,
            argument='{"importName":"scripts/a:Import"}',
            result='{"jobId":"batch-job"}',
            error=None,
            status=None,
            workflow_revision_id='revision-1',
            labels={},
        )
        client = _ExecutionClient([execution])

        listed = list_workflow_execution_records(
            'projects/p/locations/l/workflows/w',
            datetime(2025, 12, 1, tzinfo=timezone.utc),
            datetime(2026, 2, 1, tzinfo=timezone.utc),
            client=client)
        filtered = select_runs(listed, 'scripts/a:Import')

        self.assertEqual(executions_v1.ExecutionView.FULL, client.request.view)
        self.assertEqual('one', filtered['runs'][0]['id'])
        self.assertEqual('batch-job', filtered['runs'][0]['batch_job_id'])
        self.assertEqual('scripts/a:Import', filtered['runs'][0]['import_name'])
        self.assertNotIn('argument', filtered['runs'][0])
        self.assertEqual([], select_runs(listed, 'scripts/a:Other')['runs'])

    def test_without_import_filter_returns_bounded_fleet_runs(self):
        listed = {
            'executions': [{
                'id': 'one',
                'import_name': 'scripts/a:Import'
            }, {
                'id': 'two',
                'import_name': 'scripts/b:Import'
            }],
            'scan_truncated': False,
        }

        selected = select_runs(listed, run_limit=1)

        self.assertIsNone(selected['absolute_import_name'])
        self.assertEqual([{
            'id': 'one',
            'import_name': 'scripts/a:Import'
        }], selected['runs'])
        self.assertTrue(selected['result_truncated'])


if __name__ == '__main__':
    unittest.main()
