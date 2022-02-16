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
"""A library that uses the recon service to map lat/lng to DC places."""

import requests

_RECON_ROOT = 'https://staging.recon.datacommons.org/coordinate/resolve'
_RECON_COORD_BATCH_SIZE = 50


def _call_resolve_coordinates(id2latlon, filter_fn, verbose):
    revmap = {}
    coords = []
    for dcid, (lat, lon) in id2latlon.items():
        coords.append({'latitude': lat, 'longitude': lon})
        revmap[(lat, lon)] = dcid
    result = {}
    if verbose:
        print('Calling recon API with a lat/lon list of', len(id2latlon))
    resp = requests.post(_RECON_ROOT, json={'coordinates': coords})
    resp.raise_for_status()
    if verbose:
        print('Got successful recon API response')
    for coord in resp.json()['placeCoordinates']:
        # Zero lat/lons are missing
        # (https://github.com/datacommonsorg/mixer/issues/734)
        if 'latitude' not in coord:
            coord['latitude'] = 0.0
        if 'longitude' not in coord:
            coord['longitude'] = 0.0
        key = (coord['latitude'], coord['longitude'])
        assert key in revmap, key
        cips = []
        if 'placeDcids' in coord:
            cips = coord['placeDcids']
        if filter_fn:
            result[revmap[key]] = filter_fn(cips)
        else:
            result[revmap[key]] = cips
    return result


def latlng2places(id2latlon, filter_fn=None, verbose=False):
    """Given a map of ID->(lat,lng), resolves the lat/lng and returns a list of
       places by calling the Recon service (in a batched way).

    Args:
        id2latlon: A dict from any distinct ID to lat/lng. The response uses the
                   same ID as key.
        filter_fn: An optional function that takes a list of place DCIDs and
                   may return a subset of them.  For example, if you want to
                   filter out only countries.
        verbose: Print debug messages during execution.
    Returns:
        A dict keyed by the ID passed in "id2latlon" with value containing a
        list of places.
    """

    batch = {}
    result = {}
    for dcid, (lat, lon) in id2latlon.items():
        batch[dcid] = (lat, lon)
        if len(batch) == _RECON_COORD_BATCH_SIZE:
            result.update(_call_resolve_coordinates(batch, filter_fn, verbose))
            batch = {}
    if len(batch) > 0:
        result.update(_call_resolve_coordinates(batch, filter_fn, verbose))
    return result
