# Copyright 2021 Google LLC
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
Generates mcf files for country / AdministrativeArea0 boundaries from World Bank data.

MCF files are generated for both high res data from the source, and simplified boundaries for
interactive applications. Geojsons are simplified using
https://geopandas.readthedocs.io/en/latest/docs/reference/api/geopandas.GeoSeries.simplify.html

    Typical usage:
    python3 country_boundaries_mcf_generator.py

NOTE: this file generates temporary folders that are not deleted.
"""
import datacommons as dc
import geopandas as gpd
import glob
import io
import json
import numpy as np
import os
import pandas as pd
import requests
import tempfile
import zipfile

from absl import app
from absl import flags

FLAGS = flags.FLAGS
flags.DEFINE_string(
    'download_dir', '',
    'Dir to use source data from. Leave blank to download from source.')
flags.DEFINE_string(
    'export_dir', '',
    'Dir to output geojson coordinate files too. If blank, a temp folder will be used.'
)
flags.DEFINE_string(
    'mcf_dir', '',
    'Dir to output generated MCF files too. If blank, a temp folder will be used.'
)

DOWNLOAD_URI = 'https://development-data-hub-s3-public.s3.amazonaws.com/ddhfiles/779551/wb_boundaries_geojson_highres.zip'
TMP_PATH = '/tmp/wb_boundaries_geojson_highres'
GEO_JSON_PATH = 'WB_Boundaries_GeoJSON_highres/WB_countries_Admin0.geojson'

# Additional country codes to import from the ISO_A3 column in the dataset,
# applied after importing countries from the preferred WB_A3 column.
ISO_A3_CODES_TO_IMPORT = ['COD', 'ROU', 'TLS', 'AND', 'IMN', 'UMI', 'USA']

# Threshold to DP level map, from scripts/us_census/geojsons_low_res/generate_mcf.py
EPS_LEVEL_MAP = {0: 0, 0.01: 1, 0.03: 2, 0.05: 3}

MCF_PATH = '/{MCF_OUT_FOLDER}/countries.dp{dp_level}.mcfgeojson.mcf'
MCF_FORMAT_STR = "\n".join([
    "Node: dcid:country/{country_code}", "typeOf: dcs:Country",
    "{prop}: {coords_str}", "\n"
])


class CountryBoundariesMcfGenerator:
    """Generates MCF files with simplified json for the WB boundaries dataset."""

    def __init__(self, download_dir, export_dir, mcf_dir):
        self.download_dir = download_dir
        self.should_download = False
        if not self.download_dir:
            self.download_dir = tempfile.mkdtemp(prefix="wb_download_")
            self.should_download = True
        self.export_dir = export_dir
        if not export_dir:
            self.export_dir = tempfile.mkdtemp(prefix="wb_export_")
        self.mcf_dir = mcf_dir
        if not mcf_dir:
            self.mcf_dir = tempfile.mkdtemp(prefix="wb_mcf_")

    def load_data(self):
        """Download data from source, or use specified data from previous download.

        Returns:
          Geopandas dataframe with all source data loaded.
        """
        if self.should_download:
            print(f'Downloading source data to {self.download_dir}')
            r = requests.get(DOWNLOAD_URI, stream=True)
            z = zipfile.ZipFile(io.BytesIO(r.content))
            z.extractall(self.download_dir)
        else:
            print(f'Skipping download, reusing {self.download_dir}')
        return gpd.read_file(os.path.join(self.download_dir, GEO_JSON_PATH))

    def build_import_codes(self, all_countries):
        """Builds mapping of column code to country codes to import.

        Only countries with DCID of the form county/{code} are included.

        Returns:
          A dict mapping dataframe column names to iterable of values in that column to include in the import. e.g.:
          {'WB_A3': ['FRA', 'NDL',...],
          'ISO_A3': ['UMI', 'COD', ...]}
        """
        # Call DC API to get list of countries
        dc_all_countries = dc.query('''
        SELECT ?place ?name WHERE {
          ?place typeOf Country .
          ?place name ?name
        }
        ''',
                                    select=None)

        def is_dc_country(iso):
            dcid = f'country/{iso}'
            matches = filter(lambda x: x['?place'] == dcid, dc_all_countries)
            return len(list(matches)) > 0

        # Compare dataset countries with results from DC
        wb_idx = all_countries['WB_A3'].apply(is_dc_country)

        col_to_code = {}
        col_to_code['WB_A3'] = set(all_countries.loc[wb_idx]['WB_A3'])
        col_to_code['ISO_A3'] = ISO_A3_CODES_TO_IMPORT

        return col_to_code

    def _geojson_filename(self, country_code, dp_level):
        """Returns filename of the geojson output file."""
        return os.path.join(self.export_dir,
                            f'{country_code}_{dp_level}.geojson')

    def _export_country_feature(self, country_code, country_data, dp_level):
        geojson = json.loads(country_data.to_json())
        features = geojson.get('features', [])
        assert (len(features) == 1)
        geometry = features[0].get('geometry')
        fname = self._geojson_filename(country_code, dp_level)
        with open(fname, 'w') as f:
            json.dump(geometry, f)

    def _simplify_json(self, country_code, country_data):
        """Simplifies (and exports) a geojson."""
        for tolerance, dp_level in EPS_LEVEL_MAP.items():
            if dp_level == 0:
                export_data = country_data
            else:
                export_data = country_data.simplify(tolerance)
            self._export_country_feature(country_code, export_data, dp_level)

    def extract_country_geojson(self, all_countries_df, col_to_code):
        """Extract and export all geojson to tempfiles."""
        print(f'Exporting geojson to {self.export_dir}')
        for col, country_codes in col_to_code.items():
            for country_code in country_codes:
                country_data = all_countries_df[all_countries_df[col] ==
                                                country_code]
                country_data = country_data.dissolve(
                    by=col)  # Join multiple rows into a single shape
                self._simplify_json(country_code, country_data)

    def output_mcf(self, col_to_code):
        """Generates the output MCF files for all dp levels."""
        print(f'Generating MCF to {self.mcf_dir}')

        def prop_for_dp_level(dp_level):
            if dp_level == 0:
                return "geoJsonCoordinates"
            return f"geoJsonCoordinatesDP{dp_level}"

        for _, dp_level in EPS_LEVEL_MAP.items():
            mcf_path = MCF_PATH.format(MCF_OUT_FOLDER=self.mcf_dir,
                                       dp_level=dp_level)
            with open(mcf_path, 'w') as mcf_fp:
                for col, country_codes in col_to_code.items():
                    for country_code in country_codes:
                        fname = self._geojson_filename(country_code, dp_level)
                        with open(fname) as geo_fp:
                            geostr = json.load(geo_fp)
                            mcf_fp.write(
                                MCF_FORMAT_STR.format(
                                    country_code=country_code,
                                    prop=prop_for_dp_level(dp_level),
                                    coords_str=json.dumps(json.dumps(geostr))))


def main(_):
    gen = CountryBoundariesMcfGenerator(FLAGS.download_dir, FLAGS.export_dir,
                                        FLAGS.mcf_dir)
    all_countries = gen.load_data()
    col_to_code = gen.build_import_codes(all_countries)
    gen.extract_country_geojson(all_countries, col_to_code)
    gen.output_mcf(col_to_code)


if __name__ == '__main__':
    app.run(main)
