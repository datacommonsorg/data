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
import datacommons
from shapely import geometry

_FLAGS = flags.FLAGS

# Polygon simplification levels in the form of tuples: '<level>:<tolerance>'
# Simplified polygon is added as property: geoJsonCoordinates<level>
SIMPLIFICATION_LEVELS = [':0', 'DP1:0.01', 'DP2:0.03', 'DP3:0.05']

# Mandatory flags.
# Set the program to fail if these flags are not specified.
flags.DEFINE_list('input_geojson', None, 'Input geojson files to process')
flags.mark_flag_as_required('input_geojson')
flags.DEFINE_integer('num_input_nodes', sys.maxsize,
                     'Number of input nodes to process.')
flags.DEFINE_list('properties', [],
                  'List of feature properties to extract from GeoJSON.')
flags.DEFINE_string('key_property', '', 'Property to use as key.')
flags.DEFINE_list(
    'place_name_properties',
    [],
    'List of properties used to create the full place name.',
)
flags.DEFINE_string('new_dcid_template', '',
                    'Template to generate dcid for unresolved places.')
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
flags.DEFINE_string('default_type_of', 'Place',
                    'Default typeOf for output MCF nodes.')
flags.DEFINE_string(
    'places_csv',
    'resolved_places.csv',
    'CSV file with columns place_name and dcid.',
)
flags.DEFINE_string(
    'place_key',
    'place_name',
    'Column in places_csv to be used to lookup a place.',
)
flags.DEFINE_list(
    'simplification_levels',
    SIMPLIFICATION_LEVELS,
    'List of property <suffix>:<tolerance> for Douglas Peucker simplification of'
    ' geoJson coordinates.',
)
# Optional flags
flags.DEFINE_boolean(
    'output_contained',
    False,
    'Compute containedInPlace for polygons amonst other polygons in input.',
)
flags.DEFINE_boolean('fix_polygon', False, 'Fix invalid polygons if possible.')
flags.DEFINE_boolean('merge_duplicates', False,
                     'Merge polygons for duplicate dcids.')
flags.DEFINE_boolean('debug', False, 'Enable debug log messages.')

_SCRIPTS_DIR = os.path.join(
    os.path.abspath(__file__).split('/scripts/')[0], 'scripts')
sys.path.append(_SCRIPTS_DIR)
sys.path.append(os.path.join(os.path.dirname(_SCRIPTS_DIR), 'util'))

import file_util
import geojson_util

from counters import Counters
from dc_api_wrapper import dc_api_batched_wrapper

_MCF_TEMPLATE = """
Node: dcid:{dcid}
typeOf: dcid:{typeof}
geoJsonCoordinates{level}: {geojson_str}"""

# Maximum geoJsonCoordinates value in bytes.
# Polygons larger than this are simplified with a node in geoJsonCoordinatesNote.
_MAX_GEOJSON_SIZE = 10000000
# Tolerance to simplify the polygon when it exceeds _MAX_GEOJSON_SIZE
# Polygon is simplified successively by this until it fits.
_MIN_TOLERANCE = 0.01


def merge_nodes(nodes: list, fix_polygon: bool = False) -> dict:
    """Return a node that has merged values from all nodes.

    Args:
      nodes: list of nodes with each node as dict of property:value

    Returns:
      dict with merged values form nodes
    """
    node = {}
    for n in nodes:
        for prop, value in n.items():
            if value is None:
                continue
            cur_val = node.get(prop)
            if cur_val is None:
                # Add a new property:value
                node[prop] = value
            elif cur_val != value:
                # Merge property with existing value.
                if (prop == '#Geometry' or
                    (prop.startswith('geoJsonCoordinates') and
                     'Note' not in prop)):
                    # Merge geoJson polygons.
                    node[prop] = geojson_util.merge_geojson_str(
                        [cur_val, value])
                else:
                    node[prop] = f'{cur_val}, {value}'
    return node


def open_output_files(simplification_levels: list,
                      output_mcf_prefix: str) -> list:
    # Open file handles for MCF outputs for each simplification level.
    mcf_outputs = []
    output_files = []
    if output_mcf_prefix:
        for index in range(len(simplification_levels)):
            level, tolerance = simplification_levels[index].split(':', 1)
            suffix = ''
            if level:
                suffix = f'_simplified_{level}'
            filename = file_util.file_get_name(file_path=output_mcf_prefix,
                                               suffix=suffix,
                                               file_ext='.mcf')
            mcf_outputs.append(file_util.FileIO(filename, mode='w'))
            output_files.append(filename)
        logging.info(f'Opened MCF files: {output_files}')
    return mcf_outputs


