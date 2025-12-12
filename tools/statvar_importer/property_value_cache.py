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
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

import file_util
from mcf_file_util import add_pv_to_node
from counters import Counters

# Indexed properties in order for lookup.
_DEFAULT_KEY_PROPS = [
    'key',
    'dcid',
    'placeId',
    'wikidataId',
    'name',
    'place_name',
]


class PropertyValueCache:
    """Class to store property:values for a key.

  It allows lookup for an entry by any of the values for a set of key
  properties. The entries are loaded from a file and persisted in the file after
  updates.

  Example usage:
    pv_cache = PropertyValueCache('/tmp/pv-cache.csv',
                                  key_props=['name', 'dcid', 'isoCode'],
                                  normalize_key=True)

   # Add an entry to cache
   pv_cache.add( {
                   'dcid': 'country/IND',
                   'typeOf': 'Country',
                   'name': 'India',
                   'isoCode': 'IND'
                 })

   # Lookup above entry by any value of a property
   india_entry = pv_cache.get_entry(prop='isoCode', value='IND')
   # Lookup by value of any key property
   india_entry = pv_cache.get_entry('india')
  """

    def __init__(
        self,
        filename: str = '',
        key_props: list = _DEFAULT_KEY_PROPS,
        props: list = [],
        normalize_key: bool = True,
        counters: Counters = None,
    ):
        """Initialize the PropertyValueCache.

        Args:
          filename: CSV file with one row per cache entry with
            properties as columns.
            The entries in the file are loaded on init and
            saved periodically and on exit.
          key_props: list of properties that can be used for lookup.
            The values of these properties are assumed to be unique and
            values are stored in an index per property for lookup by value.
          props: List of properties across entries.
          normalize_key: if True, values are normalized (lower case)
            before lookup in the per-property index.
          counters: Counters object for cache hits and misses.
        """
        self._filename = filename
        self._normalize_key = normalize_key
        self._log_every_n = 10

        # List of properties that can be used as keys.
        # Each values for the keys are assumed to be unique across entries.
        self._key_props = []

        # Index per key_property.
        # Mapping from a key property to entry in the _entries list
        # { '<key-prop1>': { '<prop-value1>': { <entry1> },
        #                    '<prop-value2>': { <entry2> }
        #                    ...},
        #   '<key-prop2>': { '<prop-value2> : { <entry1> } ,... }
        # }
        self._prop_index = {}

        if not self._key_props:
            self._key_props = []
        self._counters = counters
        if counters is None:
            self._counters = Counters()

        # List of cache entries, each with a dict of property:values
        # The property indexes have references to the entry
        self._entries = {}

        # List of properties across all entries
        self._props = []
        self._add_props(key_props=key_props, props=props)

        # Load entries from file.
        self.load_cache_file(filename)
        # Flag to indicate cache has been updated and has changed from file.
        self._is_modified = False

    def __del__(self):
        self.save_cache_file()

    def load_cache_file(self, filename: str):
        """Load entries of property:value dicts from files.

        Args:
          filename: CSV file(s) from which property:values are loaded
              with one row per entry.
        """
        for file in file_util.file_get_matching(filename):
            with file_util.FileIO(filename) as csv_file:
                csv_reader = csv.DictReader(csv_file)
                # Add columns as properties in order of input.
                self._add_props(props=csv_reader.fieldnames)

                # Add an entry for each row in the file.
                num_rows = 0
                for row in csv_reader:
                    num_rows += 1
                    self.add(row)
            logging.info(
                f'Loaded {num_rows} with columns: {self._props} from {filename} into'
                ' cache')

    def get_entry(self, value: str, prop: str = '') -> dict:
        """Returns a dict entry that contains the prop:value.

        Args:
          value: value to be looke dup in the property index
            If normalize_key was set in init(),
            value is converted to lower case string.
          prop:  One of the key-properties in which the value is looked up.
            If not set, value is looked up in all key properties in order.

        Returns:
          dict entry that contains the prop:value if it exists.
        """
        if isinstance(value, list):
            logging.log_every_n(logging.ERROR,
                                f'Cannot lookup {value} for {prop}',
                                self._log_every_n)
            return {}
        key = self.get_lookup_key(prop=prop, value=value)
        if not prop or prop not in self._key_props:
            # Property is not a key property
            # Lookup value in map for all key properties.
            for prop in self._key_props:
                entry = self._get_prop_key_entry(prop, key)
                if entry:
                    return entry
        return self._get_prop_key_entry(prop, key)

    def get_entry_for_dict(self, pvs: dict) -> dict:
        """Return the entry for the pvs in the dict.

        Args:
          pvs: dictionary with partial set of property:values.
             The values of any of the key properties is used to lookup.
        Returns:
          dict of cache entry that matches the first prop:value in pvs.
        """
        for prop in self._key_props:
            value = pvs.get(prop, None)
            if value is not None:
                cached_entry = self.get_entry(prop=prop, value=value)
                if cached_entry:
                    return cached_entry
        return {}

    def add(self, entry: dict) -> dict:
        """Add a dict of property:values into the cache.
           If the entry already exists for an existing key,
           the entry is merged with the new values.

        Args:
          entry: dict of property:values.
            The entry is cached and values and entry is also indexed
              by value of each key-property.

        Returns:
          dict that was added or merged into.
        """
        # Add any new properties
        self._add_props(props=entry.keys())

        # Check if an entry exists, matching any of the key prop:value.
        cached_entry = self.get_entry_for_dict(entry)
        if cached_entry:
            # Merge new PVs into the existing entry
            self.update_entry(entry, cached_entry)
            entry = cached_entry
        else:
            # Add a new entry
            cached_entry = dict(entry)
            self._entries[len(self._entries)] = cached_entry
            self._counters.add_counter('pv-cache-entries', 1)

        # Add entry to the lookup index for all key properties.
        for prop in self._key_props:
            values = entry.get(prop, None)
            if values is not None:
                # Add the entry to the lookup index with each of the values
                # for key property.
                if not isinstance(values, list):
                    values = [values]
                for value in values:
                    self._add_prop_key_entry(prop, value, entry)
        self._is_modified = True
        logging.level_debug() and logging.log_every_n(
            2, f'Added cache entry {cached_entry}', self._log_every_n)
        return cached_entry

    def update_entry(self, src: dict, dst: dict):
        """Add PVs from src to dst.

    If a property exists with a value, add new values to a list.
    """
        #for prop, values in src.items():
        #    add_pv_to_node(prop,
        #                   values,
        #                   dst,
        #                   append_value=True,
        #                   normalize=self._normalize_key)
        #return dst
        for prop, values in src.items():
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
            else:
                # Add the new prop:value to dst dict
                dst[prop] = values
                self._is_modified = True
        logging.level_debug() and logging.log_every_n(
            logging.DEBUG, f'Merged {src} into {dst}', self._log_every_n)
        return dst

    def save_cache_file(self):
        """Save the cache entries into the CSV file.

        File is only written into if cache has been modified
        by adding a new entry since the last write.
        """
        if not self.is_dirty():
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

        logging.log_every_n(
            logging.INFO,
            f'Writing {len(self._entries)} cache entries with columns'
            f' {self._props} into file {filename}', self._log_every_n)
        logging.log_every_n(logging.DEBUG,
                            f'Writing cache entries: {self._entries}',
                            self._log_every_n)
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
            for entry in self._entries.values():
                # Flatten key properties with multiple values to
                # rows with one value per property.
                for pvs in flatten_dict(entry, self._key_props):
                    logging.debug(f'Saving cache entry: {pvs}')
                    csv_writer.writerow(pvs)
        self._is_modified = False

    def is_dirty(self):
        """Returns True if the cache has been modified since the last write."""
        return self._is_modified

    def num_entries(self) -> int:
        """Returns the number of entries in the cache."""
        return len(self._entries)

    def normalize_string(self, key: str) -> str:
        """Returns a normalized string for lookup.
        The key has special characters removed and converted to lower case.

        Args:
          key: string to be normalized for lookup.
        Returns:
          normalized key
        """
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

    def get_lookup_key(self, value: str, prop: str = '') -> str:
        """Returns key for lookup, normalizing if needed.

        Args:
          value: string value to be looked up in the index.
             The value is notmalized if needed.
          prop: (optional) property for the value.

        Returns:
          string to be looked up in the property index
          which is value normalized if needed.
        """
        if isinstance(value, list):
            value = value[0]
        if self._normalize_key:
            return self.normalize_string(value)
        return value

    def _add_props(self, key_props: list = [], props: list = []):
        # Add any new key property.
        if key_props:
            for prop in key_props:
                if prop not in self._key_props:
                    self._key_props.append(prop)
                    self._prop_index[prop] = dict()
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

    def _add_prop_key_entry(self, prop: str, value: str, entry: dict) -> bool:
        """Adds the entry to the lookup map for property with the key."""
        if not value:
            return False
        key = self.get_lookup_key(prop=prop, value=value)
        prop_index = self._prop_index.get(prop)
        if prop_index is None:
            logging.log_every_n(logging.ERROR,
                                f'Invalid key prop {prop}:{key} for {entry}',
                                self._log_every_n)
            return False
        existing_entry = prop_index.get(key)
        if existing_entry and existing_entry.get(prop) != value:
            logging.log_every_n(
                logging.ERROR,
                f'Conflicting {prop}:{key} old:{existing_entry} new:{entry}',
                self._log_every_n)
        prop_index[key] = entry
        return True

    def _get_prop_key_entry(self, prop: str, key: str) -> dict:
        """Returns the entry for the key in the lookup map for prop."""
        entry = self._prop_index.get(prop, {}).get(key, {})
        if entry:
            self._counters.add_counter(f'pv-cache-hits-{prop}', 1)
        else:
            self._counters.add_counter(f'pv-cache-misses-{prop}', 1)
        return entry


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
