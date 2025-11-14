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
"""A library that uses the recon service to map lat/lng to DC places.

See latlng_recon_service_test.py for usage example.
"""

import concurrent.futures
import requests
from typing import Callable, Dict, List, NewType, TypeVar, Tuple
from .dc_api_wrapper import dc_api_resolve_latlng

LatLngType = NewType('LatLngType', Tuple[float, float])
ResolvedLatLngType = NewType('ResolvedLatLngType', Dict[str, List[str]])

_RECON_COORD_BATCH_SIZE = 50

LatLng = NewType('LatLng', Tuple[float, float])
DCID = TypeVar('DCID')
ResolvedLatLng = NewType('ResolvedLatLng', Dict[DCID, List[str]])


def _session(retries: int = 5, backoff_factor: int = 0.5) -> 'requests.Session':
    """Helper method to retry calling recon service automatically.

    Args:
        retries: max number of retries allowed.
        backoff_factor:
            sleep for backoff_factor * (2 ** ({retries} - 1)) seconds
            between retries.
    Returns:
        retryable requests session.

    For more on sessions, see:
    https://requests.readthedocs.io/en/latest/user/advanced/
    """
    s = requests.Session()
    retries = requests.adapters.Retry(
        total=retries,
        backoff_factor=backoff_factor,
        # Force retries even for 5xx status codes.
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "POST"])
    s.mount('https://', requests.adapters.HTTPAdapter(max_retries=retries))
    return s


def _call_resolve_coordinates(id2latlon: Dict[LatLngType, Tuple[str]],
                              filter_fn: Callable, verbose: bool):
    revmap = {}
    coords = []
    for dcid, (lat, lon) in id2latlon.items():
        coords.append({'latitude': lat, 'longitude': lon})
        revmap[(lat, lon)] = dcid
    result = {}
    if verbose:
        print('Calling recon API with a lat/lon list of', len(id2latlon))
    resp = dc_api_resolve_latlng(coords, return_v1_response=True)
    if verbose:
        print('Got successful recon API response')
    for coord in resp['placeCoordinates']:
        # Zero lat/lons are missing
        # (https://github.com/datacommonsorg/mixer/issues/734)
        if 'latitude' not in coord:
            coord['latitude'] = 0.0
        if 'longitude' not in coord:
            coord['longitude'] = 0.0
        key = (coord['latitude'], coord['longitude'])
        cips = []
        if 'placeDcids' in coord:
            cips = coord['placeDcids']
        if filter_fn:
            result[revmap[key]] = filter_fn(cips)
        else:
            result[revmap[key]] = cips
    return result


def latlng2places(id2latlon: Dict[str, LatLngType],
                  filter_fn: Callable = None,
                  verbose: bool = False) -> Dict[str, Tuple[str]]:
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
    with concurrent.futures.ThreadPoolExecutor() as executor:
        batch = {}
        futures = []
        for dcid, (lat, lon) in id2latlon.items():
            batch[dcid] = (lat, lon)
            if len(batch) == _RECON_COORD_BATCH_SIZE:
                futures.append(
                    executor.submit(_call_resolve_coordinates, batch, filter_fn,
                                    verbose))
                batch = {}
        if len(batch) > 0:
            futures.append(
                executor.submit(_call_resolve_coordinates, batch, filter_fn,
                                verbose))
        result = {}
        for future in concurrent.futures.as_completed(futures):
            result.update(future.result())
    return result
