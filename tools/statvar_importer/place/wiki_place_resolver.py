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
"""Class to resolve places to wikidata Ids.

It uses Google Custom Search (https://developers.google.com/custom-search/v1/introduction)
with a site restrict on http://wikidata.org to lookup places matching names.
The Wikidata API is used to retrieve properties for the results.

Get a SEARCH_API_KEY following steps in
https://developers.google.com/custom-search/v1/introduction.

To resolve a list of place names into wikidataIds,
create a csv with the column 'place_name' containg the names to be resolved,
then run the command:
  python3 wiki_place_resolver.py \
      --wiki_place_input_csv=<places-csv> \
      --wiki_place_output_csv=<out-csv> \
      --custom_search_key=<SEARCH_API_KEY>

The output file will have the following columns:
  "key"
  "wikidataId": the first search result for hte place name in the key
  "CandidateWikiIds": Additional wikidata Ids for place name returned by search engine
  "name": Name of the wikidata entry
  "description": Description of the wikidata item
  "PlaceType": wikidata id of the type
  "PlaceTypeName": name of the wikidata id for type
  "ContainedInPlace": Wikidata Id of parent places
  "ContainedInPlaceName": parent place name
  "Country": parent country wikidata id
  "CountryName": parent country name
"""

import json
import os
import sys
import urllib.parse

from absl import app
from absl import flags
from absl import logging

# uncomment to run pprof
# from pypprof.net_http import start_pprof_server

_FLAGS = flags.FLAGS

flags.DEFINE_list(
    'wiki_place_input_csv',
    '',
    'Input csv with places to resolve under column "name".',
)
flags.DEFINE_string('wiki_place_output_csv', '', 'Output csv with place dcids.')
flags.DEFINE_list('wiki_place_names', [], 'List of place names to resolve.')
flags.DEFINE_string(
    'wiki_place_config',
    '',
    'Config setting for place resolution as json or python dict.',
)
flags.DEFINE_list(
    'wiki_place_properties',
    '',
    'List of wiki place property codes, such as P31',
)
flags.DEFINE_string(
    'custom_search_key', os.environ.get('SEARCH_API_KEY', ''),
    'API key for Google custom search API.'
    'Get an API key at https://developers.google.com/custom-search/v1/introduction.'
)
flags.DEFINE_integer('wiki_place_pprof_port', 0,
                     'HTTP port for running pprof server.')

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(_SCRIPT_DIR))),
                 'util'))

import download_util
import file_util
import mcf_file_util
import process_http_server

from counters import Counters
from config_map import ConfigMap
from download_util import request_url
from property_value_cache import PropertyValueCache

_DEFAULT_CONFIG = {
    # Map of wiki place property to named property
    'wiki_place_property': {
        'labels': 'name',
        'descriptions': 'description',
        'P31': 'PlaceType',
        'P131': 'ContainedInPlace',
        'P17': 'Country',
        'P626': 'Location',
    },

    # Get names in a set of languages
    'wiki_languages': ['en'],

    # Search URL for wiki names with site restrict of wikidata.org.
    # replace KEY with your key
    'wiki_search_url':
        'https://www.googleapis.com/customsearch/v1?key=KEY&cx=b5b4628916b534fef&',

    # Number of wiki search results to lookup (upto 10)
    'wiki_search_max_results':
        3,

    # URL for wiki API that returns a json with wiki properties.
    'wiki_api_url':
        ('https://www.wikidata.org/w/rest.php/wikibase/v1/entities/items/'),
}


