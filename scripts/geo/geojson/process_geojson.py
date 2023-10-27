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
"""Script to process geojson files.

Steps:
  1. Download shp files from source, such as:
  https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/access-and-downloads/digital-boundary-files

  2. Convert the shape files to geoJson using:
  ogr2ogr -f GeoJSON <output-file.geojson>  <input-file.shp>

  3. Extract the place names and features from the shp files into a csv
  python3 process_geojson.py --input_geojson=<my.gsojson>
  --output_csv=<properties.csv>

  4. Run the place_resolver.py to resolve the place names to dcid.
  Verify the dcids for the place names.

  5. Generate MCF with the polygon boundaries for each resolved dcid.
"""
import json
import os
import re
import sys

from absl import app
from absl import flags
from absl import logging
from shapely import geometry

_FLAGS = flags.FLAGS

# Polygon simplification levels in the form of tuples: '<level>:<tolerance>'
# Simplified polygon is added as property: geoJsonCoordinates<level>
SIMPLIFICATION_LEVELS = [':0', 'DP1:0.01', 'DP2:0.03', 'DP3:0.05']

# Mandatory flags.
# Set the program to fail if these flags are not specified.
flags.DEFINE_list('input_geojson', None, 'Input geojson files to process')
flags.mark_flag_as_required('input_geojson')
flags.DEFINE_integer(
    'input_nodes', sys.maxsize, 'Numbre of input nodes to process.'
)
flags.DEFINE_list(
    'properties', [], 'List of feature properties to extract from GeoJSON.'
)
flags.DEFINE_string('key_property', '', 'Property to use as key.')
flags.DEFINE_list(
    'place_name_properties',
    [],
    'List of properties used to create the full place name.',
)
flags.DEFINE_string(
    'new_dcid_template', '', 'Template to generate dcid for unresolved places.'
)
flags.DEFINE_string('output_csv', '', 'Output path for generated files.')
flags.DEFINE_string(
    'output_mcf_prefix',
    'output',
    'Output file prefix for MCF nodes with geoJsonCoordinates.',
)
flags.DEFINE_list(
    'output_mcf_pvs',
    [],
    'List of comma separated propery:value strings to be added to output MCF.'
    ' The property or value can have format strings with reference to other '
    'properties  such as  "area:[{AREASQKM21} SquareKilometer]"',
)
flags.DEFINE_string(
    'places_csv',
    'resolved_places.csv',
    'CSV file with columns place_name and dcid.',
)
flags.DEFINE_list(
    'simplification_levels',
    SIMPLIFICATION_LEVELS,
    'List of property <suffix>:<tolerance> for Douglas Pecker simplification of'
    ' geoJson coordinates.',
)

# Optional flags
flags.DEFINE_boolean('debug', False, 'Enable debug log messages.')

_SCRIPTS_DIR = os.path.join(__file__.split('/scripts/')[0], 'scripts')
sys.path.append(_SCRIPTS_DIR)
sys.path.append(os.path.join(os.path.dirname(_SCRIPTS_DIR), 'util'))

import file_util

from counters import Counters

_MCF_TEMPLATE = """
Node: dcid:{dcid}
typeOf: dcid:{typeof}
geoJsonCoordinates{level}: {polygon}"""


def open_output_files(
    simplification_levels: list, output_mcf_prefix: str
) -> list:
  # Open file handles for MCF outputs for each simplification level.
  mcf_outputs = []
  output_files = []
  if output_mcf_prefix:
    for index in range(len(simplification_levels)):
      level, tolerance = simplification_levels[index].split(':', 1)
      suffix = ''
      if level:
        suffix = f'_simplified_{level}'
      filename = file_util.file_get_name(
          file_path=output_mcf_prefix, suffix=suffix, file_ext='.mcf'
      )
      mcf_outputs.append(file_util.FileIO(filename, mode='w'))
      output_files.append(filename)
    logging.info(f'Opened MCF files: {output_files}')
  return mcf_outputs


