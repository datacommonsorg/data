# Copyright 2021 Google LLC
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

import tempfile
import unittest
from unittest import mock

from datacommons_wrappers import dc_check_existence, fetch_dcid_properties_enums


class TestDCWrappers(unittest.TestCase):

    def test_dc_check_existence(self):
        ret = dc_check_existence(['Count_Person', 'Person', 'node1'])
        self.assertEqual(ret, {
            'Count_Person': True,
            'Person': True,
            'node1': False
        })

    @mock.patch('datacommons_wrappers.request_post_json')
    def test_fetch_dcid_properties_enums_mapping_v2(self, mock_post):
        mock_post.side_effect = [
            # 1) domainIncludes for the target dcid
            self._arc_response('Count_Person', 'domainIncludes',
                               ['propEnumOnly']),
            # 2) rangeIncludes for the property dcid
            self._arc_response('propEnumOnly', 'rangeIncludes',
                               ['SomeEnumType']),
            # 3) typeOf for the enum type dcid
            self._arc_response('SomeEnumType', 'typeOf',
                               ['EnumValue1', 'EnumValue2']),
        ]

        with tempfile.TemporaryDirectory() as tempdir:
            result = fetch_dcid_properties_enums('Count_Person',
                                                 cache_path=tempdir,
                                                 use_autopush=False,
                                                 force_fetch=True)

        self.assertEqual(result, {'propEnumOnly': ['EnumValue1', 'EnumValue2']})
        self.assertEqual(mock_post.call_count, 3)

    @staticmethod
    def _arc_response(node_id, arc_label, dcids):
        return {
            'data': {
                node_id: {
                    'arcs': {
                        arc_label: {
                            'nodes': [{
                                'dcid': dcid
                            } for dcid in dcids]
                        }
                    }
                }
            }
        }


if __name__ == '__main__':
    unittest.main()
