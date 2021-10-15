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
from india.geo.states import IndiaStatesMapper
from india.formatters import CodeFormatter

FLAGS = flags.FLAGS

flags.DEFINE_string('input_state_geojson', '',
                    'Path to the India State geojson file.')
flags.DEFINE_string('input_district_geojson', '',
                    'Path to the India District geojson file.')
flags.DEFINE_string('output_geojson_dir', '/tmp', 'Output directory path.')

# Note1: When we emit geojson string, we use two json.dumps() so it
# automatically escapes all inner quotes, and encloses the entire string in
# quotes.
# Note2: Having the appropriate type helps downstream consumers of this data
#        (e.g., IPCC pipeline).
_MCF_FORMAT = """
Node: india_place_{ext_id}
typeOf: dcs:{place_type}
{ext_id_prop}: "{ext_id}"
geoJsonCoordinates: {gj_str}
"""


def generate(in_state, in_district, out_path):
    with open(in_state) as fin:
        with open(os.path.join(out_path, "India_States_GeoJson.mcf"),
                  'w') as fout:
            _generate_states(fin, fout)

    with open(in_district) as fin:
        with open(os.path.join(out_path, "India_Districts_GeoJson.mcf"),
                  'w') as fout:
            _generate_districts(fin, fout)


def _generate_states(fin, fout):
    j = json.load(fin)
    for f in j['features']:
        if ('properties' not in f or 'ST_NM' not in f['properties'] or
                'geometry' not in f):
            continue
        iso = IndiaStatesMapper.get_state_name_to_iso_code_mapping(
            f['properties']['ST_NM'])
        gj = json.dumps(json.dumps(f['geometry']))
        fout.write(
            _MCF_FORMAT.format(ext_id=iso,
                               place_type='AdministrativeArea1',
                               ext_id_prop='isoCode',
                               gj_str=gj))


def _generate_districts(fin, fout):
    j = json.load(fin)
    for f in j['features']:
        if ('properties' not in f or 'censuscode' not in f['properties'] or
                'geometry' not in f):
            continue
        census2011 = str(f['properties']['censuscode'])
        census2011 = CodeFormatter.format_census2011_code(census2011)
        gj = json.dumps(json.dumps(f['geometry']))
        fout.write(
            _MCF_FORMAT.format(ext_id=census2011,
                               place_type='AdministrativeArea2',
                               ext_id_prop='indianCensusAreaCode2011',
                               gj_str=gj))


def main(_):
    generate(FLAGS.input_state_geojson, FLAGS.input_district_geojson,
             FLAGS.output_geojson_dir)


if __name__ == "__main__":
    app.run(main)
