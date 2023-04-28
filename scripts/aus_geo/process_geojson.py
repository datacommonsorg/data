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
""" Script to process geojson files.

Steps:
  1. Download shp files from source, such as:
  https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/access-and-downloads/digital-boundary-files

  2. Convert the shape files to geoJson using:
  ogr2ogr -f GeoJSON <output-file.geojson>  <input-file.shp>

  3. Extract the place names and features from the shp files into a csv
  python3 process_geojson.py --input_geojson=<my.gsojson> --output_csv=<properties.csv>

  4. Run the place_resolver.py to resolve the place names to dcid.
  Verify the dcids for the place names.

  5. Generate MCF with the polygon boundaries for each resolved dcid.

"""
import os
import sys
import json
import re

from absl import app
from absl import flags
from absl import logging
from shapely import geometry

_FLAGS = flags.FLAGS

# Mandatory flags.
# Set the program to fail if these flags are not specified.
flags.DEFINE_list('input_geojson', None, 'Input geojson files to process')
flags.mark_flag_as_required('input_geojson')
flags.DEFINE_list('properties', [],
                  'List of feature properties to extract from GeoJSON.')
flags.DEFINE_string('key_property', '', 'Property to use as key.')
flags.DEFINE_list('place_name_properties', [],
                  'List of properties used to create the full place name.')
flags.DEFINE_string('output_csv', '', 'Output path for generated files.')
flags.DEFINE_string(
    'output_mcf_prefix', 'output',
    'Output file prefix for MCF nodes with geoJsonCoordinates.')
flags.DEFINE_list(
    'output_mcf_pvs', [],
    'List of comma separated propery:value strings to be added to output MCF.'
    ' The property or value can have format strings with reference to other '
    'properties  such as  "area:[{AREASQKM21} SquareKilometer]"')
flags.DEFINE_string('places_csv', 'resolved_places.csv',
                    'CSV file with columns place_name and dcid.')

# Optional flags
flags.DEFINE_boolean('debug', False, 'Enable debug log messages.')

_SCRIPTS_DIR = os.path.join(__file__.split('/scripts/')[0], 'scripts')
sys.path.append(_SCRIPTS_DIR)
sys.path.append(os.path.join(os.path.dirname(_SCRIPTS_DIR), 'util'))

import file_util

from counters import Counters

# Polygon simplification levels in the form of tuples: (<level>, <tolerance>)
# Simplified polygon is added as property: geoJsonCoordinates<level>
_SIMPLIFICATION_LEVELS = [('', 0), ('DP1', 0.01), ('DP2', 0.03), ('DP3', 0.05)]

_MCF_TEMPLATE = '''
Node: dcid:{dcid}
geoJsonCoordinates{level}: {polygon}'''


def process_geojson(
    geo_json: dict,
    properties: list = None,
    key_prop: str = '',
    place_name_props: list = [],
    output_dict: dict = None,
    places_dcid: dict = {},
    output_mcf_prefix: str = '',
    output_mcf_props: list = [],
    counters: Counters = Counters()) -> dict:
    '''Extract properties from geoJson into a dict.'''

    # Open file handles for MCF outputs for each simplification level.
    mcf_outputs = []
    if output_mcf_prefix:
        for level, tolerance in _SIMPLIFICATION_LEVELS:
            suffix = ''
            if level:
                suffix = f'_simplified_{level}'
            filename = file_util.file_get_name(file_path=output_mcf_prefix,
                                               suffix=suffix,
                                               file_ext='.mcf')
            mcf_outputs.append(file_util.FileIO(filename, mode='w'))

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
            f'Processing geoJson with feature properties: {feature_props} with key: {key_prop}'
        )
        for feature in features:
            row = dict()
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
                # Concatenate required properties to get the place name
                # Use the place_name to lookup the dcid from the places_csv.
                if place_name_props:
                    row['place_name'] = _get_place_name(row, place_name_props)
                    row['dcid'] = _get_place_dcid(row, place_name_props,
                                                  places_dcid)
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
                    write_place_output_mcf(row, geo_polygon, mcf_outputs,
                                           output_mcf_props, counters)
                else:
                    # Ignore duplicate entry for existing place key.
                    logging.error(
                        f'Ignoring duplicate entry for key: {key}, existing: {geojson_dict[key]}, new: {row}'
                    )
                    counters.add_counter('error-duplicate-key-ignored', 1, key)
            counters.add_counter('processed', 1)

    logging.info(
        f'Extracted {num_props} properties for {num_features} features from geojson with {len(features)} features.'
    )
    for file in mcf_outputs:
        del file
    return geojson_dict


