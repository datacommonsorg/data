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
"""Class to resolve places to wikidata Ids."""

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
flags.DEFINE_integer(
    'wiki_place_pprof_port', 0, 'HTTP port for running pprof server.'
)

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util')
)

import file_util
import download_util
import process_http_server

from counters import Counters
from config_map import ConfigMap
from download_util import request_url

_DEFAULT_CONFIG = {
    # Map of wiki place property to DC property
    'wiki_place_property': {
        'labels': 'name',
        'descriptions': 'description',
        'P31': 'PlaceType',
        'P131': 'ContainedInPlace',
        'P17': 'Country',
        'P626': 'Location',
    },
    'wiki_languages': ['en'],
    # Search URL for wiki names.
    # replace KEY with your key
    'wiki_search_url': 'https://www.googleapis.com/customsearch/v1?key=KEY&cx=b5b4628916b534fef&q=',
    # Number of wiki search results to lookup (upto 10)
    'wiki_search_max_results': 3,
    # URL for wiki API that returns a json with wiki properties.
    'wiki_api_url': (
        'https://www.wikidata.org/w/rest.php/wikibase/v0/entities/items/'
    ),
}


class WikiPlaceResolver:
  """Class to resolve places to wikidataIds.

  Uses Google Custom Search APi to lookup wiki pages for place names.
  For a wiki id, looks up wiki API for place properties.
  """

  def __init__(
      self,
      config_dict: dict = {},
      counters_dict: dict = None,
  ):
    self._config = ConfigMap(_DEFAULT_CONFIG)
    self._config.update_config(config_dict)
    self._counters = Counters(counters_dict)
    self._wiki_id_names = {}
    self._wiki_id_json = {}

  def lookup_wiki_places(self, places: dict, wiki_props: dict = None) -> dict:
    """Returns a dict with wiki properties for each place in the input places dict.

    Args:
      places: dict with properties: 'name': Name of the place to be looked up
        'wikidataId': wiki id if known.

    Returns:
      Dictionary with the properties for the place.
    """
    lookup_names = {}
    for key in places.keys():
      pvs = places[key]
      name = ''
      if not pvs:
        pvs = dict()
        places[key] = pvs
      name = pvs.get('name')
      if not name:
        name = key
      wiki_id = pvs.get('wikidataId', _get_wiki_id(name))
      if wiki_id:
        pvs['wikidataId'] = wiki_id
        continue
      lookup_names[name] = key
    self._counters.add_counter('total', len(places))

    # Get candidate wiki Ids for all names
    wiki_ids = set()
    logging.info(f'Looking up wiki items for {len(lookup_names)} names')
    for name in lookup_names.keys():
      wiki_name_ids = self.search_wiki_name(name)
      place_pvs = places[lookup_names[name]]
      if wiki_name_ids:
        place_pvs['wikidataId'] = _get_wiki_id(wiki_name_ids[0])
        if len(wiki_name_ids) > 1:
          place_pvs['CandidateWikiIds'] = wiki_name_ids[1:]

    # Lookup properties for each place
    keys = list(places.keys())
    for key in keys:
      place_pvs = places[key]
      wiki_id = _get_wiki_id(key)
      if not wiki_id:
        wiki_id = _get_wiki_id(place_pvs.get('wikidataId'))
      if wiki_id:
        wiki_pvs = self.lookup_wiki_properties(wiki_id)
        place_pvs.update(wiki_pvs)
      # Get properties for any candidates
      for candidate_wiki_id in place_pvs.get('CandidateWikiIds', []):
        wiki_pvs = self.lookup_wiki_properties(candidate_wiki_id)
        if candidate_wiki_id not in places:
          places[candidate_wiki_id] = dict()
        places[candidate_wiki_id].update(wiki_pvs)
      self._counters.add_counter('processed', 1)
    return places

  def search_wiki_name(self, name: str, max_results: int = None) -> list:
    """Returns a list of wikiIds for the given name using Custom Search API."""
    if not max_results:
      max_results = self._config.get('wiki_search_max_results', 1)
    search_url = self._config.get('wiki_search_url')
    logging.debug(f'Searching wiki for name "{name}" with {search_url}')
    search_url += urllib.parse.urlencode({'q': name})
    self._counters.add_counter('wiki-searches', 1, name)
    resp = download_util.request_url(search_url, output='json', use_cache=True)
    if not resp:
      self._counters.add_counter('wiki-searches-failures', 1, name)
      return []

    # Get all wiki results for name.
    result_wids = []
    for result in resp.get('items', []):
      link = result.get('link')
      if link and '/wiki/Q' in link:
        url, wikidata_id = link.split('wiki/', 1)
        if 'wikidata.org' in url and wikidata_id.startswith('Q'):
          result_wids.append(wikidata_id)
    logging.level_debug() and logging.debug(
        f'Got {len(result_wids)} wiki ids for "{name}": {result_wids}'
    )
    self._counters.add_counter(f'wiki-search-results-{len(result_wids)}', 1, name)
    return result_wids[:max_results]

  def lookup_wiki_properties(self, wiki_id: str, props: dict = None) -> dict:
    """Returns a dict of wiki properties for a wiki id."""
    if not wiki_id:
      return {}
    wiki_json = self._get_wiki_json(wiki_id)
    wiki_pvs = {}
    if not props:
      props = self._config.get(f'wiki_place_property')

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
            wiki_pvs[dc_prop + '_name'] = val_names
    logging.level_debug() and logging.debug(
        f'Got wiki properties for {wiki_id}: {props}: {wiki_pvs}'
    )
    return wiki_pvs

  def _get_wiki_json(self, wiki_id: str) -> dict:
    """Returns the json for the wiki id."""
    wiki_json = self._wiki_id_json.get(wiki_id)
    if wiki_json is None:
      # No cached value. Lookup wiki API
      wiki_api_url = self._config.get('wiki_api_url')
      self._counters.add_counter('wiki-api-lookups', 1, wiki_id)
      wiki_json = download_util.request_url(
          wiki_api_url + wiki_id, output='json', use_cache=True
      )
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
    return names

  def _get_wiki_json_property(
      self, wiki_json: dict, wiki_prop: str, langs: list = None
  ) -> list:
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
    return values


def _get_wiki_id(wiki_id: str) -> str:
  """Returns the wikidataId without the wikidataId/ prefix."""
  if not wiki_id:
    return ''
  q_pos = wiki_id.find('Q')
  if q_pos < 0:
    return ''
  q_str = wiki_id[q_pos:]
  if q_str[1:].isnumeric():
    return q_str
  return ''


def main(_):
  # Launch a web server if --http_port is set.
  if process_http_server.run_http_server(script=__file__, module=__name__):
    return

  logging.set_verbosity(2)

  config = ConfigMap(_FLAGS.wiki_place_config)
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
