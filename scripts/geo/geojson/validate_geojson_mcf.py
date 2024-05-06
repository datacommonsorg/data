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

# Add PATH to import modules from data/...
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_SCRIPT_PATH.split('/data/', 1)[0], 'data')
sys.path.append(_SCRIPT_PATH)
sys.path.append(os.path.join(_DATA_DIR, 'util'))
sys.path.append(os.path.join(os.path.join(_DATA_DIR, 'scripts', 'statvar')))

import geojson_util
import file_util
import mcf_file_util
from counters import Counters


def get_valid_geocordinate_nodes(nodes: dict,
                                 counters: Counters = None) -> dict:
    """Returns processed nodes with geo-coordinates."""
    valid_nodes = {}
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
                polygon = geojson_util.get_geojson_polygon(geo_json_str)
                if not polygon:
                    counters.add_counter(f'invalid-polygon-{prop}', 1, dcid)
                    node_valid = False
                else:
                    gj_str, tolerance = geojson_util.get_limited_geojson_str(
                        geo_json_str, polygon)
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
                                f'output-node-{dcid}-{note_prop}-{tolerance}', 1)
                            counters.add_counter(
                                f'output-node-{dcid}-{prop}-size', len(value))
                            counters.add_counter(
                                f'output-node-{dcid}-{prop}-resize', len(gj_str))
            else:
                new_node[prop] = value
                counters.add_counter(f'output-nodes-{prop}', 1)
            counters.add_counter('processed', 1)
        if new_node:
            valid_nodes[dcid] = new_node
        else:
            logging.error(f'Dropped invalid node for {dcid}')
    return valid_nodes


def process_geo_mcf(
    filename: str,
    output_file: str,
    nodes: dict = None,
    counters: Counters = None,
):
    """Process MCF nodes with geoJson coordinates."""
    if counters is None:
        counters = Counters()
    logging.info(f'Loading mcf nodes from {filename}')
    mcf_nodes = mcf_file_util.load_mcf_nodes(filename, nodes)
    valid_nodes = get_valid_geocordinate_nodes(mcf_nodes, counters)
    if output_file and valid_nodes:
        logging.info(f'Writing {len(valid_nodes)} into {output_file}')
        mcf_file_util.write_mcf_nodes(valid_nodes, output_file)


def main(_):
    process_geo_mcf(_FLAGS.input_geo_mcf, _FLAGS.output_geo_mcf)


if __name__ == '__main__':
    app.run(main)