class WikiPlaceResolver:
    """Class to resolve places to wikidataIds.

  Uses Google Custom Search API to lookup wiki pages for place names.
  For a wiki id, looks up wiki API for place properties.

  To lookup wikidata Ids or properties for places:
    lookup_places = {
      # Lookup wikidataId for place name
      {'name': 'Delhi' },
      # Lookup properties by wikidataId
      {'name': 'Sikkim', 'wikidataId': 'Q1505' },
    }
    wiki_resolver = WikiPlaceResolver(config={'custom_search_key': <KEY>})
    results = wiki_resolver.lookup_wiki_places(lookup_places)
  """

    def __init__(
        self,
        config_dict: dict = {},
        counters_dict: dict = None,
        cache: PropertyValueCache = None,
    ):
        self._config = ConfigMap(_DEFAULT_CONFIG)
        self._config.update_config(config_dict)
        self._counters = Counters(counters_dict)
        self._log_every_n = self._config.get('log_every_n', 10)
        # Cache of wiki properties looked up by wikiId
        self._wiki_id_json = {}
        self._wiki_id_names = {}
        # Persistent cache of property:values looked up with APIs
        self._cache = cache
        if cache is None:
            self._cache = PropertyValueCache(counters=self._counters)

    def is_ready(self) -> bool:
        """Returns True if config has the rquired settings."""
        search_url = self._get_wiki_search_url()
        if not search_url:
            return False
        return True

    def get_config_wiki_props(self) -> dict:
        """Returns the list of wiki props to be looked up."""
        return self._config.get('wiki_place_property')

    def lookup_wiki_places(self, places: dict) -> dict:
        """Returns a dict with wiki properties for each place in the input places dict.

    Args:
      places: dict with properties: 'name': Name of the place to be looked up

    Returns:
      Dictionary with the following properties for the place.
        'wikidataId': wiki id if known.
        'name': name string in double quotes to be looked up
    """
        # Get the list of names to lookup in wiki search
        lookup_names = {}
        for key in places.keys():
            pvs = places[key]
            name = ''
            if pvs is None:
                pvs = dict()
                places[key] = pvs
            name = pvs.get('name')
            if not name:
                name = pvs.get('place_name')
            if not name:
                name = key
            if not name or not isinstance(name, str):
                logging.level_debug() and logging.log_every_n(
                    logging.DEBUG,
                    f'Ignoring place {name} for wiki lookup: {key}:{pvs}',
                    self._log_every_n)
                continue
            name = name.strip('"')
            wiki_id = get_wiki_id_from_pvs(pvs, key)
            if wiki_id:
                # Reuse existing wikidataId for the name
                pvs['wikidataId'] = wiki_id
                continue
            # Place doesn't have a wikidataId.
            lookup_names[name] = key

        # Get candidate wiki Ids for all names
        wiki_ids = set()
        logging.log_every_n(
            logging.DEBUG, f'Looking up wiki ids for {len(lookup_names)} names',
            self._log_every_n)
        for name in lookup_names.keys():
            place_pvs = places[lookup_names[name]]
            wiki_name_ids = self.search_wiki_name(name)
            if wiki_name_ids:
                place_pvs['wikidataId'] = _get_wiki_id(wiki_name_ids[0])
                if len(wiki_name_ids) > 1:
                    place_pvs['CandidateWikiIds'] = wiki_name_ids[1:]

        # Lookup wiki properties for each place
        keys = list(places.keys())
        for key in keys:
            place_pvs = places[key]
            wiki_id = get_wiki_id_from_pvs(place_pvs, key)
            logging.log_every_n(
                logging.DEBUG,
                f'Looking up wiki properties for wiki: {wiki_id} for {place_pvs}',
                self._log_every_n)
            if wiki_id:
                wiki_pvs = self.lookup_wiki_properties(wiki_id)
                _update_node(wiki_pvs, place_pvs)
            # Get properties for any candidates
            for candidate_wiki_id in place_pvs.get('CandidateWikiIds', []):
                wiki_pvs = self.lookup_wiki_properties(candidate_wiki_id)
                if candidate_wiki_id not in places:
                    places[candidate_wiki_id] = {
                        'wikidataId': candidate_wiki_id
                    }
                _update_node(wiki_pvs, places[candidate_wiki_id])
            if self._cache:
                self._cache.add(place_pvs)
        return places

    def search_wiki_name(self, name: str, max_results: int = None) -> list:
        """Returns a list of wikiIds for the given name using Custom Search API.

    Args:
        name: name to lookup for wiki page.
        max_results: maximum number of matches to return

    Returns:
        list of wikidataIds that match the name.
    """
        result_wiki_ids = []
        cached_entry = self._cache.get_entry(value=name)
        if cached_entry:
            wiki_id = cached_entry.get('wikidataId')
            if wiki_id:
                result_wiki_ids.append(wiki_id)
            candidate_wiki_ids = cached_entry.get('CandidateWikiIds')
            if candidate_wiki_ids:
                result_wiki_ids.extend(candidate_wiki_ids)
        if result_wiki_ids:
            self._counters.add_counter('wiki-id-cache-hits', 1)
            return result_wiki_ids
        search_url = self._get_wiki_search_url()
        if not search_url:
            return []
        if not max_results:
            max_results = self._config.get('wiki_search_max_results', 1)
        search_url += urllib.parse.urlencode({'q': name})
        logging.level_debug() and logging.log_every_n(
            logging.DEBUG,
            f'Searching for {max_results} wikis for name "{name}" with {search_url}',
            self._log_every_n)
        self._counters.add_counter('wiki-name-searches', 1, name)
        resp = download_util.request_url(search_url,
                                         output='json',
                                         use_cache=True)
        logging.level_debug() and logging.log_every_n(
            logging.DEBUG, f'Got wiki search response for {name}: {resp}',
            self._log_every_n)
        if not resp:
            self._counters.add_counter('wiki-name-searches-failures', 1, name)
            return []

        # Get all wiki results for name.
        for result in resp.get('items', []):
            link = result.get('link')
            if link and '/wiki/Q' in link:
                wikidata_id = _get_wiki_id(link)
                if wikidata_id:
                    result_wiki_ids.append(wikidata_id)
        logging.level_debug() and logging.log_every_n(
            logging.DEBUG,
            f'Got {len(result_wiki_ids)} wiki ids for "{name}": {result_wiki_ids}',
            self._log_every_n)
        self._counters.add_counter(
            f'wiki-search-results-{len(result_wiki_ids)}', 1, name)
        return result_wiki_ids[:max_results]

    def lookup_wiki_properties(self, wiki_id: str, props: dict = None) -> dict:
        """Returns a dict of wiki properties for a wiki id.

        Args:
            wiki_id: wiki id to lookup
            props: dictionary of wiki property to property names.
        Returns:
            dictionary of property: values with property name from props.
        """
        if not wiki_id:
            return {}
        wiki_pvs = {}
        if not props:
            props = self._config.get(f'wiki_place_property')
        # Check if cache has any looked up property
        cached_entry = self._cache.get_entry(prop='wikidataId', value=wiki_id)
        if cached_entry:
            for p in props:
                if p == 'wikidataId':
                    # Look for wiki properties other than wikidataId
                    continue
                v = cached_entry.get(p)
                if v:
                    self._counters.add_counter('wiki-prop-cache-hits', 1)
                    return cached_entry
        # Get the json for wiki item with all properties.
        # Uses a cached value if present or looksup wiki API
        wiki_json = self._get_wiki_json(wiki_id)

        # Get all wiki properties
        for wiki_prop, dc_prop in props.items():
            values = self._get_wiki_json_property(wiki_json, wiki_prop)
            if values:
                wiki_pvs[dc_prop] = values
                if isinstance(values, list):
                    # Lookup names for values that are wikidata ids.
                    val_names = []
                    for val in values:
                        if val.startswith('Q'):
                            names = self._get_wiki_name(val)
                            if names:
                                val_names.append(names[0])
                    if val_names:
                        wiki_pvs[dc_prop + 'Name'] = val_names
        logging.level_debug() and logging.log_every_n(
            logging.DEBUG,
            f'Got wiki properties for {wiki_id}: {props}: {wiki_pvs}',
            self._log_every_n)
        return wiki_pvs

    def _get_wiki_search_url(self) -> str:
        """Returns the wiki search URL is config is setup properly. """
        api_key = self._config.get('custom_search_key', '')
        if not api_key:
            logging.log_every_n(
                logging.DEBUG,
                f'custom_search_key not set in config. Unable to look for wikiId',
                self._log_every_n)
            return False
        search_url = self._config.get('wiki_search_url')
        search_url = search_url.replace('KEY', api_key)
        return search_url

    def _get_wiki_json(self, wiki_id: str) -> dict:
        """Returns the json for the wiki id."""
        wiki_json = self._wiki_id_json.get(wiki_id)
        if wiki_json is None:
            # No cached value. Lookup wiki API
            wiki_api_url = self._config.get('wiki_api_url')
            self._counters.add_counter('wiki-api-lookups', 1, wiki_id)
            wiki_json = download_util.request_url(wiki_api_url + wiki_id,
                                                  output='json',
                                                  use_cache=True)
            self._wiki_id_json[wiki_id] = wiki_json
            if not wiki_json:
                self._counters.add_counter('wiki-api-failures', 1, wiki_id)
        else:
            self._counters.add_counter(f'wiki-api-cache-hits', 1)
        return wiki_json

    def _get_wiki_name(self, wiki_id: str) -> list:
        """Returns the names for the wiki id from cache or looks up using API."""
        names = self._wiki_id_names.get(wiki_id)
        if not names:
            # No cached name. Lookup name from wiki json.
            wiki_json = self._get_wiki_json(wiki_id)
            names = self._get_wiki_json_property(wiki_json, 'labels')
            if names:
                self._wiki_id_names[wiki_id] = names
        return names

    def _get_wiki_json_property(self,
                                wiki_json: dict,
                                wiki_prop: str,
                                langs: list = None) -> list:
        """Returns a list of values for a property from the wiki json."""
        if not wiki_json:
            return []
        if not langs:
            langs = self._config.get('wiki_languages', ['en'])
        values = []
        if wiki_prop in wiki_json:
            # Lookup value of direct property
            prop_item = wiki_json[wiki_prop]
            if isinstance(prop_item, dict):
                # Property has multiple values in different languages.
                if langs and '*' in langs:
                    langs = list(lang)
                    langs.append(prop_item.keys())
                for lang in langs:
                    value = prop_item.get(lang)
                    if value:
                        if lang != 'en':
                            value = value + f'@{lang}'
                        values.append('"' + value + '"')
                return values
        # Property is a statement.
        stmt = wiki_json.get('statements')
        if not stmt:
            return []
        prop_items = stmt.get(wiki_prop, [])
        for item in prop_items:
            val = item.get('value', {}).get('content')
            if val:
                values.append(val)
        # TODO: Add properties for coordinate
        return values


