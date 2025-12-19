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
"""Class to resolve places to dcids.

To resolve a set of place names on command line, create a CSV with the
place names to be resolved in a column called 'place_name',
- Get a DataCommons API key
  This is used for the /resolve API to lookup dcid by place name.
- Get a Maps API key
  This is used for Maps Place API to lookup placeid for a place name.
- Get a custom search API key (described in wiki_place_resolver.py)
  This is used for Google search lookup of wikidata page for the place name
  when dcid can't be determined using DC API and maps place API.
- Get a CSV file 'places.csv' with list of all places as described in place_name_matcher.py
  This is used for approximate string match on place names.

Create an input csv with place_name column containing places to be resolved,
then run the following:
  python place_resolver.py --resolve_input_csv=<input-csv> \
      --resolve_output_csv=<output-csv> \
      --place_names_csv=places.csv \
      --maps_key=<MAPS_API_KEY> \
      --resolve_api_key=<DC_API_KEY> \
      --custom_search_key=<CUSTOM_SEARCH_KEY> \
The output.csv will contains columns for 'dcid' with some additional columns
such as wikidataId, PlaceId, etc.
Additional candidate places may be filled in columns dcid<N>.
"""

import ast
import csv
import glob
import os
import pprint as pp
import re
import sys
import time
from typing import Union

from absl import app
from absl import flags
from absl import logging
import datacommons as dc

# uncomment to run pprof
# from pypprof.net_http import start_pprof_server

_FLAGS = flags.FLAGS

flags.DEFINE_list(
    'resolve_input_csv',
    '',
    'Input csv with places to resolve under column "name".',
)
flags.DEFINE_string('resolve_output_csv', '', 'Output csv with place dcids.')
flags.DEFINE_list('resolve_place_names', [], 'List of place names to resolve.')
flags.DEFINE_string('maps_key', os.environ.get('MAPS_API_KEY', ''),
                    'Google Maps API key')
flags.DEFINE_string(
    'resolve_config',
    '',
    'Config setting for place resolution as json or python dict.',
)
flags.DEFINE_list(
    'place_names_csv',
    '',
    'CSV files with place properties including name, dcid, containedInPlace'
    'used by the place_name_matcher',
)
flags.DEFINE_list(
    'place_names_within',
    '',
    'use place names within the list of places for name matches.',
)
flags.DEFINE_list('place_types', [], 'List of place types to resolve to.')
flags.DEFINE_string(
    'place_name_column',
    'place_name',
    'input CSV column with the name of the place to be resolved.',
)
flags.DEFINE_string(
    'place_latitude_column',
    'latitude',
    'input CSV column with the latitude of the place to be resolved.',
)
flags.DEFINE_string(
    'place_longitude_column',
    'longitude',
    'input CSV column with the longitude of the place to be resolved.',
)
flags.DEFINE_string('place_resolver_cache', '',
                    'Cache file to save resolved places.')
flags.DEFINE_list('output_place_columns', [], 'List of columns in the output.')
flags.DEFINE_string('maps_api_cache', '',
                    'Cache file to save responses from maps API.')
flags.DEFINE_integer('place_pprof_port', 0,
                     'HTTP port for running pprof server.')
flags.DEFINE_string(
    'resolve_api_url',
    'https://autopush.api.datacommons.org/v2/resolve',
    'DC API URL for resolve.',
)
flags.DEFINE_string('resolve_api_key', os.environ.get('DC_API_KEY', ''),
                    'DC API key for resolve.')
flags.DEFINE_integer(
    'dc_api_batch_size',
    3,
    'DC API batch size for number of places to lookup per request.',
)

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(_SCRIPT_DIR))),
                 'util'))

import file_util
import process_http_server
import wiki_place_resolver

from counters import Counters
from config_map import ConfigMap
from download_util import request_url
from dc_api_wrapper import dc_api_batched_wrapper, dc_api_resolve_placeid
from dc_api_wrapper import dc_api_resolve_latlng, dc_api_get_node_property
from place_name_matcher import PlaceNameMatcher
from property_value_cache import PropertyValueCache

# Google Maps API
# params used: &key=<>&address=<...>&components=country:<CC>|admin_area:<State>
_MAPS_URL = 'https://maps.googleapis.com/maps/api/geocode/json'
_MAPS_TEXT_SEARCH_URL = (
    'https://maps.googleapis.com/maps/api/place/textsearch/json')


