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
"""Script to import and clean WFIGS data.
"""
from collections.abc import Sequence
import datetime

from absl import app
from absl import logging
import json
import numpy as np
import os
import pandas as pd
import pickle
import re
import requests
import logging
import datacommons as dc
import sys

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH))  #for mapping
import mapping

sys.path.append(os.path.join(_SCRIPT_PATH, '../../util/'))  # for recon util
import latlng_recon_geojson

pd.set_option("display.max_columns", None)

PRE_2022_FIRE_LOCATIONS_URL = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Fire_History_Locations_Public/FeatureServer/0/query?where=1%3D1&outFields=InitialLatitude,InitialLongitude,InitialResponseAcres,InitialResponseDateTime,UniqueFireIdentifier,IncidentName,IncidentTypeCategory,IrwinID,FireCauseSpecific,FireCauseGeneral,FireCause,FireDiscoveryDateTime,ContainmentDateTime,ControlDateTime,IsCpxChild,CpxID,DiscoveryAcres,DailyAcres,POOFips,POOState,EstimatedCostToDate,TotalIncidentPersonnel,UniqueFireIdentifier&outSR=4326&orderByFields=FireDiscoveryDateTime&f=json&resultType=standard"
_OUTPUT = "/cns/jv-d/home/datcom/v3_resolved_mcf/fire/wfigs/"
_CACHE = {}

with open(os.path.join(_SCRIPT_PATH, 'location_file.json')) as f:
    data = f.read()

_CACHE = json.loads(data)

_FIRE_INCIDENT_MAP = {
    'CX': 'FireIncidentComplexEvent',
    'WF': 'WildlandFireEvent',
    'RX': 'PrescribedFireEvent'
}

_DAILY_ACRES_MAP = "Acre {daily_acres}"
_INITIAL_RESPONSE_AREA_MAP = "Acre {initial_response_area}"
_EXPECTED_LOSS_MAP = "USDollar {costs}"


