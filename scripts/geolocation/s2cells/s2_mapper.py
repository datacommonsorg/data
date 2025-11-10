# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ast
import csv
import math
import os
import sys
import s2sphere
from absl import app
from absl import flags
from absl import logging  
from datetime import datetime
from dateutil import parser

logging.set_verbosity(logging.INFO)

FLAGS = flags.FLAGS

flags.DEFINE_string('in_params', '', 'Input param file path (e.g., params.txt)')
flags.DEFINE_string('in_csv', '', 'Input CSV file path')
flags.DEFINE_string('out_dir', 'output_folder', 'Output directory path for mapped_*.csv and s2cells_*.mcf')

_MCF_FORMAT = """
Node: dcid:s2CellId/{cid}
typeOf: dcs:{typeof}
name: "L{level} S2 Cell {cid}"
latitude: "{lat}"
longitude: "{lng}"
"""


def _llformat(ll):
    """Formats a latitude or longitude value to 4 decimal places."""
    return str('%.4f' % ll)


def _cellid(cell):
    """Returns the S2 Cell ID in hexadecimal format."""
    return '{0:#0{1}x}'.format(cell.id(), 18)


class Processor:

    def __init__(self, in_params_path, in_csv_path, out_dir):
        # Load parameters from the specified in_params file
        try:
            with open(in_params_path, 'r') as fp:
                self._params = ast.literal_eval(fp.read())
            logging.info(f"Loaded parameters: {self._params}")
        except FileNotFoundError:
            logging.error(f"Error: in_params file not found at '{in_params_path}'")
            sys.exit(1)
        except Exception as e:
            logging.error(f"Error reading or parsing in_params file '{in_params_path}': {e}")
            sys.exit(1)

        # Validate essential parameters
        required_params = ['s2lvls', 'aggrfunc', 'latcol', 'lngcol', 'datecol', 'valcol']
        for param in required_params:
            if param not in self._params:
                logging.error(f"Missing required parameter '{param}' in in_params file.")
                sys.exit(1)

        self._levels = self._params['s2lvls']
        self._aggr_func = self._params['aggrfunc']
        
        # Get base filename for output files
        fname = os.path.basename(in_csv_path).split('.')[0]
        
        # Open input and output files
        try:
            self._in_cfp = open(in_csv_path, 'r')
            os.makedirs(out_dir, exist_ok=True) # Ensure output directory exists
            self._out_cfp = open(os.path.join(out_dir, f"mapped_{fname}.csv"), 'w')
            self._out_mfp = open(os.path.join(out_dir, f"s2cells_{fname}.mcf"), 'w')
            logging.info(f"Opened input CSV: {in_csv_path}")
            logging.info(f"Opened output mapped CSV: {os.path.join(out_dir, f'mapped_{fname}.csv')}")
            logging.info(f"Opened output S2 MCF: {os.path.join(out_dir, f's2cells_{fname}.mcf')}")
        except FileNotFoundError:
            logging.error(f"Error: Input CSV file not found at '{in_csv_path}'")
            sys.exit(1)
        except Exception as e:
            logging.error(f"Error opening files: {e}")
            sys.exit(1)

        # Key: (cellid, formatted_date), Value: list of numeric values for aggregation
        self._aggr_map = {}

    def generate(self):
        emitted_cids = set()
        num_processed = 0
        num_bad_fmt = 0
        num_nans = 0

        reader = csv.DictReader(self._in_cfp)

        #Skip the second row (the units/description row) ---

        try:
            next(reader) 
            logging.info("Successfully skipped the units/description row (2nd line) in the CSV.")
        except StopIteration:
            logging.warning("CSV is empty or only contains a header. No data rows to process.")
            self._close()
            return

        # Iterate over each data row (starting from the 3rd line of the CSV file)
        for row in reader:
            # If you want to see the row being processed, uncomment this line:
            
            try:
                lat = float(row[self._params['latcol']])
                lng = float(row[self._params['lngcol']])
                # val = float(row[self._params['valcol']])
                val = row.get(self._params['valcol']) # Safely get the value
                if val is None or (isinstance(val, str) and val.strip() == ''):
                    # If it's None or an empty string, treat it as NaN
                    val = math.nan
                    logging.debug(f"Assigned NaN to val for row due to None/empty string. Row: {row}")
                else:
                    try:
                        val = float(val)
                    except ValueError:
                        # If conversion to float fails, also treat as NaN
                        val = math.nan
                        logging.warning(f"Could not convert '{val}' to float for '{self._params['valcol']}'. Assigning NaN. Row: {row}")
                date = parser.parse(row[self._params['datecol']])
            except ValueError:
                num_bad_fmt += 1
                continue

            if math.isnan(val):
                num_nans += 1
                continue

            for lvl in self._levels:
                # Compute S2Cell
                cell = self._latlng2cell(lat, lng, lvl)
                cid = _cellid(cell)

                # Maybe emit S2Cell entity
                if cid not in emitted_cids:
                    self._out_mfp.write(self._s2mcf(cid, cell, lvl))
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
                    logging.info('Rows processed so far:', num_processed,
                          ':: bad-fmt:', num_bad_fmt, ':: nans:', num_nans)

        logging.info('Rows processed so far:', num_processed, ':: bad-fmt:',
              num_bad_fmt, ':: nans:', num_nans)
        self._aggr_and_write()
        self._close()

    def _latlng2cell(self, lat, lng, lvl):
        """Converts lat/lng to an S2 Cell ID at a given level."""
        assert 0 <= lvl <= 30, "S2 level must be between 0 and 30."
        ll = s2sphere.LatLng.from_degrees(lat, lng)
        cell = s2sphere.CellId.from_lat_lng(ll)
        if lvl < 30:
            cell = cell.parent(lvl)
        return cell

    def _s2mcf(self, cid, cell, lvl):
        """Generates an MCF string for an S2 Cell."""
        latlng = cell.to_lat_lng()
        typeof = 'S2CellLevel' + str(lvl)
        mcf_str = _MCF_FORMAT.format(cid=cid,
                                     level=lvl,
                                     typeof=typeof,
                                     lat=_llformat(latlng.lat().degrees),
                                     lng=_llformat(latlng.lng().degrees))
        if 'containedIn' in self._params:
            cip = 'containedInPlace: dcid:' + self._params['containedIn']
            mcf_str += cip + '\n'
        return mcf_str

    def _aggr(self, vals, cid, date):
        """Applies the configured aggregation function to a list of values."""
        if not vals: 
            logging.warning(f"Attempted to aggregate empty list for Cell {cid} on {date}. Returning 0.")
            return 0

        if self._aggr_func == 'sum':
            return sum(vals)
        elif self._aggr_func == 'max':
            return max(vals)
        elif self._aggr_func == 'min':
            return min(vals)
        elif self._aggr_func == 'mean':
            return sum(vals) / len(vals)
        else:
            raise ValueError(f"Unexpected aggregation function: '{self._aggr_func}'. "
                             "Supported: 'sum', 'mean', 'max', 'min'.")

    def _aggr_and_write(self):
        """Performs aggregation and writes results to the output CSV."""
        self._out_cfp.write("observationAbout,observationDate,value\n") # Write header for output CSV
        for (cid, date), vals in self._aggr_map.items():
            sval = str(self._aggr(vals, cid, date))
            self._out_cfp.write(f"dcid:s2CellId/{cid},{date},{sval}" + "\n")
        logging.info(f"Aggregation complete and data written to output CSV.")

    def _close(self):
        """Closes all open file pointers."""
        self._in_cfp.close()
        self._out_cfp.close()
        self._out_mfp.close()
        logging.info("All files closed.")


def main(_):
    # Create an instance of the Processor and run the generation
    processor = Processor(FLAGS.in_params, FLAGS.in_csv, FLAGS.out_dir)
    processor.generate()


if __name__ == "__main__":
    app.run(main)