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

import datacommons as dc
import json
from shapely import geometry

_WORLD = 'Earth'
_USA = 'country/USA'

_GJ_PROP = {
    'Country': 'geoJsonCoordinatesDP2',
    # Certain low-res geojsons are malformed for states
    'State': 'geoJsonCoordinates',
}


def _get_geojsons(place_type, parent_place):
    places = dc.get_places_in([parent_place], place_type)[parent_place]
    resp = dc.get_property_values(places, _GJ_PROP[place_type])
    geojsons = {}
    for p, gj in resp.items():
        if not gj:
            continue
        geojsons[p] = geometry.shape(json.loads(gj[0]))
    return geojsons


def _get_continent_map(countries):
    return dc.get_property_values(countries, 'containedInPlace')


class LatLng2Places:
    """Helper class to map lat/lng to DC places using GeoJSON files.

       Right now it only supports: Country, Continent and US States.

    Args:
       types: List of types to map to. If empty, all supported types are mapped.
    """

    def __init__(self, types=[]):
        self._country_geojsons = _get_geojsons('Country', _WORLD)
        self._us_state_geojsons = _get_geojsons('State', _USA)
        self._continent_map = _get_continent_map(
            [k for k in self._country_geojsons])
        self._types = types
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
        if country == _USA and self._check('State'):
            for p, gj in self._us_state_geojsons.items():
                if gj.contains(point):
                    cip.append(p)
                    break
        if country:
            if self._check('Country'):
                cip.append(country)
            if self._check('Continent'):
                cip.extend(self._continent_map[country])
        return cip

    def _check(self, typ):
        return not self._types or typ in self._types

