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
Tests for progress_log_list.py.
"""

import unittest
from unittest import mock

from test import utils
from app.resource import system_run_list
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
    @mock.patch('app.service.log_message_manager.LogMessageManager',
                utils.LogMessageManagerMock)
    def setUp(self):
        """Injects several system runs and import attempts to the database
        before every test. New progress logs will be linked to these entities.
        """
        client = utils.create_test_datastore_client()
        self.resource = progress_log_list.ProgressLogList(client)
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

    @mock.patch(utils.PARSE_ARGS)
    def test_level_not_allowed(self, parse_args):
        """Tests that POSTing a progress log with an undefined log level returns
        FORBIDDEN."""
        parse_args.return_value = {
            _LOG.level: 'not-exist',
            _LOG.message: 'hello',
            _LOG.run_id: self.runs[0][_RUN.run_id]
        }
        message, code = self.resource.post()
        self.assertEqual(403, code)
        self.assertIn('level', message)

    @mock.patch(utils.PARSE_ARGS)
    def test_time_logged_not_iso_utc(self, parse_args):
        """Tests that POSTing a progress log with time logged not following
        ISO format with UTC timezone returns FORBIDDEN."""
        parse_args.return_value = {
            _LOG.level: 'info',
            _LOG.message: 'hello',
            _LOG.time_logged: '02/14/2104 14:30',
            _LOG.run_id: self.runs[0][_RUN.run_id]
        }
        message, code = self.resource.post()
        self.assertEqual(403, code)
        self.assertIn('time_logged', message)

    @mock.patch(utils.PARSE_ARGS, lambda self: {
        _LOG.level: 'info',
        _LOG.message: 'hello'
    })
    def test_run_id_not_exist(self):
        """Tests that POSTing a progress log without run_id set
        returns FORBIDDEN."""
        message, code = self.resource.post()
        self.assertEqual(403, code)
        self.assertIn('run_id', message)

    @mock.patch(utils.PARSE_ARGS)
    def test_attempt_not_linked_to_run(self, parse_args):
        """Tests that POSTing a progress log with unrelated attempt_id and
        run_id returns FORBIDDEN. That is, the import attempt specified by
        attempt_id is not executed by the system run specified by run_id."""
        parse_args.return_value = {
            _LOG.level: 'info',
            _LOG.message: 'hello',
            _LOG.run_id: self.runs[1][_RUN.run_id],
            _LOG.attempt_id: self.attempts[0][_ATTEMPT.attempt_id]
        }
        message, code = self.resource.post()
        self.assertEqual(409, code)
        self.assertIn('run_id', message)
        self.assertIn('attempt_id', message)

    @mock.patch(utils.PARSE_ARGS)
    def test_attempt_id_not_exist(self, parse_args):
        """Tests that POSTing a progress log with an attempt_id that does
        not exist returns NOT FOUND."""
        parse_args.return_value = {
            _LOG.level: 'info',
            _LOG.message: 'hello',
            _LOG.attempt_id: 'not-exist',
            _LOG.run_id: self.runs[0][_RUN.run_id]
        }
        message, code = self.resource.post()
        self.assertEqual(404, code)
        self.assertIn(_LOG.attempt_id, message)

    @mock.patch(utils.PARSE_ARGS)
    def test_run_id_not_exist(self, parse_args):
        """Tests that POSTing a progress log with a run_id that does
        not exist returns NOT FOUND."""
        parse_args.return_value = {
            _LOG.level: 'info',
            _LOG.message: 'hello',
            _LOG.run_id: 'not-exist'
        }
        message, code = self.resource.post()
        self.assertEqual(404, code)
        self.assertIn(_LOG.run_id, message)

    @mock.patch(utils.PARSE_ARGS)
    def test_post_attempt_id(self, parse_args):
        """Tests POSTing a progress log linked to an import attempt."""
        attempt_id = self.attempts[0][_ATTEMPT.attempt_id]
        parse_args.return_value = {
            _LOG.level: 'info',
            _LOG.message: 'hello',
            _LOG.attempt_id: attempt_id,
            _LOG.run_id: self.runs[0][_RUN.run_id]
        }
        posted = self.resource.post()
        self.assertEqual('info', posted[_LOG.level])
        self.assertEqual(posted[_LOG.log_id], posted[_LOG.message])
        self.assertEqual(posted[_LOG.attempt_id], attempt_id)
        self.assertIn(_LOG.time_logged, posted)

    @mock.patch(utils.PARSE_ARGS)
    def test_post_run_id(self, parse_args):
        """Tests POSTing a progress log linked to a system run."""
        run_id = self.runs[0][_RUN.run_id]
        parse_args.return_value = {
            _LOG.level: 'info',
            _LOG.message: 'hello',
            _LOG.run_id: run_id
        }
        posted = self.resource.post()
        self.assertEqual('info', posted[_LOG.level])
        self.assertEqual(posted[_LOG.log_id], posted[_LOG.message])
        self.assertEqual(posted[_LOG.run_id], run_id)
        self.assertIn(_LOG.time_logged, posted)

    @mock.patch(utils.PARSE_ARGS)
    def test_post_attempt_and_run_id(self, parse_args):
        """Tests POSTing a progress log linked to both an import attempt and
        a system run."""
        run_id = self.runs[0][_RUN.run_id]
        for attempt in self.attempts:
            attempt_id = attempt[_ATTEMPT.attempt_id]
            parse_args.return_value = {
                _LOG.level: 'info',
                _LOG.message: 'hello',
                _LOG.run_id: run_id,
                _ATTEMPT.attempt_id: attempt_id
            }
            posted = self.resource.post()
            self.assertEqual('info', posted[_LOG.level])
            self.assertEqual(posted[_LOG.log_id], posted[_LOG.message])
            self.assertEqual(posted[_LOG.run_id], run_id)
            self.assertEqual(posted[_LOG.attempt_id], attempt_id)
            self.assertIn(_LOG.time_logged, posted)