class PlaceResolver:
    """Class to resolve places to dcid.

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
  """

    def __init__(
        self,
        maps_api_key: str = None,
        config_dict: dict = {},
        counters_dict: dict = None,
    ):
        self._maps_api_key = maps_api_key
        self._config = ConfigMap(config_dict)
        self._counters = Counters(counters_dict)
        self._log_every_n = self._config.get('log_every_n', 10)
        if not self._maps_api_key:
            self._maps_api_key = self._config.get(
                'maps_api_key', os.environ.get('MAPS_API_KEY'))
        self._place_name_matcher = PlaceNameMatcher(
            config=self._config.get_configs())
        self._load_cache()
        self._wiki_resolver = wiki_place_resolver.WikiPlaceResolver(
            config_dict, counters_dict, cache=self._cache)

    def __del__(self):
        """Save cached results into files."""
        self._save_cache()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._save_cache()

    def resolve_name(self,
                     places: dict,
                     place_types: list = [],
                     places_within: list = [],
                     filter_pvs: dict = {}) -> dict:
        """Returns a dictionary with dcid and placeId for each place.

    Args:
      places: dictionary of input places to lookup where each input place is a
        dictionary with the following keys:
        place_name: Name of the place to resolve.
        places_types: look for places of given types
        places_within: look for places within other place dcids
        filter_pvs: dictionary of property:values to filter results by.

    Returns:
      Dictionary with the following additional properties for each place:
        dcid: the data commons id for the place, if found
        placeId: the Google Maps place-id, if found.
         in case maps returns multiple places, the first one is used.
        latitude: approximate latitude for the place
        longitude: approximate longitude for the place
    """
        logging.log_every_n(logging.DEBUG, f'Resolving places: {places}...',
                            self._log_every_n)
        results = {}
        unresolved_places = {}
        results = self.resolve_name_dc_api(places)

        # Get any remaining unresolved places
        self._get_unresolved_places(places, unresolved_places, results)

        # Get the maps placeId for each remaining place.
        country_key = self._config.get('place_country_column', 'country')
        for key, place in unresolved_places.items():
            place_name = self._get_lookup_name(key, place)
            # Use composite cache key for consistent lookup/storage
            place_cache_key = self._get_cache_key([
                place_name,
                place.get(country_key, None),
                place.get('administrative_area', None)
            ])
            maps_result = self._get_cache_value(place_cache_key, 'placeId')
            if not maps_result:
                maps_result = self.get_maps_placeid(
                    name=place_name,
                    country=place.get(country_key, None),
                    admin_area=place.get('administrative_area', None),
                )
            if maps_result:
                results[key] = maps_result

        # Collect all placeIds to be resolved that are not in cache.
        places_ids = {}
        for key, result in results.items():
            if 'dcid' not in result:
                # Maps can return multiple results for a place name search.
                # Get all placeIds for each result.
                place_ids = _get_values_from_dict('placeId', result)
                for place_id in place_ids:
                    cached_place = self._get_cache_value(place_id, 'dcid')
                    if cached_place:
                        # placeId is already resolved, use the cached result.
                        _update_dict(cached_place, results[key])
                        self._counters.add_counter(
                            'dc-api-resolve-placeid-cache-hits', 1)
                    else:
                        # Add place to list of ids to be looked up.
                        places_ids[place_id] = key
        logging.log_every_n(logging.DEBUG,
                            f'Resolved place dcids from cache: {results}',
                            self._log_every_n)

        # Lookup dcid for each placeid using the resolve_placeid API
        lookup_placeids = list(places_ids.keys())
        if lookup_placeids:
            # Resolve placeIds to dcids in a batch
            recon_resp = dc_api_batched_wrapper(
                function=dc_api_resolve_placeid,
                dcids=lookup_placeids,
                args={},
                config=self._config.get_configs(),
            )
            logging.log_every_n(logging.DEBUG,
                                f'Got resolve_placeid response: {recon_resp}',
                                self._log_every_n)
            self._counters.add_counter('dc-api-resolve-placeid-lookups',
                                       len(lookup_placeids))
            self._counters.add_counter('dc-api-resolve-placeid-calls', 1)
            # Extract the dcid for each placeid looked up
            # and add it to the result.
            for key, result in results.items():
                if 'dcid' not in result:
                    # Get all resolved placeIds for each result.
                    place_ids = _get_values_from_dict('placeId', result)
                    for index in range(len(place_ids)):
                        place_id = place_ids[index]
                        dcid = recon_resp.get(place_id, '')
                        if dcid:
                            _add_to_dict('dcid', dcid, result, index)
                            # Cache the dcid for the place_id
                            self._set_cache_value('', {
                                'placeId': place_id,
                                'dcid': dcid
                            })
        logging.log_every_n(logging.DEBUG,
                            f'Resolved placeid to dcids: {results}',
                            self._log_every_n)

        # Lookup wiki ids for any remaining unresolved places
        wiki_results = self.resolve_name_wiki_search(places)
        results.update(wiki_results)

        # Resolve any remaining unresolved places using the place name matcher.
        unresolved_places = {}
        self._get_unresolved_places(places, unresolved_places, results)
        logging.log_every_n(
            logging.DEBUG,
            f'Resolving names: {places}, {unresolved_places} into {results}',
            self._log_every_n)
        if unresolved_places and self._place_name_matcher:
            logging.log_every_n(
                logging.DEBUG,
                f'Looking up unresolved places in name matcher: {unresolved_places}',
                self._log_every_n)
            self._counters.add_counter('dc-api-unresolved-places',
                                       len(unresolved_places))
            name_results = self.lookup_names(unresolved_places)
            results.update(name_results)

        logging.log_every_n(logging.DEBUG, f'Resolved names: {results}',
                            self._log_every_n)
        filtered_results = self.filter_by_pvs(results, place_types,
                                              places_within, filter_pvs)
        logging.level_debug() and logging.log_every_n(
            logging.DEBUG, f'Filtered results: {filtered_results}',
            self._log_every_n)

        return filtered_results

    def resolve_name_dc_api(self, places: dict) -> dict:
        """Returns dictionary with dcids for each place resolved using the DC API."""
        if not self._config.get('dc_api_key', ''):
            logging.log_every_n(
                logging.DEBUG,
                f'Skipping DC API resolve as dc_api_key not set.',
                self._log_every_n)
            return {}

        logging.log_every_n(
            logging.DEBUG,
            f'Resolving places using DC API resolve: {places}...',
            self._log_every_n)
        results = {}
        unresolved_places = {}
        self._get_unresolved_places(places, unresolved_places, results)

        # Get the list of names to be resolved.
        place_names_to_key = {}
        for key, place in unresolved_places.items():
            place_name = self._get_lookup_name(key, place)
            if place_name not in place_names_to_key:
                place_names_to_key[place_name] = key

        if not place_names_to_key:
            return {}

        # Get a list of dcids keyed by the place name using DC API.
        resolved_places = self.resolve_name_dc_api_batch(
            list(place_names_to_key.keys()))

        # Add dcid for resolved places to the result.
        results = {}
        for place_name, dcids in resolved_places.items():
            key = place_names_to_key.get(place_name)
            if key is not None:
                result = {}
                for dcid in dcids:
                    _add_to_dict('dcid', dcid, result)
                self._set_cache_value(place_name, result)
                results[key] = places[key]
                results[key].update(result)
        logging.log_every_n(
            logging.DEBUG,
            f'Resolved places using DC API resolve: {results}...',
            self._log_every_n)
        return results

    def resolve_name_dc_api_batch(self, place_names: list) -> dict:
        """Returns resolved places names in batches."""
        url = self._config.get('resolve_api_url')
        key = self._config.get('dc_api_key')
        if not url or not key:
            return {}

        resolve_resp = {}
        index = 0
        dc_api_batch_size = self._config.get('dc_api_batch_size', 3)
        num_places = len(place_names)

        while index < num_places:
            # Make a batch request to resolve places.
            params = {
                # List of place names to lookup.
                'nodes': place_names[index:index + dc_api_batch_size],
                # Lookup dcid by the description
                'property': '<-description->dcid',
            }
            headers = {
                'X-API-Key': key,
            }
            self._counters.add_counter('dc-api-resolve-name-lookups',
                                       len(params['nodes']))
            self._counters.add_counter('dc-api-resolve-name-calls', 1)
            batch_resp = request_url(url,
                                     method='POST',
                                     headers=headers,
                                     params=params,
                                     output='json')
            logging.log_every_n(logging.DEBUG,
                                f'Got resolve name response: {batch_resp}',
                                self._log_every_n)
            # Extract dcids from the resolve response.
            if not batch_resp:
                self._counters.add_counter('dc-api-resolve-name-call-errors', 1)
            else:
                for resp in batch_resp.get('entities', []):
                    if 'resolvedIds' in resp:
                        # Got a list of dcids for the place name.
                        resolve_resp[resp['node']] = resp['resolvedIds']
                        self._counters.add_counter('dc-api-resolve-name-dcids',
                                                   1)
            # Move to the next batch of places
            index += dc_api_batch_size
        logging.log_every_n(logging.DEBUG, f'Resolved names: {resolve_resp}',
                            self._log_every_n)
        return resolve_resp

    def resolve_latlng(self, places: dict) -> dict:
        """Returns a dictionary with a list of dcids for each lat/lng.

    Resolve a set of places with latitude/longitude using the DC recon API:
    https://api.datacommons.org/v1/recon/resolve/coordinate.

    Args:
      places: dictionary with each key referring to a value dictionary that has
        the following keys: - latitude: latitude of the place in degrees. -
        longitude: longitude of the place in degrees.

    Returns:
    dictionary with input keys and value dictionary containing the following
    keys:
      - dcid: list of dcids for the location given by lat/lng.
    """
        # Collect places not in cache to be resolved.
        results = {}
        resolve_places = []
        coords_to_key = {}
        latitude_key = self._config.get('place_latitude_column', 'latitude')
        longitude_key = self._config.get('place_longitude_column', 'longitude')
        for key, place in places.items():
            results[key] = dict(place)
            lat = place.get(latitude_key, '')
            lng = place.get(longitude_key, '')
            if lat and lng:
                place_key = self._get_cache_key([lat, lng])
                cached_place = self._get_cache_value(place_key, 'latitude')
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
                logging.log_every_n(logging.DEBUG,
                                    f'Skipping empty lat/lng in {key}:{place}',
                                    self._log_every_n)

        # Resolve any remaining lat/lng places.
        resolved_place_ids = {}
        if resolve_places:
            logging.log_every_n(
                logging.DEBUG,
                f'Resolving {len(resolve_places)} lat/long places {resolve_places}',
                self._log_every_n)
            self._counters.add_counter(f'dc-api-resolve-latlng-places',
                                       len(resolve_places))
            self._counters.add_counter(f'dc-api-resolve-latlng-calls', 1)
            resolved_place_ids = dc_api_batched_wrapper(
                function=dc_api_resolve_latlng,
                dcids=resolve_places,
                args={},
                config=self._config.get_configs(),
            )

        # Retrieve resolved dcids into results.
        if resolved_place_ids:
            for resolved_place in resolved_place_ids.values():
                place_key = self._get_cache_key(
                    [resolved_place['latitude'], resolved_place['longitude']])
                input_key = coords_to_key.get(place_key, '')
                dcids = resolved_place.get('placeDcids', '')
                self._set_cache_value('', resolved_place)
                if dcids and input_key in results:
                    results[input_key]['placeDcids'] = dcids
        logging.log_every_n(logging.DEBUG,
                            f'Returning resolved latlngs {results}',
                            self._log_every_n)
        return results

    def lookup_names(
        self,
        places: dict,
        place_types: list = [],
        places_within: list = [],
        num_results: int = 10,
    ) -> dict:
        """Returns a dictionary with dcid for each place.

    looks up the place name using the PlaceNameMatcher.

     Args:
       places: dictionary of input places to lookup where each input place is a
         dictionary with the following keys:
           name: Name of the place to resolve.
           country: 2 letter country code or the country name
           administrative_area: state or district for the place.
       place_types: List of place types in order of priority.
       places_within: DCIDs of containing In parent places allowed.

     Returns:
       Dictionary with the following additional properties for each place:
         dcid: the first result of data commons id for the place, if found
         place-name: Full name of the place for the dcid.
         dcid-<N>: Additional candidate dcids
         place-name-<N>: name for the dcid-<N>
    """

        # Get a list of unresolved places.
        results = {}
        unresolved_places = {}
        self._get_unresolved_places(places, unresolved_places, results)

        if not place_types:
            place_types = self._config.get('place_type', [])
        if not places_within:
            places_within = self._config.get('places_within', [])
        property_filters = {}
        if place_types:
            property_filters['typeOf'] = place_types
        if places_within:
            property_filters['containedInPlace'] = places_within

        # Lookup unresolved places
        logging.level_debug() and logging.log_every_n(
            logging.DEBUG,
            f'Looking up {len(unresolved_places)} places with name-matcher:'
            f'{unresolved_places} {property_filters}', self._log_every_n)
        for key, place in unresolved_places.items():
            place_name = self._get_lookup_name(key, place)
            lookup_results = self._place_name_matcher.lookup(
                place_name, num_results, property_filters)
            logging.level_debug() and logging.log_every_n(
                logging.DEBUG,
                f'Got name lookup results: {place_name}, {property_filters}:'
                f' {lookup_results}', self._log_every_n)

            # Add resolved dcids with names matched.
            suffix = ''
            place_result = {}
            for result_name, result_dcid in lookup_results:
                place_result[f'dcid{suffix}'] = result_dcid
                place_result[f'place-name{suffix}'] = result_name
                suffix = int(len(place_result) / 2)
            if place_result:
                results[key] = place
                results[key].update(place_result)
                self._set_cache_value(place_name, place_result)
                self._counters.add_counter(f'place-name-match-results', 1)
            self._counters.add_counter(f'place-name-match-lookups', 1)
        return results

    def get_maps_placeid(
        self,
        name: str,
        country: str = None,
        admin_area: str = '',
        place_types: list = [],
    ) -> dict:
        """Returns the Google maps place-id for a place.

    It uses the Google Map API for address resolution with additional hints for
    country and admin_area, like state or district.

    Args:
      name: name to be resolved which can be an address with multiple words
      country: a 2 letter country code or country name.
      admin_area: the name of the administrative area to be used as hint when
        there could be multiple places with the same name.

    Returns:
      dictionary with attributes such as placeId, latitude, and longitude.
    """
        if not name:
            logging.log_every_n(
                logging.DEBUG, f'Unable to resolve maps place with empty name',
                self._log_every_n)
            return {}

        if self._config.get('maps_api_text_search', True):
            return self.lookup_maps_placeid(name, country, admin_area,
                                            place_types)

        # Check if the place is in the maps cache.
        place_key = self._get_cache_key([name, country, admin_area])
        cached_place = self._get_cache_value(place_key, 'placeId')
        if cached_place:
            return cached_place

        # Lookup Google Maps API.
        if not self._maps_api_key:
            logging.log_every_n(
                logging.ERROR,
                f'No maps key. Please set --maps_api_key for place lookup.',
                self._log_every_n)
            return {}
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
            logging.log_every_n(logging.DEBUG, f'Got Maps results: {resp_json}',
                                self._log_every_n)
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
                            loc = first_result['geometry']['location']
                            _add_to_dict('latitude', loc.get('lat', ''), result)
                            _add_to_dict('longitude', loc.get('lng', ''),
                                         result)
                    if result:
                        self._counters.add_counter('maps-api-geocode-results',
                                                   1)
            # Cache the response
            self._set_cache_value(place_key, result)
            return result

        return {}

    def lookup_maps_placeid(
        self,
        name: str,
        country: str = None,
        admin_area: str = '',
        place_types: list = [],
    ) -> dict:
        """Returns a dictionary with attributes for a place such as placeId,
    latitude, and longitude using the Maps Place API.
    """
        # Check if the place is in the maps cache.
        place_key = self._get_cache_key([name, country, admin_area])
        cached_place = self._get_cache_value(place_key, 'placeId')
        if cached_place:
            return cached_place

        # Lookup Google Maps API.
        if not self._maps_api_key:
            logging.log_every_n(
                logging.ERROR,
                f'No maps key. Please set --maps_api_key for place lookup.',
                self._log_every_n)
            return {}
        query_tokens = [name]
        if admin_area:
            query_tokens.append(admin_area)
        if country:
            query_tokens.append(country)
        params = {
            'key': self._maps_api_key,
            'query': ','.join(query_tokens),
        }
        if place_types:
            params['type'] = '|'.join(_get_maps_place_types(place_types))
        resp_json = request_url(url=_MAPS_TEXT_SEARCH_URL,
                                params=params,
                                output='json')
        result = {}
        if resp_json:
            logging.log_every_n(logging.DEBUG,
                                f'Got Maps TextSearch results: {resp_json}',
                                self._log_every_n)
            if 'results' in resp_json:
                map_results = resp_json['results']
                for map_result in map_results:
                    result = {}
                    # Get the place id
                    if 'place_id' in map_result:
                        _add_to_dict('placeId', map_result['place_id'], result)
                    # Get the lat/lng location
                    if 'geometry' in map_result:
                        if 'location' in map_result['geometry']:
                            loc = map_result['geometry']['location']
                            _add_to_dict('latitude', loc.get('lat', ''), result)
                            _add_to_dict('longitude', loc.get('lng', ''),
                                         result)
            if result:
                self._set_cache_value(place_key, result)
                self._counters.add_counter('maps-api-textsearch-results', 1)
            else:
                self._set_failed_cache_value(place_key, result)
        return result

    def resolve_name_wiki_search(self, places: dict) -> dict:
        """Returns the wiki IDs for places.

    Args:
        places: dict of places wiht properties. Use the 'name' or 'place_name'
          property or key to lookup

    Returns:
       dictionary with additional property:values for each place such as
         wikidataId
    """
        if not self._wiki_resolver.is_ready():
            return {}

        wiki_props = self._wiki_resolver.get_config_wiki_props()
        if not wiki_props:
            # No properties to lookup. Only resolve place names.
            self._get_unresolved_places(places, unresolved_places, results)
        else:
            unresolved_places = places
        if not unresolved_places:
            logging.log_every_n(
                logging.DEBUG,
                f'No unresolved places for wiki props: {wiki_props}',
                self._log_every_n)
            return {}

        # Lookup wiki ids for places names
        logging.level_debug() and logging.debug(f'Looking up wiki for {places}')
        wiki_results = self._wiki_resolver.lookup_wiki_places(places)

        # Resolve place wikidataId to dcid
        lookup_wikis = {}
        for key, pvs in wiki_results.items():
            wiki_id = pvs.get('wikidataId')
            dcid = pvs.get('dcid')
            if not dcid and wiki_id:
                lookup_wikis[wiki_id] = key

        if not lookup_wikis:
            return wiki_results

        # Resolve wiki ids to dcids in a batch
        logging.level_debug() and logging.log_every_n(
            logging.DEBUG,
            f'Resolving {len(lookup_wikis)} wikidataId:  {lookup_wikis}',
            self._log_every_n)
        recon_resp = dc_api_batched_wrapper(
            function=dc_api_resolve_placeid,
            dcids=list(lookup_wikis.keys()),
            args={'in_prop': 'wikidataId'},
            config=self._config.get_configs(),
        )
        self._counters.add_counter('dc-api-resolve-wikidataId-calls',
                                   len(lookup_wikis))
        self._counters.add_counter('dc-api-resolve-wikidataId-results',
                                   len(recon_resp))
        logging.level_debug() and logging.log_every_n(
            logging.DEBUG, f'Got resolve_wikidataid response: {recon_resp}',
            self._log_every_n)

        for wiki_id, dcid in recon_resp.items():
            key = lookup_wikis.get(wiki_id)
            place = wiki_results.get(key)
            if place:
                place['dcid'] = dcid
                self._set_cache_value('', value=place)
        logging.level_debug() and logging.log_every_n(
            logging.DEBUG, f'Got wiki place properties: {wiki_results}',
            self._log_every_n)
        return wiki_results

    def filter_by_pvs(
        self,
        places: dict,
        place_types: list = [],
        places_within: list = [],
        filter_pvs: dict = {},
    ) -> dict:
        """Returns a dictionary of places that match the properties in filter_pvs.

    Args:
      places: dictionary that maps place_name to a dict of place
        property:values.
      filter_pvs: dictionary of allowed values for place properties. Only places
        with property values in the filter_pvs are returned.
    """
        # Convert values for filter properties into a set
        filter_value_set = {}
        for prop, filter_values in filter_pvs.items():
            value_set = _get_value_set(filter_values)
            if value_set:
                filter_value_set[prop] = value_set

        # Add the global filters if any.
        place_types = _get_value_set(place_types)
        place_types.update(_get_value_set(self._config.get('place_type', [])))
        if place_types:
            place_types.update(filter_value_set.get('typeOf', set()))
            filter_value_set['typeOf'] = place_types
        places_within = _get_value_set(places_within)
        places_within.update(
            _get_value_set(self._config.get('places_within', [])))
        if places_within:
            places_within.update(filter_value_set.get('containedInPlace',
                                                      set()))
            filter_value_set['containedInPlace'] = places_within

        logging.log_every_n(
            logging.DEBUG,
            f'Filtering {places} with filter_pvs: {filter_value_set} with config'
            f' {self._config.get_configs()}', self._log_every_n)
        lookup_props = set(filter_value_set.keys())
        if not lookup_props:
            # No property to filter by. Return all results.
            return places

        # Also lookup names and alternateName for places to set in cache.
        lookup_props.add('name')
        lookup_props.add('alternateName')

        # Get a list of dcids to lookup for each filter property.
        dcids = set()
        for place_key, place_props in places.items():
            dcid = place_props.get('dcid', '')
            if not dcid:
                continue
            dcids.update(_get_value_set(dcid))
        # Cache containedInPlace heirarchy for all dcids.
        if 'containedInPlace' in lookup_props:
            self._cache_contained_in_places(dcids)

        lookup_dcids_by_prop = {p: [] for p in lookup_props}
        for dcid in dcids:
            for prop in lookup_props:
                value = place_props.get(prop, '')
                if not value:
                    # filter property doesn't have a value for this dcid.
                    # Check if the property is cached.
                    values = self._get_cache_value(dcid, prop).get(prop)
                    if values:
                        place_props[prop] = values
                if not value:
                    lookup_dcids_by_prop[prop].append(dcid)

        # Lookup property values for the dcids from DC API.
        for prop, dcids in lookup_dcids_by_prop.items():
            dc_api_resp = dc_api_get_node_property(
                dcids=dcids,
                prop=prop,
                config=self._config.get_configs(),
            )
            self._counters.add_counter(f'dc-api-prop-value-{prop}-lookups',
                                       len(dcids))
            # Cache the property:value for the response.
            for dcid, prop_values in dc_api_resp.items():
                if prop_values:
                    self._set_cache_value('', {'dcid': dcid, **prop_values})

        # Check if the values match the filter.
        filtered_places = {}
        for place_key, place_props in places.items():
            dcid = place_props.get('dcid', '')
            if not dcid:
                continue
            allow_place = True
            for prop, filter_values in filter_value_set.items():
                if not filter_values:
                    continue
                if prop == 'containedInPlace':
                    value = self._get_contained_in_place(dcid)
                    place_props['containedInPlace'] = list(value)
                    value.update(_get_value_set(dcid))
                else:
                    value = place_props.get(prop, '')
                if not value:
                    # place doesn't have a value. Get value from cache
                    value = self._get_cache_value(dcid, prop).get(prop)
                    if value:
                        place_props[prop] = value
                if value:
                    place_values = _get_value_set(value)
                    if not place_values.intersection(filter_values):
                        # Place has no allowed value for prop. Drop it.
                        allow_place = False
                        self._counters.add_counter(
                            f'place-prop-filter-{prop}-dropped', 1, dcid)
                        logging.log_every_n(
                            logging.DEBUG,
                            f'Place {place_props} did not match {prop}:{place_values} in'
                            f' {filter_value_set}', self._log_every_n)
                        break
                    self._counters.add_counter(
                        f'place-prop-filter-{prop}-allowed', 1)
            if allow_place:
                filtered_places[place_key] = place_props
        logging.log_every_n(
            logging.DEBUG, f'Returning {len(filtered_places)} filtered places:'
            f' {filtered_places} that match {filter_value_set}',
            self._log_every_n)
        return filtered_places

    def _get_lookup_name(self, key: str, values: dict) -> str:
        """Returns the name to be looked up for the request entry.

    If values has the key, 'place_name' and 'country' it is used. else if the
    key is a string, it is used.
    """
        name_key = self._config.get('place_name_column', 'place_name')
        name = values.get(name_key, '')
        if not name and isinstance(key, str):
            name = key
        country_key = self._config.get('place_country_column', 'country')
        country = values.get(country_key, '')
        if country and len(country) > 2 and country not in name:
            name += ' ' + country
        return name

    def _get_unresolved_places(self, places: dict, unresolved_places: dict,
                               resolved_places: dict):
        """Adds unresolved and resolved places from places dict into respective
    output dictionaries.
    """
        # From entries in places, copy ones with 'dcid' to resolved_places
        # and the rest to 'unresolved_places'
        for key, place in places.items():
            dcid = place.get('dcid', '')
            resolved_place = None
            if dcid:
                # Entry already has a dcid resolved.
                resolved_place = place
            else:
                # Entry doesn't have a dcid. Lookup cache by key and name
                cached_place = self._get_cache_value(key, 'dcid')
                if not cached_place:
                    cached_place = self._get_cache_value(
                        self._get_lookup_name(key, place), 'dcid')
                if cached_place:
                    _update_dict(cached_place, place)
                    dcid = cached_place.get('dcid', '')
                    if dcid:
                        # Found a cached dcid for the place.
                        # Copy over the properties to resolved_places.
                        self._counters.add_counter(
                            f'place-resolver-name-cache-hits', 1)
                        resolved_place = place
            if resolved_place:
                resolved_places[key] = resolved_place
            else:
                unresolved_places[key] = place

    def _get_cache_key(self, items: list) -> str:
        """Returns a key for the place lookup in the maps cache."""
        tokens = []
        if isinstance(items, str):
            # Normalize string to lower case, remove extra
            # spaces and characters.
            # return re.sub(r'[^A-Za-z0-9\.,-]*', ' ', items)
            return items
        # Concatenate list of items to get the key.
        if isinstance(items, list):
            for text in items:
                if text is not None:
                    if isinstance(text, float) or isinstance(text, int):
                        text = f'{text:.6f}'
                    elif not isinstance(text, str):
                        text = str(text)
                    tokens.append(text.lower().strip())
        return ','.join(tokens)

    def _load_cache(self):
        """Load cache from file."""
        # Dictionary { <place>: <dcid> }
        self._cache_save_timestamp = time.perf_counter()
        # Persistent cache of place name to dcids.
        self._cache = PropertyValueCache(
            key_props=['place_name', 'dcid', 'placeId', 'wikidataId'],
            props=['name', 'alternateName', 'typeOf', 'containedInPlace'],
            filename=self._config.get('places_resolved_csv'),
            normalize_key=self._config.get('resolver_normalize_key', True),
        )
        # In-memory cache of failed lookups to avoid retries.
        self._failure_cache = PropertyValueCache(
            key_props=['place_name', 'dcid', 'placeId', 'wikidataId'],
            props=['name', 'alternateName', 'typeOf', 'containedInPlace'],
            filename='',
            normalize_key=self._config.get('resolver_normalize_key', True),
        )

    def _save_cache(self, time_interval: int = 0):
        """Periodically save cache of maps API and resolve API call responses"""
        if self._cache.is_dirty() and (self._cache_save_timestamp +
                                       time_interval <= time.perf_counter()):
            self._cache.save_cache_file()
            self._cache_save_timestamp = time.perf_counter()

    def _get_cache_value(self, cache_key: str, prop: str = '') -> dict:
        """Returns the value in the cache dictionary for the key
    if it has the property.
    """
        cached_entry = self._cache.get_entry(prop='', value=cache_key)
        if prop and cached_entry:
            value = cached_entry.get(prop)
            if value:
                self._counters.add_counter(f'cache-hit-{prop}', 1)
                return dict(cached_entry)
        # See if place was looked up earlier and failed.
        failed_cache_entry = self._failure_cache.get_entry(prop='',
                                                           value=cache_key)
        if failed_cache_entry:
            self._counters.add_counter(f'cache-failed-{prop}', 1)
            return failed_cache_entry
        self._counters.add_counter(f'cache-miss-{prop}', 1)
        return {}

    def _set_cache_value(self, cache_key: str, value: dict):
        """Set the result into the cache to be used for future lookups."""
        if cache_key:
            value = dict(value)
            place_name = re.sub(', *', ' ', cache_key)
            value['place_name'] = place_name
        logging.level_debug() and logging.log_every_n(
            logging.DEBUG, f'Adding cache entry: {value}', self._log_every_n)
        self._cache.add(value)
        self._save_cache(self._config.get('cache_save_interval', 30))
        return

    def _set_failed_cache_value(self, cache_key: str, value: dict):
        """Set the result into the failed cache to avoid lookup in future."""
        if cache_key:
            value = dict(value)
            value['place_name'] = cache_key
        self._failure_cache.add(value)
        return

    def _cache_contained_in_places(self, dcids: list, level: int = 0):
        """Cache the containedInPlace values for each dcid upto the root."""

        # Get dcids without containedInPlace
        lookup_dcids = []
        parent_dcids = set()
        for dcid in dcids:
            if dcid != 'Earth':
                parents = self._get_cache_value(
                    dcid, 'containedInPlace').get('containedInPlace')
                if not parents:
                    lookup_dcids.append(dcid)
                else:
                    parent_dcids.update(_get_value_set(parents))

        if lookup_dcids:
            dc_api_resp = dc_api_get_node_property(
                dcids=lookup_dcids,
                prop='containedInPlace',
                config=self._config.get_configs(),
            )
            self._counters.add_counter(
                f'dc-api-prop-value-containedInPlace-lookups',
                len(lookup_dcids))
            # Cache the property:value for the response.
            for dcid, prop_values in dc_api_resp.items():
                val = prop_values.get('containedInPlace')
                if val:
                    values_set = _get_value_set(val)
                    self._set_cache_value(
                        '',
                        {
                            'dcid': dcid,
                            'containedInPlace': values_set,
                        },
                    )
                    parent_dcids.update(values_set)

        # Lookup containedInPlace heirarchy upto 7 levels.
        if level < 7 and parent_dcids:
            # lookup new parents
            self._cache_contained_in_places(parent_dcids, level + 1)

    def _get_contained_in_place(self, dcid: str) -> set:
        """Returns the list of contained in places for a dcid from cache."""
        parents = set()
        if not dcid:
            return parents
        logging.log_every_n(logging.DEBUG,
                            f'Looking up containedInPlace for {dcid}',
                            self._log_every_n)
        cached_parents = self._get_cache_value(
            dcid, 'containedInPlace').get('containedInPlace')
        parents.update(_get_value_set(cached_parents))
        new_parents = parents
        logging.log_every_n(
            logging.DEBUG,
            f'Got containedInPlace for {dcid} from cache: {new_parents}',
            self._log_every_n)
        # Get the parents chain for each dcid.
        while new_parents:
            # For each new parent, get the cached parents.
            lookup_parents = new_parents
            new_parents = set()
            for parent in lookup_parents:
                cached_parents = _get_value_set(
                    self._get_cache_value(
                        parent, 'containedInPlace').get('containedInPlace'))
                for parent_dcid in cached_parents:
                    if parent_dcid and parent_dcid not in parents:
                        new_parents.add(parent_dcid)
            logging.log_every_n(
                logging.DEBUG,
                f'Got containedInPlace for {dcid}: {new_parents} from'
                f' {lookup_parents}', self._log_every_n)
            parents.update(new_parents)

        # Cache the parents for a place
        if parents:
            self._set_cache_value(
                '',
                {
                    'dcid': dcid,
                    'containedInPlace': parents,
                },
            )
            logging.log_every_n(
                logging.DEBUG,
                f'Setting containedInPlace for {dcid}: {parents}',
                self._log_every_n)

        return parents


