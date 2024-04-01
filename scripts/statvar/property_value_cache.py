# Copyright 2023 Google LLC
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
"""Class to store set of property:value for multiple keys.

The values are stored as a dict with any selected property such as dcid as the
key. The cache is persisted in a file.
"""

import csv
import os
import sys
import unicodedata

from absl import app
from absl import flags
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

import file_util
from counters import Counters


class PropertyValueCache:
    """Class to store property:values for a key.

  It allows lookup for an entry by any of the values for a set of key
  properties. The entries are loaded from a file and persisted in the file after
  updates.
  """

    def __init__(
        self,
        filename: str = '',
        key_props: list = ['key', 'name', 'dcid', 'placeId'],
        props: list = [],
        normalize_key: bool = True,
        counters: Counters = None,
    ):
        self._filename = filename
        self._normalize_key = normalize_key
        # List of properties that can be used as keys.
        # Each values for the keys are assumed to be unique across entries.
        self._key_props = []
        # Mapping from a key property to entry in the _entries list
        # { '<key-prop1>' : { '<prop-value1>': { <entry1> },
        #                    '<prop-value2>': { <entry2> }
        #                    ...},
        #   '<key-prop2>': { '<prop-value2> : { <entry1> } ,... }
        # }
        self._prop_key_map = {}

        if not self._key_props:
            self._key_props = []
        self._counters = counters
        if counters is None:
            self._counters = Counters()

        # List of entries, each with a dict of property:values in the cache
        self._entries = []

        # List of properties across all entries
        self._props = []
        self.add_props(key_props=key_props, props=props)

        # Load entries from file.
        self.load_cache_file(filename)
        # Flag to indicate cache has been updated and has changed from file.
        self._is_modified = False

    def __del__(self):
        self.save_cache_file()

    def load_cache_file(self, filename: str):
        """Load entries of property:value dicts from files."""
        for file in file_util.file_get_matching(filename):
            with file_util.FileIO(filename) as csv_file:
                csv_reader = csv.DictReader(csv_file)
                # Add columns as properties in order of input.
                self.add_props(props=csv_reader.fieldnames)

                # Add an entry for each row in the file.
                num_rows = 0
                for row in csv_reader:
                    num_rows += 1
                    self.add(row)
            logging.info(
                f'Loaded {num_rows} with columns: {self._props} from {filename} into'
                ' cache')

    def get_entry(self, value: str, prop: str = '') -> dict:
        """Returns an entry for the prop:value.

    prop should be one of the _key_props to be indexed.
    """
        if isinstance(value, list):
            logging.error(f'Cannot lookup {value} for {prop}')
        if not prop or prop not in self._key_props:
            # Property is not a key property
            # Lookup value in map for all key properties.
            for prop in self._key_props:
                entry = self.get_prop_key_entry(prop, value)
                if entry:
                    return entry
        return self.get_prop_key_entry(prop, value)

    def get_entry_for_dict(self, pvs: dict) -> dict:
        """Return the entry for the pvs in the dict."""
        for prop in self._key_props:
            value = pvs.get(prop, None)
            if value:
                cached_entry = self.get_entry(prop=prop, value=value)
                if cached_entry:
                    return cached_entry

    def add(self, entry: dict) -> dict:
        self.add_props(props=entry.keys())
        # Check if an entry exists, matching any of the key prop:value.
        cached_entry = None
        for prop in self._key_props:
            if prop in entry:
                cached_entry = self.get_entry(prop=prop, value=entry[prop])
                if cached_entry:
                    break

        if cached_entry:
            # Merge new PVs into the existing entry
            self.update_entry(entry, cached_entry)
            entry = cached_entry
        else:
            # Add a new entry
            self._entries.append(entry)

        # Add entry to the lookup maps for all keys.
        for prop in self._key_props:
            values = entry.get(prop, None)
            if values:
                # Add the entry to the lookup index with each of the values
                # for key property.
                if not isinstance(values, list):
                    values = [values]
                for value in values:
                    self.add_prop_key_entry(prop, value, entry)
                self._is_modified = True
        logging.level_debug() and logging.debug(f'Added cache entry {entry}')
        return entry

    def update_entry(self, src: dict, dst: dict):
        """Add PVs from src to dst.

    If a property exists with a value, add new values to a list.
    """
        for prop, values in src.items():
            if not values:
                continue
            # Add new values to list of existing values.
            dst_value = dst.get(prop, None)
            if dst_value:
                value_added = False
                dst_value = _get_value_list(dst_value)
                values = _get_value_list(values)
                for value in values:
                    if value not in dst_value:
                        dst_value.append(value)
                        value_added = True
                if value_added:
                    # New values were added.
                    dst[prop] = dst_value
                    self._is_modified = True
            else:
                # Add the new prop:value to dst dict
                dst[prop] = values
                self._is_modified = True
        logging.level_debug() and logging.debug(f'Merged {src} into {dst}')
        return dst

    def save_cache_file(self):
        if not self._is_modified:
            # No change in cache. Skip writing to file.
            return
        # Get the cache filename.
        # Save cache to the last file loaded in case of multiple files.
        filename = file_util.file_get_matching(self._filename)
        if filename:
            filename = filename[-1]
        else:
            filename = self._filename

        if not filename:
            return

        logging.info(f'Writing {len(self._entries)} cache entries with columns'
                     f' {self._props} into file {filename}')
        with file_util.FileIO(filename, mode='w') as cache_file:
            csv_writer = csv.DictWriter(
                cache_file,
                fieldnames=self._props,
                escapechar='\\',
                quotechar='"',
                quoting=csv.QUOTE_NONNUMERIC,
                extrasaction='ignore',
            )
            csv_writer.writeheader()
            for entry in self._entries:
                # Flatten key properties with multiple values to
                # rows with one value per property.
                for pvs in flatten_dict(entry, self._key_props):
                    csv_writer.writerow(pvs)
        self._is_modified = False

    def add_props(self, key_props: list = [], props: list = []):
        # Add any new key property.
        if key_props:
            for prop in key_props:
                if prop not in self._key_props:
                    self._key_props.append(prop)
                    self._prop_key_map[prop] = {}
                if prop not in self._props:
                    self._props.append(prop)

        # Add remaining properties across entries.
        if props:
            for prop in props:
                if prop not in self._props:
                    self._props.append(prop)
        if not self._key_props and self._props:
            # No key properties set. Use the first property as key.
            self._key_props.append(self._props[1])

    def is_dirty(self):
        return self._is_modified

    def add_prop_key_entry(self, prop: str, key: str, entry: dict):
        """Adds the entry to the lookup map for property with the key."""
        if self._normalize_key:
            key = _normalize_string(key)
        self._prop_key_map[prop][key] = entry

    def get_prop_key_entry(self, prop: str, key: str) -> dict:
        """Returns the entry for the key in the lookup map for prop."""
        if self._normalize_key:
            key = _normalize_string(key)
        return self._prop_key_map.get(prop, {}).get(key, {})


