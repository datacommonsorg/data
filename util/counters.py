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
'''Class for dictionary of named counters.

It also supports the following:
- Min/Max counters: to track min/max values of a metric.
- Debug counters: to track metrics with more detailed context.
- Periodic counters: to track processing rate, memory, CPU usage.
- Rate counters: to track processing rate and estimated time to completion.
'''

import os
import psutil
import sys
import time

from absl import flags
from absl import logging
from typing import NamedTuple

flags.DEFINE_integer('counters_print_interval', 300,
                     'Interval in seconds to print counters.')

_FLAGS = flags.FLAGS


# Options for counters
class CounterOptions(NamedTuple):
    '''A set of options for configuring Counters behavior.'''
    # Enable debug counters with additional suffixes.
    debug: bool = False
    # Emit counters once every 300 secs.
    show_every_n_sec: int = 300
    # Counter for processing stage
    process_stage: str = 'processing_stage'
    # Counter for records processed
    # used for computing processing rate.
    processed_counter: str = 'processed'
    # Counter for total inputs
    # Used for computing remaining time.
    total_counter: str = 'total'


def get_default_counter_options() -> CounterOptions:
    '''Returns the default counters options.'''
    show_every_n_sec = 300
    if _FLAGS.is_parsed():
        show_every_n_sec = _FLAGS.counters_print_interval

    debug = False
    if logging.get_verbosity() >= logging.DEBUG:
        debug = True

    return CounterOptions(debug=debug, show_every_n_sec=show_every_n_sec)


