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
''' Utility functions for debug messages and counters.'''

import time

from absl import app
from absl import flags

FLAGS = flags.FLAGS
flags.DEFINE_integer('debug_level', 0,
                     'Print debug messages at this level or lower.')
flags.DEFINE_integer('debug_lines', 100,
                     'Print counters once N inputs are processed.')

_COUNTERS = {}

_CONFIG = {}


def add_counter(name: str, value: int, counters:dict =_COUNTERS):
    '''Increment the counter by the given value.'''
    counters[name] = counters.get(name, 0) + value
    return counters[name]

def get_counter(name: str, counters: dict = _COUNTERS):
   '''Returns the current value of the counter.'''
   return counters.get(name, 0)

def print_counters(counters:dict = _COUNTERS, interval:int =None):
    '''Display all counters at the given interval.'''
    if interval is not None:
        delay = time.perf_counter() - print_counters._COUNTER_DISPLAY_TIME
        if delay < interval:
            return
    print('\nCounters:')
    for k in sorted(counters.keys()):
        print(f"\t{k:>40} = {counters[k]}")
    print('', flush=True)
    print_counters._COUNTER_DISPLAY_TIME = time.perf_counter()


print_counters._COUNTER_DISPLAY_TIME = 0

def print_debug(debug_level: int, *args):
    config_debug_level = _CONFIG.get('debug_level', 0)
    if 'debug_level' in FLAGS:
        config_debug_level  = FLAGS.debug_level
    if config_debug_level >= debug_level:
        print("[", datetime.datetime.now(), "] ", *args, file=sys.stderr)

def set_debug_level(max_level:int):
   '''Sets the debug level.
      print_debug calls with levels upto this will be printed.
   '''
   _CONFIG['debug_level'] = max_level


