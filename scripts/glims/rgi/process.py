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
"""Generate Glaciers data for import into DC."""

import csv
import datacommons as dc
import json
import glob
import os
from shapely import geometry
from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_string('rgi_input_csv_pattern', '', 'Glacier CSV file pattern')
flags.DEFINE_string('rgi_output_dir', '/tmp/', 'Output directory')


def _load_geojsons():
    countries = dc.get_places_in(['Earth'], 'Country')['Earth']
    resp = dc.get_property_values(countries, 'geoJsonCoordinatesDP2')
    geojsons = {}
    for p, gj in resp.items():
        if not gj:
            continue
        geojsons[p] = geometry.shape(json.loads(gj[0]))
    print('Got', len(geojsons), 'geojsons!')
    cip = dc.get_property_values(countries, 'containedInPlace')
    return geojsons, cip


def _quote(s):
    return '"' + str(s) + '"'


def _refs(refs):
    return ','.join(['dcid:' + r for r in refs])


def _strip(r):
    for k in r:
        if not isinstance(r[k], list):
            r[k] = r[k].strip()


def _get_contained_in_places(lat, lon, country_gj, continent_map):
    point = geometry.Point(lon, lat)
    cip = []
    for p, gj in country_gj.items():
        if gj.contains(point):
            cip.append(p)
            break
    if cip:
        cip.extend(continent_map[cip[0]])
    return cip


def _process_file(in_fp, in_file, country_gj, continent_map, writer):
    reader = csv.DictReader(in_fp)
    for irow in reader:
        _strip(irow)

        # Keep only large-ish glaciers
        if float(irow['Area']) < 50:
            continue

        lat = float('%.4f' % float(irow['CenLat']))
        lon = float('%.4f' % float(irow['CenLon']))
        cips = _get_contained_in_places(lat, lon, country_gj, continent_map)

        if not irow['EndDate'].startswith('-'):
            year = irow['EndDate'][0:4]
        else:
            year = '2017'  # Default is date of RGI release

        orow = {
            'rgiId': _quote(irow['RGIId']),
            'glimsId': _quote(irow['GLIMSId']),
            'dcid': _quote('rgiId/' + irow['RGIId']),
            'name': _quote(irow['Name']) if irow['Name'] else '',
            'latitude': _quote(lat),
            'longitude': _quote(lon),
            'containedInPlace': _refs(cips),
            'observationAbout': 'dcid:rgiId/' + irow['RGIId'],
            'observationDate': _quote(year),
            'value': irow['Area'],
        }
        writer.writerow(orow)


def _process(in_pattern, out_dir, country_gj, continent_map):
    with open(os.path.join(out_dir, 'rgi6_glaciers.csv'), 'w') as out_fp:
        writer = csv.DictWriter(out_fp,
                                fieldnames=[
                                    'rgiId', 'glimsId', 'dcid', 'name',
                                    'latitude', 'longitude', 'observationAbout',
                                    'observationDate', 'value',
                                    'containedInPlace'
                                ],
                                doublequote=False,
                                escapechar='\\')
        writer.writeheader()
        for fpath in glob.glob(in_pattern):
            with open(fpath, 'r', encoding='ISO-8859-1') as in_fp:
                print('Processing ' + fpath)
                _process_file(in_fp, fpath, country_gj, continent_map, writer)


def main(_):
    assert FLAGS.rgi_input_csv_pattern and FLAGS.rgi_output_dir
    country_gj, continent_map = _load_geojsons()
    _process(FLAGS.rgi_input_csv_pattern, FLAGS.rgi_output_dir, country_gj,
             continent_map)


if __name__ == "__main__":
    app.run(main)
