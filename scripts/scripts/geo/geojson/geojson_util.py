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

import ast
import json
import os
import sys

from absl import logging
from shapely import geometry
from typing import Union

_SCRIPTS_DIR = os.path.join(
    os.path.abspath(__file__).split('/scripts/')[0], 'scripts')
sys.path.append(_SCRIPTS_DIR)
sys.path.append(os.path.join(os.path.dirname(_SCRIPTS_DIR), 'util'))

from counters import Counters

# Maximum geoJsonCoordinates value in bytes.
# Polygons larger than this are simplified with a node in geoJsonCoordinatesNote.
_MAX_GEOJSON_SIZE = 10000000  # ~10MB
# Tolerance to simplify the polygon when it exceeds _MAX_GEOJSON_SIZE
# Polygon is simplified successively by this until it fits.
_MIN_TOLERANCE = 0.005

# Maximum number of iterations to simplify a polygon.
_MAX_SIMPLIFY_ITERATIONS = 10

# Remove loops with area smaller than threshold when simplifying polygons.
_MIN_AREA_DEGREES = 0.000001

from json import JSONEncoder
from shapely.geometry import MultiPolygon


# Custom Json Encoder for MultiPolygon
class GeoJsonEncoder(JSONEncoder):

    def default(self, obj):
        if isinstance(obj, MultiPolygon):
            return obj.__geo_interface__
        return JSONEncoder.default(self, obj)


def get_geojson_dict(geojson: Union[str, dict]) -> dict:
    """Returns a geoJson dict parsed from string.

    Args:
      geoJson: geojson as astring with escaped quotes or a dictionary

    Returns:
      dictionary of geojson
    """
    geo_json = geojson
    if isinstance(geojson, geometry.Polygon):
        geo_json = geometry.mapping(geojson)
    if isinstance(geojson, dict):
        geo_json = geojson
    elif isinstance(geojson, str):
        # Convert geojson to a dict
        try:
            # Parse quoted string with escaped double quotes
            geo_json = json.loads(json.loads(geojson))
        except (TypeError, json.decoder.JSONDecodeError) as e:
            geo_json = None
            logging.error(
                f'Failed to load geojson: error: {e} \n{geojson[:100]}')
        if geo_json is None:
            #Parse dictionary as a string
            try:
                geo_json = ast.literal_eval(geojson)
            except (TypeError, SyntaxError) as e:
                geo_json = None
                logging.error(
                    f'Failed to eval geojson: error:{e}\n{geojson[:100]}')
    return geo_json


def get_geojson_polygon(geojson: dict,
                        check_is_valid: bool = True,
                        fix_polygon: bool = False) -> geometry.Polygon:
    """Returns a polygon for the geoJson.

    Args:
      geoJson: polygon as a dictionary of lines wiht lat/long
      check_is_valid: if True, only returns Polygon that is valid.
      fix_polygon: if True, will attempt to fix invalid polygons.

    Returns:
      geometry.Polygon object created from the input dict
    """
    if geojson and isinstance(geojson, geometry.Polygon):
        return geojson
    geo_json = get_geojson_dict(geojson)
    if not geo_json or not isinstance(geo_json, dict):
        return None
    polygon = geometry.shape(geo_json)
    if (fix_polygon or check_is_valid):
        if polygon and not polygon.is_valid:
            if fix_polygon:
                fixed_polygon = polygon.buffer(0)
                if fixed_polygon.is_valid:
                    return fixed_polygon
            else:
                return None
    return polygon


def merge_geojson_str(geo_json_list: list, fix_polygon: bool = False) -> str:
    """Returns a geoJSON after merging all boundaries in geo_json_list

    Args:
      geo_json_list: List of geoJson dicts to be merged.

    Returns:
      geojson dict that is union of all input geoJsons.
    """
    merged_polygon = geometry.Polygon()
    for gj in geo_json_list:
        polygon = get_geojson_polygon(gj,
                                      check_is_valid=True,
                                      fix_polygon=fix_polygon)
        if not polygon:
            return None
        merged_polygon = merged_polygon.union(polygon)
        if not merged_polygon:
            logging.error(f'Unable to merge polygon')
            return None
    geojson_str, tolerance = get_limited_geojson_str(geojson_str='',
                                                     polygon=merged_polygon)
    if not geojson_str:
        logging.error(f'Unable to get geoJson for merged polygon')
    return geojson_str


def round_floats(data, decimal_digits: int = 7) -> float:
    """Returns the float orounded to the rquired precision.
    If the data is a dict or a list, rounds the floats within it."""
    if isinstance(data, float):
        return round(data, decimal_digits)
    if isinstance(data, (list, tuple)):
        return [round_floats(element, decimal_digits) for element in data]
    if isinstance(data, dict):
        return {k: round_floats(v, decimal_digits) for k, v in data.items()}
    return data


def get_geojson_str(geojson: dict, decimal_places: int = 7) -> str:
    """Returns a geoJson string with lat/lng coordinates rounded to decimal places.

    Args:
      geojson: dictionary of polygon to be converted to string.
      decimal_places: number of decimal places to round the coordinates to.
         Default is 7 which is roughly 1cm
    """
    rounded_json = round_floats(get_geojson_dict(geojson))
    #rounded_json = json.loads(json.dumps(get_geojson_dict(geojson),
    #                                     cls=GeoJsonEncoder),
    #                          parse_float=lambda x: round(float(x), 7))
    return json.dumps(json.dumps(rounded_json, cls=GeoJsonEncoder))


