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
import datacommons as dc
import glob
import os
import pickle
import re
import s2sphere
import sys
import tempfile

from absl import logging
from geopy import distance
from s2sphere import LatLng, Cell, CellId
from shapely.geometry import Polygon
from typing import Union

_SCRIPTS_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(_SCRIPTS_DIR)
sys.path.append(os.path.dirname(_SCRIPTS_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPTS_DIR)))

from util.config_map import ConfigMap, read_py_dict_from_file, write_py_dict_to_file
from util.dc_api_wrapper import dc_api_wrapper


# Utilities for dicts.
def aggregate_value(value1: str, value2: str, aggregate: str = 'sum') -> str:
    '''Return value aggregated from src and dst as per the config.'''
    value = None
    if aggregate == 'sum':
        value = value1 + value2
    elif aggregate == 'min':
        value = min(value1, value2)
    elif aggregate == 'max':
        value = max(value1, value2)
    elif aggregate == 'list':
        # Create a list of unique values combining lists.
        value = set(str(value1).split(','))
        value.update(str(value2).split(','))
        value = ','.join(sorted(value))
    else:
        logging.fatal(
            f'Unsupported aggregation: {aggregate} for {value1}, {value2}')
    return value


def dict_aggregate_values(src: dict, dst: dict, config: dict) -> dict:
    '''Aggregate values for keys in src dict into dst.
  The mode of aggregation (sum, mean, min, max) per property is
  defined in the config.
  Assumes properties to be aggregated have numeric values.

  Args:
    src: dictionary with property:value to be aggregated into dst
    dst: dictionary with property:value which is updated.
    config: dictionary with aggregation settings per property.
  Returns:
    dst dictionary with updated property:values.
  '''
    if config is None:
        config = {}
    default_aggr = config.get('aggregate', 'sum')
    for prop, new_val in src.items():
        if prop not in dst:
            # Add new property to dst without any aggregation.
            dst[prop] = new_val
        else:
            # Combine new value in src with current value in dst by aggregation.
            aggr = config.get(prop, {}).get('aggregate', default_aggr)
            cur_val = dst[prop]
            if aggr == 'mean':
                cur_num = dst.get(f'#{prop}:count', 1)
                new_num = src.get(f'#{prop}:count', 1)
                dst[prop] = ((cur_val * cur_num) +
                             (new_val * new_num)) / (cur_num + new_num)
                dst[f'#{prop}:count'] = cur_num + new_num
            else:
                dst[prop] = aggregate_value(cur_val, new_val, aggr)
    return dst


def dict_filter_values(pvs: dict, config: dict = {}) -> bool:
    '''Returns true if the property values are allowed by the config.
     removes the properties not allowed by the config from the dict.
  Args:
    pvs: dictionary with property values to be filtered.
    config: dictionary with a per property filter settings:
      {
        <prop> : {
          'min': <min_value>',
          'max': <max_value>',
          'regex': <regex pattern>',
        },
      }
  '''
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
                    matches = re.search(prop_config['regex'], value)
                    if not matches:
                        allow_value = False
        if not allow_value:
            pvs.pop(p)
            is_allowed = False
    return is_allowed


# Utilities related to S2 Cells


def is_s2_cell_id(dcid: str) -> bool:
    '''Returns true if the dcid is an s2 cell id.'''
    return strip_namespace(dcid).startswith('s2CellId/')


def s2_cell_from_latlng(lat: float, lng: float, level: int) -> s2sphere.CellId:
    assert level >= 0 and level <= 30
    ll = s2sphere.LatLng.from_degrees(lat, lng)
    cell = s2sphere.CellId.from_lat_lng(ll)
    if level < 30:
        cell = cell.parent(level)
    return cell


def s2_cell_to_hex_str(s2cell_id: int) -> str:
    if isinstance(s2cell_id, CellId):
        s2cell_id = s2cell_id.id()
    return f'{s2cell_id:#018x}'


def s2_cell_to_dcid(s2cell_id: int) -> str:
    if isinstance(s2cell_id, CellId):
        s2cell_id = s2cell_id.id()
    return 'dcid:s2CellId/' + s2_cell_to_hex_str(s2cell_id)


def s2_cell_from_dcid(s2_dcid: str) -> s2sphere.CellId:
    if isinstance(s2_dcid, str):
        return s2sphere.CellId(int(s2_dcid[s2_dcid.find('/') + 1:], 16))
    if isinstance(s2_dcid, int):
        return s2sphere.CellId(s2_dcid)
    if isinstance(s2_dcid, s2sphere.CellId):
        return s2_dcid
    return None