def get_data(url):
    """Get data from the API.

    This method does that by retrieving 32K records(API call return size) in a
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
          url = url,
          record_count = str(full_page_record_count * i)))
        response_json = r.json()
        for row in response_json["features"]:
            data.append(row["attributes"])
        i += 1
        full_page_record_count = max(full_page_record_count, len(response_json["features"]))
        if not((response_json["features"]) and len(response_json["features"]) == full_page_record_count):
          break
    df = pd.DataFrame(data)
    return df


def process_df(df):
    """Process input fire data and return it in an DC-ingest-able form.

  This method process the input dataframe and converts various field into
  datacommons ingest-able data formats.

  Args:
    df: input wfigs locations dataframe.

  Returns:
    A Pandas dataframe containing process field values for various incidents.
  """
    ll2p = latlng_recon_geojson.LatLng2Places()
    df = df[df["IncidentName"].str.contains("DO NOT USE") == False]
    initial_size = df.shape[0]
    df = df.drop_duplicates()
    logging.info("Initial size: %s, without duplicates: %s" %
                 (initial_size, df.shape[0]))
    df["POOFips"] = df["POOFips"].astype(str)

    # convert epoch time in milliseconds to datetime
    def get_datetime(x):
        if not pd.isna(x):
            return datetime.datetime.fromtimestamp(x / 1000)
        else:
            return None

    def get_date_str(x):
        if not pd.isna(x):
            return x.strftime("%Y-%m-%d")
        return None

    # Get location associated with each incident.
    def get_place(x):
        try:
            geoIds = []
            location = ''
            if not (pd.isna(x.InitialLatitude) or pd.isna(x.InitialLongitude)
                   ) and abs(x.InitialLatitude) <= 90 and abs(
                       x.InitialLongitude) <= 180:
                if str(x.InitialLatitude) in _CACHE:
                    if str(x.InitialLongitude) in _CACHE[str(
                            x.InitialLatitude)]:
                        return _CACHE[str(x.InitialLatitude)][str(
                            x.InitialLongitude)]
                geoIds = ll2p.resolve(x.InitialLatitude, x.InitialLongitude)
                for geoId in geoIds:
                    if geoId not in ('northamerica', 'country/CAN',
                                     'country/MEX'):
                        location += 'dcid:%s, ' % geoId
                if 'northamerica' in geoIds:
                    return_val = (location +
                                  ('[LatLong %s %s]' %
                                   (x.InitialLatitude, x.InitialLongitude)))
                    if x.InitialLatitude in _CACHE:
                        _lat_dict = CACHE[str(x.InitialLatitude)]
                        _lat_dict[str(x.InitialLongitude)] = return_val
                    else:
                        _CACHE[str(x.InitialLatitude)] = {
                            str(x.InitialLongitude): return_val
                        }
                    return return_val
            if not x.POOFips or pd.isna(x.POOFips):
                location = mapping.POOSTATE_GEOID_MAP[x.POOState]
                return location
            else:
                return None
        except Exception as e:
            logging.debug("Failed resolution for ({0},{1} for fire {2})".format(
                x.InitialLatitude, x.InitialLongitude, x.UniqueFireIdentifier))
            return ''

    # Get FIPS codes associated with each incident.
    def get_fips(x):
        if x.POOFips and not pd.isna(x.POOFips):
            fips_str = (x.POOFips.zfill(5))
            return "dcid:%s, dcid:%s, dcid:%s" % (
                "geoId/" + fips_str[:2], "geoId/" + fips_str, "country/USA")
        else:
            return None

    # Write expected loss in an ingest-able format.
    def get_cost(x):
        if x and not np.isnan(x):
            return _EXPECTED_LOSS_MAP.format_map({'costs': x})
        else:
            return None

    # Write fire area in an ingest-able format.
    def get_area(x, label, mapping):
        if x and not np.isnan(x):
            return mapping.format_map({label: x})
        else:
            return None

    # Get cause-dcid for the fire cause.
    def get_cause(x):
        if x:
            cause = x.replace(" ", "").replace("/", "Or")
            if cause in mapping.CAUSE_DCID_MAP:
                cause = mapping.CAUSE_DCID_MAP[cause]
            return cause
        else:
            return None

    # get personnel count for the incident.
    def get_personnel(x):
        if x and not np.isnan(x):
            x
        else:
            return None

    # If a parent fire exists, associate it with given fire.
    def get_parent_fire(x):
        if not (np.isnan(x.IsCpxChild)) and x.IsCpxChild == 1 and x.CpxID:
            # remove curly brackets from front and end of string.
            return ('fire/IrwinId/%s' % x.CpxID[1:-1].lower())
        else:
            return None

    df["FireDiscoveryDateTime"] = df["FireDiscoveryDateTime"].apply(
        get_datetime)
    df["Year"] = df["FireDiscoveryDateTime"].apply(lambda x: x.year)
    df["FireDiscoveryDateTime"] = df["FireDiscoveryDateTime"].apply(
        get_date_str)
    df = df[df["Year"] >= 2014]
    df["ContainmentDateTime"] = df["ContainmentDateTime"].apply(
        get_datetime).apply(get_date_str)
    df["ControlDateTime"] = df["ControlDateTime"].apply(get_datetime).apply(
        get_date_str)
    df["InitialResponseDateTime"] = df["InitialResponseDateTime"].apply(
        get_datetime).apply(get_date_str)
    df["Costs"] = df["EstimatedCostToDate"].apply(get_cost)
    df['BurnedArea'] = df['DailyAcres'].apply(get_area,
                                              args=('daily_acres',
                                                    _DAILY_ACRES_MAP))
    df["FireCause"] = df["FireCause"].apply(get_cause)
    df["FireCauseGeneral"] = df["FireCauseGeneral"].apply(get_cause)
    df["FireCauseSpecific"] = df["FireCauseSpecific"].apply(get_cause)
    df["TotalIncidentPersonnel"] = df["TotalIncidentPersonnel"].apply(
        get_personnel)
    df["ParentFire"] = df.apply(get_parent_fire, axis=1)
    df['InitialResponseAcres'] = df['InitialResponseAcres'].apply(
        get_area, args=('initial_response_area', _INITIAL_RESPONSE_AREA_MAP))

    df["Location"] = df.apply(get_place, axis=1)
    df["FIPS"] = df.apply(get_fips, axis=1)
    df["Location"] = df["Location"].fillna(df["FIPS"])
    df.loc[df["Location"] == '', 'Location'] = df["FIPS"]
    df["IrwinID"] = df["IrwinID"].apply(lambda x: x.lower())
    df["dcid"] = df["IrwinID"].apply(lambda x: "fire/irwinId/%s" % x)
    df["name"] = df["IncidentName"].apply(lambda x: re.sub(
        ' +', ' ',
        x.replace("\n", "").replace("'", "").replace('"', "").replace('[', ""))
                                          + ' Fire').apply(lambda x: x.title())
    df["typeOf"] = df["IncidentTypeCategory"].apply(
        lambda x: _FIRE_INCIDENT_MAP[x])
    df["wfigsFireID"] = df["UniqueFireIdentifier"]
    col_list = [
        "dcid", "name", "typeOf", "Location", "FireCause", "FireCauseGeneral",
        "FireCauseSpecific", "FireDiscoveryDateTime", "ControlDateTime",
        "ContainmentDateTime", "BurnedArea", "Costs", "TotalIncidentPersonnel",
        "IrwinID", "wfigsFireID", "ParentFire", "InitialResponseDateTime",
        "InitialResponseAcres"
    ]
    return df[col_list]


def main(_) -> None:
    pre_2022_df = get_data(PRE_2022_FIRE_LOCATIONS_URL)
    df = pre_2022_df
    df = process_df(df)
    df.to_csv("final_processed_data.csv", index=False)
    with open('location_file.json', 'w') as locations:
        locations.write(json.dumps(_CACHE))


if __name__ == "__main__":
    app.run(main)
