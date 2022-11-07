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
"""Script to download and preprocess USGS earthquake data."""

import csv
import glob
import os
import subprocess
import sys
from typing import Dict, List, Union

from absl import app
from absl import flags
from absl import logging

# for latlng_recon_service
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../..'))
from util import latlng_recon_service
from util import gcs

FLAGS = flags.FLAGS
flags.DEFINE_string('usgs_earthquake_input', '/tmp/usgs/*.csv',
                    'Glob pattern for a set of raw USGS earthquake CSV files.')

flags.DEFINE_string(
    'usgs_earthquake_output', 'earthquake.csv',
    'Path to the output preprocessed csv that this script will produce.')

# A place resolution cache file is a csv file where first two values
# are lat and lng respectively, the rest of the values in the
# same line are place ids that (lat, lng) resolves to.
# If the whole line consists of lat,lng then it means that the coordinate
# does not resolve to places known by Data Commons.
flags.DEFINE_string('usgs_earthquake_cache_path',
                    'gs://datcom-import-cache/earthquake/place_cache.txt',
                    'Path to place resolution cache file.')

REVIEW_MAP = {
    'reviewed': 'ReviewedEvent',
    'automatic': 'UnreviewedAutomatedEvent',
    'deleted': 'DeletedEvent',
}

MAGTYPE_REMAP = {
    'Fa': 'Mfa',
    'Lg': 'MLg',
    'Mlg': 'MLg',
    'Mb_lg': 'MLg',
    'Mblg': 'MLg',
    'Ms20': 'Ms',
    'Ms_20': 'Ms',
    'Uk': 'Unknown',
}

CSV_COL_HEADERS = [
    'name', 'occurrence_time', 'mag', 'mag_type', 'mag_err', 'location',
    'depth', 'depth_err', 'reviewed_status', 'affected_places'
]


def double_quote(s: str):
    """Wrap s in double quotes."""
    return f'"{s}"'


def square_bracket(s: str):
    """Wrap s with []."""
    return f'[{s}]'


def dcid(s: str):
    """Prefix s with 'dcid:'."""
    return f'dcid:{s}'


def dcs(s: str):
    """Prefix s with 'dcs:'."""
    return f'dcs:{s}'


class PlaceCache:
    """Cache of (lat,lng) -> DC places mapping."""

    def __init__(self, path: str):
        self._path = path
        self._read = False
        self._updated = False
        self.cache = {}

    def read(self) -> None:
        """Read cache. Can only be called once."""
        if self._read:
            return
        try:
            with gcs.File(self._path, 'r') as file:
                raw_cache = file.read().decode()
                for line in raw_cache.split('\n'):
                    latlng, places = self.parse(line)
                    self.cache[latlng] = places
                self._read = True
        except gcs.BlobNotFoundError:
            self._read = True

    def update(self, cache: Dict):
        for k, v in cache.items():
            self.cache[k] = v

    def write(self):
        """Append to the existing cache. Can only be called once."""
        if self._updated:
            return
        # Cache dict -> lines of text.
        lines = []
        for latlng, places in self.cache.items():
            line = ','.join([str(latlng[0]), str(latlng[1])] + places)
            lines.append(line)
        # Write to gcs.
        with gcs.File(self._path, 'w') as file:
            file.write('\n'.join(lines).encode())
            self._updated = True

    def parse(self, line: str):
        """lat,lng,place1,place2... -> (lat, lng), [place1, place2 ...]"""
        vals = line.rstrip().split(',')
        if len(vals) < 2:
            raise Exception('Bad cache line %s. Please delete it.' % line)
        latlng = (float(vals[0]), float(vals[1]))
        return latlng, vals[2:]


