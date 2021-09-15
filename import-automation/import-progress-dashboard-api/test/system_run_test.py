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

_MODEL = system_run_model.SystemRun


def setUpModule():
    utils.EMULATOR.start_emulator()


class SystemRunByIDTest(unittest.TestCase):
    """Tests for SystemRunByID."""
    def setUp(self):
        """Creates the endpoints before every test."""
        client = utils.create_test_datastore_client()
        # Used for querying system runs by run_id
        self.resource = system_run.SystemRunByID(client)
        # Used for creating system runs
        list_resource = system_run_list.SystemRunList(client)
        runs = [{}, {_MODEL.commit_sha: 'commit-sha'}]
        self.runs = utils.ingest_system_runs(list_resource, runs)

    def test_get(self):
        """Tests that GET returns the correct system run."""
        for run in self.runs:
            self.assertEqual(run, self.resource.get(run[_MODEL.run_id]))

    def test_get_not_exist(self):
        """Tests that GET returns NOT FOUND if the run_id does not exist."""
        _, err = self.resource.get('does-not-exist')
        self.assertEqual(404, err)

    @mock.patch(utils.PARSE_ARGS, lambda self: {_MODEL.pr_number: 1})
    def test_patch_creates_field(self):
        """Tests that PATCHing a field that does not exist creates the field."""
        run_id = self.runs[0][_MODEL.run_id]
        self.resource.patch(run_id)
        self.assertEqual(1, self.resource.get(run_id)[_MODEL.pr_number])

    @mock.patch(utils.PARSE_ARGS)
    def test_patch(self, parse_args):
        """Tests that PATCHing a field succeeds."""
        parse_args.side_effect = [
            {
                _MODEL.commit_sha: 'patched'
            },
            {
                _MODEL.commit_sha: 'commit_sha'
            },
        ]
        run_id = self.runs[1][_MODEL.run_id]
        self.resource.patch(run_id)
        patched = self.resource.get(run_id)
        self.assertEqual('patched', patched[_MODEL.commit_sha])
        self.resource.patch(run_id)
        patched = self.resource.get(run_id)
        self.assertEqual('commit_sha', patched[_MODEL.commit_sha])

    @mock.patch(utils.PARSE_ARGS)
    def test_patch_run_id_not_allowed(self, parse_args):
        """Tests that patching run_id and import_attempts fails and
        returns FORBIDDEN."""
        parse_args.side_effect = [{
            'run_id': 'not-allowed'
        }, {
            'import_attempts': 'not-allowed'
        }]
        run_id = self.runs[0][_MODEL.run_id]
        _, err = self.resource.patch(run_id)
        self.assertEqual(403, err)
        _, err = self.resource.patch(run_id)
        self.assertEqual(403, err)
