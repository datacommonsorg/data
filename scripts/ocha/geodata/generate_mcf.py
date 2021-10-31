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
"""Generates ID maps and GeoJSON MCF for Pakistan, Nepal and Bangladesh."""

import glob
import os
import json
from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_string('ocha_input_geojson_pattern', '', 'GeoJSON file pattern')
flags.DEFINE_string('ocha_output_dir', '/tmp', 'Output directory path.')

# Note1: When we emit geojson string, we use two json.dumps() so it
# automatically escapes all inner quotes, and encloses the entire string in
# quotes.
# Note2: Having the appropriate type helps downstream consumers of this data
#        (e.g., IPCC pipeline).
_MCF_FORMAT = """
Node: dcid:{dcid}
typeOf: dcs:{place_type}
{gj_prop}: {gj_val}
"""

_FILE_ID_PROP = {
    'bgd_admbnda_adm1_bbs_20201113.geojson': ('ADM1', 'Division', 'Bangladesh'),
    'bgd_admbnda_adm2_bbs_20201113.geojson': ('ADM2', 'District', 'Bangladesh'),
    'npl_admbnda_adm1_nd_20201117.geojson': ('ADM1', 'Province', 'Nepal'),
    'npl_admbnda_districts_nd_20201117.geojson': ('DIST', 'District', 'Nepal'),
    'pak_admbnda_adm1_ocha_pco_gaul_20181218.geojson': ('ADM1', 'Province', 'Pakistan'),
    'pak_admbnda_adm2_ocha_pco_gaul_20181218.geojson': ('ADM2', 'District', 'Pakistan'),
}


def generate_id_map(in_pattern, out_dir):
    with open(os.path.join(out_dir, 'id_map.csv'), 'w') as out_fp:
        out_fp.write('ochaPCode,name\n')
        for fpath in glob.glob(in_pattern):
            fname = os.path.basename(fpath)
            if fname not in _FILE_ID_PROP:
                continue
            vals = _FILE_ID_PROP[fname]
            print('Processing ' + fname)
            _generate_id_map_from_file(fpath, out_fp, vals[0] + '_PCODE',
                                       vals[0] + '_EN', vals[1], vals[2])


def _generate_id_map_from_file(in_file, out_fp, id_key,
                               name_key, place_type, country):
    with open(os.path.join(in_file), 'r') as fin:
        j = json.load(fin)
        for f in j['features']:
            if ('properties' not in f or id_key not in f['properties'] or
                    name_key not in f['properties']):
                print(f['properties'])
                continue
            id_val = f['properties'][id_key]
            name_val = f['properties'][name_key]
            out_fp.write(id_val + ',"' + name_val + ' ' +
                         place_type + ', ' + country + '"\n')


def main(_):
    generate_id_map(FLAGS.ocha_input_geojson_pattern, FLAGS.ocha_output_dir)


if __name__ == "__main__":
    app.run(main)
