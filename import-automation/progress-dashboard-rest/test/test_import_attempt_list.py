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
Tests for import_attempt_list.py.
"""

import unittest
from unittest import mock

from test import utils
from app.resource import import_attempt_list
from app.resource import system_run_list
from app.model import system_run_model
from app.model import import_attempt_model

_ATTEMPT = import_attempt_model.ImportAttemptModel
_RUN = system_run_model.SystemRunModel


def setUpModule():
    utils.EMULATOR.start_emulator()


class ImportAttemptListTest(unittest.TestCase):
    """Tests for ImportAttemptList."""

    @mock.patch('app.utils.create_datastore_client',
                utils.create_test_datastore_client)
    def setUp(self):
        """Injects a system run and several import attempts to the database."""
        self.resource = import_attempt_list.ImportAttemptList()

        run_list_resource = system_run_list.SystemRunList()
        run_list_resource.database.client = self.resource.client

        attempts = [
            {_ATTEMPT.import_name: 'cpi-u'},
            {_ATTEMPT.import_name: 'cpi-w'},
            {_ATTEMPT.import_name: 'cpi-w'},
            {_ATTEMPT.import_name: 'c-cpi-u'}
        ]
        self.attempts = utils.ingest_import_attempts(
            run_list_resource, self.resource, attempts)

    @mock.patch(utils.PARSE_ARGS, lambda self: {_ATTEMPT.import_name: 'ppi'})
    def test_post_run_id_not_set(self):
        """Tests that POSTing an import attempt without run_id
        returns FORBIDDEN."""
        _, code = self.resource.post()
        self.assertEqual(403, code)

    @mock.patch(utils.PARSE_ARGS, lambda self: {_ATTEMPT.run_id: 'not-exist'})
    def test_post_run_id_not_exist(self):
        """Tests that POSTing an import attempt with a run_id that
        does not exist returns NOT FOUND."""
        _, code = self.resource.post()
        self.assertEqual(404, code)

    @mock.patch(utils.PARSE_ARGS)
    def test_post_logs_not_saved(self, parse_args):
        """Tests that POSTing an import attempt with logs set does not actually
        save the logs."""
        parse_args.return_value = {
            _ATTEMPT.run_id: self.attempts[0][_ATTEMPT.run_id],
            _ATTEMPT.logs: ['log-id-0']
        }
        attempt = self.resource.post()
        self.assertIn(_ATTEMPT.attempt_id, attempt)
        self.assertEqual([], attempt[_ATTEMPT.logs])

    @mock.patch(utils.PARSE_ARGS)
    def test_post_attempt_id_not_saved(self, parse_args):
        """Tests that POSTing an import attempt with attempt_id set still
        generates a new attempt_id."""
        to_post = self.attempts[0]
        parse_args.return_value = dict(to_post)
        posted = self.resource.post()
        self.assertNotEqual(to_post[_ATTEMPT.attempt_id],
                            posted[_ATTEMPT.attempt_id])
