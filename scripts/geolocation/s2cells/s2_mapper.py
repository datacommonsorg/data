import ast
import csv
import math
import os
import sys

import s2sphere
from absl import app
from absl import flags
from datetime import datetime
from dateutil import parser


FLAGS = flags.FLAGS

# Params:
# -------
# {
#   "s2lvl": 10,
#   "aggrfunc": "sum" | "mean" | "max" | "min",
#   "latcol": <col-name>,
#   "lngcol": <col-name>,
#   "datecol": <col-name>,
#   "valcol": <col-name>,
#   "datefmt": "YYYY-mm-dd" | "YYYY-mm" | "YYYY"  #  Optional
# }
flags.DEFINE_string('in_params', '', 'Input param file')
flags.DEFINE_string('in_csv', '', 'Input CSV file')
flags.DEFINE_string('out_dir', '/tmp', 'Output directory path.')


_MCF_FORMAT = """
Node: dcid:s2CellId/{cid}
typeOf: dcs:{typeof}
name: "L{level} S2 Cell {cid}"
latitude: "{lat}"
longitude: "{lng}"
"""


def _llformat(ll):
    # 4 decimal degree is 11.1m
    # (http://wiki.gis.com/wiki/index.php/Decimal_degrees)
    return str('%.4f' % ll)


def _cellid(cell):
    return '{0:#0{1}x}'.format(cell.id(), 18)


class Processor:
    def __init__(self, in_params, in_csv, out_dir):
        with open(in_params, 'r') as fp:
            self._params = ast.literal_eval(fp.read())
        self._level = self._params['s2lvl']
        self._aggr_func = self._params['aggrfunc']
        fname = os.path.basename(in_csv).split('.')[0]
        self._in_cfp = open(in_csv, 'r')
        self._out_cfp = open(os.path.join(out_dir, f"mapped_{fname}.csv"), 'w')
        self._out_mfp = open(os.path.join(out_dir, f"s2cells_{fname}.mcf"), 'w')
        # Key: {cellid, date}, Value: numeric
        self._aggr_map = {}

    def generate(self):
        emitted_cids = set()
        num_processed = 0
        num_bad_fmt = 0
        num_nans = 0
        for row in csv.DictReader(self._in_cfp):
            # Load row values
            try:
                lat = float(row[self._params['latcol']])
                lng = float(row[self._params['lngcol']])
                val = float(row[self._params['valcol']])
                date = parser.parse(row[self._params['datecol']])
            except ValueError:
                num_bad_fmt += 1
                continue

            if math.isnan(val):
                num_nans += 1
                continue

            # Compute S2Cell
            cell = self._latlng2cell(lat, lng)
            cid = _cellid(cell)

            # Maybe emit S2Cell entity
            if cid not in emitted_cids:
                self._out_mfp.write(self._s2mcf(cid, cell))
                emitted_cids.add(cid)

            # Update date
            if 'datefmt' in self._params:
                fmt = self._params['datefmt']
            else:
                fmt = '%Y'
            # Append values for aggregation
            akey = (cid, date.strftime(fmt))
            if akey not in self._aggr_map:
                self._aggr_map[akey] = []
            self._aggr_map[akey].append(val)

            num_processed += 1
            if num_processed % 100000 == 0:
                print('Rows processed so far:', num_processed,
                      ':: bad-fmt:', num_bad_fmt, ':: nans:', num_nans)

        print('Rows processed so far:', num_processed,
              ':: bad-fmt:', num_bad_fmt, ':: nans:', num_nans)
        self._aggr_and_write()
        self._close()

    def _latlng2cell(self, lat, lng):
        assert self._level >= 0 and self._level <= 30
        ll = s2sphere.LatLng.from_degrees(lat, lng)
        cell = s2sphere.CellId.from_lat_lng(ll)
        if self._level < 30:
            cell = cell.parent(self._level)
        return cell

    def _s2mcf(self, cid, cell):
        latlng = cell.to_lat_lng()
        typeof = 'S2CellIdLevel' + str(self._level)
        return _MCF_FORMAT.format(cid=cid,
                                  level=self._level,
                                  typeof=typeof,
                                  lat=_llformat(latlng.lat().degrees),
                                  lng=_llformat(latlng.lng().degrees))

    def _aggr(self, vals, cid, date):
        assert len(vals) > 0, cid + date
        if self._aggr_func == 'sum':
            return sum(vals)
        elif self._aggr_func == 'max':
            return max(vals)
        elif self._aggr_func == 'min':
            return min(vals)
        elif self._aggr_func == 'mean':
            return sum(vals) / len(vals)
        else:
            raise ValueError(f"Unexpected aggr_func {self._aggr_func}")

    def _aggr_and_write(self):
        self._out_cfp.write("observationAbout,observationDate,value\n")
        for (cid, date), vals in self._aggr_map.items():
            sval = str(self._aggr(vals, cid, date))
            self._out_cfp.write(f"dcid:s2CellId/{cid},{date},{sval}" + "\n")

    def _close(self):
        self._in_cfp.close()
        self._out_cfp.close()
        self._out_mfp.close()


def main(_):
    p = Processor(FLAGS.in_params, FLAGS.in_csv, FLAGS.out_dir)
    p.generate()


if __name__ == "__main__":
    app.run(main)