class Counters():
    '''A dictionary of named counters for tracking metrics.

    This class provides a flexible way to handle various types of counters,
    including min/max values, debug counters, and periodic metrics like
    processing rate, memory usage, and CPU time.

    Example usage:
      counters = Counters(prefix='my_process')
      ...
      counters.add_counter('input_rows')
         .add_counter('output_rows', 10)
      counters.add_counter('processed', 1)

      # Min/Max counters
      counters.min_counter('min_area', 12.34)
      counters.max_counter('max_temp', 36.5)

      # Print counters on STDERR
      counters.print_counters()
      #       my_process_input_rows =          1
      #      my_process_output_rows =         10
      #         my_process_max_temp =      36.50
      #         my_process_min_area =      12.34

    Note: This object is not thread-safe.
    '''

    def __init__(self,
                 counters_dict: dict = None,
                 prefix: str = '',
                 options: CounterOptions = None):
        '''Initializes the Counters object.

        Args:
            counters_dict: An optional dictionary of pre-existing counters.
              If provided, the Counters object will operate on this dictionary
              directly, allowing multiple Counters instances to share state.
              If not provided, a new dictionary is created.
            prefix: A string prefix to be added to every counter name.
            options: A CounterOptions object for configuring behavior.
        '''
        if counters_dict is None:
            self._counters = {}
        else:
            self._counters = counters_dict
        self._prefix = prefix
        if options:
            self._options = options
        else:
            self._options = get_default_counter_options()

        # Internal state
        # Start time for rate counters.
        self.reset_start_time()
        self._next_counter_print_time = 0

    def __del__(self):
        '''Log the counters when the object is deleted.'''
        self._update_periodic_counters()
        logging.debug(self.get_counters_string())

    def add_counter(self,
                    counter_name: str,
                    value: int = 1,
                    debug_context: str = None):
        '''Increment a named counter and debug counter by the given value.

        It also displays counters periodically based on 'show_every_n_sec' option.

        Args:
            counter_name: Name of the counter to update.
            value: Value to be added to the counter.
            debug_context: Optional suffix for the debug counter.

        Returns:
          This Counters object.
        
        Usage:
            >>> counters = Counters()
            >>> counters.add_counter('my_counter', 10)
            >>> counters.get_counter('my_counter')
            10
            >>> counters.add_counter('my_counter', -5)
            >>> counters.get_counter('my_counter')
            5
        '''
        name = self._get_counter_name(counter_name)
        self._counters[name] = self._counters.get(name, 0) + value
        if debug_context and self._options.debug:
            # Add debug counter with the context message.
            ext_name = self._get_counter_name(counter_name, debug_context)
            self._counters[ext_name] = self._counters.get(ext_name, 0) + value

        # Display all counters if required.
        self.print_counters_periodically()
        return self

    def add_counters(self, counters_dict: dict):
        '''Add all counters from the given dict.

        Args:
          counters_dict: A dictionary of counter names and their values.

        Returns:
          This Counters object.

        Usage:
            >>> counters = Counters()
            >>> counters.add_counters({'a': 1, 'b': 2})
            >>> counters.get_counter('a')
            1
            >>> counters.get_counter('b')
            2
            >>> counters.add_counters({'a': 3, 'c': 4})
            >>> counters.get_counter('a')
            4
            >>> counters.get_counter('c')
            4
        '''
        if counters_dict:
            for counter, value in counters_dict.items():
                self.add_counter(counter, value)
        return self

    def set_counter(self, name: str, value: int, debug_context: str = None):
        '''Set the value of a counter, overwriting any previous value.

        Args:
          name: Name of the counter to set.
          value: The value to set the counter to.
          debug_context: Optional suffix for the debug counter.

        Returns:
          This Counters object.

        Usage:
            >>> counters = Counters()
            >>> counters.set_counter('my_counter', 100)
            >>> counters.get_counter('my_counter')
            100
            >>> counters.set_counter('my_counter', 200)
            >>> counters.get_counter('my_counter')
            200
        '''
        self._counters[self._get_counter_name(name)] = value
        if debug_context:
            self._counters[self._get_counter_name(name, debug_context)] = value
        return self

    def get_counters(self) -> dict:
        '''Return the dictionary of all counter names and their values.
        
        Usage:
            >>> counters = Counters()
            >>> counters.add_counter('a', 1)
            >>> counters.add_counter('b', 2)
            >>> sorted(counters.get_counters().items())
            [('a', 1), ('b', 2), ('process-mem', ...), ('process-mem-rss', ...), ('process-time-sys-secs', ...), ('process-time-user-secs', ...), ('process_elapsed_time', ...), ('processed', 0), ('start_time', ...)]
        '''
        return self._counters

    def get_counter(self, name: str) -> int:
        '''Return the value of a named counter.

        Args:
          name: Name of the counter to look up.

        Returns:
          The value of the counter if it exists, otherwise 0.

        Usage:
            >>> counters = Counters()
            >>> counters.set_counter('my_counter', 10)
            >>> counters.get_counter('my_counter')
            10
            >>> counters.get_counter('non_existent_counter')
            0
        '''
        return self._counters.get(self._get_counter_name(name), 0)

    def min_counter(self, name: str, value: int, debug_context: str = None):
        '''Sets the named counter to the minimum of its current value and the given value.

        Args:
          name: Name of the counter.
          value: The new value to consider for the minimum.
          debug_context: Optional suffix for the debug counter.

        Returns:
          This Counters object.

        Usage:
            >>> counters = Counters()
            >>> counters.min_counter('min_val', 10)
            >>> counters.get_counter('min_val')
            10
            >>> counters.min_counter('min_val', 5)
            >>> counters.get_counter('min_val')
            5
            >>> counters.min_counter('min_val', 15)
            >>> counters.get_counter('min_val')
            5
        '''
        if value <= self._counters.get(self._get_counter_name(name), value):
            self.set_counter(name, value, debug_context)
        return self

    def max_counter(self, name: str, value: int, debug_context: str = None):
        '''Sets the named counter to the maximum of its current value and the given value.

        Args:
          name: Name of the counter.
          value: The new value to consider for the maximum.
          debug_context: Optional suffix for the debug counter.

        Returns:
          This Counters object.

        Usage:
            >>> counters = Counters()
            >>> counters.max_counter('max_val', 10)
            >>> counters.get_counter('max_val')
            10
            >>> counters.max_counter('max_val', 5)
            >>> counters.get_counter('max_val')
            10
            >>> counters.max_counter('max_val', 15)
            >>> counters.get_counter('max_val')
            15
        '''
        if value >= self._counters.get(self._get_counter_name(name), value):
            self.set_counter(name, value, debug_context)
        return self

    def get_counters_string(self) -> str:
        '''Returns a formatted string of counter names and values, sorted by name.
        
        The output is a multi-line string where each line is formatted as:
        <counter_name> = <value>
        
        Usage:
            >>> counters = Counters()
            >>> counters.add_counter('c1', 1)
            >>> counters.set_counter('c2', 2.3)
            >>> counters.set_counter('c3', 'v3')
            >>> print(counters.get_counters_string())
            Counters:
                                                    c1 =          1
                                                    c2 =       2.30
                                                    c3 = v3
                                           process-mem = ...
                                       process-mem-rss = ...
                                 process-time-sys-secs = ...
                                process-time-user-secs = ...
                                  process_elapsed_time = ...
                                             processed =          0
                                            start_time = ...
        '''
        lines = ['Counters:']
        for c in sorted(self._counters.keys()):
            v = self._counters[c]
            if isinstance(v, int):
                lines.append(f'{c:>50s} = {v:>10d}')
            elif isinstance(v, float):
                lines.append(f'{c:>50s} = {v:>10.2f}')
            else:
                lines.append(f'{c:>50s} = {v}')
        return '\n'.join(lines)

    def print_counters(self, file=None):
        '''Prints the counter values to the specified file.

        Args:
            file: The file handle to write the counters string to. Defaults to stderr.
        '''
        self._update_periodic_counters()
        counters_str = self.get_counters_string()
        logging.info(counters_str)
        if file:
            print(counters_str, file=file)

    def print_counters_periodically(self):
        '''Prints the counters periodically based on the 'show_every_n_sec' option.'''
        interval = self._options.show_every_n_sec
        if interval > 0:
            curr_time = time.perf_counter()
            if curr_time > self._next_counter_print_time:
                self._next_counter_print_time = curr_time + interval
                self.print_counters()

    def reset_start_time(self):
        '''Resets the start time for rate counters.'''
        self.set_counter('start_time', time.perf_counter())
        self.set_counter(self._options.processed_counter, 0)

    def set_prefix(self, prefix: str):
        '''Sets the prefix for counter names.

        It also resets the start_time and processing rate counters.

        Usage:
            >>> counters = Counters()
            >>> counters.set_prefix('p1_')
            >>> counters.add_counter('c1')
            >>> counters.get_counter('c1')
            1
            >>> 'p1_c1' in counters.get_counters()
            True
        '''
        self._update_periodic_counters()
        self._prefix = prefix
        self.reset_start_time()
        logging.info(self.get_counters_string())

    def get_prefix(self) -> str:
        '''Returns the counter prefix.
        
        Usage:
            >>> counters = Counters()
            >>> counters.get_prefix()
            ''
            >>> counters.set_prefix('p1_')
            >>> counters.get_prefix()
            'p1_'
        '''
        return self._prefix

    # Internal functions
    def _get_counter_name(self, name: str, debug_context: str = None) -> str:
        '''Returns the name of the counter with the prefix and debug context.'''
        name = f'{self._prefix}{name}'
        if debug_context:
            name = name + f'_{debug_context}'
        return name

    def _update_periodic_counters(self):
        '''Updates periodic counters such as processing rate and process counters.'''
        self._update_processing_rate()
        self._update_process_counters()

    def _update_processing_rate(self):
        '''Update the processing rate and remaining time.
        Uses the option: 'processed' to get the counter for processing rate
        and option 'inputs' to estimate remaining time.
        '''
        start_time = self.get_counter('start_time')
        if not start_time:
            self.reset_start_time()
            start_time = time.perf_counter()
        time_taken = time.perf_counter() - start_time + 0.0001
        self.set_counter('process_elapsed_time', time_taken)
        num_processed = self.get_counter(self._options.processed_counter)
        rate = 0.0001
        if num_processed:
            rate = num_processed / time_taken
            self.set_counter('processing_rate', rate)
        totals = self.get_counter(self._options.total_counter)
        if totals:
            self.set_counter('process_remaining_time',
                             max(0, (totals - num_processed)) / rate)

    def _update_process_counters(self):
        '''Update process counters for memory and time.'''
        process = psutil.Process(os.getpid())
        mem = process.memory_info()
        self.max_counter('process-mem-rss', mem.rss)
        self.max_counter('process-mem', mem.vms)
        cpu_times = process.cpu_times()
        self.set_counter('process-time-user-secs', cpu_times.user)
        self.set_counter('process-time-sys-secs', cpu_times.system)