def s2_cell_latlng_dcid(lat: float, lng: float, level: int) -> str:
    return s2_cell_to_dcid(s2_cell_from_latlng(lat, lng, level).id())


def s2_cells_distance(cell_id1: int, cell_id2: int) -> float:
    '''Returns the distance between the centroid of the S2 cells.'''
    p1 = CellId(cell_id1).to_lat_lng()
    p2 = CellId(cell_id2).to_lat_lng()
    return distance.distance((p1.lat().degrees, p1.lng().degrees),
                             (p2.lat().degrees, p2.lng().degrees)).km


def s2_cell_area(cell_id: s2sphere.CellId) -> float:
    '''Returns the area of the S2 cell in sqkm

     Converts the are of the S2 cell into sqkm using a fixed radius of 6371 km.

     Args:
       cell_id: S2 CellId

     Returns:
       Area of the cell in sq km.
     '''
    _EARTH_RADIUS = 6371  # Radius of Earth in Km.
    s2_cell = s2_cell_from_dcid(cell_id)
    return s2sphere.Cell(s2_cell).exact_area() * _EARTH_RADIUS * _EARTH_RADIUS


def s2_cell_get_neighbor_ids(s2_cell_id: str) -> str:
    '''Returns the neighbouring cell ids for a given s2 cell dcid.'''
    s2_cell = s2_cell_from_dcid(s2_cell_id)
    return [
        s2_cell_to_dcid(cell)
        for cell in s2_cell.get_all_neighbors(s2_cell.level())
    ]


def s2_cell_to_polygon(s2_cell_id: str) -> Polygon:
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
    '''Returns the area of the rectangular cell in km2.
    Args:
      lat: latitude of a corner.
      lng: Longitude of a corner
      width: width in degrees
      height: height in degrees
    Returns:
      area in square kilometers.'''
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
    '''Returns true if the dcid is a grid id.'''
    return strip_namespace(dcid).startswith('grid_')


def is_ipcc_id(dcid: str) -> bool:
    '''Returns true if the dcid is an ipcc grid id.'''
    return strip_namespace(dcid).startswith('ipcc_')


def grid_id_from_lat_lng(degrees: float,
                         lat: float,
                         lng: float,
                         prefix: str = 'grid_',
                         suffix: str = '') -> str:
    '''Returns the dcid for grid of given degrees for the lat/lng.'''
    # Get lat/lng rounded to the grid degrees
    degree_str = str_from_number(degrees)
    if prefix == 'ipcc_':
        degree_str = str_from_number(int(degrees * 100))
    lat_str = str_from_number(lat, 2)
    lng_str = str_from_number(lng, 2)
    return f'dcid:{prefix}{degree_str}/{lat_str}_{lng_str}{suffix}'


def grid_id_to_deg_lat_lng(
        grid_id: str, default_deg: float = 1) -> (float, float, float, str):
    '''Returns a tuple of degree, latitude longitude, suffix for the grid id.'''
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
        suffix = ''
        if len(latlngs) > 2 and latlngs[2]:
            suffix = '_' + latlngs[2]
        return (deg, lat, lng, suffix)


def grid_get_neighbor_ids(grid_id: str) -> list:
    '''Returns all the 8 neighbour ids of the grid.'''
    grid_id = strip_namespace(grid_id)
    prefix = grid_id[:grid_id.find('_') + 1]
    deg, lat, lng, suffix = grid_id_to_deg_lat_lng(grid_id)
    neighbours = []
    for lat_offset in [-1, 0, 1]:
        for lng_offset in [-1, 0, 1]:
            if lat_offset != 0 or lng_offset != 0:
                neighbour_lat = lat + lat_offset * deg
                neighbour_lng = lng + lng_offset * deg
                if abs(neighbour_lat) < 90.0 and abs(neighbour_lng) < 180:
                    neighbours.append(
                        grid_id_from_lat_lng(deg, neighbour_lat, neighbour_lng,
                                             prefix, suffix))
    return neighbours


def grid_ids_distance(grid1: str, grid2: str) -> float:
    '''Returns the distance between grid points.'''
    deg1, lat1, lng1, suffix1 = grid_id_to_deg_lat_lng(grid1)
    deg2, lat2, lng2, suffix2 = grid_id_to_deg_lat_lng(grid2)
    return distance.distance((lat1, lng1), (lat2, lng2)).km


