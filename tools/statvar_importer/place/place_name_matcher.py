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
"""Script to lookup places by names.
Uses the ngram_matcher to search for names by substring matches.

Download all place properties in the KG with the dcid using BQ:
  EXPORT DATA
   OPTIONS (
      uri = 'gs://unresolved_mcf/places/$place_type/$date/${place_type}_shard_*.csv',
      format = 'CSV',
      overwrite = true,
      header = true,
      field_delimiter = ',')
  AS (
    SELECT
      id as dcid,
      type as typeOf,
      name,
      alternate_name,
      latitude,
      longitude,
      ARRAY_TO_STRING(linked_contained_in_place, ',') as containedInPlace
    FROM \`datcom-store.dc_kg_latest.Place\`
    WHERE SUBSTRING(id, 4) not in ('ipcc', 'grid', 's2Ce')
  )

Use place_name_matcher as follows:
  import place_name_matcher

  matcher = PlaceNameMatcher(<places.csv>)

  results = matcher.lookup(<place-name>)
  # Results is list of tuples: [(<name>, <dcid>)...]

To resolve places in a csv file on command line:
  python3 place_name_matcher.py --input_csv=<csv-file> \
      --place_output_csv=resolved-places.csv \
      --place_csv=<place-csv> \
  where:
    <place-csv> contains place dcids with columns for properties like typeOf, containedInPlace
    <csv-file> has input data with a column 'name' to be resolved to a place dcid
"""

import ast
import csv
import glob
import itertools
import os
import sys

from absl import app
from absl import flags
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(_SCRIPT_DIR))),
                 'util'))

from counters import Counters
import file_util
from ngram_matcher import NgramMatcher

flags.DEFINE_string('input_csv', '',
                    'CSV file with names of places to resolve.')
flags.DEFINE_string('input_name_column', 'name',
                    'CSV column for names in the input_csv.')
flags.DEFINE_list(
    'place_within',
    '',
    'Comma separated list of parent places, eg: country/BRA.',
)
flags.DEFINE_string('ngram_matcher_config', '',
                    'Configuration settings for ngram matcher.')
flags.DEFINE_list('lookup_names', '',
                  'Comma separated list of places to lookup.')
flags.DEFINE_string('place_output_csv', '',
                    'Output CSV with place dcids added.')
flags.DEFINE_string('place_csv', '',
                    'CSV file with place names and dcids to match.')

_FLAGS = flags.FLAGS

_DEFAULT_CONFIG = {
    # Ordered list of parent places
    'parent_place_types': [
        'Country',
        'State',
        'AdministrativeArea',
        'AdministrativeArea1',
        'EurostatNUTS1',
        'District',
        'AdministrativeArea2',
        'EurostatNUTS2',
        'County',
        'AdministrativeArea3',
        'EurostatNUTS3',
        'AdministrativeArea4',
        'AdministrativeArea5',
        'City',
        'Village',
        'Place',
        'Neighborhood',
    ],
    'ngram_size': 4,
    'ignore_non_alphanum': True,
    'min_match_fraction': 0.1,
    'num_results': 10,
}


