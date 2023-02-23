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
'''Class to resolve places to dcids.'''

import ast
import csv
import glob
import os
import pprint as pp
import sys
import time

from absl import app
from absl import flags
from absl import logging
from typing import Union

_FLAGS = flags.FLAGS

flags.DEFINE_string('maps_api_key', '', 'Google Maps API key')

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

from counters import Counters
from config_map import ConfigMap
from download_util import request_url
from dc_api_wrapper import dc_api_batched_wrapper, dc_api_resolve_placeid
from dc_api_wrapper import dc_api_resolve_latlng

# Google Maps API
# params used: &key=<>&address=<...>&components=country:<CC>|admin_area:<State>
_MAPS_URL = "https://maps.googleapis.com/maps/api/geocode/json"


class PlaceResolver:
    '''Class to resolve places to dcid.
  Uses maps API to get the place-id based on a name string:
    https://maps.googleapis.com/maps/api/geocode/json with params:
    key: Maps API key
    address: name to resolve
    components: hints to resolve that are:
      country: <2-letter country code>
      administrative_area: <state or district>

  This returns a place id that is resolved using the DC recon API:
    https://api.datacommons.org/v1/recon/resolve/id with the params:
      in_prop: 'placeId'
      out_prop: 'dcid'
      ids: list of ids to lookup
  '''

    def __init__(self,
                 maps_api_key: str = None,
                 config_dict: dict = {},
                 counters_dict: dict = None):
        self._maps_api_key = maps_api_key
        self._config = ConfigMap(config_dict)
        if not self._maps_api_key:
            self._maps_api_key = self._config.get('maps_api_key', '')
        self._counters = Counters(counters_dict)
        self._load_cache()

    def __del__(self):
        '''Save state into files.'''
        self._save_cache()

    def resolve_name(self, places: dict) -> dict:
        '''Returns a dictionary with dcid and placeId for each place.

         Args:
           places: dictionary of input places to lookup where
           each input place is a dictionary with the following keys:
             name: Name of the place to resolve.
             country: 2 letter country code or the country name
             administrative_area: state or district for the place.

         Returns:
           Dictionary with the following additional properties for each place:
             dcid: the data commons id for the place, if found
             placeId: the Google Maps place-id, if found.
              in case maps returns multiple places, the first one is used.
             lat: approximate latitude for the place
             lng: approximate longitude for the place
         '''
        logging.debug(f'Resolving places: {places}...')
        results = {}
        # Get the maps placeId for each place.
        for key, place in places.items():
            maps_result = self.get_maps_placeid(
                name=place.get('name', ''),
                country=place.get('country', None),
                admin_area=place.get('administrative_area', None))
            if maps_result:
                results[key] = maps_result

        # Collect all placeIds to be resolved that are not in cache.
        places_ids = {}
        for key, result in results.items():
            if 'placeId' in result:
                place_id = result['placeId']
                if place_id in self._place_cache:
                    # PlaceId is already resolved, use the cached result.
                    results[key]['dcid'] = self._place_cache[place_id]
                    self._counters.add_counter(
                        'dc-api-resolve-placeid-cache-hits', 1)
                else:
                    places_ids[result['placeId']] = key

        lookup_placeids = list(places_ids.keys())
        if lookup_placeids:
            # Resolve placeIds to dcids in a batch
            recon_resp = dc_api_batched_wrapper(
                function=dc_api_resolve_placeid,
                dcids=lookup_placeids,
                args={},
                config=self._config.get_configs())
            self._counters.add_counter('dc-api-resolve-placeid-lookups',
                                       len(lookup_placeids))
            self._counters.add_counter('dc-api-resolve-placeid-calls', 1)
            # Extract the dcid for each place from the response
            for place_id, dcid in recon_resp.items():
                key = places_ids.get(place_id, '')
                if place_id and dcid and key:
                    results[key]['dcid'] = dcid
                    # Cache the response for future requests.
                    self._set_cache_value(self._place_cache, place_id, dcid)
        logging.debug(f'Resolved place dcids: {results}')
        return results

    def resolve_latlng(self, places: dict) -> dict:
        '''Returns a dictionary with a list of dcids for each lat/lng.
        Resolve a set of places with latitude/longitude using the DC recon API:
        https://api.datacommons.org/v1/recon/resolve/coordinate.

        Args:
          places: dictionary with each key referring to a value dictionary
            that has the following keys:
            - latitude: latitude of the place in degrees.
            - longitude: longitude of the place in degrees.

        Returns:
        dictionary with input keys and value dictionary containing the following keys:
          - dcid: list of dcids for the location given by lat/lng.
        '''
        # Collect places not in cache to be resolved.
        results = {}
        resolve_places = []
        coords_to_key = {}
        for key, place in places.items():
            results[key] = dict(place)
            lat = place.get('latitude', '')
            lng = place.get('longitude', '')
            if lat and lng:
                place_key = self._get_cache_key([lat, lng])
                cached_place = self._get_cache_value(self._place_cache,
                                                     place_key)
                if cached_place:
                    self._counters.add_counter(
                        f'dc-api-resolve-latlng-cache-hits', 1)
                    results[key].update(cached_place)
                else:
                    resolve_places.append({
                        'latitude': lat,
                        'longitude': lng,
                    })
                    coords_to_key[place_key] = key
            else:
                logging.debug(f'Skipping empty lat/lng in {key}:{place}')

        # Resolve any remaining lat/lng places.
        resolved_place_ids = {}
        if resolve_places:
            logging.debug(
                f'Resolving {len(resolve_places)} lat/long places {resolve_places}'
            )
            self._counters.add_counter(f'dc-api-resolve-latlng-places',
                                       len(resolve_places))
            self._counters.add_counter(f'dc-api-resolve-latlng-calls', 1)
            resolved_place_ids = dc_api_batched_wrapper(
                function=dc_api_resolve_latlng,
                dcids=resolve_places,
                args={},
                config=self._config.gets())

        # Retrieve resolved dcids into results.
        if resolved_place_ids:
            for resolved_place in resolved_place_ids.values():
                place_key = self._get_cache_key(
                    [resolved_place['latitude'], resolved_place['longitude']])
                input_key = coords_to_key.get(place_key, '')
                dcids = resolved_place.get('placeDcids', '')
                self._set_cache_value(self._place_cache, place_key,
                                      resolved_place)
                if dcids and input_key in results:
                    results[input_key]['placeDcids'] = dcids
        logging.debug(f'Returning resolved latlngs {results}')
        return results

    def get_maps_placeid(self,
                         name: str,
                         country: str = None,
                         admin_area: str = '') -> dict:
        '''Returns the Google maps place-id for a place.
     It uses the Google Map API for address resolution with additional hints
     for country and admin_area, like state or district.

     Args:
       name: name to be resolved whcih can be an address with multiple words
       country: a 2 letter country code or country name.
       admin_area: the name of the administrative area to be used as hint
         when there could be multiple places with the same name.

     Returns:
       dictionary with attributes such as placeId, latitude, longitude.
     '''
        if not name:
            logging.debug(f'Unable to resolve maps place with empty name')
            return {}

        # Check if the place is in the maps cache.
        place_key = self._get_cache_key([name, country, admin_area])
        if place_key in self._maps_cache:
            self._counters.add_counter('maps-cache-hits', 1)
            return self._maps_cache[place_key]

        # Lookup Google Maps API.
        if not self._maps_api_key:
            logging.error(
                f'No maps key. Please set --maps_api_key for place lookup.')
        params = {
            'key': self._maps_api_key,
            'address': f'{name}',
        }
        components = []
        if country:
            components.append(f'country:{country}')
        if admin_area:
            components.append(f'administrative_area:{admin_area}')
        if components:
            params['components'] = '|'.join(components)
        self._counters.add_counter('maps-api-geocode-lookups', 1)
        resp_json = request_url(url=_MAPS_URL, params=params, output='json')
        if resp_json:
            # Get placeid from the response.
            logging.debug(f'Got Maps results: {resp_json}')
            result = {}
            if 'results' in resp_json:
                results = resp_json['results']
                if len(results) > 0:
                    # Get the place id
                    first_result = results[0]
                    if 'place_id' in first_result:
                        result['placeId'] = first_result['place_id']
                    # Get the lat/lng location
                    if 'geometry' in first_result:
                        if 'location' in first_result['geometry']:
                            result.update(first_result['geometry']['location'])
            # Cache the response
            self._maps_cache[place_key] = result
            self._save_cache(self._config.get('cache_save_interval', 30))
            return result

        return None

    def _get_cache_key(self, items: list) -> str:
        '''Returns a key for the place lookup in the maps cache.'''
        tokens = []
        if isinstance(items, str):
            # Items is a string, use it as cache key.
            return items
        # Concatenate list of items to get the key.
        for text in items:
            if text is not None:
                if isinstance(text, float) or isinstance(text, int):
                    text = f'{text:.6f}'
                elif not isinstance(text, str):
                    text = str(text)
                tokens.append(text.lower().strip())
        return ','.join(tokens)

    def _load_cache(self):
        '''Load cache from file.'''
        self._maps_cache = _read_dict_from_file(
            self._config.get('maps_api_cache'))
        self._place_cache = _read_dict_from_file(
            self._config.get('place_resolver_cache'))
        self._cache_save_timestamp = time.perf_counter()

    def _save_cache(self, time_interval: int = 0):
        '''Periodically save cache of maps API and resolve API call responses'''
        if self._cache_save_timestamp + time_interval <= time.perf_counter():
            _write_dict_to_file(self._maps_cache,
                                self._config.get('maps_api_cache'))
            _write_dict_to_file(self._place_cache,
                                self._config.get('place_resolver_cache'))
            self._cache_save_timestamp = time.perf_counter()

    def _get_cache_value(self, cache_dict: dict, cache_key: str) -> dict:
        '''Returns the value in the cache dictionary for the key.'''
        return cache_dict.get(self._get_cache_key(cache_key), None)

    def _set_cache_value(self, cache_dict: dict, cache_key: str, value: dict):
        '''Set the result into the cache to be used for future lookups.'''
        cache_dict[cache_key] = value