def grid_area(grid: str) -> float:
    '''Returns the area for the grid.'''
    deg, lat, lng, suffix = grid_id_to_deg_lat_lng(grid)
    return latlng_cell_area(lat, lng, deg, deg)


def grid_to_polygon(grid: str) -> Polygon:
    '''Returns the rectangular polygon for the grid.
    Assumes the lat/lng from the dcid is the center.'''
    deg, lat, lng, suffix = grid_id_to_deg_lat_lng(grid)
    bottom_left_lat = max(lat - deg / 2, -90)
    bottom_left_lng = max(lng - deg / 2, -180)
    return Polygon.from_bounds(bottom_left_lng, bottom_left_lat,
                               min(bottom_left_lng + deg, 180),
                               min(bottom_left_lat + deg, 90))


def place_id_to_lat_lng(placeid: str,
                        dc_api_lookup: bool = True) -> (float, float):
    '''Returns the lat/lng degrees for the place.'''
    lat = None
    lng = None
    if is_s2_cell_id(placeid):
        s2_cell = s2_cell_from_dcid(placeid)
        point = s2_cell.to_lat_lng()
        return (point.lat().degrees, point.lng().degrees)
    if is_grid_id(placeid) or is_ipcc_id(placeid):
        deg, lat, lng, suffix = grid_id_to_deg_lat_lng(placeid)
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
                api_root='http://autopush.api.datacommons.org')
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
    '''Returns the distance between two places.'''
    lat1, lng1 = place_id_to_lat_lng(place1)
    lat2, lng2 = place_id_to_lat_lng(place2)
    return distance.distance((lat1, lng1), (lat2, lng2)).km


def place_area(place: str) -> float:
    '''Returns the area for the place.'''
    if is_s2_cell_id(place):
        s2_cell = s2_cell_from_dcid(placeid)
        return s2_cell_area(s2_cell)
    if is_grid_id(place) or is_ipcc_id(place):
        return grid_area(place)
    # Unknown place type
    return 0


def place_to_polygon(place_id: str) -> Polygon:
    '''Returns the polygon for the place.'''
    if is_s2_cell_id(place_id):
        return s2_cell_to_polygon(place_id)
    if is_grid_id(place_id) or is_ipcc_id(place_id):
        return grid_to_polygon(place_id)
    return None


# Utilities for files.
def file_get_matching(filepat: str) -> list:
    '''Return a list of matching file names.
    Args:
      filepat: string with comma seperated list of file patterns to lookup
    Returns:
      list of matching filenames.
    '''
    # Get a list of input file patterns to lookup
    input_files = filepat
    if isinstance(filepat, str):
        input_files = [filepat]
    if isinstance(input_files, list):
        for files in input_files:
            for file in files.split(','):
                if file not in input_files:
                    input_files.append(file)
    # Get all matching files for each file pattern.
    files = list()
    if input_files:
        for file in input_files:
            for f in glob.glob(file):
                if f not in files:
                    files.append(f)
    return sorted(files)


def file_estimate_num_rows(filename: str) -> int:
    '''Returns an estimated number of rows based on size of the first few rows.
    Args:
      filename: string name of the file.
    Returns:
      An estimated number of rows.
    '''
    filesize = os.path.getsize(filename)
    with open(filename) as fp:
        lines = fp.read(4000)
    line_size = max(len(lines) / (lines.count('\n') + 1), 1)
    return int(filesize / line_size)


def file_get_name(file_path: str,
                  suffix: str = '',
                  file_ext: str = '.csv') -> str:
    '''Returns the filename with suffix and extension.
    Creates the directory path for the file if it doesn't exist.
    Args:
      file_path: file path with directory and file name prefix
      suffix: file name suffix
      file_ext: file extension
    Returns:
      file name combined from path, suffix and extension.
    '''
    # Create the file directory if it doesn't exist.
    file_dir = os.path.dirname(file_path)
    if file_dir:
        os.makedirs(file_dir, exist_ok=True)
    file_prefix, ext = os.path.splitext(file_path)
    if file_prefix.endswith(suffix):
        # Suffix already present in name, ignore it.
        suffix = ''
    # Set the file extension
    if file_ext and file_ext[0] != '.':
        file_ext = '.' + file_ext
    return file_prefix + suffix + file_ext