class PlaceNameMatcher:

    def __init__(self,
                 place_file: str = '',
                 places_within: list = [],
                 config: dict = {}):
        self._config = dict(_DEFAULT_CONFIG)
        if config:
            self._config.update(config)
        logging.info(f'Setting up PlaceNameMatcher with config: {self._config}')

        # Dictionary of place dcid to set of property-values
        # { 'country/IND': {
        #   'typeOf': 'Country',
        #   'name': 'India',
        #   'containedInPlace': 'asia,Earth' ...}
        # }
        self._places_dict = dict()
        place_files = [place_file]
        place_files.extend(
            file_util.file_get_matching(self._config.get('places_csv', [])))
        places_within.extend(self._config.get('places_within', []))
        self._load_places_dict(place_files, places_within)

        # Load the ngrams for place names into the matcher.
        self._setup_name_matcher()
        self._log_every_n = self._config.get('log_every_n', 10)

    def _load_places_dict(self, place_csv: str, places_within: list):
        """Add place names from csv to the name matcher."""
        for file in file_util.file_get_matching(place_csv):
            # Load large place files only when places_within is set.
            file_size = file_util.file_get_size(file)
            if file_size > self._config.get('max_places_csv_file_size',
                                            10000000):
                if not places_within:
                    logging.warning(
                        f'Skip places file: {file} with size: {file_size} as'
                        ' places_within not set')
                    continue
            places_dict = file_util.file_load_csv_dict(file, key_column='dcid')
            places_filter = set(places_within)
            for dcid, pvs in places_dict.items():
                # Check if the place is within places of interest
                if places_filter:
                    parentids = set(pvs.get('containedInPlace', '').split(','))
                    if not parentids.intersection(places_filter):
                        continue
                if dcid in self._places_dict:
                    self._places_dict[dcid].update(pvs)
                else:
                    self._places_dict[dcid] = pvs
        logging.info(
            f'Loaded {len(self._places_dict)} places from {place_csv} within'
            f' {places_within}')

    def _setup_name_matcher(self):
        """Add the place names to the ngram matcher."""
        count = 0
        self._ngram_matcher = NgramMatcher(self._config)
        for place_dcid, pvs in self._places_dict.items():
            place_names = self._get_full_place_names(place_dcid)
            for place_name in place_names:
                self._ngram_matcher.add_key_value(place_name, place_dcid)
                count += 1
        num_ngrams = self._ngram_matcher.get_ngrams_count()
        logging.info(
            f'Loaded {count} names into ngram matcher with {num_ngrams} ngrams')

    def get_place_value(self,
                        place_dcid: str,
                        prop: str,
                        default: str = '') -> str:
        """Returns the property for the place id."""
        return self._places_dict.get(place_dcid, {}).get(prop, default)

    def lookup(
        self,
        place_name: str,
        num_results: int = None,
        property_filters: dict = {},
    ) -> list:
        """Returns dcids that match the place name."""
        if num_results is None:
            num_results = self._config.get('num_results', 10)
        matches = self._ngram_matcher.lookup(key=place_name,
                                             num_results=num_results,
                                             config=self._config)
        logging.log_every_n(
            logging.DEBUG,
            f'Got {len(matches)} lookup results for {place_name}: {matches}',
            self._log_every_n)
        # Filter results for matching properties such as typeOf.
        if not property_filters:
            property_filters = self._config.get('match_filters', None)
        if property_filters:
            filtered_matches = []
            for name, dcid in matches:
                for prop, values in property_filters.items():
                    place_values = self.get_place_value(dcid, prop)
                    for value in values:
                        if value in place_values:
                            filtered_matches.append((name, dcid))
                            break
            matches = filtered_matches

        # Get unique dcids.
        dcids = set()
        unique_matches = []
        for name, dcid in matches:
            if dcid not in dcids:
                unique_matches.append((name, dcid))
                dcids.add(dcid)
        matches = unique_matches
        logging.log_every_n(
            logging.DEBUG,
            f'Got {len(matches)} matches for {place_name} with {property_filters}:'
            f' {matches}', self._log_every_n)
        return matches

    def process_csv(self, input_csv: str, name_column: str, output_csv: str):
        counters = Counters()
        with file_util.FileIO(output_csv, mode='w') as csv_output:
            csv_writer = csv.writer(csv_output)
            # Process each input file
            files = file_util.file_get_matching(input_csv)
            for file in files:
                counters.add_counter('total',
                                     file_util.file_estimate_num_rows(file))
            for file in files:
                logging.log_every_n(logging.INFO,
                                    f'Looking up dcids for places in {file}',
                                    self._log_every_n)
                with file_util.FileIO(file) as csvfile:
                    csv_reader = csv.reader(
                        csvfile,
                        **file_util.file_get_csv_reader_options(csvfile))
                    name_column_index = None
                    num_results = self._config.get('num_results', 10)
                    for row in csv_reader:
                        if name_column_index is None:
                            # Add header
                            name_column_index = row.index(name_column)
                            row.append('dcid')
                            row.append('place-name')
                            row.append('typeOf')
                            for i in range(1, num_results):
                                row.append(f'dcid-{i}')
                                row.append(f'place-name-{i}')
                                row.append(f'typeOf-{i}')
                            csv_writer.writerow(row)
                            continue
                        # Lookup name for each row.
                        place_name = row[name_column_index]
                        if place_name:
                            matches = self.lookup(place_name, num_results)
                            if matches:
                                for key, place_dcid in matches:
                                    place_type = self.get_place_value(
                                        place_dcid,
                                        'typeOf',
                                    )
                                    row.append(place_dcid)
                                    row.append(key)
                                    row.append(place_type)
                                logging.log_every_n(
                                    logging.DEBUG,
                                    f'Found matches for {row}: {matches}',
                                    self._log_every_n)
                                counters.add_counter('places_resolved', 1)
                            else:
                                counters.add_counter('places_not_resolved', 1)
                        csv_writer.writerow(row)
                        counters.add_counter('processed', 1)
        counters.print_counters()

    def get_parent_places(self, dcid: str) -> list:
        """Returns the list of containedInPlace parents."""
        place_values = self._places_dict.get(dcid, {})
        if not place_values:
            return None
        contained_places = place_values.get('containedInPlace', '').split(',')
        # Get the place type for all parents.
        parent_types = {}
        for parentid in contained_places:
            parent_type = self.get_place_value(parentid, 'typeOf').split(',')
            parent_types[parentid] = parent_type
        # Get the parents ordered by type
        ordered_parents = []
        for parent_type in self._config.get('parent_place_types'):
            for parentid in list(parent_types.keys()):
                if parent_type in parent_types[parentid]:
                    ordered_parents.append(parentid)
                    parent_types.pop(parentid)
                    break
        return reversed(ordered_parents)

    def _get_place_names(self, dcid: str) -> list:
        """Returns the list of names of the dcid."""
        place_values = self._places_dict.get(dcid, {})
        if not place_values:
            return []
        name_properties = self._config.get(
            'name_properties', ['name', 'alternate_name', 'description'])
        place_names = []
        for name_property in name_properties:
            name = place_values.get(name_property, '')
            name = name.strip()
            if name:
                place_names.append(name)
        return place_names

    def _get_full_place_names(self, dcid: str) -> list:
        """Get the full place name for the id with parent places appended."""
        # List of list of names for each name component in contained in order.
        full_names = []
        place_names = self._get_place_names(dcid)
        if not place_names:
            # Skip parents names if place doesn't have a name.
            return []
        full_names.append(place_names)
        parent_places = self.get_parent_places(dcid)
        parent_names = []
        for parentid in parent_places:
            parent_names = self._get_place_names(parentid)
            if parent_names:
                full_names.append(parent_names)
        full_place_names = [' '.join(n) for n in itertools.product(*full_names)]
        if self._config.get('use_place_names', True):
            full_place_names.extend(place_names)
        return full_place_names


def main(_):
    config = {}
    if _FLAGS.ngram_matcher_config:
        config = ast.literal_eval(_FLAGS.ngram_matcher_config)
    place_name_matcher = PlaceNameMatcher(_FLAGS.place_csv, _FLAGS.place_within,
                                          config)
    if _FLAGS.input_csv:
        place_name_matcher.process_csv(
            input_csv=_FLAGS.input_csv,
            name_column=_FLAGS.input_name_column,
            output_csv=_FLAGS.place_output_csv,
        )
    for name in _FLAGS.lookup_names:
        results = place_name_matcher.lookup(name)
        print(f'query: "{name}", matches: {results}')


if __name__ == '__main__':
    app.run(main)
