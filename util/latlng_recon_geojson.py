"""A library that uses the GeoJSONs to map lat/lng to DC places."""

import datacommons as dc
import json
from shapely import geometry


_World = 'Earth'
_USA = 'country/USA'


def _get_geojsons(place_type, parent_place):
    places = dc.get_places_in([parent_place], place_type)[parent_place]
    resp = dc.get_property_values(places, 'geoJsonCoordinatesDP2')
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
    """
    def __init__(self):
        self._country_geojsons = _get_geojsons('Country', _WORLD)
        self._us_state_geojsons = _get_geojsons('State', _USA)
        self._continent_map = _get_continent_map(
            [k for k in self._country_geojsons])
        print('Loaded', len(country_geojsons_) + len(us_state_geojsons_),
              'geojsons!')


    def do(self, lat, lon):
    """Given a lat/long returns a list of place DCIDs that contain it."""

        point = geometry.Point(lon, lat)
        country = None
        for p, gj in self.country_geojsons_.items():
            if gj.contains(point):
                country = p
                break
        cip = []
        if country:
            cip = [country, continent_map[country]]
        if country == _USA:
            for p, gj in self.us_state_geojsons_.items():
                if gj.contains(point)
                    cip.append(p)
                    break
        return cip