def _get_maps_place_types(place_types: list) -> list:
    """Returns a list of DC places types converted to maps API type names.

  Currently only supports maps place types: administrative_area_level_[1-7].
  https://developers.google.com/maps/documentation/places/web-service/supported_types#table2
  """
    maps_types = []
    for place_type in place_types:
        if place_type.startswith('AdministrativeArea'):
            maps_types.append(
                place_type.replace('AdministrativeArea',
                                   'administrative_area_level_'))
    return maps_types


def _add_to_dict(key: str, value: str, pvs: dict, key_num: int = 0) -> dict:
    """Adds a key and value to the dict

  If the key already exists, adds a numeric suffix to the key to make it unique.
  """
    if not key_num:
        # Get the number of keys matching the key prefix
        key_num = 0
        for k in pvs.keys():
            if k.startswith(key):
                if value == pvs[k]:
                    # Value already set in dict. Ignore new value.
                    return
                key_num += 1
        if key_num:
            # Set the suffix to the next index.
            key_num += 1
    if key_num:
        key = f'{key}{key_num:02d}'
    pvs[key] = value


def _update_dict(src: dict, dst: dict) -> dict:
    """Returns the dst dict after adding all key:value from the src dict."""
    for key, value in src.items():
        _add_to_dict(key, value, dst)
    return dst


