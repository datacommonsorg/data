# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import csv
import os
import sys
import threading

import s2sphere
import time
from absl import app
from absl import flags

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../util/'))  # for recon util

import latlng_recon_geojson
import latlng2place_mapsapi

FLAGS = flags.FLAGS

flags.DEFINE_boolean('no_resolution', False, 'If true, no resolution is done.')
flags.DEFINE_string('s2_out_dir', 'scratch', 'Output directory path.')
flags.DEFINE_string('maps_api_key', '', 'Maps API Key.')
flags.DEFINE_string(
    'placeid2dcid_csv', '', 'CSV of placeid,dcid for efficient '
    'resolution with talking to recon API')

_NTHREADS = 10


def _llformat(ll):
    # 4 decimal degree is 11.1m
    # (http://wiki.gis.com/wiki/index.php/Decimal_degrees)
    return str('%.4f' % ll)


def _cid(cell):
    return '{0:#0{1}x}'.format(cell.id(), 18)


def _cip(parents):
    return ','.join(['dcid:' + p for p in parents])


def _str(s):
    return '"' + s + '"'


def _compute_cells(level):
    country_resolver = latlng_recon_geojson.LatLng2Places(['Country'])

    cells = {}
    nproc = 0
    start = time.time()
    for cell in s2sphere.CellId.walk_fast(level):
        cid = _cid(cell)
        latlng = cell.to_lat_lng()
        lat = latlng.lat().degrees
        lng = latlng.lng().degrees
        if country_resolver.resolve(lat, lng):
            cells[cid] = (lat, lng, True)
        else:
            cells[cid] = (lat, lng, False)

        if nproc % 100000 == 1:
            end = time.time()
            print(end - start, nproc)
            start = end
        nproc += 1

    print('Computed cells:', len(cells))
    return cells


def _generate_thread(idx, level, cells, filepath, mapsapi_resolver):
    with open(filepath, 'w') as fp:
        csvw = csv.writer(fp, doublequote=False, escapechar='\\')
        csvw.writerow(
            ['dcid', 'name', 'latitude', 'longitude', 'containedInPlace'])
        start = time.time()
        i = -1
        nproc = 0
        for (cid, (lat, lng, call_maps)) in cells.items():
            i += 1
            if i % _NTHREADS != idx:
                continue

            parents = []
            if call_maps:
                try:
                    parents = mapsapi_resolver.resolve(lat, lng)
                except Exception as e:
                    print('ERROR: Unable to resolve (', lat, ',', lng, ')')
                if nproc % 100 == 1:
                    end = time.time()
                    print(end - start, ':', lat, ',', lng, '->', parents)
                    start = end

            nproc += 1
            csvw.writerow([
                f's2CellId/{cid}',
                _str(f'L{level} S2 Cell {cid}'),
                _llformat(lat),
                _llformat(lng),
                _cip(parents)
            ])


def generate(level, out_dir, maps_api_key, placeid2dcid_csv):
    print('Creating S2 level ', level)
    cells = _compute_cells(level)
    mapsapi_resolver = latlng2place_mapsapi.Resolver(
        maps_api_key,
        cache_file=os.path.join(out_dir, 'cache.txt'),
        placeid2dcid_csv=placeid2dcid_csv)
    threads = []
    for i in range(_NTHREADS):
        fname = 's2_level' + str(level) + '_' + str(i) + '.csv'
        fpath = os.path.join(out_dir, fname)
        t = threading.Thread(target=_generate_thread,
                             args=(i, level, cells, fpath, mapsapi_resolver))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


def generate_noresolution(level, out_dir):
    print('Creating S2 level ', level)
    fpath = os.path.join(out_dir, 's2_level' + str(level) + '.csv')
    with open(fpath, 'w') as fp:
        csvw = csv.writer(fp, doublequote=False, escapechar='\\')
        csvw.writerow(
            ['dcid', 'name', 'latitude', 'longitude', 'containedInPlace'])
        for cell in s2sphere.CellId.walk_fast(level):
            cid = _cid(cell)
            latlng = cell.to_lat_lng()
            csvw.writerow([
                f's2CellId/{cid}',
                _str(f'L{level} S2 Cell {cid}'),
                _llformat(latlng.lat().degrees),
                _llformat(latlng.lng().degrees), ''
            ])


def main(_):
    if FLAGS.no_resolution:
        generate_noresolution(level=10, out_dir=FLAGS.s2_out_dir)
    else:
        generate(level=10,
                 no_resolution=FLAGS.no_resolution,
                 out_dir=FLAGS.s2_out_dir,
                 maps_api_key=FLAGS.maps_api_key,
                 placeid2dcid_csv=FLAGS.placeid2dcid_csv)


if __name__ == "__main__":
    app.run(main)
