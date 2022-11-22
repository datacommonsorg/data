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
'''Class for named counters.'''

import sys

from absl import logging

class Counters():
    '''Dictionary of named counters.'''

    def __init__(self,
                 counters_dict: dict = None,
                 debug: bool = False,
                 config_dict: dict = None):
        '''Initialize the counters.
        Args:
          counters_dict: dictionary of pre-existing counters to load.
          debug: Enable or disable debug context counters.
          config_dict: Dictionary with config parameter:values.
        '''
        self._counters = counters_dict
        self._debug = debug
        if counters_dict is None:
            self._counters = {}
        self._counter_config = config_dict
        if config_dict is None:
            self._counter_config = {}
        # Parameters to show counters periodically.
        self._num_calls = 0
        self._show_counters_every_n = self._counter_config.get(
            'show_counters_every_n', 0)
        self._show_counters_every_secs = self._counter_config.get(
            'show_counters_every_sec', 0)

    def _get_debug_counter(self, name: str, debug_context: str):
        '''Returns the name of the counter with debug context.'''
        return f'{name}-{debug_context}'

    def add_counter(self,
                    name: str,
                    value: int = 1,
                    debug_context: str = None) -> int:
        '''Increment a named counter by the given value.
        Args:
            name: Name of the counter to update
            value: value to be added to the counter
            context: debug string added to the counter.
        Returns:
          current value of the counter after update.
        '''
        self._counters[name] = self._counters.get(name, 0) + value
        if self._debug and debug_context:
            # Add debug counter with the context message.
            ext_name = self._get_debug_counter(name, debug_context)
            self._counters[ext_name] = self._counters.get(ext_name, 0) + value
        # Diplay all counters if required.
        self.show_counters_periodically()
        return self._counters[name]

    def add_counters(self, counters_dict: dict) -> dict:
        '''Add all counters from the given dict.
        Args:
          counters_dict: dictionary of counter values.
        Returns:
          dictionary with all counter:values.
        '''
        if counters_dict:
            for counter, value in counters_dict.items():
                self.add_counter(counter, value)
        return self._counters

    def set_counter(self,
                    name: str,
                    value: int,
                    debug_context: str = None) -> int:
        '''Set the value of a counter overwriting any previous value.
        Args:
          name: Name of the counter to set.
          value: counter value to set it to.
          debug_context: Debug context for the counter.
        '''
        self._counters[name] = 0
        if debug_context:
            self._counters[self._get_debug_counter(name, debug_context)] = 0
        self.add_counter(name, value, debug_context)

    def get_counters(self) -> dict:
        '''Return the dictionary of all counter:values.'''
        return self._counters

    def get_counter(self, name: str) -> int:
        '''Return the value of a counter.
        Args:
          name: Name of the counter to lookup.
        Returns:
          value if the counter if it exists, 0 otherwise.
        '''
        return self._counters.get(name, 0)

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
        print(self.get_counters_string(), file=file)

    def show_counters_periodically(self):
        '''Show the counters periodically by time or by number of calls
        based on the config 'show_counters_every_sec' or 'show_counters_every_n'.
        '''
        self._num_calls += 1
        if self._show_counters_every_n > 0 and (self._num_calls %
                                                self._show_counters_every_n):
            self.print_counters()
        else:
            if self._show_counters_every_secs and (
                    time.perf_counter() -
                    self._last_display_time) > self._show_counters_every_secs:
                self.print_counters()
                self._last_display_time = time.perf_counter()

    def log_counters(self):
        logging.info(self.get_counters_string())