def get_limited_geojson_str(geojson_str: str,
                            polygon: geometry.Polygon = None,
                            simplify_tolerance: float = 0.0,
                            fix_polygon: bool = False,
                            max_length: int = _MAX_GEOJSON_SIZE,
                            min_area: float = _MIN_AREA_DEGREES,
                            counters: Counters = None) -> (str, float):
    """Returns a polygon that is within the max length.

    Args:
      geojson_str: string representation of polygon geojson
      polygon: olygon object to be converted to string
      simplify_tolerance: simplification factor for Douglas Peucker algo
      fix_polygon: fix the polygon if it is invalid
      max_length: Maximum length of the geojson string
         polygons larger than that size are successivly simplified
         until it is within the max_length

    Returns:
      geojson as a string with double quotes escaped that is less than max_length.
    """
    if geojson_str is None:
        geojson_str = ''
    if counters is None:
        counters = Counters()
    sgeojson_str = geojson_str
    iteration_count = 0
    loop_iteration_count = 0
    tolerance = simplify_tolerance + _MIN_TOLERANCE * iteration_count
    while (not sgeojson_str or len(sgeojson_str) > max_length and
           iteration_count < _MAX_SIMPLIFY_ITERATIONS and
           loop_iteration_count < _MAX_SIMPLIFY_ITERATIONS):
        if len(sgeojson_str) > 10 * max_length:
            # Try removing small loops before simplifying
            loop_iteration_count += 1
            loop_min_area = loop_iteration_count * min_area
            spolygon = polygon_remove_small_loops(
                polygon, min_area_degrees=loop_min_area, counters=counters)
            sgeojson_str = get_geojson_str(spolygon)
            continue
        tolerance = simplify_tolerance + _MIN_TOLERANCE * iteration_count
        if polygon is None:
            polygon = get_geojson_polygon(geojson_str,
                                          check_is_valid=True,
                                          fix_polygon=fix_polygon)
        if polygon:
            if tolerance >= _MIN_TOLERANCE:
                logging.debug(f'Simplifying polygon of {len(geojson_str)} bytes'
                              f'with tolerance: {tolerance}')
                spolygon = polygon.simplify(tolerance)
            else:
                spolygon = polygon
            sgeojson_str = get_geojson_str(spolygon)
            logging.debug(
                f'Simplified {len(geojson_str)} bytes polygon with tolerance'
                f' {tolerance} to {len(sgeojson_str)}')
        else:
            break
        iteration_count += 1
    counters.add_counter(f'polygons-simplified-in-{iteration_count}-iterations',
                         1)
    counters.add_counter(f'polygons-simplification-iterations', iteration_count)
    if iteration_count >= _MAX_SIMPLIFY_ITERATIONS:
        # Unable to simplify polygon to required size. Try removing loops.
        processed_polygon = polygon_remove_small_loops(
            polygon, min_area_degrees=min_area, counters=counters)
        if processed_polygon and abs(processed_polygon.area -
                                     polygon.area) >= min_area:
            # Got a smaller polygon. Simplify it.
            logging.debug(f'Simplyfying polygon without small loops')
            return get_limited_geojson_str('', processed_polygon,
                                           simplify_tolerance, fix_polygon,
                                           max_length, min_area * 2, counters)

    return sgeojson_str, tolerance


def polygon_remove_small_loops(polygon: geometry.Polygon,
                               min_area_degrees: float = _MIN_AREA_DEGREES,
                               counters: Counters = None) -> geometry.Polygon:
    """Returns a polygon with loops smaller than min_area removed.

  Args:
    polygon: polygon to be processed. It can be a Polygon or a MultiPolygon.
    min_area_degrees: min area in square degrees.
      Assumes the polygon ins in degrees.

  Returns:
    Polygon with loops removed.
  """
    if not polygon:
        return polygon
    if counters is None:
        counters = Counters()
    if isinstance(polygon, geometry.MultiPolygon):
        # Remove small nested polygons
        nested_polygons = []
        num_dropped = 0
        for nested_polygon in polygon.geoms:
            processed_polygon = polygon_remove_small_loops(
                nested_polygon, min_area_degrees, counters)
            polygon_area = processed_polygon.area
            if polygon_area >= min_area_degrees:
                nested_polygons.append(processed_polygon)
            else:
                num_dropped += 1
                logging.debug(
                    f'Dropping nested polygon with area {polygon_area}')
        processed_polygon = geometry.MultiPolygon(nested_polygons)
        logging.debug(
            f'Dropped {num_dropped} polygons smaller than {min_area_degrees} '
            f'from polygon of area {polygon.area} '
            f'to get {processed_polygon.area}')
        counters.add_counter(
            f'num-dropped-small-polygons-area-{min_area_degrees}', num_dropped)
    elif isinstance(polygon, geometry.Polygon):
        # Remove any small inner loops
        inner_loops = []
        dropped_loops = 0
        for interior in polygon.interiors:
            inner_polygon = geometry.Polygon(interior)
            if inner_polygon.area >= min_area_degrees:
                inner_loops.append(interior)
            else:
                dropped_loops += 1
        processed_polygon = geometry.Polygon(polygon.exterior.coords,
                                             holes=inner_loops)
        logging.debug(f'Dropped {dropped_loops} loops from polygon'
                      f'of area {polygon.area} to get {processed_polygon.area}')
        counters.add_counter(f'num-dropped-small-loops-area-{min_area_degrees}',
                             dropped_loops)
    else:
        logging.error(f'Unable to remove loops from non-polygon {polygon}')
        processed_polygon = polygon
        counters.add_counter(f'failed-to-remove-small-loops', 1)
    return processed_polygon
