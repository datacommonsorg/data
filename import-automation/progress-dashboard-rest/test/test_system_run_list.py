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

from app.model import system_run_model
from app.resource import system_run_list
from test import utils

_MODEL = system_run_model.SystemRunModel


class SystemRunListTest(unittest.TestCase):
    """Tests for SystemRunList."""

    # TODO(intrepiditee): Replace with module level setup
    @classmethod
    def setUpClass(cls):
        cls.emulator = utils.start_emulator()

    @classmethod
    def tearDownClass(cls):
        utils.terminate_emulator(cls.emulator)

    @mock.patch('app.utils.create_datastore_client',
                utils.create_test_datastore_client)
    def setUp(self):
        """Injects several system runs to the database before every test."""
        self.resource = system_run_list.SystemRunList()
        runs = [
            {_MODEL.repo_name: 'dddd', _MODEL.pr_number: 0},
            {_MODEL.repo_name: 'data', _MODEL.pr_number: 1},
            {_MODEL.repo_name: 'data', _MODEL.pr_number: 1},
            {_MODEL.repo_name: 'aaaa', _MODEL.pr_number: 2}
        ]
        self.runs = utils.ingest_system_runs(self.resource, runs)

    @mock.patch(utils.PARSE_ARGS, lambda self: {})
    def test_get_all(self):
        """Tests that empty filter returns all the runs."""
        self.assertCountEqual(self.runs, self.resource.get())

    @mock.patch(utils.PARSE_ARGS, lambda self: {_MODEL.repo_name: 'data'})
    def test_get_by_repo_name(self):
        """Tests that filtering by repo_name returns the correct runs."""
        self.assertCountEqual([self.runs[1], self.runs[2]], self.resource.get())

    @mock.patch(utils.PARSE_ARGS,
                lambda self: {'repo_name': 'dddd', 'pr_number': 0})
    def test_get_by_repo_name_and_pr_number(self):
        """Tests that filtering by repo_name and pr_number returns
        the correct runs."""
        self.assertCountEqual([self.runs[0]], self.resource.get())

    @mock.patch(utils.PARSE_ARGS, lambda self: {'does-not-exist': 'data'})
    def test_get_field_not_exist(self):
        """Tests that filtering by a field that does not exist
        returns empty result."""
        self.assertEqual([], self.resource.get())

    @mock.patch(utils.PARSE_ARGS, lambda self: {'repo_name': 'does-not-exist'})
    def test_get_value_not_exist(self):
        """Tests that filtering by a value that does not exist
        returns empty result."""
        self.assertEqual([], self.resource.get())
