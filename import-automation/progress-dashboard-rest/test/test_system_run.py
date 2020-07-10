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
Tests for system_run.py.
"""

import unittest
from unittest import mock

from app.model import system_run_model
from app.resource import system_run
from app.resource import system_run_list
from test import utils

_MODEL = system_run_model.SystemRunModel


class SystemRunByIDTest(unittest.TestCase):
    """Tests for SystemRunByID."""

    @classmethod
    def setUpClass(cls):
        cls.emulator = utils.start_emulator()

    @classmethod
    def tearDownClass(cls):
        utils.terminate_emulator(cls.emulator)

    @mock.patch('app.utils.create_datastore_client',
                utils.create_test_datastore_client)
    def setUp(self):
        """Creates the endpoints before every test."""
        # Used for querying system runs by run_id
        self.resource = system_run.SystemRunByID()
        # Used for creating system runs
        self.list_resource = system_run_list.SystemRunList()
        self.list_resource.database.client = self.resource.database.client

    @mock.patch(utils.PARSE_ARGS)
    def test_get(self, parse_args):
        """Tests that GET returns the correct system run."""
        runs = [{}, {}, {}]
        parse_args.side_effects = runs
        for i in range(len(runs)):
            runs[i] = self.list_resource.post()
        for run in runs:
            self.assertEqual(run, self.resource.get(run[_MODEL.run_id]))

    def test_get_not_exist(self):
        """Tests that GET returns NOT FOUND if the run_id does not exist."""
        _, err = self.resource.get('does-not-exist')
        self.assertEqual(404, err)

    @mock.patch(utils.PARSE_ARGS,
                side_effect=({'pr_number': 1}, {'pr_number': 9999}))
    def test_patch(self, _):
        """Tests that patching a field succeeds."""
        run = self.list_resource.post()
        run_id = run[_MODEL.run_id]
        self.assertEqual(1, self.resource.get(run_id)[_MODEL.pr_number])
        self.resource.patch(run_id)
        self.assertEqual(9999, self.resource.get(run_id)[_MODEL.pr_number])

    @mock.patch(utils.PARSE_ARGS,
                side_effect=({},
                             {'run_id': 'not-allowed'},
                             {'import_attempts': 'not-allowed'}))
    def test_patch_run_id_not_allowed(self, _):
        """Tests that patching run_id fails and
        returns FORBIDDEN."""
        run = self.list_resource.post()
        run_id = run[_MODEL.run_id]
        _, err = self.resource.patch(run_id)
        self.assertEqual(403, err)
        _, err = self.resource.patch(run_id)
        self.assertEqual(403, err)
