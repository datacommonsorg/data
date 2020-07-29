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
Tests for progress_log_database.py.
"""

import unittest
from unittest import mock

from google.cloud import exceptions

from test import utils
from app.model import progress_log_model
from app.service import progress_log_database

_MODEL = progress_log_model.ProgressLog


def setUpModule():
    utils.EMULATOR.start_emulator()


class ProgressLogDatabaseTest(unittest.TestCase):
    """Tests for BaseDatabase."""

    @mock.patch('app.utils.create_datastore_client',
                utils.create_test_datastore_client)
    @mock.patch('app.service.log_message_manager.LogMessageManager',
                utils.LogMessageManagerMock)
    def setUp(self):
        """Ingests several logs before every test."""
        self.database = progress_log_database.ProgressLogDatabase()
        logs = [self.database.get(make_new=True) for _ in range(4)]
        logs[0].update({_MODEL.level: 'info', _MODEL.message: 'first'})
        logs[1].update({_MODEL.level: 'warning', _MODEL.message: 'second'})
        logs[2].update({_MODEL.level: 'warning', _MODEL.message: 'third'})
        logs[3].update({_MODEL.level: 'severe', _MODEL.message: 'fourth'})
        self.logs_save_content = [logs[0], logs[1]]
        self.logs_not_save_content = [logs[2], logs[3]]
        for i, log in enumerate(self.logs_save_content):
            self.logs_save_content[i] = self.database.save(log,
                                                           save_content=True)
        for i, log in enumerate(self.logs_not_save_content):
            self.logs_not_save_content[i] = self.database.save(
                log, save_content=False)

    def test_load_content(self):
        """Tests that get with load_content=True loads the message."""
        expected = ['first', 'second']
        for i, message in enumerate(expected):
            log = self.logs_save_content[i]
            retrieved = self.database.get(entity_id=log[_MODEL.log_id],
                                          load_content=True)
            self.assertEqual(message, retrieved[_MODEL.message])

    def test_not_load_content(self):
        """Tests that get with load_content=False does not load the message."""
        for log in self.logs_save_content:
            log_id = log[_MODEL.log_id]
            retrieved = self.database.get(entity_id=log_id, load_content=False)
            self.assertEqual(log_id, retrieved[_MODEL.message])

    def test_not_save_content(self):
        """Tests that save with save_content=False does not save the message to
        a bucket."""
        expected = ['third', 'fourth']
        for i, message in enumerate(expected):
            log_id = self.logs_not_save_content[i][_MODEL.log_id]
            retrieved = self.database.get(entity_id=log_id, load_content=False)
            self.assertEqual(message, retrieved[_MODEL.message])
            self.assertRaises(exceptions.NotFound,
                              self.database.get,
                              entity_id=log_id,
                              load_content=True)

    def test_load_logs(self):
        """Tests that load_logs correctly loads log messages and throws
        an exception when the messages have not been saved."""
        loaded = self.database.load_logs(
            [log[_MODEL.log_id] for log in self.logs_save_content])
        messages = [log[_MODEL.message] for log in loaded]
        self.assertEqual(['first', 'second'], messages)

        self.assertRaises(
            exceptions.NotFound, self.database.load_logs,
            [log[_MODEL.log_id] for log in self.logs_not_save_content])
