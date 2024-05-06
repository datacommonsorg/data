# Copyright 2024 Google LLC
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
"""Utilities for geoJson coordinates."""

import json
import sys

from absl import logging
from shapely import geometry
from typing import Union

# Maximum geoJsonCoordinates value in bytes.
# Polygons larger than this are simplified with a node in geoJsonCoordinatesNote.
_MAX_GEOJSON_SIZE = 10000000  # ~10MB
# Tolerance to simplify the polygon when it exceeds _MAX_GEOJSON_SIZE
# Polygon is simplified successively by this until it fits.
_MIN_TOLERANCE = 0.005

def get_geojson_dict(geojson: Union[str, dict]) -> dict:
    """Returns a geoJson dict parsed from string.

    Args:
      geoJson: geojson as astring with escaped quotes or a dictionary

    Returns:
      dictionary of geojson
    """
    geo_json = None
    if isinstance(geojson, dict):
        geo_json = geojson
    elif isinstance(geojson, str):
        # Convert geojson to a dict
        try:
            # Parse quoted string with escaped double quotes
            geo_json = json.loads(json.loads(geojson))
        except TypeError:
            geo_json = None
            logging.debug(f'Failed to load geojson: {geojson[:100]}')
        if geo_json is None:
            # Parse dictionary as a string
            try:
                geo_json = ast.literal_eval(geojson)
            except TypeError:
                geo_json = None
                logging.debug(f'Failed to eval geojson: {geojson[:100]}')
    return geo_json


def get_geojson_polygon(geojson: dict) -> geometry.Polygon:
    """Returns a polygon for the geoJson.

    Args:
      geoJson: polygon as s dictionary of lines wiht lat/long

    Returns:
      geometry.Polygon object created from the input dict
    """
    geo_json = get_geojson_dict(geojson)
    if not geo_json:
        return None
    polygon = geometry.shape(geo_json)
    if not polygon or not polygon.is_valid:
      return None
    return polygon


def get_limited_geojson_str(geojson_str: str,
                            polygon: geometry.Polygon = None,
                            tolerance: float = 0.0,
                            max_length: int = _MAX_GEOJSON_SIZE) -> str:
    """Returns a polygon that is within the max length.

    Args:
      geojson_str: string representation of polygon geojson
      polygon: olygon object to be converted to string
      tolerance: simplification factor for Douglas Peucker algo
      max_length: Maximum length of the geojson string
         polygons larger than that size are successivly simplified
         until it is within the max_length

    Returns:
      geojson as a string with double quotes escaped that is less than max_length.
    """
    if geojson_str is None:
      geojson_str = ''
    sgeojson_str = geojson_str
    iteration_count = 0
    while not sgeojson_str or len(sgeojson_str) > max_length:
        tolerance = tolerance + _MIN_TOLERANCE * iteration_count
        if polygon is None:
            polygon = get_geojson_polygon(geojson_str)
        if polygon:
            spolygon = polygon.simplify(tolerance)
            sgeojson_str = json.dumps(json.dumps(geometry.mapping(spolygon)))
            logging.debug(
                f'Simplifying {len(geojson_str)} bytes polygon with tolerance'
                f' {tolerance} to {len(sgeojson_str)}')
        else:
            break
        iteration_count += 1
    return sgeojson_str, tolerance
