# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utility functions"""

import csv
import datetime
from datetime import date
from datetime import datetime
import glob
import os
import pickle
import re
import sys
import tempfile
from typing import Union

from absl import logging
import datacommons as dc
from dateutil.relativedelta import relativedelta
from geopy import distance
import s2sphere
from s2sphere import Cell, CellId, LatLng
from shapely.geometry import Polygon

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPTS_DIR)
sys.path.append(os.path.dirname(_SCRIPTS_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPTS_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPTS_DIR)), 'util'))

from config_map import ConfigMap, read_py_dict_from_file, write_py_dict_to_file
from dc_api_wrapper import dc_api_wrapper

# Constants
_MAX_LATITUDE = 90.0
_MAX_LONGITUDE = 180.0
_DC_API_ROOT = 'http://autopush.api.datacommons.org'

# Utilities for dicts.


def dict_filter_values(pvs: dict, config: dict = {}) -> bool:
    """Returns true if the property values are allowed by the config.

     removes the properties not allowed by the config from the dict.
  Args:
    pvs: dictionary with property values to be filtered.
    config: dictionary with a per property filter settings: { <prop> : { 'min':
      <min_value>', 'max': <max_value>', 'regex': <regex pattern>', }, }

  Returns:
    True if the key:values in pvs meet all config criteria.
  """
    props = list(pvs.keys())
    is_allowed = True
    for p in props:
        value = pvs.get(p, None)
        allow_value = True
        if value is None:
            allow_value = False
        else:
            prop_config = config.get(p, config)
            if prop_config:
                if 'min' in prop_config:
                    if value < prop_config['min']:
                        allow_value = False
                if 'max' in prop_config:
                    if value > prop_config['max']:
                        allow_value = False
                if 'regex' in prop_config:
                    if not isinstance(value, str):
                        value = str(value)
                    matches = re.search(prop_config['regex'], value)
                    if not matches:
                        allow_value = False
                if 'ignore' in prop_config:
                    if not isinstance(value, str):
                        value = str(value)
                    matches = re.search(prop_config['ignore'], value)
                    if matches:
                        allow_value = False
        if not allow_value:
            pvs.pop(p)
            is_allowed = False
    return is_allowed


# Utilities related to S2 Cells


def is_s2_cell_id(dcid: str) -> bool:
    """Returns true if the dcid is an s2 cell id."""
    return strip_namespace(dcid).startswith('s2CellId/')


def s2_cell_from_latlng(lat: float, lng: float, level: int) -> CellId:
    """Returns an S2 CellId object of level for the given location lat/lng.

  Args:
    lat: Latitude in degrees
    lng: Longitude in degrees
    level: desired S2 level for cell id. Should be <30, the max s2 level
      supported.

  Returns:
    CellId object oof the desired level that contains the lat/lng point.
  """
    assert level >= 0 and level <= 30
    ll = s2sphere.LatLng.from_degrees(lat, lng)
    cell = s2sphere.CellId.from_lat_lng(ll)
    if level < 30:
        cell = cell.parent(level)
    return cell


def s2_cell_to_hex_str(s2cell_id: Union[int, CellId]) -> str:
    """Returns the s2 cell id in hex."""
    if isinstance(s2cell_id, CellId):
        s2cell_id = s2cell_id.id()
    return f'{s2cell_id:#018x}'


def s2_cell_to_dcid(s2cell_id: Union[int, CellId]) -> str:
    """Returns the dcid for the s2 cell of the form s2CellId/0x1234."""
    if isinstance(s2cell_id, CellId):
        s2cell_id = s2cell_id.id()
    return 'dcid:s2CellId/' + s2_cell_to_hex_str(s2cell_id)


def s2_cell_from_dcid(s2_dcid: Union[str, int, CellId]) -> CellId:
    """Returns the s2 CellId object for the s2 cell."""
    if isinstance(s2_dcid, str):
        return s2sphere.CellId(int(s2_dcid[s2_dcid.find('/') + 1:], 16))
    if isinstance(s2_dcid, int):
        return s2sphere.CellId(s2_dcid)
    if isinstance(s2_dcid, s2sphere.CellId):
        return s2_dcid
    return None


def s2_cell_latlng_dcid(lat: float, lng: float, level: int) -> str:
    """Returns dcid of the s2 cell of given level containing the point lat/lng."""
    return s2_cell_to_dcid(s2_cell_from_latlng(lat, lng, level).id())


def s2_cells_distance(cell_id1: int, cell_id2: int) -> float:
    """Returns the distance between the centroid of two S2 cells in kilometers."""
    p1 = CellId(cell_id1).to_lat_lng()
    p2 = CellId(cell_id2).to_lat_lng()
    return distance.distance((p1.lat().degrees, p1.lng().degrees),
                             (p2.lat().degrees, p2.lng().degrees)).km


