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

import datacommons as dc
import geojson
import os


# TODO(fpernice-google): Support downloading more than just US states.
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
        dc.set_api_key('dev')
        self.geojsons = None

    def download_data(self, place='country/USA'):
        """Downloads GeoJSON data for a specified location.

        Given the specified location, extracts the GeoJSONs of all
        administrative areas one level below it (as specified by the
        LEVEL_MAP class constant). For example, if the input is country/USA,
        extracts all AdministrativeArea1's within the US (US states).

        Args:
            place: A string that is a valid value for the geoId property of a
                   DataCommons node.

        Raises:
            ValueError: If a Data Commons API call fails.
        """
        geolevel = dc.get_property_values([place], "typeOf")
        # There is an extra level of nesting in geojson files, so we have
        # to get the 0th element explicitly.
        assert len(geolevel[place]) == 1
        geolevel = geolevel[place][0]
        geos_contained_in_place = dc.get_places_in(
            [place], self.LEVEL_MAP[geolevel])[place]
        self.geojsons = dc.get_property_values(geos_contained_in_place,
                                               "geoJsonCoordinates")
        for area, coords in self.iter_subareas():
            self.geojsons[area][0] = geojson.loads(coords)

    def get_subarea(self, area):
        assert len(self.geojsons[area]) == 1
        return self.geojsons[area][0]

    def iter_subareas(self):
        for area in self.geojsons:
            yield area, self.get_subarea(area)

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
