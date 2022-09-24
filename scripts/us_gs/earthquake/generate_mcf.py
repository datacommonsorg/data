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
"""Script to process USGS earthquake data.

Note: Please call download.sh first.
"""

from bdb import set_trace
import csv
import datetime
import glob
import os
import sys
from typing import Dict, List, NewType

from absl import app
from absl import flags
from absl import logging

# for latlng_recon_service
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../..'))
from util import latlng_recon_service

FLAGS = flags.FLAGS
flags.DEFINE_string('input', '/tmp/usgs/*.csv',
                    'Glob pattern for a set of raw USGS earthquake CSV files.')

_TODAY = datetime.date.today().strftime('%Y_%m_%d')
flags.DEFINE_string('output', f'/tmp/usgs/usgs_comcat_1900_01_01_{_TODAY}.mcf',
                    'Path to the output MCF that this script will produce.')

# A place resolution cache file is a csv file where first two values
# are lat and lng respectively, the rest of the values in the
# same line are place ids that (lat, lng) resolves to.
# If the whole line consists of lat,lng then it means that the coordinate
# does not resolve to places known by Data Commons.
flags.DEFINE_string('cache_path',
                    os.path.join(_SCRIPT_PATH, 'usgs_comcat_places.cache'),
                    'Path to place resolution cache file.')

# Place cache is a mapping of (lat,lng) -> list of places in Data Commons.
PlaceCache = NewType('PlaceCache', Dict[latlng_recon_service.LatLng, List[str]])

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


def process_row(row: Dict, affected_places: List[str]) -> str:
    """Process a row and returns the string representation of a node."""
    assert row['id'], row
    node = ['Node: dcid:earthquake/' + row['id']]
    node.append('typeOf: dcs:EarthquakeEvent')
    if row['place']:
        node.append('name: "' + row['place'] + '"')
    if row['time']:
        # Keep until seconds only.
        node.append('occurrenceTime: "' + row['time'].split('.', 1)[0] + '"')
    if row['mag']:
        node.append('magnitude: ' + row['mag'])
    if row['magType']:
        mt = row['magType'].capitalize()
        if mt in MAGTYPE_REMAP:
            mt = MAGTYPE_REMAP[mt]
        node.append('magnitudeType: dcs:Magnitude' + mt)
    if row['magError']:
        node.append('magnitudeError: ' + row['magError'])
    if row['depth']:
        node.append('depth: [' + row['depth'] + ' Kilometer]')
    if row['depthError']:
        node.append('depthError: [' + row['depthError'] + ' Kilometer]')
    if row['latitude'] and row['longitude']:
        node.append('location: [LatLong ' + row['latitude'] + ' ' +
                    row['longitude'] + ']')
        for affected_place in affected_places:
            node.append('affectedPlace: dcid:' + affected_place)
    if row['status'] and row['status'] in REVIEW_MAP:
        node.append('reviewStatus: dcs:' + REVIEW_MAP[row['status']])
    node.append('\n')
    return '\n'.join(node)


def iter_csv_row(glob_pattern: str) -> None:
    """Row iterator for csv files."""
    for file in glob.glob(glob_pattern):
        with open(file, 'r') as csvfile:
            for row in csv.DictReader(csvfile):
                yield row


def read_cache(cache_path: str) -> PlaceCache:
    """Reads cache and returns a latlng -> places mapping."""
    if not os.path.isfile(cache_path):
        return dict()

    def parse_cache(line: str):
        vals = line.rstrip().split(',')
        if len(vals) < 2:
            raise Exception('Bad cache line %s. Please delete it.' % line)
        latlng = (float(vals[0]), float(vals[1]))
        return latlng, vals[2:]

    cache = dict()
    with open(cache_path, 'r') as file:
        for line in file:
            latlng, places = parse_cache(line)
            cache[latlng] = places
    return cache


def update_cache(cache_path: str, cache: PlaceCache) -> None:
    """Writes newly resolved coordinates to the cache file."""
    with open(cache_path, 'a+') as file:
        for latlng, places in cache.items():
            line = ','.join([str(latlng[0]), str(latlng[1])] + places) + '\n'
            file.write(line)
    logging.info('Wrote %s new entries in cache.' % len(cache))


def resolve_affected_places(
        input, cache_path: str) -> Dict[str, latlng_recon_service.LatLng]:
    """Returns a mapping of dcid -> resolve places mapping."""
    latlng_to_places_cache = read_cache(cache_path)
    logging.info('Num entries in cache: %s' % len(latlng_to_places_cache))

    unresolved_id_to_latlng = dict()
    resolved_id_to_latlng = dict()
    for row in iter_csv_row(input):
        latlng: latlng_recon_service.LatLng = (float(row['latitude']),
                                               float(row['longitude']))
        if latlng in latlng_to_places_cache:
            resolved_id_to_latlng[row['id']] = latlng_to_places_cache[latlng]
        else:
            unresolved_id_to_latlng[row['id']] = latlng

    logging.info('Num coords to be resolved %s' % len(unresolved_id_to_latlng))
    newly_resolved = latlng_recon_service.latlng2places(unresolved_id_to_latlng)
    resolved_id_to_latlng.update(newly_resolved)

    # Transform new id->places to (lat,lng)->places.
    cache_updates = dict()
    for id, places in newly_resolved.items():
        latlng = unresolved_id_to_latlng[id]
        cache_updates[latlng] = places
    update_cache(cache_path, cache_updates)

    return resolved_id_to_latlng


def generate_mcf(input, output, cache_path: str) -> None:
    """Generates MCF for earthquake events."""
    # Resolve a list of affected places for each earthquake.
    # Not all coordinates will resolve (ex: in the middle of ocean).
    ids_to_resolved_places = resolve_affected_places(input, cache_path)
    logging.info("Finished resolving affected places.")

    with open(output, 'w') as f:
        for row in iter_csv_row(input):
            affected_places = ids_to_resolved_places.get(row['id'], [])
            f.write(process_row(row, affected_places))


def main(_) -> None:
    generate_mcf(FLAGS.input, FLAGS.output, FLAGS.cache_path)


if __name__ == '__main__':
    app.run(main)