def process_geojson(
        geo_json: dict,
        num_input_nodes: int,
        properties: list = None,
        key_prop: str = '',
        place_name_props: list = [],
        dcid_template: str = '',
        output_dict: dict = None,
        places_dcid: dict = {},
        mcf_outputs: list = [],
        output_mcf_props: list = [],
        default_type_of: str = 'Place',
        simplification_levels: list = SIMPLIFICATION_LEVELS,
        fix_polygon: bool = False,
        merge_duplicates: bool = False,
        compute_contained: bool = False,
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
    if not features:
        logging.error(f'No features in geojson. Ignoring')
        counters.add_counters(f'geojson-without-features', 1)
        return geojson_dict

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
        f' {key_prop}')
    row_index = 0
    for feature in features:
        if row_index > num_input_nodes:
            break
        geo_polygon = feature.get('geometry')
        if not geo_polygon:
            logging.level_debug() and logging.debug(
                f'input {row_index} has no geometry {feature}')
            counters.add_counter(f'warning-input-without-geometry', 1)
            continue
        row_index += 1
        row = {'RowIndex': row_index, '#Geometry': geo_polygon}
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
        # Set empty value for missing properties.
        for prop in properties:
            if prop not in row:
                row[prop] = ''
        # Concatenate required properties to get the place name
        # Use the place_name to lookup the dcid from the places_csv.
        if place_name_props or key_prop:
            # Lookup place properties by name
            row['place_name'] = _get_place_name(row, place_name_props)
            place_props = _get_place_dcid_from_props(row, place_name_props,
                                                     places_dcid)
            if not place_props and key_prop:
                # Lookup place properties by key_property
                place_props = _get_place_dcid_from_props(
                    row, [key_prop], places_dcid)
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
                    logging.level_debug() and logging.debug(
                        f'Generated dcid: {row}')
        else:
            key = dcid
        num_features += 1
        if not key:
            key = row.get('dcid')
            if not key:
                key = len(geojson_dict)
        # Emit the place features if the place key is unique.
        if key not in geojson_dict:
            geojson_dict[key] = row
        else:
            if merge_duplicates:
                geojson_dict[key] = merge_nodes([geojson_dict[key], row],
                                                fix_polygon)
                logging.info(f'Merged node for {key}')
                counters.add_counter('warning-merged-node', 1, key)
            else:
                # Ignore duplicate entry for existing place key.
                logging.error(
                    f'Ignoring duplicate entry for key: {key}, existing:'
                    f' {geojson_dict[key]}, new: {row}')
                counters.add_counter('error-duplicate-key-ignored', 1, key)
    _set_place_types(geojson_dict, places_dcid, default_type_of, counters)
    for key, row in geojson_dict.items():
        # Emit MCFs for the polygon for each simplification level.
        if '#Geometry' in row:
            geo_polygon = row.pop('#Geometry')
            write_place_output_mcf(
                geojson_dict,
                row,
                geo_polygon,
                mcf_outputs,
                output_mcf_props,
                simplification_levels,
                fix_polygon,
                compute_contained,
                counters,
            )
            counters.add_counter('processed', 1)
        else:
            logging.error(f'Ignored row without geometry: {row}')
            counters.add_counter('ignored-geo-dict', 1)

    logging.info(
        f'Extracted {num_props} properties for {num_features} features from'
        f' geojson with {len(features)} features')
    return geojson_dict