def _get_values_from_dict(key: str, pvs: dict) -> list:
    """Returns a list of values that match the key prefix."""
    return [pvs[k] for k in sorted(pvs.keys()) if k.startswith(key)]


def _get_value_set(values: str) -> set:
    """Returns a set of values from a comma separated string."""
    if not values:
        return set()
    values_set = set()
    if isinstance(values, str):
        values = values.split(',')
    else:
        logging.log_every_n(logging.DEBUG, f'flattening into set {values}',
                            self._log_every_n)
        values = ','.join(values).split(',')
    values_set.update(values)
    return values_set


def process(
    input_filenames: list,
    output_filename: str,
    input_place_names: list = [],
    maps_api_key: str = '',
    output_columns: list = [],
    config: ConfigMap = None,
):
    """Resolve the places in a csv file and save in output.

  Assumes the csv file has the following columns: - name: place name to be
  resolved - country: (optional) name of the country or 2-letter country code -
  administrative_area: (optional) name of the state, district.

  The output csv file will have the following additional columns:
  - dcid: dcid of the place if resolved
  - placeId: google maps placeId.
  - lat: latitude of the place
  - lng: longitude of the place

  Args:
    input_filenames: list of input csv files with names of places to be
      resolved.
    output_filename: output csv with additional columns.
    place_names: list of place names to resolve.
    config_file: file with dictionary of config parameters for resolution.
  """
    counters = Counters()
    if not config:
        config = ConfigMap()
    pr = PlaceResolver(
        maps_api_key=maps_api_key,
        config_dict=config.get_configs(),
        counters_dict=counters.get_counters(),
    )
    place_names = {}
    place_coords = {}
    columns = []
    num_inputs = -1
    # Load all input places to be resolved.
    place_name_column = config.get('place_name_column', 'place_name')
    place_location_column = config.get('place_latitude_column', 'latitude')
    for filename in file_util.file_get_matching(input_filenames):
        with file_util.FileIO(filename) as csvfile:
            reader = csv.DictReader(csvfile)
            columns.extend(reader.fieldnames)
            logging.log_every_n(
                logging.INFO,
                f'Loading places from csv file {filename} with columns:'
                f' {reader.fieldnames}...', self._log_every_n)
            for row in reader:
                num_inputs += 1
                if num_inputs > config.get('input_rows', sys.maxsize):
                    break
                if place_name_column in row:
                    place_names[num_inputs] = row
                elif place_location_column in row:
                    place_coords[num_inputs] = row
    if input_place_names:
        for name in input_place_names:
            num_inputs += 1
            place_names[num_inputs] = {place_name_column: name}
    counters.add_counter('input-rows', num_inputs)
    counters.add_counter('input-place-names', len(place_names))
    counters.add_counter('input-place-coords', len(place_coords))
    # Resolve all places in batch.
    resolved_places = {}
    if place_names:
        logging.log_every_n(logging.DEBUG,
                            f'Resolving {len(place_names)} places names...',
                            self._log_every_n)
        resolved_places.update(pr.resolve_name(place_names))
        columns.extend(['dcid', 'placeId', 'lat', 'lng'])
    if place_coords:
        logging.log_every_n(logging.DEBUG,
                            f'Resolving {len(place_coords)} places coords...',
                            self._log_every_n)
        resolved_places.update(pr.resolve_latlng(place_coords))
        columns.append('placeDcids')
    counters.print_counters()
    if not output_filename:
        for key in range(num_inputs + 1):
            row = {}
            row.update(place_names.get(key, {}))
            row.update(place_coords.get(key, {}))
            row.update(resolved_places.get(key, {}))
            pp.pprint(row)
        return

    output_filename = file_util.file_get_name(output_filename, file_ext='.csv')
    if output_columns is None:
        output_columns = []
    for col in columns:
        if col not in output_columns:
            output_columns.append(col)
    logging.log_every_n(
        logging.INFO,
        f'Writing output {len(resolved_places)} rows with columns: {output_columns} into'
        f' {output_filename}', self._log_every_n)
    with file_util.FileIO(output_filename, mode='w') as output_fp:
        writer = csv.DictWriter(
            output_fp,
            escapechar='\\',
            fieldnames=output_columns,
            quotechar='"',
            quoting=csv.QUOTE_NONNUMERIC,
            extrasaction='ignore',
        )
        writer.writeheader()
        for key in range(num_inputs + 1):
            row = {}
            row.update(place_names.get(key, {}))
            row.update(place_coords.get(key, {}))
            row.update(resolved_places.get(key, {}))
            writer.writerow(row)


