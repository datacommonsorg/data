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
"""Tests for extract_source_dataset_provenance.py."""

import json
import os
import sys
import tempfile
import unittest
from unittest import mock

# Python path is managed by running from the data directory.

from util import extract_source_dataset_provenance


class TestExtractSourceDatasetProvenance(unittest.TestCase):

    def setUp(self):
        super().setUp()
        # Create a temporary directory for output files
        self.test_dir = tempfile.TemporaryDirectory()
        self.output_file = os.path.join(self.test_dir.name, 'output.json')

    def tearDown(self):
        self.test_dir.cleanup()
        super().tearDown()

    def test_get_node_property(self):
        """Tests extracting string values from node property structures."""
        # Value exists
        node_data_with_val = {
            'arcs': {
                'name': {
                    'nodes': [{
                        'value': 'Test Name'
                    }]
                }
            }
        }
        self.assertEqual(
            extract_source_dataset_provenance.get_node_property(
                node_data_with_val, 'name'), 'Test Name')

        # Empty list of nodes
        node_data_empty = {'arcs': {'name': {'nodes': []}}}
        self.assertEqual(
            extract_source_dataset_provenance.get_node_property(
                node_data_empty, 'name', default='Fallback'), 'Fallback')

        # Missing arcs
        self.assertEqual(
            extract_source_dataset_provenance.get_node_property(
                {}, 'name', default='Fallback'), 'Fallback')

    def test_get_node_dcid(self):
        """Tests extracting DCID values from node property structures."""
        # DCID exists
        node_data_with_dcid = {
            'arcs': {
                'isPartOf': {
                    'nodes': [{
                        'dcid': 'dc/ds/ds1'
                    }]
                }
            }
        }
        self.assertEqual(
            extract_source_dataset_provenance.get_node_dcid(
                node_data_with_dcid, 'isPartOf'), 'dc/ds/ds1')

        # Empty nodes list
        node_data_empty = {'arcs': {'isPartOf': {'nodes': []}}}
        self.assertIsNone(
            extract_source_dataset_provenance.get_node_dcid(
                node_data_empty, 'isPartOf'))

        # Missing property
        self.assertIsNone(
            extract_source_dataset_provenance.get_node_dcid({}, 'isPartOf'))

    @mock.patch('util.extract_source_dataset_provenance.dc_api_wrapper')
    @mock.patch('util.extract_source_dataset_provenance.get_datacommons_client')
    def test_fetch_all_provenances_success(self, mock_get_client, mock_wrapper):
        """Tests successful fetches and hierarchy resolver end-to-end."""
        # Standard configuration for API mocks
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client

        # Define mock return objects
        res_type_of = mock.Mock()
        res_type_of.to_dict.return_value = {
            'data': {
                'Provenance': {
                    'arcs': {
                        'typeOf': {
                            'nodes': [
                                {
                                    'dcid': 'dc/prov/prov1'
                                },
                                {
                                    'dcid': 'dc/prov/prov2'
                                },
                                {
                                    'dcid': ''
                                },  # testing filtering out empty dcids
                            ]
                        }
                    }
                }
            }
        }

        res_prov_details = mock.Mock()
        res_prov_details.to_dict.return_value = {
            'data': {
                'dc/prov/prov1': {
                    'arcs': {
                        'name': {
                            'nodes': [{
                                'value': 'Provenance One'
                            }]
                        },
                        'description': {
                            'nodes': [{
                                'value': 'Desc One'
                            }]
                        },
                        'sourceDataUrl': {
                            'nodes': [{
                                'value': 'http://url1'
                            }]
                        },
                        'license': {
                            'nodes': [{
                                'value': 'CC-BY'
                            }]
                        },
                        'isPartOf': {
                            'nodes': [{
                                'dcid': 'dc/ds/ds1'
                            }]
                        },
                    }
                },
                'dc/prov/prov2': {
                    'arcs': {
                        'name': {
                            'nodes': [{
                                'value': 'Provenance Two'
                            }]
                        },
                        'license': {
                            'nodes': [{
                                'value': 'Public Domain'
                            }]
                        },
                        'isPartOf': {
                            'nodes': []
                        },  # lacks dataset link
                    }
                },
            }
        }

        res_ds_details = mock.Mock()
        res_ds_details.to_dict.return_value = {
            'data': {
                'dc/ds/ds1': {
                    'arcs': {
                        'name': {
                            'nodes': [{
                                'value': 'Dataset One'
                            }]
                        },
                        'url': {
                            'nodes': [{
                                'value': 'http://dataset1'
                            }]
                        },
                        'isPartOf': {
                            'nodes': [{
                                'dcid': 'dc/src/src1'
                            }]
                        },
                    }
                }
            }
        }

        res_src_details = mock.Mock()
        res_src_details.to_dict.return_value = {
            'data': {
                'dc/src/src1': {
                    'arcs': {
                        'name': {
                            'nodes': [{
                                'value': 'Source One'
                            }]
                        },
                        'url': {
                            'nodes': [{
                                'value': 'http://source1'
                            }]
                        },
                    }
                }
            }
        }

        # API calls matching order of execution in script:
        # 1. Fetch Provenances by typeOf
        # 2. Fetch details for batch of provenances
        # 3. Fetch details for batch of datasets
        # 4. Fetch details for batch of sources
        mock_wrapper.side_effect = [
            res_type_of,
            res_prov_details,
            res_ds_details,
            res_src_details,
        ]

        extract_source_dataset_provenance.fetch_all_provenances(
            api_key='dummy_key', output_file=self.output_file)

        # 1. Verify client was created
        mock_get_client.assert_called_once_with({'dc_api_key': 'dummy_key'})

        # 2. Verify Output file generated correctly
        self.assertTrue(os.path.exists(self.output_file))
        with open(self.output_file, 'r') as f:
            output_data = json.load(f)

        # 3. Validate resulting structure matching expected hierarchy
        expected_output = [
            {
                'dcid': 'dc/prov/prov1',
                'name': 'Provenance One',
                'description': 'Desc One',
                'sourceDataUrl': 'http://url1',
                'license': 'CC-BY',
                'dataset': {
                    'name': 'Dataset One',
                    'url': 'http://dataset1',
                    'source': {
                        'name': 'Source One',
                        'url': 'http://source1'
                    },
                },
            },
            {
                'dcid': 'dc/prov/prov2',
                'name': 'Provenance Two',
                'description': None,
                'sourceDataUrl': None,
                'license': 'Public Domain',
                'dataset': None,
            },
        ]
        self.assertEqual(output_data, expected_output)

    @mock.patch('util.extract_source_dataset_provenance.dc_api_wrapper')
    @mock.patch('util.extract_source_dataset_provenance.get_datacommons_client')
    def test_fetch_all_provenances_empty(self, mock_get_client, mock_wrapper):
        """Tests execution flow when no provenances are returned."""
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client

        res_type_of = mock.Mock()
        res_type_of.to_dict.return_value = {
            'data': {
                'Provenance': {
                    'arcs': {
                        'typeOf': {
                            'nodes': []
                        }
                    }
                }
            }
        }
        mock_wrapper.return_value = res_type_of

        extract_source_dataset_provenance.fetch_all_provenances(
            api_key='dummy_key', output_file=self.output_file)

        # Output file should not have been written to
        self.assertFalse(os.path.exists(self.output_file))

    @mock.patch('util.extract_source_dataset_provenance.dc_api_wrapper')
    @mock.patch('util.extract_source_dataset_provenance.get_datacommons_client')
    def test_fetch_all_provenances_api_failure(self, mock_get_client,
                                               mock_wrapper):
        """Tests correct handling of exceptions thrown by the API wrapper."""
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client

        mock_wrapper.side_effect = RuntimeError('API failure')

        # Should not raise exception out of function, but log and return gracefully
        extract_source_dataset_provenance.fetch_all_provenances(
            api_key='dumm_key', output_file=self.output_file)
        self.assertFalse(os.path.exists(self.output_file))


if __name__ == '__main__':
    unittest.main()
