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
import copy
import tempfile
import matplotlib.pyplot as plt


class McfGenerator:
    PLACE_TO_IMPORT = 'country/USA'

    def __init__(self):
        self.downloader = download.GeojsonDownloader()
        self.simplifier = simplify.GeojsonSimplifier()
        self.simple_geojsons = {}

    def generate_simple_geojsons(self, verbose=True):
        self.downloader.download_data(place=self.PLACE_TO_IMPORT)
        for geoid, coords in self.downloader.iter_subareas():
            if int(geoid.split('/')[1]) > 100:
                continue
            if verbose:
                print(f"Simplifying {geoid}...")
            try:
                f1 = tempfile.TemporaryFile(mode='r+')
                f2 = tempfile.TemporaryFile(mode='r+')

                original = copy.deepcopy(coords)
                simple = self.simplifier.simplify(coords, verbose=verbose,
                                                  epsilon=0.05)
                print()

                f1.write(geojson.dumps(original))
                f2.write(geojson.dumps(simple))

                f1.seek(0)
                f2.seek(0)

                plotter.compare_plots(gpd.read_file(f1),
                                      gpd.read_file(f2), show=False)
                f1.close()
                f2.close()
            except AssertionError:
                print("Simplifier failure on GeoJSON below:")
                print(coords)
        plt.show()


    # def generate_mcf(self, path='low_res_geojsons.mcf'):
    #     with open(path, 'w') as f:


if __name__ == "__main__":
    gen = McfGenerator()
    gen.generate_simple_geojsons()