def main(_):
    # Launch a web server if --http_port is set.
    if process_http_server.run_http_server(script=__file__, module=__name__):
        return

    logging.set_verbosity(2)
    config = ConfigMap(filename=_FLAGS.resolve_config)
    config.set_config('places_csv', _FLAGS.place_names_csv)
    config.set_config('places_within', _FLAGS.place_names_within)
    config.set_config('place_type', _FLAGS.place_types)
    config.set_config('place_name_column', _FLAGS.place_name_column)
    config.set_config('place_latitude_column', _FLAGS.place_latitude_column)
    config.set_config('place_longitude_column', _FLAGS.place_longitude_column)
    config.set_config('places_resolved_csv', _FLAGS.place_resolver_cache)
    config.set_config('maps_api_key', _FLAGS.maps_key)
    config.set_config('maps_api_cache', _FLAGS.maps_api_cache)
    config.set_config('dc_api_key', _FLAGS.resolve_api_key)
    config.set_config('resolve_api_url', _FLAGS.resolve_api_url)
    config.set_config('dc_api_batch_size', _FLAGS.dc_api_batch_size)

    # uncomment to run pprof
    # if _FLAGS.place_pprof_port:
    #    start_pprof_server(port=FLAGS.place_pprof_port)
    process(
        _FLAGS.resolve_input_csv,
        _FLAGS.resolve_output_csv,
        _FLAGS.resolve_place_names,
        _FLAGS.maps_key,
        _FLAGS.output_place_columns,
        config,
    )


if __name__ == '__main__':
    app.run(main)