def s2_cell_area(cell_id: s2sphere.CellId) -> float:
    """Returns the area of the S2 cell in sqkm

  Converts the are of the S2 cell into sqkm using a fixed radius of 6371 km.

  Args:
    cell_id: S2 CellId

  Returns:
    Area of the cell in sq km.
  """
    _EARTH_RADIUS = 6371  # Radius of Earth in Km.
    s2_cell = s2_cell_from_dcid(cell_id)
    return s2sphere.Cell(s2_cell).exact_area() * _EARTH_RADIUS * _EARTH_RADIUS


def s2_cell_get_neighbor_ids(s2_cell_id: str) -> list:
    """Returns a list of neighbouring cell dcids for a given s2 cell dcid.

  An interior cell will have 8 neighbours: 3 above, 1 left, 1 right and 3 below.
  A cell near the edge may have a subset of these.
  """
    s2_cell = s2_cell_from_dcid(s2_cell_id)
    return [
        s2_cell_to_dcid(cell)
        for cell in s2_cell.get_all_neighbors(s2_cell.level())
    ]


def s2_cell_to_polygon(s2_cell_id: str) -> Polygon:
    """Returns the polygon with 4 vertices for an s2 cell."""
    s2_cell = Cell(s2_cell_from_dcid(s2_cell_id))
    if not s2_cell:
        return None
    # Get vertices for all corners.
    vertices = []
    for index in range(4):
        point = s2_cell.get_vertex(index)
        ll = LatLng.from_point(point)
        vertices.append((ll.lng().degrees, ll.lat().degrees))
    vertices.append(vertices[0])
    # Create a polygon for the vertices.
    return Polygon(vertices)


def latlng_cell_area(lat: float, lng: float, height: float,
                     width: float) -> float:
    """Returns the area of the rectangular region in sqkm.

  Args:
    lat: latitude of a corner in degrees
    lng: Longitude of a corner in degrees
    width: width in degrees
    height: height in degrees

  Returns:
    area in square kilometers.
  """
    try:
        bottom_left = (lat, lng)
        top_left = (min(90, lat + height), lng)
        bottom_right = (lat, min(lng + width, 180))
        width_km = distance.geodesic(bottom_left, bottom_right).km
        height_km = distance.geodesic(top_left, bottom_left).km
        return width_km * height_km
    except ValueError:
        logging.error(f'Invalid coordinates for area: {locals()}')
        return 0


# Utilities for grid ids.


def is_grid_id(dcid: str) -> bool:
    """Returns true if the dcid is a grid id."""
    return strip_namespace(dcid).startswith('grid_')


def is_ipcc_id(dcid: str) -> bool:
    """Returns true if the dcid is an ipcc grid id."""
    return strip_namespace(dcid).startswith('ipcc_')


def grid_id_from_lat_lng(
    degrees: float,
    lat: float,
    lng: float,
    prefix: str = 'grid_',
    suffix: str = '',
    lat_offset: float = 0,
    lng_offset: float = 0,
) -> str:
    """Returns the dcid for grid of given degrees for the lat/lng."""
    # Get lat/lng rounded to the grid degrees
    degree_str = str_from_number(degrees)
    if prefix == 'ipcc_':
        # Get the dcid prefix with the grid degree,
        # such as ipcc_50 for 0.5 deg grids.
        degree_str = str_from_number(int(degrees * 100))
    lat_rounded = int(lat / degrees) * degrees + lat_offset
    lng_rounded = int(lng / degrees) * degrees + lng_offset
    lat_str = str_from_number(number=lat_rounded, precision_digits=2)
    lng_str = str_from_number(number=lng_rounded, precision_digits=2)
    return f'dcid:{prefix}{degree_str}/{lat_str}_{lng_str}{suffix}'


def grid_id_to_deg_lat_lng(
        grid_id: str, default_deg: float = 1) -> (float, float, float, str):
    """Returns a tuple of degree, latitude longitude, suffix for the grid id."""
    grid = strip_namespace(grid_id)
    deg, lat_lng = grid.split('/', 1)
    if deg is not None:
        deg = deg[deg.find('_') + 1:]
        deg = float(deg)
    else:
        deg = default_deg
    if is_ipcc_id(grid_id):
        # Decimal degrees are represented with fractional part.
        deg = deg / 100
    if lat_lng:
        latlngs = lat_lng.split('_')
        lat = float(latlngs[0])
        lng = float(latlngs[1])
        lat_offset = lat - int(lat / deg) * deg
        lng_offset = lng - int(lng / deg) * deg
        suffix = ''
        if len(latlngs) > 2 and latlngs[2]:
            suffix = '_' + latlngs[2]
        return (deg, lat, lng, lat_offset, lng_offset, suffix)