def process_geojson_files(input_files: list, properties: list,
                          key_property: str, place_name_props: str,
                          output_csv_file: str, place_csv_file: str,
                          output_mcf_prefix: str, output_mcf_props):
    '''Process geoJSON files.'''
    counters = Counters()
    place_dict = dict()
    if place_csv_file:
        place_dict = file_util.file_load_csv_dict(filename=place_csv_file,
                                                  key_column='place_name',
                                                  value_column='dcid')
        counters.add_counter(f'places_dcid', len(place_dict))

    geojson_dict = dict()
    for file in file_util.file_get_matching(input_files):
        with file_util.FileIO(file) as fp:
            logging.info(f'Loading geoJson from file:{file}')
            geo_json = json.load(fp)
            if geo_json:
                process_geojson(geo_json, properties, key_property,
                                place_name_props, geojson_dict, place_dict,
                                output_mcf_prefix, output_mcf_props, counters)
    if output_csv_file:
        file_util.file_write_csv_dict(geojson_dict, output_csv_file)


def write_place_output_mcf(place_pvs: dict, place_geojson: dict,
                           output_mcf_files: list, output_mcf_props: list,
                           counters: Counters):
    '''Write the place properties to the output mcf file.'''
    if not output_mcf_files:
        return

    # Emit MCFs for the polygon for each simplification level.
    dcid = place_pvs.get('dcid')
    if not dcid:
        logging.info(f'Ignoring place without dcid {place_pvs}')
        counters.add_counter(f'ignore-place-without-dcid', 1,
                             place_pvs.get('place_name'))
    elif not place_geojson:
        logging.info(f'Ignoring place without geometry {place_pvs}')
        counters.add_counter(f'ignore-place-without-geometry', 1,
                             place_pvs.get('place_name'))
    else:
        # Emit the MCF for the polygon
        polygon = geometry.shape(place_geojson)
        for index in range(len(_SIMPLIFICATION_LEVELS)):
            level, tolerance = _SIMPLIFICATION_LEVELS[index]
            node_mcf_str = ''
            if not level or not tolerance:
                # No simplification needed. Emit polygon.
                node_mcf = []
                gjs = json.dumps(json.dumps(place_geojson))
                node_mcf.append(
                    _MCF_TEMPLATE.format(dcid=dcid,
                                         level='',
                                         polygon=place_geojson))
                # Add any additional properties.
                for format_pv in output_mcf_props:
                    prop_value = _format_pv(format_pv, place_pvs)
                    if prop_value:
                        node_mcf.append(prop_value)
                        out_prop = prop_value.split(':', 1)[0]
                        counters.add_counter(f'output-mcf-prop-{out_prop}', 1)
                node_mcf_str = '\n'.join(node_mcf)
                counters.add_counter(f'output-mcf-geometry', 1)
            else:
                # Simplify polygon to the desired level.
                spolygon = polygon.simplify(tolerance)
                gjs = json.dumps(json.dumps(geometry.mapping(spolygon)))
                node_mcf_str = _MCF_TEMPLATE.format(dcid=dcid,
                                                    level=level,
                                                    polygon=gjs)
                counters.add_counter(f'output-mcf-geometry-{level}', 1)
            if node_mcf_str:
                # Emit the MCF with the polygon to the output file.
                output_mcf_files[index].write('\n')
                output_mcf_files[index].write(node_mcf_str)


def _format_pv(format_str: str, pvs: dict) -> str:
    '''Returns a formatted string with values applied from the pvs dict.'''
    try:
        return format_str.format(**pvs)
    except KeyError as e:
        logging.debug(f'Missing prop in format {format_str}, {e}')
        return ''


def _get_place_dcid(pvs: dict, place_name_props: list,
                    place_to_dcid: dict) -> str:
    '''Returns the dcid for the place with property values in pvs.
  Uses the place_props to get the dcid from the place_to_dcid map.'''
    dcid = pvs.get('dcid', '')
    if dcid:
        return dcid

    # Lookup dcid for the place name
    place_name = _get_place_name(pvs, place_name_props)
    dcid = place_to_dcid.get(place_name, '')
    if dcid:
        pvs['dcid'] = dcid
    return dcid


def _get_place_name(pvs: dict, place_props: list) -> str:
    '''Return the place name concatenating the values of place_props in order from the pvs.'''
    place_names = []
    for prop in place_props:
        value = pvs.get(prop)
        if value:
            place_names.append(value)
    return ', '.join(place_names)


def main(_):
    if _FLAGS.debug:
        logging.set_verbosity(2)
    output_props = {}
    process_geojson_files(_FLAGS.input_geojson, _FLAGS.properties,
                          _FLAGS.key_property, _FLAGS.place_name_properties,
                          _FLAGS.output_csv, _FLAGS.places_csv,
                          _FLAGS.output_mcf_prefix, _FLAGS.output_mcf_pvs)


if __name__ == '__main__':
    app.run(main)
