# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''Tests for config.py'''

import os
import sys
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)

from counters import Counters, CounterOptions


class TestCounters(unittest.TestCase):

    def test_add_counter(self):
        '''Verify increment and decrement counters.'''
        counters = Counters(prefix='test_')
        counters.add_counter('inputs', 10,
                             'test-case-1').add_counter('outputs', 2)
        self.assertEqual(10, counters.get_counter('inputs'))
        self.assertEqual(2, counters.get_counter('outputs'))
        counters.add_counter('inputs', 1, 'test-case-1')
        self.assertEqual(11, counters.get_counter('inputs'))
        counters.add_counter('inputs', -5, 'test-case-1')
        self.assertEqual(6, counters.get_counter('inputs'))
        counters.add_counter('inputs')
        self.assertEqual(7, counters.get_counter('inputs'))

    def test_set_counter(self):
        '''Verify set_counter overrides current value.'''
        counters = Counters(prefix='test2_', options=CounterOptions(debug=True))
        counters.add_counter('lines', 1, 'file1')
        counters.add_counter('lines', 10, 'file1')
        counters.print_counters()
        self.assertEqual(11, counters.get_counter('lines'))
        self.assertEqual(11, counters.get_counter('lines_file1'))
        counters.set_counter('lines', 100, 'file1')
        self.assertEqual(100, counters.get_counter('lines'))
        self.assertEqual(100, counters.get_counter('lines_file1'))

    def test_debug_counters(self):
        '''Verify counters with debug string suffixes.'''
        counters = Counters(prefix='test3_', options=CounterOptions(debug=True))
        counters.add_counter('inputs', 10, 'test-case-2')
        counters.add_counter('inputs', 11, 'file2')
        counters.add_counter('outputs', 2)
        self.assertEqual(21, counters.get_counter('inputs'))
        self.assertEqual(10, counters.get_counter('inputs_test-case-2'))
        self.assertEqual(11, counters.get_counter('inputs_file2'))
        self.assertEqual(2, counters.get_counter('outputs'))

    def test_counter_dict(self):
        '''Verify counter dict is shared across counters.'''
        common_dict = {}
        counters1 = Counters(counters_dict=common_dict)
        counters2 = Counters(counters_dict=common_dict)
        counters1.add_counter('test_ctr', 1)

    def test_show_counters(self):
        counters = Counters(prefix='test-',
                            options=CounterOptions(
                                total_counter='file-rows',
                                processed_counter='read-rows',
                                show_every_n_sec=1,
                            ))
        counters.add_counter('file-rows', 100)
        counters.add_counter('read-rows', 10)
        counters.print_counters()
        c_str = counters.get_counters_string()
        self.assertTrue(c_str.find('test-process_elapsed_time') > 0)
        self.assertTrue(c_str.find('test-processing_rate') > 0)
        self.assertTrue(counters.get_counter('process_remaining_time') > 0)
