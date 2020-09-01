# Copyright 2020 Google LLC
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
"""
Generates the file low_res_geojsons.mcf with the desired simplified geojsons
for US states.

    Typical usage:
    python3 generate_mcf.py
"""
import geopandas as gpd
import download
import simplify
import plotter
import geojson
import json
import tempfile
import re
import matplotlib.pyplot as plt
from absl import logging
from absl import app
from absl import flags


class McfGenerator:
    PLACE_TO_IMPORT = 'country/USA'

    EPS_LEVEL_MAP = {
        0.01: 1,
        0.03: 2,
        0.05: 3
    }

    def __init__(self):
        self.downloader = download.GeojsonDownloader()
        self.simplifier = simplify.GeojsonSimplifier()
        self.simple_geojsons = {}
        self.eps = 0.01

    def generate_simple_geojsons(self, show=False):
        self.downloader.download_data(place=self.PLACE_TO_IMPORT)
        for geoid, coords in self.downloader.iter_subareas():

            # This an admitedly hacky way of getting rid of bogus geographies
            # that are, for some mysterious reason, included as part of the US
            # states query (with geoIds like geoId/7000).
            # TODO(jeffreyoldham): (potentially) find a cleaner way to do this.
            if int(geoid.split('/')[1]) > 100:
                continue
            logging.info(f"Simplifying {geoid}...")
            try:
                with tempfile.TemporaryFile(mode='r+') as f1, \
                     tempfile.TemporaryFile(mode='r+') as f2:

                    geojson.dump(coords, f1)
                    simple = self.simplifier.simplify(coords, epsilon=self.eps)
                    geojson.dump(simple, f2)

                    # Rewind files to start for reading.
                    f1.seek(0)
                    f2.seek(0)

                    plotter.compare_plots(gpd.read_file(f1),
                                          gpd.read_file(f2),
                                          show=show)
                    self.simple_geojsons[geoid] = simple
            except AssertionError:
                logging.error("Simplifier failure on GeoJSON below:\n", coords)
        plt.show()

    def generate_mcf(self, path='low_res_geojsons.mcf', mode='w'):
        """Writes the simplified GeoJSONs to an MCF file.

        Args:
            path: Path to MCF file to write simplified GeoJSON to.
            mode: mode parameter to be passed to open() function when writing
                  to MCF.
        """
        temp = "\n".join([
            "Node: dcid:{geoid}",
            "typeOf: dcs:{type}",
            "geoJsonCoordinatesDP{level}: {coords_str}",
            "\n"
        ])
        with open(path, mode) as f:
            for geoid in self.simple_geojsons:
                # Note: the double use of json.dumps automatically escapes all
                # inner quotes, and encloses the entire string in quotes.
                geostr = json.dumps(json.dumps(self.simple_geojsons[geoid]))
                f.write(temp.format(geoid=geoid, type="State",
                                    level=self.EPS_LEVEL_MAP[self.eps],
                                    coords_str=geostr))


def main(_):
    gen = McfGenerator()
    gen.generate_simple_geojsons(show=False)
    gen.generate_mcf()


if __name__ == "__main__":
    FLAGS = flags.FLAGS
    flags.DEFINE_boolean('show',
                         default=False,
                         help='If True, plots comparison of original vs. '
                         'simplified for each geography.')
    app.run(main)
