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
'''Class for python dictionary persisted in a file.'''

import os
import csv
import sys

from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

from config_map import ConfigMap
from counters import Counters


class CacheDict:
    '''Python dictionary persisted as a file.

  The dictionary is stored as a key to an ordered list,
  with each index in the list corresponding to a specific property for the entry:
  {
    <key>: [<value1>, <value2> ..]
  }
  This saves space for dense dictionaries.

  The dictionary is loaded from a file when the object is created
  and saved back into the file when it is destroyed if it was modified.
  '''

    def __init__(self, filename: str, config_dict: dict = {}, counters=None):
        self._config = ConfigMap(config_dict=config_dict)
        self._counters = counters
        if not self._counters:
            self._counters = Counters()
        self._filename = filename
        self._key_column = self._config.get('cache_key_column', None)
        # list of properties per entry
        self._entry_props = []
        # dictionary of property name to index.
        self._prop_index = {}
        # Dictionary of key to values-list
        self._dict = {}
        self.load_file(filename)
        self._is_modified = False

    def __del__(self):
        if self._is_modified:
            self.save_to_file(self._filename)

    def add_key_values(self, key: str, prop_values: dict = {}):
        '''Add property:values for a key.'''
        for prop, value in prop_values.items():
            self.set(key, prop, value)

    def get(self, key: str, prop: str = None, default: str = None) -> str:
        '''Returns the value of the property for a key.
      Args:
        key: string key to lookup
        prop: string property value.
          if None, the first value is returned.
        default_value:
          value returned if the key or the property for the key is missing
      Returns:
        value for the property for the key or the default value.
      '''
        entry = self._dict.get(key, None)
        if not entry:
            # Key is not present
            self._counters.add_counter(f'cache-miss-key', 1)
            return default

        prop_index = self._get_property_index(prop)
        if prop_index is None or prop_index >= len(entry):
            # Property for the key is not present
            self._counters.add_counter(f'cache-miss-{prop}', 1)
            return default

        self._counters.add_counter(f'cache-hit-{prop}', 1)
        return entry[prop_index]

    def get_entry(self, key: str) -> dict:
        '''Returns a dictionary with property:values for the entry.'''
        entry_dict = {}
        entry_row = self._dict.get(key, None)
        if entry_row:
            for index in range(len(entry_row)):
                prop = self._get_property_for_index(index)
                entry_dict[prop] = entry_row[index]
        return entry_dict

    def set(self, key: str, prop: str, value: str):
        '''Sets the value for a property for a key.'''
        entry = self._dict.get(key, None)
        if not entry:
            entry = [None] * len(self._entry_props)
            self._dict[key] = entry
            self._is_modified = True

        # Get the index for the property, create one if needed.
        prop_index = self._add_property_index(prop)

        # Append empty values until entry has values for all properties
        for index in range(prop_index, len(self._entry_props)):
            entry.append('')

        # Set the value for the entry property
        entry[prop_index] = value
        self._is_modified = True

    def load_file(self, filename: str) -> bool:
        if not os.path.exists(filename):
            logging.info(f'Skipping non-existant file: {filename}')
            return False

        with open(filename) as csvfile:
            reader = csv.DictReader(csvfile)
            if not self._key_column:
                self._key_column = reader.fieldnames[0]
            for row in reader:
                key = ''
                if self._key_column in row:
                    key = row.pop(self._key_column)
                self.add_key_values(key, row)
            logging.info(
                f'Loaded {len(self._dict)} entries with properties: {self._entry_props} from {filename}'
            )
            self._is_modified = False
            return True

    def save_to_file(self, filename: str):
        if not filename:
            filename = self._filename
        dirname = os.path.dirname(filename)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        columns = [self._key_column]
        columns.extend(self._entry_props)
        with open(filename, 'w') as csvfile:
            csv_writer = csv.DictWriter(csvfile,
                                        escapechar='\\',
                                        fieldnames=columns,
                                        quotechar='"',
                                        quoting=csv.QUOTE_NONNUMERIC)
            csv_writer.writeheader()
            for key in self._dict.keys():
                row = self.get_entry(key)
                if row:
                    csv_writer.writerow(row)
        logging.info(
            f'Wrote {len(self._dict)} rows with columns:{columns} into {filename}'
        )
        self._is_modified = False

    def _get_property_index(self, prop) -> int:
        return self._prop_index.get(prop, None)

    def _get_property_for_index(self, index: int) -> str:
        if index < len(self._entry_props):
            return self._entry_props[index]
        return ''

    def _add_property_index(self, prop: str) -> int:
        prop_index = self._get_property_index(prop)
        if prop_index is not None:
            # Use existing property index.
            return prop_index

        # Add a new property to the list or properties.
        prop_index = len(self._entry_props)
        self._entry_props.append(prop)
        self._prop_index[prop] = prop_index

        return prop_index