def _read_dict_from_file(filename: str) -> dict:
    '''Load a python dict from a file.
    Args:
      filename: JSON or a python file containing parameter to value mappings.
    Returns:
      dictionary loaded from the file.
    '''
    if not filename or not os.path.exists(filename):
        return {}
    logging.info(f'Loading python dict from {filename}...')
    with open(filename) as file:
        pv_map_str = file.read()

    # Load the map assuming a python dictionary.
    # Can also be used with JSON with trailing commas and comments.
    param_dict = ast.literal_eval(pv_map_str)
    logging.debug(f'Loaded {filename} into dict {param_dict}')
    return param_dict


def _write_dict_to_file(cache_dict: dict, filename: str):
    '''Save the dict into a file.'''
    if filename:
        logging.info(f'Saving dict to {filename}')
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as fp:
            pp.pprint(cache_dict, stream=fp)


def process(input_filenames: list,
            output_filename: str,
            maps_api_key: str = '',
            config_file: str = None):
    '''Resolve the places in a csv file and save in output.
    Assumes the csv file has the following columns:
    - name: place name to be resolved
    - country: (optional) name of the country or 2-letter country code
    - administrative_area: (optional) name of the state, district.

    The output csv file will have the following additional columns:
    - dcid: dcid of the place if resolved
    - placeId: google maps placeId.
    - lat: latitude of the place
    - lng: longitude of the place

    Args:
      input_filenames: list of input csv files with names of places to be resolved.
      output_filename: output csv with additional columns.
      config_file: file with dictionary of config parameters for resolution.
    '''
    config = ConfigMap(filename=config_file)
    logging.info(f'Using config from {config_file}: {config.get_configs()}')
    counters = Counters()
    pr = PlaceResolver(maps_api_key=maps_api_key,
                       config_dict=config.get_configs(),
                       counters_dict=counters.get_counters())
    input_files = set()
    for file in input_filenames:
        input_files.update(glob.glob(file))
    place_names = {}
    place_coords = {}
    columns = set()
    num_inputs = -1
    for filename in input_files:
        with open(filename) as csvfile:
            logging.info(f'Loading places from csv file {filename}...')
            reader = csv.DictReader(csvfile)
            columns.update(reader.fieldnames)
            for row in reader:
                num_inputs += 1
                if num_inputs > config.get('input_rows', sys.maxsize):
                    break
                if 'name' in row:
                    place_names[num_inputs] = row
                elif 'latitude' in row:
                    place_coords[num_inputs] = row
    resolved_places = {}
    if place_names:
        logging.debug(f'Resolving {len(place_names)} places names...')
        resolved_places.update(pr.resolve_name(place_names))
        columns.update({'dcid', 'placeId', 'lat', 'lng'})
    if place_coords:
        logging.debug(f'Resolving {len(place_coords)} places coords...')
        resolved_places.update(pr.resolve_latlng(place_coords))
        columns.update({'placeDcids'})
    counters.print_counters()
    file, ext = os.path.splitext(output_filename)
    if ext != '.csv':
        output_filename = output_filename + '.csv'
    logging.info(
        f'Writing {len(resolved_places)} rows with columns: {columns} into {output_filename}'
    )
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    with open(output_filename, 'w') as output_fp:
        writer = csv.DictWriter(output_fp,
                                escapechar='\\',
                                fieldnames=columns,
                                quotechar='"',
                                quoting=csv.QUOTE_NONNUMERIC)
        writer.writeheader()
        for key in range(num_inputs + 1):
            row = {}
            row.update(place_names.get(key, {}))
            row.update(place_coords.get(key, {}))
            row.update(resolved_places.get(key, {}))
            writer.writerow(row)


def main(_):
    process(_FLAGS.input_data, _FLAGS.output_path, _FLAGS.maps_api_key,
            _FLAGS.config)


if __name__ == '__main__':
    app.run(main)
