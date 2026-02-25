# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""A library that uses the GeoJSONs (from DC KG) to map lat/lng to DC places.

See latlng_recon_geojson_test.py for usage example.
"""

import json
import logging
from pathlib import Path
from shapely import geometry
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from util.dc_api_wrapper import dc_api_batched_wrapper
from util.dc_api_wrapper import dc_api_wrapper
from util.dc_api_wrapper import get_datacommons_client

_WORLD = 'Earth'
_USA = 'country/USA'
_MAX_RETRIES = 3
_RETRY_DELAY = 15
_DC_API_CONFIG = {
    'dc_api_retries': _MAX_RETRIES,
    'dc_api_retry_secs': _RETRY_DELAY,
}

_GJ_PROP = {
    'Country': 'geoJsonCoordinatesDP2',
    # Certain low-res geojsons are malformed for states
    'State': 'geoJsonCoordinates',
    'County': 'geoJsonCoordinates',
}


def _get_dc_client():
    return get_datacommons_client(_DC_API_CONFIG)


def _get_geojsons(place_type, parent_place):
    client = _get_dc_client()
    places_response = dc_api_wrapper(
        function=client.node.fetch_place_children,
        args={
            'place_dcids': [parent_place],
            'children_type': place_type,
            'as_dict': True,
        },
        retries=_MAX_RETRIES,
        retry_secs=_RETRY_DELAY,
    )
    if not places_response or parent_place not in places_response:
        response_keys = None
        if isinstance(places_response, dict):
            response_keys = sorted(places_response.keys())
        logging.error(
            'Failed to fetch place children. place_type=%s parent_place=%s '
            'response_type=%s response_keys=%s',
            place_type,
            parent_place,
            type(places_response).__name__,
            response_keys,
        )
        raise RuntimeError
    places = [
        node.get('dcid')
        for node in places_response.get(parent_place, [])
        if node.get('dcid')
    ]
    resp = dc_api_batched_wrapper(function=client.node.fetch_property_values,
                                  dcids=places,
                                  args={'properties': _GJ_PROP[place_type]},
                                  dcid_arg_kw='node_dcids',
                                  config=_DC_API_CONFIG)
    geojsons = {}
    for place in places:
        nodes = (resp.get(place, {}).get('arcs',
                                         {}).get(_GJ_PROP[place_type],
                                                 {}).get('nodes', []))
        if not nodes:
            continue
        geojson = nodes[0].get('value')
        if not geojson:
            continue
        geojsons[place] = geometry.shape(json.loads(geojson))
    return geojsons


def _get_continent_map(countries):
    client = _get_dc_client()
    resp = dc_api_batched_wrapper(function=client.node.fetch_property_values,
                                  dcids=countries,
                                  args={'properties': 'containedInPlace'},
                                  dcid_arg_kw='node_dcids',
                                  config=_DC_API_CONFIG)
    continent_map = {}
    for country in countries:
        nodes = (resp.get(country, {}).get('arcs',
                                           {}).get('containedInPlace',
                                                   {}).get('nodes', []))
        continent_map[country] = [
            node.get('dcid') for node in nodes if node.get('dcid')
        ]
    return continent_map


class LatLng2Places:
    """Helper class to map lat/lng to DC places using GeoJSON files.

       Right now it only supports: Country, Continent and US States.
    """

    def __init__(self):
        self._country_geojsons = _get_geojsons('Country', _WORLD)
        self._us_state_geojsons = _get_geojsons('State', _USA)
        self._us_county_geojsons = {}
        for state in self._us_state_geojsons.keys():
            self._us_county_geojsons.update(_get_geojsons('County', state))
        self._continent_map = _get_continent_map(
            [k for k in self._country_geojsons])
        print('Loaded',
              len(self._country_geojsons) + len(self._us_state_geojsons),
              'geojsons!')

    def resolve(self, lat, lon):
        """Given a lat/long returns a list of place DCIDs that contain it."""

        point = geometry.Point(lon, lat)
        country = None
        for p, gj in self._country_geojsons.items():
            if gj.contains(point):
                country = p
                break
        cip = []
        if country == _USA:
            for p, gj in self._us_state_geojsons.items():
                if gj.contains(point):
                    cip.append(p)
                    break
            for p, gj in self._us_county_geojsons.items():
                if gj.contains(point):
                    cip.append(p.zfill(5))
                    break
        if country:
            cip.append(country)
            cip.extend(self._continent_map[country])
        return cip
