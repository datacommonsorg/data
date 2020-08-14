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
Tests for system_run_list.py.
"""

import unittest
from unittest import mock

from app import main
from app.model import system_run_model
from app.resource import system_run_list
from test import utils

_MODEL = system_run_model.SystemRun
_ENDPOINT = '/system_runs'


def setUpModule():
    utils.EMULATOR.start_emulator()


class SystemRunListTest(unittest.TestCase):
    """Tests for SystemRunList."""

    @mock.patch('app.utils.create_datastore_client',
                utils.create_test_datastore_client)
    def setUp(self):
        """Injects several system runs to the database before every test."""
        self.resource = system_run_list.SystemRunList()
        runs = [{
            _MODEL.repo_name: 'dddd',
            _MODEL.pr_number: 0
        }, {
            _MODEL.repo_name: 'data',
            _MODEL.pr_number: 1
        }, {
            _MODEL.repo_name: 'data',
            _MODEL.pr_number: 3
        }, {
            _MODEL.repo_name: 'aaaa',
            _MODEL.pr_number: 2
        }]
        self.runs = utils.ingest_system_runs(self.resource, runs)

    def test_get_all(self):
        """Tests that empty filter returns all the runs."""
        with main.FLASK_APP.test_request_context(_ENDPOINT, json={}):
            self.assertCountEqual(self.runs, self.resource.get())

    def test_get_by_repo_name(self):
        """Tests that filtering by repo_name returns the correct runs."""
        with main.FLASK_APP.test_request_context(
                _ENDPOINT, json={_MODEL.repo_name: 'data'}):
            self.assertCountEqual([self.runs[1], self.runs[2]],
                                  self.resource.get())

    def test_get_by_repo_name_and_pr_number(self):
        """Tests that filtering by repo_name and pr_number returns
        the correct runs."""
        with main.FLASK_APP.test_request_context(_ENDPOINT,
                                                 json={
                                                     'repo_name': 'dddd',
                                                     'pr_number': 0
                                                 }):
            self.assertCountEqual([self.runs[0]], self.resource.get())

    def test_get_field_not_exist(self):
        """Tests that filtering by a field that does not exist
        returns BAD REQUEST."""
        with main.FLASK_APP.test_request_context(
                _ENDPOINT, json={'does-not-exist': 'data'}):
            _, code = self.resource.get()
            self.assertEqual(400, code)

    def test_get_value_not_exist(self):
        """Tests that filtering by a value that does not exist
        returns empty result."""
        with main.FLASK_APP.test_request_context(
                _ENDPOINT, json={'repo_name': 'does-not-exist'}):
            self.assertEqual([], self.resource.get())

    def test_limit_order(self):
        with main.FLASK_APP.test_request_context(
                f'{_ENDPOINT}?limit=3&order=repo_name&order=-pr_number',
                json={}):
            runs = self.resource.get()
            self.assertEqual(['aaaa', 'data', 'data'],
                             list(run[_MODEL.repo_name] for run in runs))
            self.assertEqual([2, 3, 1],
                             list(run[_MODEL.pr_number] for run in runs))