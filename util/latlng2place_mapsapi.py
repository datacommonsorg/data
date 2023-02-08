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
"""Library that converts a lat/lng into one or more place DCIDs using Maps API.

Currently supports resolution from lat/lng to admin-area2 (county-equivalent)
places, admin-area1 (state-equivalent) places and countries.

IMPORTANT NOTE: Please do not hardcode the API key in the calling programs,
instead pass it as flag arguments while running them.

Example:
  ll2p = latlng2place_mapsapi.Resolver(api_key='XYZ')
  try:
    dcids = ll2p.resolve(12.0, -34.0)
  except:
    logging.error('Failed to resolve 12.0, -34.0')
  ... more calls to ll2p.resolve() ...

CACHING: If you would like to cache results of lat/lng calls across runs, you
can set the `cache_file` argument to a file path.

"""

import os
import requests
import sys
import threading

# Allows the following module imports to work when running as a script
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))

import aa_isocode2dcid
import alpha2_to_dcid

_LOCK = threading.Lock()

# The MapsAPI place types that we map corresponding DCID to.  This list is
# ordered.
_PLACE_TYPES = ['administrative_area2', 'administrative_area1', 'country']

_RECON_ROOT = 'https://api.datacommons.org/v1/recon/resolve/id'


def _call_rpc(url):
    return requests.get(url, timeout=30).json()


def _placeid2dcid(place_id):
    resp = requests.post(_RECON_ROOT,
                         json={
                             'in_prop': 'placeId',
                             'out_prop': 'dcid',
                             'ids': [place_id]
                         })
    resp.raise_for_status()
    resp_json = resp.json()
    if 'entities' in resp_json and resp_json['entities']:
        return resp_json['entities'][0]['outIds'][0]
    return ''


class Resolver(object):
    """Resolves lat lngs to DCIDs using Maps API.

    Args:
        api_key: Maps API key
        cache_file: Optional path to the cache file
        cache_only: If true, then only the cache_file is used and
                    no API calls are made. Requires that cache_file is set.
    """

    def __init__(self, api_key, cache_file='', cache_only=False):
        assert api_key, 'Resolver() needs a valid API key'
        self._api_key = api_key
        self._cache_only = cache_only

        # lat/lngs -> list of DCIDs:  map of previous resolutions
        self._latlng2place = {}
        # Opened cache file
        self._cf = None

        if cache_file:
            try:
                with open(cache_file, 'r') as cf:
                    for line in cf:
                        parts = line.strip().split(',')
                        if len(parts) < 3:
                            continue
                        latlng = parts[0] + ',' + parts[1]
                        self._latlng2place[latlng] = parts[2:]
            except Exception:
                pass
            self._cf = open(cache_file, 'a+')

    def _url(self):
        return 'https://maps.googleapis.com/maps/api/geocode/json?sensor=false&key=' + self._api_key

    def _parse_result(self, result):
        """Parse results rom Cloud reverse geocoding service."""
        # Find the placeId in the result.
        if 'place_id' not in result or 'types' not in result:
            return []

        place_type = ''
        # Note: _PLACE_TYPES is specifically ordered.
        for pt in _PLACE_TYPES:
            mt = pt.replace('_area', '_area_level_')
            if mt in result['types']:
                place_type = pt
                break
        place_id = result['place_id']

        # Extract short-names.
        short_names = {}
        for place in result['address_components']:
            # Note: _PLACE_TYPES is specifically ordered.
            for pt in _PLACE_TYPES:
                mt = pt.replace('_area', '_area_level_')
                if mt in place['types']:
                    short_names[pt] = place['short_name']
                    break

        dcids = {}
        resolved_id = _placeid2dcid(place_id)
        if resolved_id:
            dcids[place_type] = resolved_id

        for pt, val in short_names.items():
            if pt in dcids:
                continue
            if pt == 'country':
                if val in alpha2_to_dcid.COUNTRY_MAP:
                    dcids[pt] = alpha2_to_dcid.COUNTRY_MAP[val]
            elif 'country' in short_names:
                key = short_names['country'] + '-' + val
                if key in aa_isocode2dcid.AA_ISOCODE2DCID_MAP:
                    dcids[pt] = aa_isocode2dcid.AA_ISOCODE2DCID_MAP[key]

        return [] if not dcids else list(dcids.values())

    def _geocode(self, latlng):
        """Use the Cloud reverse geocoding service to resolve lat longs to dcids."""
        # Result from a smaller place type (like county) contains info about the
        # larger place (state, country), and is generally preferred. However, the
        # smaller place type may not exist for some lat/lngs, and in such cases,
        # we try the larger place.
        dcids = []
        for place_type in _PLACE_TYPES:
            url = (self._url() + '&result_type=' +
                   place_type.replace('_area', '_area_level_') + '&latlng=' +
                   latlng)
            resp_json = _call_rpc(url)
            if not resp_json:
                continue
            if resp_json['status'] not in ['OK', 'ZERO_RESULTS']:
                raise LookupError(resp_json['status'] + ': ' +
                                  resp_json['error_message'])
            if resp_json['results']:
                dcids = self._parse_result(resp_json['results'][0])
                break
        return dcids

    def resolve(self, lat, lng):
        """Takes a lat, lng in decimal format; returns list of containing DCIDs."""
        latlng = str(lat) + ',' + str(lng)
        dcids = []
        with _LOCK:
            if latlng in self._latlng2place:
                dcids = self._latlng2place[latlng]
        if not dcids and not self._cache_only:
            dcids = self._geocode(latlng)
            if not dcids:
                raise LookupError('Could not resolve to DCID')
            with _LOCK:
                self._latlng2place[latlng] = dcids
                if self._cf:
                    self._cf.write(latlng + ',' + ','.join(dcids) + '\n')
        return dcids