def get_wiki_id_from_pvs(pvs: dict, key: str = '') -> str:
    """Returns the wiki id from the property:values."""
    wiki_id = _get_wiki_id(key)
    if wiki_id:
        return wiki_id
    wiki_id = _get_wiki_id(pvs.get('wikidataId'))
    if wiki_id:
        return wiki_id
    wiki_id = _get_wiki_id(pvs.get('dcid', pvs.get('Node')))
    return wiki_id


def _get_wiki_id(wiki_id: str) -> str:
    """Returns the wikidataId of the form Q<NNNNN> from wiki_id string."""
    if not wiki_id or not isinstance(wiki_id, str):
        return ''
    q_pos = wiki_id.find('Q')
    if q_pos < 0:
        return ''
    q_str = wiki_id[q_pos:]
    if q_str[1:].isnumeric():
        return q_str
    return ''


def _update_node(pvs: dict, node: dict) -> dict:
    """Returns the node with property:values from pvs added."""
    for prop, value in pvs.items():
        mcf_file_util.add_pv_to_node(prop, value, node)
    return node


def main(_):
    # Launch a web server if --http_port is set.
    if process_http_server.run_http_server(script=__file__, module=__name__):
        return

    logging.set_verbosity(2)

    config = ConfigMap(_FLAGS.wiki_place_config)
    if _FLAGS.custom_search_key:
        config.set_config('custom_search_key', _FLAGS.custom_search_key)
    wiki_place_resolver = WikiPlaceResolver(config_dict=config.get_configs())
    input_csv = _FLAGS.wiki_place_input_csv
    places = file_util.file_load_py_dict(input_csv)
    logging.info(f'Looking up wiki properties for {len(places)}')
    wiki_places = wiki_place_resolver.lookup_wiki_places(places)
    if wiki_places:
        output_csv = _FLAGS.wiki_place_output_csv
        if not output_csv:
            output_csv = input_csv
        file_util.file_write_py_dict(wiki_places, output_csv)


if __name__ == '__main__':
    app.run(main)