def grid_get_neighbor_ids(grid_id: str) -> list:
    """Returns all the 8 neighbour ids of the grid."""
    grid_id = strip_namespace(grid_id)
    prefix = grid_id[:grid_id.find('_') + 1]
    deg, lat, lng, lat_deg_offset, lng_deg_offset, suffix = (
        grid_id_to_deg_lat_lng(grid_id))
    neighbours = []
    for lat_offset in [-1, 0, 1]:
        for lng_offset in [-1, 0, 1]:
            if lat_offset != 0 or lng_offset != 0:
                neighbour_lat = lat + lat_offset * deg
                neighbour_lng = lng + lng_offset * deg
                if abs(neighbour_lat) < _MAX_LATITUDE and abs(
                        neighbour_lng) < _MAX_LONGITUDE:
                    neighbours.append(
                        grid_id_from_lat_lng(
                            deg,
                            neighbour_lat,
                            neighbour_lng,
                            prefix,
                            suffix,
                            lat_deg_offset,
                            lng_deg_offset,
                        ))
    return neighbours


def grid_ids_distance(grid1: str, grid2: str) -> float:
    """Returns the distance between grid points."""
    deg1, lat1, lng1, lat1_offset, lng1_offset, suffix1 = grid_id_to_deg_lat_lng(
        grid1)
    deg2, lat2, lng2, lat2_offset, lng2_offset, suffix2 = grid_id_to_deg_lat_lng(
        grid2)
    return distance.distance((lat1, lng1), (lat2, lng2)).km


def grid_area(grid: str) -> float:
    """Returns the area for the grid."""
    deg, lat, lng, lat_offset, lng_offset, suffix = grid_id_to_deg_lat_lng(grid)
    return latlng_cell_area(lat, lng, deg, deg)


def grid_to_polygon(grid: str) -> Polygon:
    """Returns the rectangular polygon for the grid.

  Assumes the lat/lng from the dcid is the center.
  """
    deg, lat, lng, lat_offset, lng_offset, suffix = grid_id_to_deg_lat_lng(grid)
    bottom_left_lat = max(lat - deg / 2, -90)
    bottom_left_lng = max(lng - deg / 2, -180)
    return Polygon.from_bounds(
        bottom_left_lng,
        bottom_left_lat,
        min(bottom_left_lng + deg, 180),
        min(bottom_left_lat + deg, 90),
    )


def place_id_to_lat_lng(placeid: str,
                        dc_api_lookup: bool = True) -> (float, float):
    """Returns the lat/lng degrees for the place."""
    lat = None
    lng = None
    if is_s2_cell_id(placeid):
        s2_cell = s2_cell_from_dcid(placeid)
        point = s2_cell.to_lat_lng()
        return (point.lat().degrees, point.lng().degrees)
    if is_grid_id(placeid) or is_ipcc_id(placeid):
        deg, lat, lng, lat_offset, lng_offset, suffix = grid_id_to_deg_lat_lng(
            placeid)
    elif dc_api_lookup:
        # Get the lat/lng from the DC API
        latlng = []
        for prop in ['latitude', 'longitude']:
            # dc.utils._API_ROOT = 'http://autopush.api.datacommons.org'
            # resp = dc.get_property_values([placeid], prop)
            resp = dc_api_wrapper(
                function=dc.get_property_values,
                args={
                    'dcids': [placeid],
                    'prop': prop,
                },
                use_cache=True,
                api_root=_DC_API_ROOT,
            )
            if not resp or placeid not in resp:
                return (0, 0)
            values = resp[placeid]
            if not len(values):
                return (0, 0)
            latlng.append(float(values[0]))
        lat = latlng[0]
        lng = latlng[1]
    return (lat, lng)


def place_distance(place1: str, place2: str) -> float:
    """Returns the distance between two places."""
    lat1, lng1 = place_id_to_lat_lng(place1)
    lat2, lng2 = place_id_to_lat_lng(place2)
    return distance.distance((lat1, lng1), (lat2, lng2)).km


def place_area(place: str) -> float:
    """Returns the area for the place in sqkm."""
    if is_s2_cell_id(place):
        s2_cell = s2_cell_from_dcid(place)
        return s2_cell_area(s2_cell)
    if is_grid_id(place) or is_ipcc_id(place):
        return grid_area(place)
    # Unknown place type
    return 0


