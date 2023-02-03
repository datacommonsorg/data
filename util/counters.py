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
'''Class for dictionary of named counters.'''

import sys
import time

from absl import logging
from typing import NamedTuple


# Options for counters
class CounterOptions(NamedTuple):
    # Enable debug counters with additional suffixes.
    debug: bool = False
    # Emit counters once every 30 secs.
    show_every_n_sec: int = 30
    # Counter for processing stage
    process_stage: str = 'processing_stage'
    # Counter for records processed
    # used for computing processing rate.
    processed_counter: str = 'processed'
    # Counter for total inputs
    # Used for computing remaining time.
    total_counter: str = 'total'


class Counters():
    '''Dictionary of named counters.

    Example usage:
      counters = Counters(prefix='my_process')
      ...
      counters.add_counter('input_rows')
         .add_counter('output_rows', 10)
      counters.add_counter('processed', 1)

      # Min/Max counters
      counters.min_counter('min_area', some_area)
      counters.max_counter('max_temp', some_temp)

      # Print counters on STDERR
      counters.print_counters()
      #   my_process_input_rows = 1
      #  my_process_output_rows = 10
      #     my_process_max_temp = 36.5
      #     my_process_min_area = 12.34

    Note: This object is not thread-safe.
    '''

    def __init__(self,
                 counters_dict: dict = None,
                 prefix: str = '',
                 options: CounterOptions = None):
        '''Initialize the counters.

        Args:
          counters_dict: dictionary of pre-existing counters to updated.
            Note that it updates existing reference to counters.
          debug: Enable or disable debug context counters.
          options: Dictionary with parameter:values.
        '''
        if counters_dict is None:
            self._counters = {}
        else:
            self._counters = counters_dict
        self._prefix = prefix
        if options:
            self._options = options
        else:
            self._options = CounterOptions()

        # Internal state
        # Start time for rate counters.
        self.reset_start_time()
        self._next_counter_print_time = 0

    def __del__(self):
        '''Log the counters.'''
        self._update_processing_rate()
        logging.info(self.get_counters_string())

    def add_counter(self,
                    counter_name: str,
                    value: int = 1,
                    debug_context: str = None):
        '''Increment a named counter and degun counter by the given value.
        Also displays counters periodically based on option 'show_every_n_sec'.

        Args:
            name: Name of the counter to update
            value: value to be added to the counter
            debug_context: optional suffix for the debug counter.

        Returns:
          this Counters object
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
          counters_dict: dictionary of counter values.

        Returns:
          this Counters object
        '''
        if counters_dict:
            for counter, value in counters_dict.items():
                self.add_counter(counter, value)
        return self

    def set_counter(self, name: str, value: int, debug_context: str = None):
        '''Set the value of a counter overwriting any previous value.

        Args:
          name: Name of the counter to set.
          value: counter value to set it to.
          debug_context: Debug context for the counter.

        Returns:
          this Counters object
        '''
        self._counters[self._get_counter_name(name)] = value
        if debug_context:
            self._counters[self._get_counter_name(name, debug_context)] = value
        return self

    def get_counters(self) -> dict:
        '''Return the dictionary of all counter:values.'''
        return self._counters

    def get_counter(self, name: str) -> int:
        '''Return the value of a named counter.

        Args:
          name: Name of the counter to lookup.

        Returns:
          value if the counter if it exists, 0 otherwise.
        '''
        return self._counters.get(self._get_counter_name(name), 0)

    def min_counter(self, name: str, value: int, debug_context: str = None):
        '''Sets the named counter to the minimum of value.

        Args:
          name: name of the counter
          value: new value to consider for minimum.
          debug_context: Debug context suffix for the counter.
        Returns:
          this counter object
        '''
        if value <= self._counters.get(self._get_counter_name(name), value):
            self.set_counter(name, value, debug_context)
        return self

    def max_counter(self, name: str, value: int, debug_context: str = None):
        '''Sets the named counter to the maximum of values passed in.

        Args:
          name: name of the counter
          value: new value to consider for maximum.
          debug_context: Debug context suffix for the counter.
        Returns:
          this counter object
        '''
        if value >= self._counters.get(self._get_counter_name(name), value):
            self.set_counter(name, value, debug_context)
        return self

    def get_counters_string(self) -> str:
        '''Returns a formatted string of counter and values sorted by name.'''
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

    def print_counters(self, file=sys.stderr):
        '''Print the counter values.
        If a file is specified, emits the counters to the file.
        If no file is specified, displays on error console.

        Args:
            file: file handle to emit counters string.
        '''
        self._update_processing_rate()
        print(self.get_counters_string(), file=file)

    def print_counters_periodically(self):
        '''Display the counters periodically by time or by number of calls
        based on the option 'show_counters_every_sec' or 'show_counters_every_n'.
        '''
        interval = self._options.show_every_n_sec
        if interval > 0:
            curr_time = time.perf_counter()
            if curr_time > self._next_counter_print_time:
                self._next_counter_print_time = curr_time + interval
                self.print_counters()

    def reset_start_time(self):
        '''Reset process start time for rate counters.'''
        self.set_counter('start_time', time.perf_counter())
        self.set_counter(self._options.processed_counter, 0)

    def set_prefix(self, prefix: str):
        '''Set the prefix for the counter names.
        Also resets the start_time and processing rate counters.'''
        self._update_processing_rate()
        self._prefix = prefix
        self.reset_start_time()
        logging.info(self.get_counters_string())

    def get_prefix(self) -> str:
        '''Returns the counter prefix.'''
        return self._prefix

    # Internal functions
    def _get_counter_name(self, name: str, debug_context: str = None):
        '''Returns the name of the counter with debug context.'''
        name = f'{self._prefix}{name}'
        if debug_context:
            name = name + f'_{debug_context}'
        return name

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