def process_geojson_files(
    input_files: list,
    num_input_nodes: int,
    properties: list,
    key_property: str,
    place_name_props: list,
    dcid_template: str,
    output_csv_file: str,
    place_csv_files: str,
    place_csv_key: str,
    output_mcf_prefix: str,
    output_mcf_props: list,
    default_type_of: str = 'Place',
    simplification_levels: list = SIMPLIFICATION_LEVELS,
    fix_polygon: bool = False,
    merge_duplicates: bool = False,
    compute_contained: bool = False,
):
    """Process geoJSON files."""
    counters = Counters()
    place_dict = dict()
    for place_file in file_util.file_get_matching(place_csv_files):
        place_dict.update(
            file_util.file_load_csv_dict(filename=place_file,
                                         key_column=place_csv_key,
                                         value_column=None))
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
                    num_input_nodes,
                    properties,
                    key_property,
                    place_name_props,
                    dcid_template,
                    geojson_dict,
                    place_dict,
                    mcf_outputs,
                    output_mcf_props,
                    default_type_of,
                    simplification_levels,
                    fix_polygon,
                    merge_duplicates,
                    compute_contained,
                    counters,
                )
    if output_csv_file:
        columns = []
        for key, pvs in geojson_dict.items():
            for prop in pvs.keys():
                if prop and not prop.startswith('#') and prop not in columns:
                    columns.append(prop)
        file_util.file_write_csv_dict(geojson_dict, output_csv_file, columns)

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
    fix_polygon: bool,
    compute_contained: bool,
    counters: Counters,
):
    """Write the place properties to the output mcf file."""
    if not output_mcf_files:
        return

    # Emit MCFs for the polygon for each simplification level.
    dcid = _get_dcid(place_pvs)

    polygon = None
    if not dcid:
        logging.info(f'Ignoring place without dcid {place_pvs}')
        counters.add_counter(f'ignore-place-without-dcid', 1,
                             place_pvs.get('place_name'))
        return polygon
    if not place_geojson:
        logging.info(f'Ignoring place without geometry {place_pvs}')
        counters.add_counter(f'ignore-place-without-geometry', 1,
                             place_pvs.get('place_name'))
        return polygon

    # Remove any property with empty values
    for prop in list(place_pvs.keys()):
        value = place_pvs.get(prop)
        if not value:
            place_pvs.pop(prop)

    # Add any polygon properties
    logging.debug(f'Writing geometry for place {dcid}: {place_pvs}')
    polygon = geojson_util.get_geojson_polygon(place_geojson, fix_polygon)
    if place_geojson and polygon is None:
        logging.error(f'Invalid polygon for {dcid}')
        counters.add_counter(f'error-invalid-polygon', 1, dcid)
        return None
    place_pvs['#Polygon'] = polygon
    lat = place_pvs.get('latitude')
    lng = place_pvs.get('longitude')
    if not lat:
        # Add Lat/Lng properties.
        lat, lng = _get_latlng(polygon)
    if lat is not None:
        place_pvs['latitude'] = float(lat)
    if lng is not None:
        place_pvs['longitude'] = float(lng)

    # Add any output properties to the place_pvs
    output_pvs = {}
    for format_pv in output_mcf_props:
        prop_value = eval_format_str(format_pv, place_pvs)
        if prop_value:
            out_prop, out_value = prop_value.split(':', 1)
            if out_value:
                output_pvs[out_prop] = out_value
    place_pvs.update(output_pvs)
    typeof = _get_prop_value(place_pvs, 'typeOf', 'Place')

    # Get the contained in parent polygons.
    if compute_contained:
        parents = get_contained_polygons(dcid, polygon, geojson_dict)
        if parents:
            # parents.extend(place_pvs.get('containedInPlace', '').split(','))
            place_pvs['containedInPlace'] = ','.join(parents)
            counters.add_counter('output-with-containedInPlace', 1)
    for index in range(len(simplification_levels)):
        level, tolerance = simplification_levels[index].split(':', 1)
        tolerance = float(tolerance)
        node_mcf = []
        if tolerance > 0.0001:
            # Simplify polygon to the desired level.
            spolygon = polygon.simplify(tolerance)
        else:
            spolygon = polygon
        gjson_str, output_tolerance = geojson_util.get_limited_geojson_str(
            '', spolygon, tolerance, fix_polygon, counters=counters)
        if gjson_str:
            node_mcf.append(
                _MCF_TEMPLATE.format(dcid=dcid,
                                     typeof=typeof,
                                     level=level,
                                     geojson_str=gjson_str))
            counters.add_counter(f'output-mcf-geometry-{level}-{typeof}', 1)
        else:
            logging.error(f'Failed to generate geojsonCoordinates for {dcid}')
            counters.add_counter(f'error-geometry-{level}-{typeof}', 1, dcid)

        if output_tolerance > (tolerance + 0.00001):
            # Add a note on simplification
            logging.info(
                f'Simplified polygon for {dcid}:{level} to {output_tolerance}')
            node_mcf.append(
                f'geoJsonCoordinates{level}Note: "Polygon simplified using Douglas-Peucker algorithm with tolerance {output_tolerance}"'
            )
            counters.add_counter(
                f'extra-simplification-{level}-{output_tolerance}', 1)
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
            place_polygon = place_pvs.get('#Polygon')
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
        f'Formated {format_str} using {pvs} into {value}')
    return value


def get_place_typeof(dcid: str, place_pvs: str, default: str = 'Place') -> str:
    """Returns the typeOf for the node."""
    typeof = place_pvs.get('typeOf')
    if not typeof:
        # Lookup DC API for typeOf
        types = dc_api_batched_wrapper(datacommons.get_property_values, [dcid],
                                       {'prop': 'typeOf'})
        if types:
            typeof = types.get(dcid)
            if typeof and isinstance(typeof, list):
                typeof = typeof[0]
    if typeof and ':' in typeof:
        # strip the namespace
        typeof = typeof.split(':', 1)[1]
    if typeof:
        return typeof
    return default


