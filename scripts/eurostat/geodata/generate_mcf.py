# Copyright 2021 Google LLC
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
"""Generates GeoJSON MCF for Indian State and Districts."""

import os
import json
from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_string('input_eu_01m_geojson', '',
                    'Path to input files with 1:1 Million Eurostat geojson')
flags.DEFINE_string('input_eu_10m_geojson', '',
                    'Path to input files with 1:10 Million Eurostat geojson')
flags.DEFINE_string('input_eu_20m_geojson', '',
                    'Path to input files with 1:20 Million Eurostat geojson')
flags.DEFINE_string('output_geojson_dir', '/tmp', 'Output directory path.')

# Note1: When we emit geojson string, we use two json.dumps() so it
# automatically escapes all inner quotes, and encloses the entire string in
# quotes.
# Note2: Having the appropriate type helps downstream consumers of this data
#        (e.g., IPCC pipeline).
_MCF_FORMAT = """
Node: dcid:{nuts_dcid}
typeOf: dcs:{place_type}
{gj_prop}: {gj_val}
"""

# Outermost regions:
# https://en.wikipedia.org/wiki/Special_member_state_territories_and_the_European_Union#Outermost_regions
# https://user-images.githubusercontent.com/4375037/138797281-834bdcfe-a355-439b-af6f-4569a99cd27b.png
_OUTERMOST_REGIONS_NUTS1 = {
    'FRY',  # French outermost regions
    'ES7',  # Spanish Canary Islands
    'PT2',  # Portugese Azores
    'PT3',  # Portueges Madeira
}


def _is_outermost_geo(nuts_id):
    for n in _OUTERMOST_REGIONS_NUTS1:
        if nuts_id.startswith(n):
            return True
    return False


# From https://gisco-services.ec.europa.eu/distribution/v2/nuts/nuts-2016-files.html
# (https://user-images.githubusercontent.com/4375037/138574628-68bb52e5-87dc-4e02-9218-bb3bad836177.png)
# - "RG" aka region file with polygons
# - "4326" coordinates in decimal degrees
def _fname(res, lvl):
    return 'NUTS_RG_' + res + '_2016_4326_LEVL_' + lvl + '.geojson'


def generate(in_01m_gj, in_10m_gj, in_20m_gj, out_dir):
    for lvl in ['1', '2', '3']:
        _generate_file(in_20m_gj, out_dir, '20M', lvl, 'geoJsonCoordinatesDP2')
        _generate_file(in_10m_gj, out_dir, '10M', lvl, 'geoJsonCoordinatesDP1')
        _generate_file(in_01m_gj, out_dir, '01M', lvl, 'geoJsonCoordinates')


def _generate_file(in_dir, out_dir, res, lvl, gj_prop):
    with open(os.path.join(in_dir, _fname(res, lvl)), 'r') as fin:
        with open(
                os.path.join(out_dir, 'EU_NUTS' + lvl + '_' + gj_prop + '.mcf'),
                'w') as fout:
            j = json.load(fin)
            for f in j['features']:
                if ('properties' not in f or 'NUTS_ID' not in f['properties'] or
                        'geometry' not in f):
                    continue
                gj = json.dumps(json.dumps(f['geometry']))
                nuts_id = f['properties']['NUTS_ID']
                if (gj_prop != 'geoJsonCoordinates' and
                    _is_outermost_geo(nuts_id)):
                    continue
                fout.write(
                    _MCF_FORMAT.format(nuts_dcid='nuts/' + nuts_id,
                                       place_type='EurostatNUTS' + lvl,
                                       gj_prop=gj_prop,
                                       gj_val=gj))


def main(_):
    generate(FLAGS.input_eu_01m_geojson, FLAGS.input_eu_10m_geojson,
             FLAGS.input_eu_20m_geojson, FLAGS.output_geojson_dir)


if __name__ == "__main__":
    app.run(main)