def preprocess_row(row: Dict, affected_places: List[str]) -> str:
    """Return preprocessed csv row string from a raw csv row dict."""
    if 'id' not in row:
        logging.info('skipping row, id not found in %s' % str(row))
    p = {}

    # TODO(alex): custom dcid: node = ['Node: dcid:earthquake/' + row['id']]

    if row.get('place'):
        p['name'] = double_quote(row['place'])

    if row.get('time'):
        p['occurrence_time'] = double_quote(row['time'].split('.', 1)[0])

    if row.get('mag'):
        p['mag'] = row['mag']

    if row.get('magType'):
        mt = row['magType'].capitalize()
        mt = MAGTYPE_REMAP.get(mt, mt)
        p['mag_type'] = dcs(f'Magnitude{mt}')

    if row.get('magError'):
        p['mag_err'] = row['magError']

    if row.get('depth'):
        p['depth'] = square_bracket(f'{row["depth"]} Kilometer')

    if row.get('depthError'):
        p['depth_err'] = square_bracket(f'{row["depthError"]} Kilometer')

    if row.get('status') and row['status'] in REVIEW_MAP:
        p['reviewed_status'] = dcs(REVIEW_MAP[row['status']])

    if row.get('latitude') and row.get('longitude'):
        latlng = f'LatLong {row["latitude"]} {row["longitude"]}'
        p['location'] = square_bracket(latlng)

        affected_places = [dcid(a) for a in affected_places]
        if affected_places:
            p['affected_places'] = double_quote(','.join(affected_places))

    return ','.join([p.get(h, '') for h in CSV_COL_HEADERS])


def iter_csv_row(glob_pattern: str) -> None:
    """Row iterator for csv files."""
    for file in glob.glob(glob_pattern):
        with open(file, 'r') as csvfile:
            for row in csv.DictReader(csvfile):
                yield row


def resolve_affected_places(
    input_path: str,
    cache_path: Union[str,
                      None] = None) -> Dict[str, latlng_recon_service.LatLng]:
    """Returns a mapping of dcid -> resolved places mapping."""
    latlng_to_places_cache = {}
    if cache_path:
        place_cache = PlaceCache(cache_path)
        place_cache.read()
        latlng_to_places_cache = place_cache.cache
        logging.info('Num entries in cache: %s' % len(latlng_to_places_cache))

    unresolved_id_to_latlng = dict()
    resolved_id_to_latlng = dict()
    for row in iter_csv_row(input_path):
        latlng: latlng_recon_service.LatLng = (float(row['latitude']),
                                               float(row['longitude']))
        if latlng in latlng_to_places_cache:
            resolved_id_to_latlng[row['id']] = latlng_to_places_cache[latlng]
        else:
            unresolved_id_to_latlng[row['id']] = latlng

    logging.info('Num coords to be resolved %s' % len(unresolved_id_to_latlng))
    newly_resolved = latlng_recon_service.latlng2places(unresolved_id_to_latlng)
    resolved_id_to_latlng.update(newly_resolved)

    # Ignore cache update if cache path is not specified.
    if not cache_path:
        return resolved_id_to_latlng

    # Update the place cache for future runs.
    cache_updates = dict()
    for id, places in newly_resolved.items():
        latlng = unresolved_id_to_latlng[id]
        cache_updates[latlng] = places
    place_cache.update(cache_updates)
    place_cache.write()

    return resolved_id_to_latlng


def preprocess(input_path,
               output_path: str,
               cache_path: Union[str, None] = None):
    """"""
    # Resolve a list of affected places for each earthquake.
    # Not all coordinates will resolve (ex: in the middle of ocean).
    ids_to_resolved_places = resolve_affected_places(input_path, cache_path)
    logging.info("Finished resolving affected places.")

    if os.path.dirname(output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(','.join(CSV_COL_HEADERS) + '\n')
        for row in iter_csv_row(input_path):
            affected_places = ids_to_resolved_places.get(row['id'], [])
            f.write(preprocess_row(row, affected_places) + '\n')


def main(_) -> None:
    download_sh_path = os.path.join(_SCRIPT_PATH, 'download.sh')
    subprocess.call(f'chmod +x {download_sh_path} && sh {download_sh_path}',
                    shell=True)

    gcs.init()  # for writing to place cache.
    preprocess(FLAGS.usgs_earthquake_input, FLAGS.usgs_earthquake_output,
               FLAGS.usgs_earthquake_cache_path)


if __name__ == '__main__':
    app.run(main)
