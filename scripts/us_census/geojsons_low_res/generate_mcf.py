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
import tempfile
import matplotlib.pyplot as plt
from absl import logging


class McfGenerator:
    PLACE_TO_IMPORT = 'country/USA'

    def __init__(self):
        self.downloader = download.GeojsonDownloader()
        self.simplifier = simplify.GeojsonSimplifier()
        self.simple_geojsons = {}

    def generate_simple_geojsons(self, verbose=True):
        self.downloader.download_data(place=self.PLACE_TO_IMPORT)
        for geoid, coords in self.downloader.iter_subareas():

            # This an admitedly hacky way of getting rid of bogus geographies
            # that are, for some mysterious reason, included as part of the US
            # states query (with geoIds like geoId/7000).
            # TODO(jeffreyoldham): (potentially) find a cleaner way to do this.
            if int(geoid.split('/')[1]) > 100:
                continue
            if verbose:
                logging.info(f"Simplifying {geoid}...")
            try:
                with tempfile.TemporaryFile(mode='r+') as f1, \
                     tempfile.TemporaryFile(mode='r+') as f2:

                    geojson.dump(coords, f1)
                    geojson.dump(self.simplifier.simplify(coords,
                                                          verbose=verbose,
                                                          epsilon=0.05), f2)

                    # Rewind files to start for reading.
                    f1.seek(0)
                    f2.seek(0)

                    plotter.compare_plots(gpd.read_file(f1),
                                          gpd.read_file(f2), show=False)
            except AssertionError:
                logging.error("Simplifier failure on GeoJSON below:\n", coords)
        plt.show()


    # def generate_mcf(self, path='low_res_geojsons.mcf'):
    #     with open(path, 'w') as f:


if __name__ == "__main__":
    gen = McfGenerator()
    gen.generate_simple_geojsons()
