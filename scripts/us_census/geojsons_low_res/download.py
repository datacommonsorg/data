# Copyright 2020 Google LLC
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
"""
Downloads and saves GeoJson map files from DataCommons.
    Typical usage:
    python3 download.py
"""

import geojson
import os
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from util.dc_api_wrapper import dc_api_get_node_property, get_datacommons_client


class GeojsonDownloader:
    """Downloads desired GeoJSON files from the DataCommons Knowledge Graph.

    Attributes:
        geojsons: A dictionary that maps each queried area to another
                  dictionary containing the GeoJSON coordinate information. An
                  example of this is the following

                {   # Multipolygon of the state of Alabama (fake).
                    "geoId/01": [{
                        "type": "MultiPolygon",

                        # Set of individual Polygons that compose it.
                        "coordinates": [
                            # Polygon 1
                            [[ [1.5, 12.4], [5.3, 45.2], [1.1, 3.5],
                                                            [1.5, 12.4] ]],
                            # Polygon 2
                            [[ [1, 2], [3, 4], [5, 6], [2, -1], [1, 2] ]],
                            # Polygon 3
                            [[ [53, 23], [65, 2], [31, 12], [53, 23] ]]
                        ]
                    }],
                    # Polygon of the state of Wyoming (fake).
                    # Since Wyoming is a single chunk of land, its type
                    # is Polygon instead of Multipolygon.
                    "geoId/17": [{
                        "type": "Polygon",
                        "coordinates": [
                            # Polygon 1
                            [[ [1.5, 12.4], [5.3, 45.2], [1.1, 3.5],
                                                            [1.5, 12.4] ]]
                        ]
                    }]

                }
    """
    LEVEL_MAP = {
        "Country": "AdministrativeArea1",
        "AdministrativeArea1": "AdministrativeArea2",
        "AdministrativeArea2": "City"
    }

    def __init__(self):
        self._dc_client = get_datacommons_client()
        self.geojsons = None

    def download_data(self, place='country/USA', level=1):
        """Downloads GeoJSON data for a specified location.

        Given the specified location, extracts the GeoJSONs of all
        administrative areas one level below it (as specified by the
        LEVEL_MAP class constant). For example, if the input is country/USA,
        extracts all AdministrativeArea1's within the US (US states).

        Args:
            place: A string that is a valid value for the geoId property of a
                   DataCommons node.
            level: Number of administrative levels down from place that should
                   be fetched. For example if place='country/USA' and level=1,
                   US states will be fetched. If instead level=2, US counties
                   will be fetched, and so on.

        Raises:
            ValueError: If a Data Commons API call fails.
        """
        geolevel_response = dc_api_get_node_property([place], 'typeOf')
        geolevel_values = geolevel_response.get(place, {}).get('typeOf', '')
        geolevel_values = [
            x.strip().strip('"')
            for x in geolevel_values.split(',')
            if x.strip()
        ]
        assert len(geolevel_values) == 1
        geolevel = geolevel_values[0]

        for i in range(level):
            if geolevel not in self.LEVEL_MAP:
                raise ValueError("Desired level does not exist.")
            geolevel = self.LEVEL_MAP[geolevel]

        geos_contained_in_place = []
        place_children = self._dc_client.node.fetch_place_children(
            place_dcids=[place], children_type=geolevel, as_dict=True)
        for node in place_children.get(place, []):
            dcid = node.get("dcid") if isinstance(node, dict) else node.dcid
            if dcid:
                geos_contained_in_place.append(dcid)

        geojson_response = self._dc_client.node.fetch_property_values(
            node_dcids=geos_contained_in_place,
            properties="geoJsonCoordinates").get_properties()
        self.geojsons = {}
        for area in geos_contained_in_place:
            coords = []
            for node in geojson_response.get(area,
                                             {}).get("geoJsonCoordinates", []):
                value = node.get("value") if isinstance(node,
                                                        dict) else node.value
                if value:
                    coords.append(value)
            self.geojsons[area] = coords
        for area, coords in self.iter_subareas():
            self.geojsons[area][0] = geojson.loads(coords)

    def get_subarea(self, area):
        if not self.geojsons[area]:
            return False
        assert len(self.geojsons[area]) == 1
        return self.geojsons[area][0]

    def iter_subareas(self):
        for area in self.geojsons:
            obj = self.get_subarea(area)
            if not obj or 'geoId' not in area:
                continue
            yield area, obj

    def save(self, prefix='', path='./original-data'):
        """Saves the downloaded geojsons to disk.

        Args:
            prefix: Prefix prepended to the geoId of a given GeoJSON to
                    determine the name of its filename. For example, if
                    prefix='original-', a resulting filename might be
                    'original-geoId-01.geojson'.
            path: Directory in which to save the desired files, as a string.
        """
        for geoid, coords in self.iter_subareas():
            filename = geoid.replace('/', '-')
            with open(os.path.join(path, prefix + filename + '.geojson'),
                      'w') as f:
                geojson.dump(coords, f)


if __name__ == '__main__':
    loader = GeojsonDownloader()
    loader.download_data()
    loader.save()
