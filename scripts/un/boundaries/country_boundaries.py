# Copyright 2023 Google LLC
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
Generates mcf files for country / AdministrativeArea0 boundaries from UN data.

MCF files are generated for both high res data from the source, and simplified boundaries for
interactive applications. Geojsons are simplified using
https://geopandas.readthedocs.io/en/latest/docs/reference/api/geopandas.GeoSeries.simplify.html

NOTE: this file generates temporary folders that are not deleted.
"""

from typing import Dict

import datacommons as dc
import geopandas as gpd
from geojson_rewind import rewind
import json
import os
import requests

from absl import app
from absl import flags

FLAGS = flags.FLAGS
flags.DEFINE_string('input_file', 'data/UNGIS_BNDA.geojson',
                    'Input geojson file')
flags.DEFINE_string(
    'output_dir', 'output',
    'Dir to output generated MCF files too. If blank, a temp folder will be used.'
)

# Threshold to DP level map, from scripts/us_census/geojsons_low_res/generate_mcf.py
EPS_LEVEL_MAP = {0: 0, 0.03: 2, 0.05: 3, 0.125: 6, 0.225: 10, 0.3: 13}

MCF_PATH = '{MCF_OUT_FOLDER}/mcf/countries.dp{dp_level}.mcfgeojson.mcf'
MCF_FORMAT_STR = "\n".join([
    "Node: dcid:country/{country_code}", "typeOf: dcs:Country",
    "{prop}: {coords_str}", "\n"
])
MULTILINE_GEOJSON_TYPE = "MultiLineString"
MULTIPOLYGON_GEOJSON_TYPE = "MultiPolygon"
POLYGON_GEOJSON_TYPE = "Polygon"

# Map from parent-place DCID to DP level
PARENT_PLACES = {
    'Earth': 13,
    'asia': 10,
    'africa': 10,
    'europe': 6,
    'northamerica': 13,
    'oceania': 13,
    'southamerica': 10,
    'AustraliaAndNewZealand': 6,
    'Caribbean': 6,
    'CentralAmerica': 6,
    'CentralAsia': 6,
    'ChannelIslands': 6,
    'EasternAfrica': 6,
    'EasternAsia': 6,
    'EasternEurope': 6,
    'EuropeanUnion': 6,
    'LatinAmericaAndCaribbean': 6,
    'Melanesia': 6,
    'MiddleAfrica': 6,
    'NorthernAfrica': 6,
    'NorthernEurope': 6,
    'SouthEasternAsia': 6,
    'SouthernAfrica': 6,
    'SouthernAsia': 6,
    'SouthernEurope': 6,
    'SubSaharanAfrica': 6,
    'WesternAfrica': 6,
    'WesternAsia': 6,
    'WesternEurope': 6,
    # Americas
    'undata-geo/G00134000': 6,
}


def get_countries_in(dcids):
    resp = requests.post('https://autopush.api.datacommons.org/v2/node',
                         headers={
                             'X-API-Key': os.environ['MIXER_API_KEY']
                         },
                         json={
                             'nodes': dcids,
                             'property': "<-containedInPlace+{typeOf:Country}"
                         }).json()
    node2children = {}
    for place, d in resp.get('data', {}).items():
        node2children[place] = []
        for n in d.get('arcs', {}).get('containedInPlace+',
                                       {}).get('nodes', []):
            node2children[place].append(n['dcid'])
    return node2children


#
# Code from @chejennifer.
#
def get_multipolygon_geojson_coordinates(geojson):
    """
  Gets geojson coordinates in the form of multipolygon geojson coordinates that
  are in the reverse of the righthand_rule.

  GeoJSON is stored in DataCommons following the right hand rule as per rfc
  spec (https://www.rfc-editor.org/rfc/rfc7946). However, d3 requires geoJSON
  that violates the right hand rule (see explanation on d3 winding order here:
  https://stackoverflow.com/a/49311635). This function returns coordinates in
  the format expected by D3 and turns all polygons into multipolygons for
  downstream consistency.
      Args:
          geojson: geojson of type MultiPolygon or Polygon
      Returns:
          Nested list of geo coordinates.
  """
    # The geojson data for each place varies in whether it follows the
    # righthand rule or not. We want to ensure geojsons for all places
    # does follow the righthand rule.
    right_handed_geojson = rewind(geojson)
    geojson_type = right_handed_geojson['type']
    geojson_coords = right_handed_geojson['coordinates']
    if geojson_type == POLYGON_GEOJSON_TYPE:
        geojson_coords[0].reverse()
        return [geojson_coords]
    elif geojson_type == MULTIPOLYGON_GEOJSON_TYPE:
        for polygon in geojson_coords:
            polygon[0].reverse()
        return geojson_coords
    else:
        assert False, f"Type {geojson_type} unknown!"


def get_geojson_feature(geo_id: str, geo_name: str, geojson: Dict):
    """
  Gets a single geojson feature from a list of json strings
  """
    # Exclude geo if no renderings are present.
    geo_feature = {
        "type": "Feature",
        "id": geo_id,
        "properties": {
            "name": geo_name,
            "geoDcid": geo_id,
        }
    }
    geojson_type = geojson.get("type", "")
    if geojson_type == MULTILINE_GEOJSON_TYPE:
        geo_feature['geometry'] = geojson
    elif geojson_type == POLYGON_GEOJSON_TYPE or geojson_type == MULTIPOLYGON_GEOJSON_TYPE:
        coordinates = get_multipolygon_geojson_coordinates(geojson)
        geo_feature['geometry'] = {
            "type": "MultiPolygon",
            "coordinates": coordinates
        }
    else:
        assert False, geojson_type
        geo_feature = None
    return geo_feature


class CountryBoundariesGenerator:
    """Generates MCF files with simplified json for the WB boundaries dataset."""

    def __init__(self, input_file, output_dir):
        self.input_file = input_file
        self.output_dir = output_dir
        for d in ['tmp', 'mcf', 'cache']:
            os.makedirs(os.path.join(self.output_dir, d), exist_ok=True)

    def load_data(self):
        with open(self.input_file) as fp:
            gj = json.load(fp)
            with open(os.path.join(self.output_dir, 'input_formatted.json'),
                      'w') as ofp:
                json.dump(gj, ofp, indent=1)
        return gpd.read_file(self.input_file)

    def existing_codes(self, all_countries):
        """Builds mapping of column code to country codes to import.

        Only countries with DCID of the form county/{code} are included.
        """
        # Call DC API to get list of countries
        dc_all_countries = dc.get_property_values(['Country'],
                                                  'typeOf',
                                                  out=False,
                                                  limit=500)['Country']
        dc_all_countries = set(dc_all_countries)

        def is_dc_country(iso):
            dcid = f'country/{iso}'
            return dcid in dc_all_countries

        # Compare dataset countries with results from DC
        idx = all_countries['iso3cd'].apply(is_dc_country)
        return sorted(all_countries.loc[idx]['iso3cd'])

    def _geojson_tmpfile(self, country_code, dp_level):
        """Returns filename of the geojson output file."""
        return os.path.join(self.output_dir, 'tmp',
                            f'{country_code}_{dp_level}.geojson')

    def _geojson(self, country_code, dp_level):
        fname = self._geojson_tmpfile(country_code, dp_level)
        with open(fname) as fp:
            return json.load(fp)

    def _export_country_feature(self, country_code, country_data, dp_level):
        geojson = json.loads(country_data.to_json())
        features = geojson.get('features', [])
        assert (len(features) == 1)
        geometry = features[0].get('geometry')
        fname = self._geojson_tmpfile(country_code, dp_level)
        with open(fname, 'w') as f:
            json.dump(geometry, f, indent=2)

    def _simplify_json(self, country_code, country_data):
        """Simplifies (and exports) a geojson."""
        for tolerance, dp_level in EPS_LEVEL_MAP.items():
            if dp_level == 0:
                export_data = country_data
            else:
                export_data = country_data.simplify(tolerance)
            self._export_country_feature(country_code, export_data, dp_level)

    def extract_country_geojson(self, all_countries_df, existing_codes):
        """Extract and export all geojson to tempfiles."""

        print(f'Exporting geojson to {self.output_dir}')
        col = 'iso3cd'
        for country_code in existing_codes:
            country_data = all_countries_df[
                (all_countries_df[col] == country_code) &
                (all_countries_df['geometry'].geom_type != 'LineString') &
                (all_countries_df['geometry'].geom_type != 'MultiLineString')]
            country_data = country_data.dissolve(
                by=col)  # Join multiple rows into a single shape
            self._simplify_json(country_code, country_data)

    def build_cache(self, existing_codes):
        parent2children = get_countries_in(list(PARENT_PLACES.keys()))
        all_children = set()
        for children in parent2children.values():
            all_children.update(children)

        child2name = {}
        for child, values in dc.get_property_values(list(all_children),
                                                    'name').items():
            if values:
                child2name[child] = values[0]

        for parent, dp_level in PARENT_PLACES.items():
            if not parent2children.get(parent):
                print(f'Missing children for {parent}')
                continue
            features = []
            for child in parent2children[parent]:
                if not child.startswith('country/'):
                    print(f'{child} of parent {parent} is not a country!')
                    continue
                code = child.replace('country/', '')
                if code not in existing_codes:
                    print(f'Missing geojson for {child}')
                    continue
                geo = self._geojson(code, dp_level)
                feature = get_geojson_feature(child, child2name.get(child, ''),
                                              geo)
                if feature:
                    features.append(feature)
            result = {
                "type": "FeatureCollection",
                "features": features,
                "properties": {
                    "current_geo": "Earth"
                }
            }
            fname = f'{parent.replace("/", "").lower()}_country_dp{dp_level}.json'
            with open(os.path.join(self.output_dir, 'cache', fname), 'w') as fp:
                json.dump(result, fp, indent=2)

    def output_mcf(self, existing_codes):
        """Generates the output MCF files for all dp levels."""
        print(f'Generating MCF to {self.output_dir}')

        def prop_for_dp_level(dp_level):
            if dp_level == 0:
                return "geoJsonCoordinatesUN"
            return f"geoJsonCoordinatesUNDP{dp_level}"

        for _, dp_level in EPS_LEVEL_MAP.items():
            mcf_path = MCF_PATH.format(MCF_OUT_FOLDER=self.output_dir,
                                       dp_level=dp_level)
            with open(mcf_path, 'w') as mcf_fp:
                for country_code in existing_codes:
                    geostr = self._geojson(country_code, dp_level)
                    mcf_fp.write(
                        MCF_FORMAT_STR.format(country_code=country_code,
                                              prop=prop_for_dp_level(dp_level),
                                              coords_str=json.dumps(
                                                  json.dumps(geostr))))


def main(_):
    gen = CountryBoundariesGenerator(FLAGS.input_file, FLAGS.output_dir)
    all_countries = gen.load_data()
    existing_codes = gen.existing_codes(all_countries)
    gen.extract_country_geojson(all_countries, existing_codes)
    gen.build_cache(existing_codes)
    gen.output_mcf(existing_codes)


if __name__ == '__main__':
    app.run(main)
