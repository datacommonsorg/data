# Copyright 2020 Google LLC
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
Tests for progress_log.py.
"""

import unittest
from unittest import mock

from test import utils
from app.resource import system_run_list
from app.resource import progress_log
from app.resource import progress_log_list
from app.resource import import_attempt_list
from app.model import system_run_model
from app.model import import_attempt_model
from app.model import progress_log_model

_ATTEMPT = import_attempt_model.ImportAttempt
_RUN = system_run_model.SystemRun
_LOG = progress_log_model.ProgressLog


def setUpModule():
    utils.EMULATOR.start_emulator()


class ProgressLogListTest(unittest.TestCase):
    """Tests for ProgressLogList."""

    @mock.patch('app.utils.create_datastore_client',
                utils.create_test_datastore_client)
    @mock.patch('app.service.log_message_manager.LogMessageManager',
                utils.LogMessageManagerMock)
    def setUp(self):
        """Injects several system runs, import attempts, and progress logs
        to the database before every test.
        """
        client = utils.create_test_datastore_client()
        manager = utils.LogMessageManagerMock()
        self.by_log_id = progress_log.ProgressLogByID(client, manager)
        self.by_run_id = progress_log.ProgressLogByRunID(client, manager)
        self.by_attempt_id = progress_log.ProgressLogByAttemptID(
            client, manager)
        log_list_resource = progress_log_list.ProgressLogList(client, manager)
        run_list_resource = system_run_list.SystemRunList(client)
        attempt_list_resource = import_attempt_list.ImportAttemptList(client)

        runs = [{
            _RUN.branch_name: 'test-branch',
            _RUN.pr_number: 0
        }, {
            _RUN.branch_name: 'prod-branch',
            _RUN.pr_number: 1
        }]
        self.runs = utils.ingest_system_runs(run_list_resource, runs)

        # Linked to the first run
        attempts = [
            {
                _ATTEMPT.import_name: 'cpi-u'
            },
            {
                _ATTEMPT.import_name: 'cpi-w'
            },
        ]
        self.attempts = utils.ingest_import_attempts(run_list_resource,
                                                     attempt_list_resource,
                                                     attempts,
                                                     system_run=self.runs[0])

        self.logs = [
            # Linked to the first attempt
            {
                _LOG.level: 'info',
                _LOG.message: 'first',
                _LOG.attempt_id: self.attempts[0][_ATTEMPT.attempt_id]
            },
            # Linked to the first attempt and first run
            {
                _LOG.level: 'critical',
                _LOG.message: 'second',
                _LOG.attempt_id: self.attempts[0][_ATTEMPT.attempt_id],
                _LOG.run_id: self.runs[0][_RUN.run_id]
            },
            # Linked to the first run
            {
                _LOG.level: 'debug',
                _LOG.message: 'third',
                _LOG.run_id: self.runs[0][_RUN.run_id]
            }
        ]
        with mock.patch(utils.PARSE_ARGS) as parse_args:
            parse_args.side_effect = self.logs
            for i, _ in enumerate(self.logs):
                self.logs[i] = log_list_resource.post()

    def test_progress_log_by_id(self):
        """Tests querying a progress log by its log_id."""
        for log in self.logs:
            retrieved = self.by_log_id.get(log[_LOG.log_id])
            self.assertEqual(log[_LOG.log_id], retrieved[_LOG.log_id])
            self.assertNotEqual(log[_LOG.log_id], retrieved[_LOG.message])

    def test_progress_log_by_run_id(self):
        """Tests querying the progress logs of a system run by its run_id."""
        expected = [self.logs[1], self.logs[2]]
        retrieved = self.by_run_id.get(self.runs[0][_RUN.run_id])[_RUN.logs]
        self.assertEqual(len(expected), len(retrieved))
        for i, log in enumerate(expected):
            self.assertEqual(log[_LOG.log_id], retrieved[i][_LOG.log_id])

    def test_progress_log_by_attempt_id(self):
        """Tests querying the progress logs of an import attempt by
        its attempt_id."""
        expected = [self.logs[0], self.logs[1]]
        retrieved = self.by_attempt_id.get(
            self.attempts[0][_ATTEMPT.attempt_id])[_ATTEMPT.logs]
        self.assertEqual(len(expected), len(retrieved))
        for i, log in enumerate(expected):
            self.assertEqual(log[_LOG.log_id], retrieved[i][_LOG.log_id])