def file_load_csv_dict(filename: str,
                       key_column: str = None,
                       value_column: str = None,
                       delimiter: str = ',',
                       config: dict = {}) -> dict:
    '''Returns a CSV file loaded into a dict.
  Each row is added to the dict with value from column 'key_column' as key
  and  value from 'value_column.
  Args:
    filename: csv file name to be loaded into the dict.
      it can be a comma separated list of file patterns as well.
    key_column: column in the csv to be used as the key for the dict
      if not set, uses the first column as the key.
    value_column: column to be used as value in the dict.
      If not set, value is a dict of all remaining columns.
    config: dictionary of aggregation settings in case there are
      multiple rows with the same key.
      refer to dict_aggregate_values() for config settings.

  Returns:
    dictionary of {key:value} loaded from the CSV file.
  '''
    csv_dict = {}
    input_files = file_get_matching(filename)
    for filename in input_files:
        logging.info(f'Loading csv data file: {filename}')
        num_rows = 0
        # Load each CSV file
        with open(filename) as csvfile:
            reader = csv.DictReader(csvfile, delimiter=delimiter)
            if not key_column:
                key_column = reader.fieldnames[0]
            if not value_column and len(reader.fieldnames) == 2:
                value_column = reader.fieldnames[1]
            # Process a row from the csv file
            for row in reader:
                # Get the key for the row.
                key = None
                if key_column in row:
                    key = row.pop(key_column)
                value = ''
                if value_column:
                    value = row.get(value_column, '')
                else:
                    value = row
                if key is None or value is None:
                    logging.debug(f'Ignoring row without key or value: {row}')
                    continue
                # Add the row to the dict
                if key in csv_dict:
                    # Key already exists. Merge values.
                    old_value = csv_dict[key]
                    if isinstance(old_value, dict):
                        dict_aggregate_values(row, old_value, config)
                    else:
                        aggr = config.get(prop, config).get('aggregate', 'sum')
                        value = aggregate_value(old_value, value, aggr)
                        csv_dict[key] = value
                else:
                    csv_dict[key] = value
                num_rows += 1
        logging.info(f'Loaded {num_rows} rows from {filename} into dict')
    return csv_dict


def file_load_py_dict(dict_filename: str) -> dict:
    '''Returns a py dictionary loaded from the file.
    The file can be a pickle file (.pkl) or a .py or JSON dict (.json)'''
    input_files = file_get_matching(dict_filename)
    py_dict = {}
    for filename in input_files:
        file_size = os.path.getsize(filename)
        if file_size:
            if filename.endswith('.pkl'):
                logging.info(f'Loading dict from pickle file: {filename}')
                with open(filename, 'rb') as file:
                    py_dict.update(pickle.load(file))
            else:
                # Assumes the file is a py or json dict.
                logging.info(f'Loading dict from py from file: {filename}')
                py_dict.update(read_py_dict_from_file(filename))
                logging.info(
                    f'Loaded py dict of size: {file_size} from {filename}')
    return py_dict


def file_write_py_dict(py_dict: dict, filename: str):
    '''Save the py dictionary into a file.
    First writes the dict into a temp file and moves the tmp file to the required file.
    so that any interruption during write will not corrupt the existing file.
    '''
    if not py_dict or not filename:
        return
    output_files = file_get_matching(filename)
    if output_files:
        # Save into the last file
        filename = output_files[-1]
    # Save the active events into a tmp file and move it to the required file.
    fd, tmp_filename = tempfile.mkstemp()
    if filename.endswith('.pkl'):
        logging.info(
            f'Writing py dict of size {sys.getsizeof(py_dict)} to pickle file: {filename}'
        )
        with open(tmp_filename, 'wb') as file:
            pickle.dump(py_dict, file)
    else:
        logging.info(
            f'Writing py dict of size {sys.getsizeof(py_dict)} to file: {filename}'
        )
        write_py_dict_to_file(py_dict, tmp_filename)
    # Rename tmp file into the required file.
    os.rename(tmp_filename, filename)
    file_size = os.path.getsize(filename)
    logging.info(f'Saved py dict into file: {filename} of size: {file_size}')


# String utilities


def strip_namespace(dcid: str) -> str:
    '''Returns the id without the namespace prefix.'''
    return dcid[dcid.find(':') + 1:]


def add_namespace(dcid: str, prefix: str = 'dcid:') -> str:
    '''Returns the dcid with the namespace set to prefix.'''
    return f'{prefix}{strip_namespace(dcid)}'


def str_get_numeric_value(
        value: Union[str, list, int, float]) -> Union[int, float, None]:
    '''Returns the numeric value from input string or None.'''
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
    '''Returns the number converted to string.
    Ints and floats with 0 decimal parts get int strings.
    Floats get precision digits.'''
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