def process_geojson(
    geo_json: dict,
    input_nodes: int,
    properties: list = None,
    key_prop: str = '',
    place_name_props: list = [],
    dcid_template: str = '',
    output_dict: dict = None,
    places_dcid: dict = {},
    mcf_outputs: list = [],
    output_mcf_props: list = [],
    simplification_levels: list = SIMPLIFICATION_LEVELS,
    counters: Counters = Counters(),
) -> dict:
  """Extract properties from geoJson into a dict."""
  # Create a dictionary of place->properties.
  geojson_dict = output_dict
  if geojson_dict is None:
    geojson_dict = dict()
  num_features = 0
  num_props = 0

  # Process all place features in the geoJson
  features = geo_json.get('features', [])
  if features:
    # Get the properties to extract
    counters.add_counter('total', len(features))
    feature_props = features[0].get('properties', {}).keys()
    if not properties:
      properties = list(feature_props)

    # Get the property to be used as key
    if key_prop:
      for prop in feature_props:
        if re.match(key_prop, prop):
          key_prop = prop

    # Process each place feature in the geoJson
    logging.info(
        f'Processing geoJson with feature properties: {feature_props} with key:'
        f' {key_prop}'
    )
    row_index = 0
    for feature in features:
      if row_index > input_nodes:
        break
      row_index += 1
      row = {'RowIndex': row_index}
      key = ''
      feature_props = feature.get('properties', {})
      # Get all output properties for the feature
      for prop in properties:
        value = feature_props.get(prop, feature.get(prop, None))
        if value:
          row[prop] = value
          num_props += 1
          if prop == key_prop:
            key = value
      if row:
        # Set empty value for missing properties.
        for prop in properties:
          if prop not in row:
            row[prop] = ''
        # Concatenate required properties to get the place name
        # Use the place_name to lookup the dcid from the places_csv.
        if place_name_props:
          row['place_name'] = _get_place_name(row, place_name_props)
          place_props = _get_place_props(row, place_name_props, places_dcid)
          for p, v in place_props.items():
            if v and not row.get(p):
              row[p] = v
        dcid = row.get('dcid')
        if not dcid:
          # Generate new DCID
          if dcid_template:
            dcid = eval_format_str(dcid_template, row)
            if dcid:
              row['dcid'] = dcid
              counters.add_counter('generated-dcids', 1, dcid)
              logging.level_debug() and logging.debug(f'Generated dcid: {row}')
        num_features += 1
        if not key:
          key = row.get('dcid')
          if not key:
            key = len(geojson_dict)
        # Emit the place features if the place key is unique.
        if key not in geojson_dict:
          geojson_dict[key] = row
          # Emit MCFs for the polygon for each simplification level.
          geo_polygon = feature.get('geometry')
          write_place_output_mcf(
              geojson_dict,
              row,
              geo_polygon,
              mcf_outputs,
              output_mcf_props,
              simplification_levels,
              counters,
          )
        else:
          # Ignore duplicate entry for existing place key.
          logging.error(
              f'Ignoring duplicate entry for key: {key}, existing:'
              f' {geojson_dict[key]}, new: {row}'
          )
          counters.add_counter('error-duplicate-key-ignored', 1, key)
      counters.add_counter('processed', 1)

  logging.info(
      f'Extracted {num_props} properties for {num_features} features from'
      f' geojson with {len(features)} features'
  )
  return geojson_dict


