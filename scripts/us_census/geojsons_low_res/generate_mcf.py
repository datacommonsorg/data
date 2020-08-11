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
import download
import simplify


class McfGenerator:
    PLACE_TO_IMPORT = 'country/USA'

    def __init__(self):
        self.downloader = download.GeojsonDownloader()
        self.simplifier = simplify.GeojsonSimplifier()
        self.simple_geojsons = {}

    def generate_simple_geojsons(self):
        self.downloader.download_data(place=self.PLACE_TO_IMPORT)
        for geoid, coords in self.downloader.iter_subareas():
            print(f"Simplifying geoid = {geoid}")
            self.simple_geojsons[geoid] = self.simplifier.simplify(coords)

    # def generate_mcf(self, path='low_res_geojsons.mcf'):
    #     with open(path, 'w') as f:


if __name__ == "__main__":
    gen = McfGenerator()
    gen.generate_simple_geojsons()