def flatten_dict(pvs: dict, props: list) -> list:
    """Returns a list of dicts, flattening out props with multiple values."""
    # Get dictionary with prop:value not to be flattend
    base_pvs = {}
    for prop, value in pvs.items():
        if prop not in props:
            if isinstance(value, list) or isinstance(value, set):
                base_pvs[prop] = ','.join([str(v) for v in value])
            else:
                base_pvs[prop] = value

    # List of dicts with expanded prop:values
    pvs_list = [base_pvs]
    for prop in props:
        values = pvs.get(prop, '')
        if not values:
            continue
        if not isinstance(values, list) and not isinstance(values, set):
            values = [values]
        list_with_prop = []
        for value in values:
            for item in pvs_list:
                pvs_with_prop = {prop: value}
                pvs_with_prop.update(item)
                list_with_prop.append(pvs_with_prop)
        pvs_list = list_with_prop
    return pvs_list


def _get_value_list(values: str) -> list:
    """Returns a list of unique values from a comma separated string."""
    if not values:
        return []
    values_list = []
    if isinstance(values, str):
        values = values.split(',')
    if not isinstance(values, list) and not isinstance(values, set):
        values = [values]
    for value in values:
        if value not in values_list:
            values_list.append(value)
    return values_list


def _normalize_string(key: str) -> str:
    """Returns a normalized string removing special characters"""
    if not isinstance(key, str):
        key = str(key)
    normalized_key = unicodedata.normalize('NFKD', key)
    normalized_key = normalized_key.lower()
    # Remove extra spaces
    normalized_key = ' '.join([w for w in normalized_key.split(' ') if w])
    # Remove extra punctuation.
    normalized_key = ''.join(
        [c for c in normalized_key if c.isalnum() or c == ' '])
    return normalized_key