def _get_prop_value(pvs: dict, prop: str, default_value: str = '') -> str:
    value = pvs.get(prop, default_value)
    if value:
        value = value.strip()
        value = value[value.find(':') + 1:]
    return value


def _get_dcid(pvs: dict) -> str:
    """Returns the dcid from the property values."""
    dcid = _get_prop_value(pvs, 'dcid')
    if not dcid:
        dcid = _get_prop_value(pvs, 'Node')
    if dcid and '/' in dcid:
        return dcid
    return ''


def _get_place_dcid_from_props(pvs: dict, place_name_props: list,
                               place_to_dcid: dict) -> str:
    """Returns the dcid for the place with property values in pvs.

  Uses the place_props to get the dcid from the place_to_dcid map.
  """
    dcid = _get_dcid(pvs)
    if dcid:
        # Get place properties for the dcid
        for key, place_pvs in place_to_dcid.items():
            place_dcid = _get_dcid(place_pvs)
            if dcid == place_dcid:
                return place_pvs

    # Lookup properties for the place name
    place_name = _get_place_name(pvs, place_name_props)
    return place_to_dcid.get(place_name, {})


def _get_place_name(pvs: dict, place_props: list) -> str:
    """Return the place name concatenating the values of place_props in order from the pvs."""
    place_names = []
    for prop in place_props:
        value = str(pvs.get(prop, ''))
        if value:
            place_names.append(value)
    return ', '.join(place_names)


def _get_latlng(polygon) -> (float, float):
    """Returns the lat/lng of a point within the polygon."""
    if not polygon:
        return None, None
    # xy = polygon.centroid.coords.xy
    xy = polygon.representative_point().coords.xy
    return (xy[1][0], xy[0][0])


def _set_place_types(
        geojson_dict: dict,
        place_dict: dict,
        default_typeof: str,
        counters: Counters = Counters(),
) -> dict:
    """Sets the property such as typeOf for each node in geojson_dict."""
    # Get typeOf for any places in place_dict.
    if place_dict:
        for place_pvs in place_dict.values():
            dcid = _get_dcid(place_pvs)
            typeof = _get_prop_value(place_pvs, 'typeOf')
            if dcid and typeof:
                if dcid in geojson_dict:
                    pvs = geojson_dict[dcid]
                    place_type = _get_prop_value(pvs, 'typeOf')
                    if not place_type:
                        pvs['typeOf'] = typeof
                        counters.add_counter('node-place-typeof-{typeof}', 1,
                                             dcid)

    # Lookup typeOf for places without type.
    resolve_type_dcids = []
    for dcid, pvs in geojson_dict.items():
        typeof = pvs.get('typeOf')
        if not typeof and dcid and isinstance(dcid, str):
            resolve_type_dcids.append(dcid)
    if resolve_type_dcids:
        place_types = dc_api_batched_wrapper(datacommons.get_property_values,
                                             resolve_type_dcids,
                                             {'prop': 'typeOf'})
        counters.add_counter('dc-api-lookup-typeof', len(resolve_type_dcids))
        for dcid, typeof in place_types.items():
            if typeof and isinstance(typeof, list):
                typeof = typeof[0]
            if typeof:
                geojson_dict[dcid]['typeOf'] = typeof
            counters.add_counter(f'node-dc-api-typeof-{typeof}', 1, dcid)

    # Set default typeof for nodes without type
    for dcid, pvs in geojson_dict.items():
        typeof = pvs.get('typeOf')
        if not typeof:
            pvs['typeOf'] = default_typeof
            counters.add_counter(f'node-default-typeof-{default_typeof}', 1,
                                 dcid)
    return geojson_dict


def main(_):
    if _FLAGS.debug:
        logging.set_verbosity(2)
    output_props = {}
    process_geojson_files(
        _FLAGS.input_geojson,
        _FLAGS.num_input_nodes,
        _FLAGS.properties,
        _FLAGS.key_property,
        _FLAGS.place_name_properties,
        _FLAGS.new_dcid_template,
        _FLAGS.output_csv,
        _FLAGS.places_csv,
        _FLAGS.place_key,
        _FLAGS.output_mcf_prefix,
        _FLAGS.output_mcf_pvs,
        _FLAGS.default_type_of,
        _FLAGS.simplification_levels,
        _FLAGS.fix_polygon,
        _FLAGS.merge_duplicates,
        _FLAGS.output_contained,
    )


if __name__ == '__main__':
    app.run(main)