def place_to_polygon(place_id: str) -> Polygon:
    """Returns the polygon for the place."""
    if is_s2_cell_id(place_id):
        return s2_cell_to_polygon(place_id)
    if is_grid_id(place_id) or is_ipcc_id(place_id):
        return grid_to_polygon(place_id)
    return None


# String utilities


def strip_namespace(dcid: str) -> str:
    """Returns the id without the namespace prefix."""
    return dcid[dcid.find(':') + 1:]


def add_namespace(dcid: str, prefix: str = 'dcid:') -> str:
    """Returns the dcid with the namespace set to prefix."""
    return f'{prefix}{strip_namespace(dcid)}'


def str_get_numeric_value(
        value: Union[str, list, int, float]) -> Union[int, float, None]:
    """Returns the numeric value from input string or None."""
    if isinstance(value, list):
        value = value[0]
    if isinstance(value, int) or isinstance(value, float):
        return value
    if value and isinstance(value, str):
        normalized_value = value.strip()
        if not normalized_value:
            return None
        if (normalized_value[0].isdigit() or normalized_value[0] == '.' or
                normalized_value[0] == '-' or normalized_value[0] == '+'):
            # Input looks like a number. Remove allowed extra characters.
            # Parse numbers of the form 10,000,000 or 20,00,000.
            normalized_value = normalized_value.replace(',', '')
            if normalized_value.count('.') > 1:
                # Period may be used instead of commas. Remove it.
                normalized_value = normalized_value.replace('.', '')
        try:
            if normalized_value.count('.') == 1:
                return float(normalized_value)
            if normalized_value.startswith('0x'):
                return int(normalized_value, 16)
            return int(normalized_value)
        except ValueError:
            # Value is not a number. Ignore it.
            return None
    return None


def str_from_number(number: Union[int, float],
                    precision_digits: int = None) -> str:
    """Returns the number converted to string.

  Ints and floats with 0 decimal parts get int strings. Floats get precision
  digits.
  """
    # Check if number is an integer or float without any decimals.
    if int(number) == number:
        number_int = int(number)
        return f'{number_int}'
    # Return float rounded to precision digits.
    if precision_digits:
        number = round(number, precision_digits)
    return f'{number}'


def str_format_float(data: float, precision_digits: int = 6):
    if isinstance(data, float):
        return f'{data:.{precision_digits}f}'
    return data


# Date utilities


def date_today(date_format: str = '%Y-%m-%d') -> str:
    """Returns today's date in the given format."""
    return date.today().strftime(date_format)


def date_yesterday(date_format: str = '%Y-%m-%d') -> str:
    """Returns yesterday's date in the given format."""
    return date_advance_by_period(date_today(date_format), '-1d', date_format)


def date_parse_time_period(time_period: str) -> (int, str):
    """Parse time period into a tuple of (number, unit),

  for eg: for 'P1M' returns (1, month).
  Time period is assumed to be of the form: P<Nunmber><Duration>
  where duration is a letter: D: days, M; months, Y: years.
  .
  """
    # Extract the number and duration letter from the time period.
    re_pat = r'P?(?P<delta>[+-]?[0-9]+)(?P<unit>[A-Z])'
    m = re.search(re_pat, time_period.upper())
    if m:
        m_dict = m.groupdict()
        delta = int(m_dict.get('delta', '0'))
        unit = m_dict.get('unit', 'M')
        # Convert the duration letter to unit: days/months/years
        period_dict = {'D': 'days', 'M': 'months', 'Y': 'years'}
        period = period_dict.get(unit, 'day')
        return (delta, period)
    return (0, 'days')


def date_advance_by_period(date_str: str,
                           time_period: str,
                           date_format: str = '%Y-%m-%d') -> str:
    """Returns the date string advanced by the time period."""
    if not date_str:
        return ''
    dt = datetime.strptime(date_str, date_format)
    (delta, unit) = date_parse_time_period(time_period)
    if not delta or not unit:
        logging.error(
            f'Unable to parse time period: {time_period} for date: {date_str}')
        return ''
    next_dt = dt + relativedelta(**{unit: delta})
    return next_dt.strftime(date_format)


def date_format_by_time_period(date_str: str, time_period: str) -> str:
    """Returns date in the format of the time_period: P<N><L>

  If the last letter in the time_period is Y, returns date in YYYY,
  for 'M', returns date as YYYY-MM, for D returns date as YYYY-MM-DD.
  """
    if not time_period:
        return date_str
    (delta, unit) = date_parse_time_period(time_period)
    date_parts = date_str.split('-')
    if unit == 'years':
        return date_parts[0]
    if unit == 'months':
        return '-'.join(date_parts[0:2])
    return date_str
