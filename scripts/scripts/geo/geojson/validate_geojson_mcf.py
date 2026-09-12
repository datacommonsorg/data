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
"""Script to process geojson coordinates in MCF files."""
import json
import os
import re
import sys

from absl import app
from absl import flags
from absl import logging
from shapely import geometry

_FLAGS = flags.FLAGS

flags.DEFINE_string('input_geo_mcf', '',
                    'Input MCF with geoJsonCoordinate properties.')
flags.DEFINE_string('output_geo_mcf', '',
                    'Input MCF with geoJsonCoordinate properties.')
flags.DEFINE_boolean('check_polygon_valid', True,
                     'If set, only emits polygons that have is_valid set.')
flags.DEFINE_boolean('fix_polygon', False, 'Fix invalid polygons if possible.')
flags.DEFINE_boolean('debug', False, 'Enable debug logs.')

# Add PATH to import modules from data/...
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_SCRIPT_PATH.split('/data/', 1)[0], 'data')
sys.path.append(_SCRIPT_PATH)
sys.path.append(os.path.join(_DATA_DIR, 'util'))
sys.path.append(os.path.join(_DATA_DIR, 'tools', 'statvar_importer'))
sys.path.append(os.path.join(os.path.join(_DATA_DIR, 'scripts', 'statvar')))

import geojson_util
import file_util
import mcf_file_util
from counters import Counters


def get_valid_geocordinate_nodes(nodes: dict,
                                 check_polygon_valid: bool = True,
                                 fix_polygon: bool = False,
                                 counters: Counters = None) -> (dict, dict):
    """Returns tuple of valid and invalid nodes with geo-coordinates."""
    valid_nodes = {}
    invalid_nodes = {}
    if counters is None:
        counters = Counters()

    dcids = list(nodes.keys())
    counters.add_counter('total', len(nodes))
    for dcid in dcids:
        node = nodes.get(dcid)
        node_valid = True
        polygon = None
        new_node = {}
        for prop, value in node.items():
            if prop.startswith('geoJsonCoordinates'):
                # Found a geoJson coordinate. Check if it is valid.
                geo_json_str = value
                polygon = geojson_util.get_geojson_polygon(
                    geo_json_str, check_polygon_valid, fix_polygon)
                if not polygon:
                    logging.error(
                        f'Invalid polygon for {dcid}: {geo_json_str[:100]}')
                    counters.add_counter(f'invalid-polygon-{prop}-{dcid}', 1,
                                         dcid)
                    counters.add_counter(f'invalid-polygon-{prop}', 1, dcid)
                    node_valid = False
                    new_node[prop] = value
                else:
                    gj_str, tolerance = geojson_util.get_limited_geojson_str(
                        geo_json_str,
                        polygon,
                        0.0,
                        fix_polygon,
                        counters=counters)
                    if gj_str:
                        new_node[prop] = gj_str
                        counters.add_counter(f'output-nodes-{prop}', 1, dcid)
                        if tolerance > 0.001:
                            # Node has been simplified due to size. Add a note
                            note_prop = prop + 'Note'
                            new_node[note_prop] = (
                                f'"Polygon simplified with tolerance {tolerance}"'
                            )
                            counters.add_counter(
                                f'output-nodes-{note_prop}-{tolerance}', 1,
                                dcid)
                            counters.add_counter(
                                f'output-node-{dcid}-{note_prop}-{tolerance}',
                                1)
                            counters.add_counter(
                                f'output-node-{dcid}-{prop}-size', len(value))
                            counters.add_counter(
                                f'output-node-{dcid}-{prop}-resize',
                                len(gj_str))
                    else:
                        logging.error(
                            f'Invalid geojson for {dcid}: {geo_json_str[:100]}')
                        counters.add_counter(f'invalid-geoson-{prop}-{dcid}', 1,
                                             dcid)
                        counters.add_counter(f'invalid-geojson-{prop}', 1, dcid)
                        node_valid = False
            else:
                new_node[prop] = value
                counters.add_counter(f'output-nodes-{prop}', 1)
            counters.add_counter('processed', 1)
        if new_node and node_valid:
            valid_nodes[dcid] = new_node
            counters.add_counter(f'output-valid-nodes', 1, dcid)
        else:
            invalid_nodes[dcid] = new_node
            counters.add_counter(f'invalid-nodes', 1, dcid)
    return (valid_nodes, invalid_nodes)


def process_geo_mcf(
    filename: str,
    output_file: str,
    check_polygon_valid: bool = True,
    fix_polygon: bool = False,
    nodes: dict = None,
    counters: Counters = None,
):
    """Process MCF nodes with geoJson coordinates."""
    if counters is None:
        counters = Counters()
    logging.info(f'Loading mcf nodes from {filename}')
    mcf_nodes = mcf_file_util.load_mcf_nodes(filename,
                                             nodes,
                                             append_values=False,
                                             normalize=False)
    (valid_nodes,
     invalid_nodes) = get_valid_geocordinate_nodes(mcf_nodes,
                                                   check_polygon_valid,
                                                   fix_polygon, counters)
    if output_file and valid_nodes:
        logging.info(f'Writing {len(valid_nodes)} into {output_file}')
        mcf_file_util.write_mcf_nodes(valid_nodes, output_file)
    if output_file and invalid_nodes:
        invalid_nodes_file = file_util.file_get_name(output_file, "_invalid",
                                                     "mcf")
        logging.info(f'Writing {len(invalid_nodes)} into {invalid_nodes_file}')
        mcf_file_util.write_mcf_nodes(invalid_nodes, invalid_nodes_file)


def main(_):
    if _FLAGS.debug:
        logging.set_verbosity(logging.DEBUG)
    process_geo_mcf(_FLAGS.input_geo_mcf, _FLAGS.output_geo_mcf,
                    _FLAGS.check_polygon_valid, _FLAGS.fix_polygon)


if __name__ == '__main__':
    app.run(main)
