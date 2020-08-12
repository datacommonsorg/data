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
Tests for import_executor.py.
"""

import unittest
from unittest import mock

from app.service import import_service

_CLIENT = 'app.service.import_service.ImportServiceClient'


class ImportServiceTest(unittest.TestCase):

    @mock.patch('google.cloud.storage.Client', mock.MagicMock)
    def setUp(self):
        self.importer = import_service.ImportServiceClient(
            'project_id', 'unresolved_mcf_bucket_name',
            'resolved_mcf_bucket_name', 'importer_output_prefix',
            'executor_output_prefix')

    def test_fix_input_path(self):
        expected = ('/bigstore/unresolved_mcf_bucket_name/'
                    'executor_output_prefix/foo/bar/data.csv')
        self.assertEqual(expected,
                         self.importer._fix_input_path('foo/bar/data.csv'))

    @mock.patch(f'{_CLIENT}.import_table')
    @mock.patch(f'{_CLIENT}.import_node')
    def test_smart_import(self, import_node, import_table):
        self.importer.smart_import('import_dir',
                                   import_service.ImportInputs(
                                       cleaned_csv='import.csv',
                                       template_mcf='import.tmcf',
                                       node_mcf='import.mcf'),
                                   import_spec={})
        import_table.assert_called_once()

        self.importer.smart_import(
            'import_dir',
            import_service.ImportInputs(node_mcf='import.mcf'),
            import_spec={})
        import_node.assert_called_once()

        self.assertRaises(ValueError,
                          self.importer.smart_import,
                          'import_dir',
                          import_service.ImportInputs(cleaned_csv='import.csv',
                                                      node_mcf='import.mcf'),
                          import_spec={})

    @mock.patch(f'{_CLIENT}.get_import_log')
    @mock.patch(f'{_CLIENT}._SLEEP_DURATION', 0.00001)
    def test_block_on_import(self, get_import_log):
        expected = {'id': 'id1', 'state': 'SUCCESSFUL'}
        return_values = [{
            'entry': [{
                'id': 'id1',
                'state': 'QUEUED'
            }, {
                'id': 'id2',
                'state': 'QUEUED'
            }]
        }, {
            'entry': [{
                'id': 'id1',
                'state': 'RUNNING'
            }, {
                'id': 'id2',
                'state': 'QUEUED'
            }]
        }, {
            'entry': [{
                'id': 'id2',
                'state': 'PREEMPTED_WHILE_QUEUED',
                'importName': 'importName',
                'userEmail': 'userEmail'
            }, expected]
        }]
        get_import_log.side_effect = return_values
        self.assertEqual(
            expected,
            self.importer._block_on_import('id1',
                                           'import_name',
                                           'curator_email',
                                           timeout=1))
        get_import_log.side_effect = return_values
        self.assertRaises(TimeoutError,
                          self.importer._block_on_import,
                          'id1',
                          'import_name',
                          'curator_email',
                          timeout=0)
        self.assertRaises(import_service.ImportFailedError,
                          self.importer._block_on_import,
                          'id2',
                          'import_name',
                          'curator_email',
                          timeout=1)

    def test_get_fixed_absolute_import_name(self):
        self.assertEqual(
            'foo_bar_treasury_import',
            import_service._get_fixed_absolute_import_name(
                'foo/bar', 'treasury_import'))

    def test_get_import_id(self):
        logs_before = [{
            'id': 'id1',
            'importName': 'name1',
            'userEmail': 'email1'
        }, {
            'id': 'id2',
            'importName': 'name2',
            'userEmail': 'email2'
        }]
        logs_after = [{
            'id': 'id2',
            'importName': 'name2',
            'userEmail': 'email2'
        }, {
            'id': 'id3',
            'importName': 'name1',
            'userEmail': 'email1'
        }]
        self.assertEqual(
            'id3',
            import_service._get_import_id('name1', 'email1', logs_before,
                                          logs_after))
        self.assertRaises(import_service.ImportNotFoundError,
                          import_service._get_import_id, 'name2', 'email2',
                          logs_before, logs_after)

    def test_are_imports_finished(self):
        logs = [{
            'importName': 'name1',
            'userEmail': 'email1',
            'state': 'RUNNING'
        }, {
            'importName': 'name1',
            'userEmail': 'email1',
            'state': 'QUEUED'
        }, {
            'importName': 'name3',
            'userEmail': 'email3',
            'state': 'FAILED'
        }, {
            'importName': 'name4',
            'userEmail': 'email4',
            'state': 'SUCCESSFUL'
        }]

        self.assertFalse(
            import_service._are_imports_finished(logs, 'name1', 'email1'))
        self.assertTrue(
            import_service._are_imports_finished(logs, 'name3', 'email3'))

    def test_format_import_info(self):
        self.assertEqual(
            'import_name: name, curator_email: email, import_id: id',
            import_service._format_import_info('name', 'email', 'id'))
        self.assertEqual('import_name: name, curator_email: email',
                         import_service._format_import_info('name', 'email'))
