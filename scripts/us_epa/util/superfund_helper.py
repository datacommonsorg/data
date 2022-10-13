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
"""Helper functions used in the superfund data processing"""

import numpy as np
import pandas as pd
import json
import requests

_GEO_COORDS = []
_DC_RECON_API = "https://api.datacommons.org/v1/recon/resolve/coordinate"


def make_list_of_geos_to_resolve(latitude: np.float64,
                                 longitude: np.float64) -> None:
    """
    Utility function that adds a pair of latitiude and longitude to a list
    """
    _GEO_COORDS.append({"latitude": str(latitude), "longitude": str(longitude)})


def resolve_with_recon(output_path: str,
                       coords_list: list = _GEO_COORDS,
                       batch_size: int = 50) -> dict:
    """
    Calls the Recon API for every 50 location pairs and builds a map of resolved geoIds
    """
    # divide the list into non-overlapping chunk of batch_size
    coords_chunk_list = [
        coords_list[i:i + batch_size]
        for i in range(0, len(coords_list), batch_size)
    ]

    resolved_geos_map = {}

    # for each chunk resolve the coords to geoIds
    for chunk in coords_chunk_list:
        payload = {"coordinates": chunk}
        response_json = requests.post(_DC_RECON_API,
                                      data=json.dumps(payload),
                                      timeout=100.000).json()
        for response_elem in response_json['placeCoordinates']:
            try:
                place_dcid = [
                    x for x in response_elem["placeDcids"]
                    if 'zip' in x or ('geoId' in x and 'geoId/sch' not in x)
                ]
                resolved_geos_map[(
                    str(response_elem["latitude"]) + ',' +
                    str(response_elem["longitude"]))] = place_dcid
            except:
                print("This coordinate pair needs to be manually resolved: ",
                      response_elem)
                resolved_geos_map[(str(response_elem["latitude"]) + ',' +
                                   str(response_elem["longitude"]))] = ''

    # manual resolution for the missing geoIds
    ## resolution for zip code done by lookups at https://www.zipdatamaps.com/ & GMaps based on location name
    resolved_geos_map["40.464589,-74.258017"] = [
        'zip/08879', 'geoId/3465790', 'geoId/34023', 'geoId/34'
    ]
    resolved_geos_map["47.583889,-122.3625"] = [
        'zip/98106', 'geoId/5363000', 'geoId/53033', 'geoId/53'
    ]
    resolved_geos_map["43.749444,-87.70075"] = [
        'zip/53081', 'geoId/5572975', 'geoId/55117', 'geoId/55'
    ]

    # write resolved geo map to file, if output_path is specified
    if output_path:
        f = open(f"{output_path}/resolved_superfund_site_geoIds.json", "w")
        json.dump(resolved_geos_map, f, indent=4)
        f.close()
    return resolved_geos_map