def process_geojson_files(
    input_files: list,
    input_nodes: int,
    properties: list,
    key_property: str,
    place_name_props: list,
    dcid_template: str,
    output_csv_file: str,
    place_csv_file: str,
    output_mcf_prefix: str,
    output_mcf_props: list,
    simplification_levels: list,
):
  """Process geoJSON files."""
  counters = Counters()
  place_dict = dict()
  if place_csv_file:
    place_dict = file_util.file_load_csv_dict(
        filename=place_csv_file, key_column='place_name', value_column=None
    )
    counters.add_counter(f'places_dcid', len(place_dict))

  mcf_outputs = open_output_files(simplification_levels, output_mcf_prefix)
  geojson_dict = dict()
  input_geojson_files = file_util.file_get_matching(input_files)
  logging.info(f'Processing geoJSON files: {input_geojson_files}')
  counters.add_counter('input-geojson-files', len(input_geojson_files))
  for file in input_geojson_files:
      with file_util.FileIO(file) as fp:
        logging.info(f'Loading geoJson from file:{file}')
        geo_json = json.load(fp)
        if geo_json:
          process_geojson(
              geo_json,
              input_nodes,
              properties,
              key_property,
              place_name_props,
              dcid_template,
              geojson_dict,
              place_dict,
              mcf_outputs,
              output_mcf_props,
              simplification_levels,
              counters,
          )
  if output_csv_file:
    file_util.file_write_csv_dict(geojson_dict, output_csv_file)

  # Close any open mcf output files.
  for mcf_file in mcf_outputs:
    del mcf_file

  return geojson_dict


def write_place_output_mcf(
    geojson_dict: dict,
    place_pvs: dict,
    place_geojson: dict,
    output_mcf_files: list,
    output_mcf_props: list,
    simplification_levels: list,
    counters: Counters,
):
  """Write the place properties to the output mcf file."""
  if not output_mcf_files:
    return

  # Emit MCFs for the polygon for each simplification level.
  dcid = place_pvs.get('dcid')

  # Add any output properties to the place_pvs
  output_pvs = {}
  for format_pv in output_mcf_props:
    prop_value = eval_format_str(format_pv, place_pvs)
    if prop_value:
      out_prop, out_value = prop_value.split(':', 1)
      if out_value:
        output_pvs[out_prop] = out_value
  place_pvs.update(output_pvs)

  # Get the place type added to all output MCFs
  typeof = place_pvs.get('typeOf', 'Place')
  if ':' in typeof:
    # strip the namespace
    typeof = typeof.split(':', 1)[1]

  polygon = None
  if not dcid:
    logging.info(f'Ignoring place without dcid {place_pvs}')
    counters.add_counter(
        f'ignore-place-without-dcid', 1, place_pvs.get('place_name')
    )
  elif not place_geojson:
    logging.info(f'Ignoring place without geometry {place_pvs}')
    counters.add_counter(
        f'ignore-place-without-geometry', 1, place_pvs.get('place_name')
    )
  else:
    # Emit the MCF for the polygon
    logging.debug(f'Writing geometry for place {dcid}: {place_pvs}')
    counters.add_counter(f'output-mcf-prop-typeOf-{typeof}', 1)
    polygon = geometry.shape(place_geojson)
    lat = place_pvs.get('latitude')
    lng = place_pvs.get('longitude')
    if not lat:
      # Add Lat/Lng properties.
      lat, lng = _get_latlng(polygon)
    if lat is not None:
      place_pvs['latitude'] = float(lat)
    if lng is not None:
      place_pvs['longitude'] = float(lng)
    # Get the contained in parent polygons.
    place_pvs['Polygon'] = polygon
    parents = get_contained_polygons(dcid, polygon, geojson_dict)
    if parents:
      # parents.extend(place_pvs.get('containedInPlace', '').split(','))
      place_pvs['containedInPlace'] = ','.join(parents)
      counters.add_counter('output-with-containedInPlace', 1)
    for index in range(len(simplification_levels)):
      level, tolerance = simplification_levels[index].split(':', 1)
      tolerance = float(tolerance)
      node_mcf = []
      if not tolerance:
        # No simplification needed. Emit polygon.
        gjs = json.dumps(json.dumps(place_geojson))
        node_mcf.append(
            _MCF_TEMPLATE.format(
                dcid=dcid, typeof=typeof, level=level, polygon=gjs
            )
        )
      else:
        # Simplify polygon to the desired level.
        spolygon = polygon.simplify(tolerance)
        gjs = json.dumps(json.dumps(geometry.mapping(spolygon)))
        node_mcf.append(
            _MCF_TEMPLATE.format(
                dcid=dcid, typeof=typeof, level=level, polygon=gjs
            )
        )
        counters.add_counter(f'output-mcf-geometry-{level}', 1)
      if index == 0:
        # Add place properties from geojson into the first mcf
        for prop, value in output_pvs.items():
          if prop and value and prop != 'typeOf':
            node_mcf.append(f'{prop}: {value}')
            counters.add_counter(f'output-mcf-prop-{prop}', 1)
        logging.info(f'Generated node for {place_pvs}')
        counters.add_counter(f'output-mcf-geometry', 1)
      if node_mcf:
        # Emit the MCF with the polygon to the output file.
        output_mcf_files[index].write('\n')
        output_mcf_files[index].write('\n'.join(node_mcf))
  return polygon


