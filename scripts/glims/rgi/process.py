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
import glob
import json
import os
from pathlib import Path
import sys

from absl import app
from absl import flags
from shapely import geometry

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from util.dc_api_wrapper import get_datacommons_client

FLAGS = flags.FLAGS

flags.DEFINE_string('rgi_input_csv_pattern', '', 'Glacier CSV file pattern')
flags.DEFINE_string('rgi_output_dir', '/tmp/', 'Output directory')


def _extract_node_dcid(node):
    if isinstance(node, dict):
        return node.get('dcid')
    return getattr(node, 'dcid', None)


def _extract_node_value(node):
    if isinstance(node, dict):
        return node.get('value')
    return getattr(node, 'value', None)


def _get_response_data(response):
    if isinstance(response, dict):
        return response
    response_data = getattr(response, 'data', None)
    if response_data:
        return response_data
    if hasattr(response, 'to_dict'):
        return response.to_dict().get('data', {})
    return {}


def _get_property_nodes(node_data, prop):
    if not node_data:
        return []
    if isinstance(node_data, dict):
        return node_data.get('arcs', {}).get(prop, {}).get('nodes', [])
    arcs = getattr(node_data, 'arcs', {})
    if not arcs:
        return []
    arc_data = arcs.get(prop, {})
    if isinstance(arc_data, dict):
        return arc_data.get('nodes', [])
    return getattr(arc_data, 'nodes', [])


def _load_geojsons():
    client = get_datacommons_client()
    countries_response = client.node.fetch_place_children(
        place_dcids=['Earth'],
        children_type='Country',
        as_dict=True,
    )
    countries = []
    for node in countries_response.get('Earth', []):
        dcid = _extract_node_dcid(node)
        if dcid:
            countries.append(dcid)

    geojson_response = _get_response_data(
        client.node.fetch_property_values(node_dcids=countries,
                                          properties='geoJsonCoordinatesDP2'))
    geojsons = {}
    for country in countries:
        nodes = _get_property_nodes(geojson_response.get(country),
                                    'geoJsonCoordinatesDP2')
        if not nodes:
            continue
        geojson = _extract_node_value(nodes[0])
        if not geojson:
            continue
        geojsons[country] = geometry.shape(json.loads(geojson))

    print('Got', len(geojsons), 'geojsons!')

    cip_response = _get_response_data(
        client.node.fetch_property_values(node_dcids=countries,
                                          properties='containedInPlace'))
    cip = {}
    for country in countries:
        nodes = _get_property_nodes(cip_response.get(country),
                                    'containedInPlace')
        cip[country] = [
            dcid for dcid in (_extract_node_dcid(node) for node in nodes)
            if dcid
        ]
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
