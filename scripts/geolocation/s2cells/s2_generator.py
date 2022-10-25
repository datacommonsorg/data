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

import s2sphere
from absl import app
from absl import flags
from datetime import datetime
from dateutil import parser

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../util/'))  # for recon util

import latlng_recon_geojson

FLAGS = flags.FLAGS

flags.DEFINE_string('s2_out_dir', 'scratch', 'Output directory path.')


def _llformat(ll):
    # 4 decimal degree is 11.1m
    # (http://wiki.gis.com/wiki/index.php/Decimal_degrees)
    return str('%.4f' % ll)


def _cid(cell):
    return '{0:#0{1}x}'.format(cell.id(), 18)


def _str(s):
    return '"' + s + '"'


def generate(level, parent_level, out_dir):
  with open(os.path.join(out_dir, 's2_level' + str(level) + '.csv'), 'w') as fp:
      csvw = csv.writer(fp, doublequote=False, escapechar='\\')
      csvw.writerow(['dcid', 'name', 'latitude',
                     'longitude', 'containedInPlace'])
      print('Creating S2 level ', level)
      for cell in s2sphere.CellId.walk_fast(level):
          cid = _cid(cell)
          latlng = cell.to_lat_lng()

          if parent_level >= 2:
            pcid = _cid(cell.parent(level - 2))
            parent_dcid = f'dcid:s2CellId/{pcid}'
          else:
            # TODO(shanth): Compute country overlap.
            parent_dcid = ''

          csvw.writerow([f's2CellId/{cid}',
                         _str(f'L{level} S2 Cell {cid}'),
                         _llformat(latlng.lat().degrees),
                         _llformat(latlng.lng().degrees),
                         parent_dcid])


def main(_):
    generate(level=10, parent_level=9, out_dir=FLAGS.s2_out_dir)
    generate(level=9, parent_level=7, out_dir=FLAGS.s2_out_dir)
    generate(level=7, parent_level=-1, out_dir=FLAGS.s2_out_dir)


if __name__ == "__main__":
    app.run(main)