def get_contained_polygons(dcid: str, polygon, geojson_dict: dict) -> list:
  """Returns a list of keys which contain the polygon."""
  parents = []
  for place_key, place_pvs in geojson_dict.items():
    if place_key != dcid:
      place_polygon = place_pvs.get('Polygon')
      if place_polygon and place_polygon.intersects(polygon):
        parents.append(place_key)
  if parents:
    logging.info(f'Place {dcid} is containedIn parents {parents}')
  return parents


def eval_format_str(format_str: str, pvs: dict) -> str:
  """Returns a formatted string with values applied from the pvs dict."""
  value = format_str
  try:
    if '{' in format_str:
      # Evaluate the value as an f-string literal
      quote = '"'
      if '"' in format_str:
        quote = "'"
      eval_str = 'f' + quote + format_str + quote
      value = eval(eval_str, {}, pvs)
    elif '=' in format_str:
      prop, eval_str = format_str.split('=', 1)
      eval_value = eval(eval_str, {}, pvs)
      value = f'{prop}{eval_value}'
  except (NameError, ValueError, TypeError, SyntaxError) as e:
    logging.error(f'Unable to format {format_str} with {pvs}, error: {e}')
    return ''
  logging.level_debug() and logging.debug(
      f'Formated {format_str} using {pvs} into {value}'
  )
  return value

def _get_place_props(
    pvs: dict, place_name_props: list, place_to_dcid: dict
) -> str:
  """Returns the dcid for the place with property values in pvs.

  Uses the place_props to get the dcid from the place_to_dcid map.
  """
  dcid = pvs.get('dcid', '')
  if dcid:
    return dcid

  # Lookup dcid for the place name
  place_name = _get_place_name(pvs, place_name_props)
  return place_to_dcid.get(place_name, {})


def _get_place_name(pvs: dict, place_props: list) -> str:
  """Return the place name concatenating the values of place_props in order from the pvs."""
  place_names = []
  for prop in place_props:
    value = pvs.get(prop)
    if value:
      place_names.append(value)
  return ', '.join(place_names)


def _get_latlng(polygon) -> (float, float):
  if not polygon:
    return None, None
  xy = polygon.centroid.coords.xy
  return (xy[1][0], xy[0][0])


def main(_):
  if _FLAGS.debug:
    logging.set_verbosity(2)
  output_props = {}
  process_geojson_files(
      _FLAGS.input_geojson,
      _FLAGS.input_nodes,
      _FLAGS.properties,
      _FLAGS.key_property,
      _FLAGS.place_name_properties,
      _FLAGS.new_dcid_template,
      _FLAGS.output_csv,
      _FLAGS.places_csv,
      _FLAGS.output_mcf_prefix,
      _FLAGS.output_mcf_pvs,
      _FLAGS.simplification_levels,
  )


if __name__ == '__main__':
  app.run(main)
