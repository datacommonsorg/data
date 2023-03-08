# Copyright 2022 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Script to import and clean WFIGS Perimeter data.
"""
import requests
import pandas as pd
import json
import datetime
from absl import app
from shapely import geometry
from arcgis2geojson import arcgis2geojson

_FIRE_DCID_FORMAT = "fire/irwinId/{id}"
_PERIMETER_DCID_FORMAT = "firePerimeter/irwinId/{id}/date/{perimeter_date}"
_DP1_TOLERANCE = 0.01
_PERIMETER_URL = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Fire_History_Perimeters_Public/FeatureServer/0/query?where=1%3D1&outFields=irwin_IrwinID,irwin_IncidentTypeCategory,poly_DateCurrent,poly_CreateDate&outSR=4326&f=json"

_FIRE_INCIDENT_MAP = {
    'CX': 'FireIncidentComplexEvent',
    'WF': 'WildlandFireEvent',
    'RX': 'PrescribedFireEvent'
}

pd.set_option("display.max_columns", None)


def merge_dictionaries(dict1, dict2):
    res = {**dict1, **dict2}
    return res


def get_data(url):
    """Get data from the API.

  This method does that by retrieving 32K records (API call return size) in a
  loop till we get to the end of the dataset.

  Args:
    url: URL for the API call.

  Returns:
    A Pandas dataframe containing merged historical and YTD data.
  """
    data = []
    full_page_record_count = 0
    i = 0
    while True:
        r = requests.get("{url}&resultOffset={record_count}".format(
            url=url, record_count=str(full_page_record_count * i)))
        response_json = r.json()
        if not (response_json["features"]):
            break
        for row in response_json["features"]:
            if "geometry" in row:
                geometry = (row['geometry'])
                geojson = {'geojson': geometry}
                data.append(merge_dictionaries(geojson, row["attributes"]))
        i += 1
        # use max to get page size for the first request
        # the value shouldn't change after first iteration, but keep checking
        # in case behavior changes in the future.
        full_page_record_count = max(full_page_record_count,
                                     len(response_json["features"]))
        # Exit if latest response has lesser rows than page size, as it
        # indicates that this is the end of the response.
        if not (len(response_json["features"]) == full_page_record_count):
            break
    df = pd.DataFrame(data)
    return df


def get_gj_dp(gj):
    poly = geometry.shape(arcgis2geojson(gj))
    spoly = poly.simplify(_DP1_TOLERANCE)
    gjs = json.dumps(json.dumps(geometry.mapping(spoly)))
    return gjs


def create_dcid(row):
    id_without_brackets = row["irwin_IrwinID"][1:-1].lower()
    return _PERIMETER_DCID_FORMAT.format(id=id_without_brackets,
                                         perimeter_date=row["poly_DateCurrent"])


def create_fire_id(irwin_id):
    id_without_brackets = irwin_id[1:-1].lower()
    return _FIRE_DCID_FORMAT.format(id=id_without_brackets)


def extract_geojsons(df):
    df["geojson_dp1"] = df["geojson"].apply(lambda x: get_gj_dp(x))
    df["fire_id"] = df["irwin_IrwinID"].apply(create_fire_id)
    df["typeOf"] = df["irwin_IncidentTypeCategory"].apply(
        lambda x: _FIRE_INCIDENT_MAP[x])
    df = df[["typeOf", "fire_id", "geojson_dp1"]]
    return df


def main(_) -> None:
    df = get_data(_PERIMETER_URL)
    df = extract_geojsons(df)
    df.to_csv("perimeter_data.csv",
              index=False,
              doublequote=False,
              escapechar='\\')


if __name__ == "__main__":
    app.run(main)
