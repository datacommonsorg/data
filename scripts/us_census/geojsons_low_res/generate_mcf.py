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
import matplotlib.pyplot as plt
from absl import logging
from absl import app
from absl import flags


class McfGenerator:
    PLACE_TO_IMPORT = 'country/USA'

    # Mapping from the epsilon parameter (abbreviated eps) in the
    # Ramer–Douglas–Peucker algorithm to the "degree" of precision, as defined
    # by DataCommons.
    EPS_LEVEL_MAP = {0.01: 1, 0.03: 2, 0.05: 3}
    LEVEL_MAP = {1: 'State', 2: 'County'}

    def __init__(self):
        self.downloader = download.GeojsonDownloader()
        self.simplifier = simplify.GeojsonSimplifier()
        self.simple_geojsons = {}
        self.eps = 0.01

    def download_data(self, levels_down=1):
        self.levels_down = levels_down
        self.downloader.download_data(place=self.PLACE_TO_IMPORT,
                                      level=self.levels_down)

    def generate_simple_geojsons(self, show=False, eps=None):
        original_pts = 0
        compressed_pts = 0
        for geoid, coords in self.downloader.iter_subareas():
            # This an admitedly hacky way of getting rid of bogus geographies
            # that are, for some mysterious reason, included as part of the US
            # states query (with geoIds like geoId/7000).
            # TODO(jeffreyoldham): (potentially) find a cleaner way to do this.
            if self.levels_down == 1 and int(geoid.split('/')[1]) > 100:
                continue
            logging.info(f"Simplifying {geoid}...")
            if eps is not None:
                self.eps = eps
            try:
                with tempfile.TemporaryFile(mode='r+') as f1, \
                     tempfile.TemporaryFile(mode='r+') as f2:

                    geojson.dump(coords, f1)
                    s, o_sz, c_sz = self.simplifier.simplify(coords,
                                                             epsilon=self.eps)
                    original_pts += o_sz
                    compressed_pts += c_sz
                    geojson.dump(s, f2)  # Save simple geojson in tempfile.

                    # Rewind files to start for reading.
                    f1.seek(0)
                    f2.seek(0)

                    plotter.compare_plots(gpd.read_file(f1),
                                          gpd.read_file(f2),
                                          show=show)
                    self.simple_geojsons[geoid] = s
            except AssertionError:
                logging.error("Simplifier failure on GeoJSON below:\n", coords)
        logging.info(f"Total original points = {original_pts}\n"
                     f"Compressed points = {compressed_pts}\n")
        plt.show()
        plt.clf()

    def generate_mcf(self, path='low_res_geojsons.mcf', mode='w'):
        """Writes the simplified GeoJSONs to an MCF file.

        Args:
            path: Path to MCF file to write simplified GeoJSON to.
            mode: mode parameter to be passed to open() function when writing
                  to MCF.
        """
        temp = "\n".join([
            "Node: dcid:{geoid}", "typeOf: dcs:{type}",
            "geoJsonCoordinatesDP{level}: {coords_str}", "\n"
        ])
        with open(path, mode) as f:
            for geoid in self.simple_geojsons:
                # Note: the double use of json.dumps automatically escapes all
                # inner quotes, and encloses the entire string in quotes.
                geostr = json.dumps(json.dumps(self.simple_geojsons[geoid]))
                f.write(
                    temp.format(geoid=geoid,
                                type=self.LEVEL_MAP[self.levels_down],
                                level=self.EPS_LEVEL_MAP[self.eps],
                                coords_str=geostr))


def main(_):
    gen = McfGenerator()
    gen.download_data(FLAGS.level)
    for eps in McfGenerator.EPS_LEVEL_MAP:
        gen.generate_simple_geojsons(show=FLAGS.show, eps=eps)
        filename = (f"low_res_geojsons_level_{FLAGS.level}_DP"
                    f"{McfGenerator.EPS_LEVEL_MAP[eps]}.mcf")
        gen.generate_mcf(path=filename)


if __name__ == "__main__":
    FLAGS = flags.FLAGS
    flags.DEFINE_boolean('show',
                         default=False,
                         help=('If True, plots comparison of original vs. '
                               'simplified for each geography.'))
    flags.DEFINE_integer('level',
                         default=1,
                         help=("Number of administrative levels down from "
                               "'country/USA'. For example, level=1 "
                               "corresponds to US states and level=2 to US "
                               "counties"))
    app.run(main)
