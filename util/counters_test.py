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
import time

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)

from counters import Counters, CounterOptions


class TestCounters(unittest.TestCase):

    def test_add_counter_increment(self):
        counters = Counters(prefix='test_')
        counters.add_counter('inputs', 10)
        self.assertEqual(10, counters.get_counter('inputs'))
        counters.add_counter('inputs', 1)
        self.assertEqual(11, counters.get_counter('inputs'))

    def test_add_counter_decrement(self):
        counters = Counters(prefix='test_')
        counters.add_counter('inputs', 10)
        self.assertEqual(10, counters.get_counter('inputs'))
        counters.add_counter('inputs', -5)
        self.assertEqual(5, counters.get_counter('inputs'))

    def test_add_counter_default_increment(self):
        counters = Counters(prefix='test_')
        counters.add_counter('inputs')
        self.assertEqual(1, counters.get_counter('inputs'))

    def test_add_counters(self):
        counters = Counters()
        counters.add_counters({'a': 1, 'b': 2})
        self.assertEqual(1, counters.get_counter('a'))
        self.assertEqual(2, counters.get_counter('b'))
        counters.add_counters({'a': 3, 'c': 4})
        self.assertEqual(4, counters.get_counter('a'))
        self.assertEqual(2, counters.get_counter('b'))
        self.assertEqual(4, counters.get_counter('c'))

    def test_set_counter_overwrites_value(self):
        '''Verify set_counter overrides current value.'''
        counters = Counters(prefix='test2_')
        counters.add_counter('lines', 1)
        counters.set_counter('lines', 100)
        self.assertEqual(100, counters.get_counter('lines'))

    def test_debug_counters_are_correctly_updated(self):
        '''Verify counters with debug string suffixes.'''
        counters = Counters(prefix='test3_', options=CounterOptions(debug=True))
        counters.add_counter('inputs', 10, 'test-case-2')
        counters.add_counter('inputs', 11, 'file2')
        self.assertEqual(21, counters.get_counter('inputs'))
        self.assertEqual(10, counters.get_counter('inputs_test-case-2'))
        self.assertEqual(11, counters.get_counter('inputs_file2'))

    def test_debug_counters_are_not_created_when_debug_is_false(self):
        counters = Counters(prefix='test4_',
                            options=CounterOptions(debug=False))
        counters.add_counter('inputs', 10, 'test-case-3')
        self.assertEqual(10, counters.get_counter('inputs'))
        self.assertEqual(0, counters.get_counter('inputs_test-case-3'))

    def test_counter_dict_is_shared(self):
        '''Verify counter dict is shared across counters.'''
        common_dict = {}
        counters1 = Counters(counters_dict=common_dict)
        counters2 = Counters(counters_dict=common_dict)
        counters1.add_counter('test_ctr', 1)
        self.assertEqual(1, counters2.get_counter('test_ctr'))

    def test_get_non_existent_counter(self):
        counters = Counters()
        self.assertEqual(0, counters.get_counter('non_existent'))

    def test_prefix(self):
        counters = Counters()
        self.assertEqual('', counters.get_prefix())
        counters.set_prefix('p1_')
        self.assertEqual('p1_', counters.get_prefix())
        counters.add_counter('c1')
        self.assertEqual(1, counters.get_counter('c1'))
        self.assertIn('p1_c1', counters.get_counters())

    def test_processing_rate(self):
        counters = Counters(options=CounterOptions(
            total_counter='total', processed_counter='processed'))
        counters.add_counter('total', 100)
        counters.add_counter('processed', 10)
        time.sleep(1)
        counters._update_processing_rate()
        self.assertGreater(counters.get_counter('processing_rate'), 0)
        self.assertGreater(counters.get_counter('process_remaining_time'), 0)

    def test_get_counters_string(self):
        counters = Counters()
        counters.add_counter('c1', 1)
        counters.set_counter('c2', 2.3)
        counters.set_counter('c3', 'v3')
        self.assertIn('c1 =          1', counters.get_counters_string())
        self.assertIn('c2 =       2.30', counters.get_counters_string())
        self.assertIn('c3 = v3', counters.get_counters_string())

    def test_show_counters_produces_correct_output(self):
        counters = Counters(prefix='test-',
                            options=CounterOptions(
                                total_counter='file-rows',
                                processed_counter='read-rows',
                                show_every_n_sec=1,
                            ))
        counters.add_counter('file-rows', 100)
        counters.add_counter('read-rows', 10)
        c_str = counters.get_counters_string()
        self.assertTrue(c_str.find('test-file-rows') > 0)
        self.assertTrue(c_str.find('test-read-rows') > 0)

    def test_min_counter(self):
        counters = Counters()
        counters.min_counter('min_val', 10)
        self.assertEqual(10, counters.get_counter('min_val'))
        counters.min_counter('min_val', 5)
        self.assertEqual(5, counters.get_counter('min_val'))
        counters.min_counter('min_val', 15)
        self.assertEqual(5, counters.get_counter('min_val'))

    def test_max_counter(self):
        counters = Counters()
        counters.max_counter('max_val', 10)
        self.assertEqual(10, counters.get_counter('max_val'))
        counters.max_counter('max_val', 5)
        self.assertEqual(10, counters.get_counter('max_val'))
        counters.max_counter('max_val', 15)
        self.assertEqual(15, counters.get_counter('max_val'))


if __name__ == '__main__':
    unittest.main()
