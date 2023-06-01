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

from shapely import geometry
import datacommons as dc
import json
import logging
import time
import urllib

_WORLD = 'Earth'
_USA = 'country/USA'
_MAX_RETRIES = 3
_RETRY_DELAY = 15

_GJ_PROP = {
    'Country': 'geoJsonCoordinatesDP2',
    # Certain low-res geojsons are malformed for states
    'State': 'geoJsonCoordinates',
    'County': 'geoJsonCoordinates',
}


def _get_geojsons(place_type, parent_place, retry=0):
    try:
        places = dc.get_places_in([parent_place], place_type)[parent_place]
        resp = dc.get_property_values(places, _GJ_PROP[place_type])
        geojsons = {}
        for p, gj in resp.items():
            if not gj:
                continue
            geojsons[p] = geometry.shape(json.loads(gj[0]))
        return geojsons
    except urllib.error.URLError:
        if retry > _MAX_RETRIES:
            logging.error("Exceeded max retries(%s)" % str(_MAX_RETRIES))
            raise RuntimeError
        else:
            # retry after a small delay
            time.sleep(_RETRY_DELAY)
            return _get_geojsons(place_type, parent_place, retry + 1)


def _get_continent_map(countries):
    return dc.get_property_values(countries, 'containedInPlace')


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
