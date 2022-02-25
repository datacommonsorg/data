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

import csv
import glob
import os
import json
from shapely import geometry
from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_string('ocha_input_geojson_pattern', '', 'GeoJSON file pattern')
flags.DEFINE_string('ocha_resolved_id_map', '', 'Resolved ID map')
flags.DEFINE_string('ocha_output_dir', '/tmp', 'Output directory path.')
flags.DEFINE_boolean(
    'ocha_generate_id_map', False, 'If true, then this just generates '
    'the ID maps for resolution')

# Note1: When we emit geojson string, we use two json.dumps() so it
# automatically escapes all inner quotes, and encloses the entire string in
# quotes.
# Note2: Having the appropriate type helps downstream consumers of this data
#        (e.g., IPCC pipeline).
_GJ_MCF = """
Node: dcid:{dcid}
typeOf: dcs:{place_type}
{gj_prop}: {gj_val}
"""

_ID_MCF = """
Node: dcid:{dcid}
typeOf: dcs:{place_type}
ochaPCode: "{pcode}"
"""

_ID_CONTAINS_MCF = """
Node: dcid:{dcid}
typeOf: dcs:{place_type}
ochaPCode: "{pcode}"
containedInPlace: dcid:{parent}
"""

_FILE_METADATA = {
    'bgd_admbnda_adm1_bbs_20201113':
        ('ADM1', 'Division', 'Bangladesh', 'AdministrativeArea1'),
    'bgd_admbnda_adm2_bbs_20201113':
        ('ADM2', 'District', 'Bangladesh', 'AdministrativeArea2'),
    'npl_admbnda_adm1_nd_20201117':
        ('ADM1', 'Province', 'Nepal', 'AdministrativeArea1'),
    'npl_admbnda_districts_nd_20201117':
        ('DIST', 'District', 'Nepal', 'AdministrativeArea2'),
    'pak_admbnda_adm1_ocha_pco_gaul_20181218':
        ('ADM1', 'Province', 'Pakistan', 'AdministrativeArea1'),
    'pak_admbnda_adm2_ocha_pco_gaul_20181218':
        ('ADM2', 'District', 'Pakistan', 'AdministrativeArea3'),
    'chn_admbnda_adm1_ocha_2020':
        ('ADM1', 'Province', 'China', 'AdministrativeArea1'),
    'chn_admbnda_adm2_ocha_2020':
        ('ADM2', 'Prefecture', 'China', 'AdministrativeArea2'),
}


# Threshold to DP level map, from
# scripts/us_census/geojsons_low_res/generate_mcf.py
_DP_LEVEL_MAP = {1: 0.01, 2: 0.03, 3: 0.05}


def _process_file(in_fp, md, args):
    pcode_key = md[0] + '_PCODE'
    name_key = md[0] + '_EN'
    type_name = md[1]
    country = md[2]
    place_type = md[3]

    if not args['generate_id_map']:
        fname = '_'.join([country, place_type, 'GeoJSON']) + '.mcf'
        gj_mcf = open(os.path.join(args['out_dir'], fname), 'w')

        fname = '_'.join([country, place_type, 'GeoJSON_Simplified']) + '.mcf'
        simplified_gj_mcf = open(os.path.join(args['out_dir'], fname), 'w')

        fname = '_'.join([country, place_type, 'PCode']) + '.mcf'
        id_mcf = open(os.path.join(args['out_dir'], fname), 'w')

    j = json.load(in_fp)
    for f in j['features']:
        if ('properties' not in f or pcode_key not in f['properties'] or
                name_key not in f['properties'] or 'geometry' not in f):
            print(f['properties'])
            continue
        pcode_val = f['properties'][pcode_key]
        name_val = f['properties'][name_key]

        if args['generate_id_map']:
            args['id_fp'].write(pcode_val + ',"' + name_val + ' ' + type_name +
                                ', ' + country + '"\n')
        else:
            # Write Geo JSON
            gj = json.dumps(json.dumps(f['geometry']))
            if pcode_val not in args['id_map']:
                print('Missing DCID for ' + pcode_val)
                continue
            dcid = args['id_map'][pcode_val]
            gj_mcf.write(_GJ_MCF.format(dcid=dcid, place_type=place_type,
                                        gj_prop='geoJsonCoordinates',
                                        gj_val=gj))

            poly = geometry.shape(f['geometry'])
            for dp, tolerance in _DP_LEVEL_MAP.items():
                spoly = poly.simplify(tolerance)
                gjs = json.dumps(json.dumps(geometry.mapping(spoly)))
                simplified_gj_mcf.write(_GJ_MCF.format(
                    dcid=dcid, place_type=place_type,
                    gj_prop='geoJsonCoordinatesDP' + str(dp),
                    gj_val=gjs))

            # Write PCode and containment
            pcode_parent = pcode_val[:-2]
            if (place_type != 'AdministrativeArea1' and
                    pcode_parent in args['id_map']):
                id_mcf_str = _ID_CONTAINS_MCF.format(
                    dcid=dcid,
                    place_type=place_type,
                    pcode=pcode_val,
                    parent=args['id_map'][pcode_parent])
            else:
                id_mcf_str = _ID_MCF.format(dcid=dcid,
                                            place_type=place_type,
                                            pcode=pcode_val)
            id_mcf.write(id_mcf_str)

    if not args['generate_id_map']:
        gj_mcf.close()
        simplified_gj_mcf.close()
        id_mcf.close()


def _process(in_pattern, args):
    for fpath in glob.glob(in_pattern):
        fname = os.path.basename(fpath).split('.')[0]
        if fname not in _FILE_METADATA:
            continue
        print('Processing ' + fname)
        with open(os.path.join(fpath), 'r') as in_fp:
            _process_file(in_fp, _FILE_METADATA[fname], args)


def _generate_mcf(in_pattern, id_file, out_dir):
    id_map = {}
    with open(id_file, 'r') as id_fp:
        csvr = csv.DictReader(id_fp)
        for row in csvr:
            if not row['dcid']:
                continue
            id_map[row['ochaPCode']] = row['dcid']
    _process(in_pattern, {
        'generate_id_map': False,
        'id_map': id_map,
        'out_dir': out_dir
    })


def _generate_id_map(in_pattern, out_dir):
    with open(os.path.join(out_dir, 'id_map.csv'), 'w') as id_fp:
        id_fp.write('ochaPCode,name\n')
        _process(in_pattern, {'generate_id_map': True, 'id_fp': id_fp})


def main(_):
    if FLAGS.ocha_generate_id_map:
        _generate_id_map(FLAGS.ocha_input_geojson_pattern,
                         FLAGS.ocha_output_dir)
    else:
        _generate_mcf(FLAGS.ocha_input_geojson_pattern,
                      FLAGS.ocha_resolved_id_map, FLAGS.ocha_output_dir)


if __name__ == "__main__":
    app.run(main)
