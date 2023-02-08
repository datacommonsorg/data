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
from absl import flags
from absl import logging
from google.cloud import storage
import json
import numpy as np
import os
import pandas as pd
import pickle
import re
import requests
import datacommons as dc
import sys

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH))  #for mapping
import mapping

sys.path.append(os.path.join(_SCRIPT_PATH, '../../util/'))  # for recon util
import latlng_recon_geojson

pd.set_option("display.max_columns", None)

FLAGS = flags.FLAGS

flags.DEFINE_boolean('read_location_cache', True,
                     'save location cache to file.')

flags.DEFINE_boolean('save_location_cache', False,
                     'save location cache to file.')

# FIRE_LOCATIONS_URL = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Fire_History_Locations_Public/FeatureServer/0/query?where=1%3D1&returnGeometry=false&outFields=InitialLatitude,InitialLongitude,InitialResponseAcres,InitialResponseDateTime,UniqueFireIdentifier,IncidentName,IncidentTypeCategory,IrwinID,FireCauseSpecific,FireCauseGeneral,FireCause,FireDiscoveryDateTime,ContainmentDateTime,ControlDateTime,IsCpxChild,CpxID,DailyAcres,POOFips,POOState,EstimatedCostToDate,TotalIncidentPersonnel,UniqueFireIdentifier&outSR=4326&orderByFields=FireDiscoveryDateTime&f=json&resultType=standard"
# Only download data from Oct 10, 2022 to make auto refresh manageable.
POST_OCT_2022_FIRE_LOCATIONS_URL = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Fire_History_Locations_Public/FeatureServer/0/query?where=FireDiscoveryDateTime>'2022-10-10'&outFields=*&outSR=4326&f=json"
_LAT_LNG_CACHE = {}
_START_YEAR = 2014
_GCS_PROJECT_ID = "datcom-204919"
_GCS_BUCKET = "datcom-import-cache"
_GCS_FILE_PATH = "fires/location_file.json"
_ACRE_TO_SQ_KM_MULTIPLIER = 0.00404686

_FIRE_INCIDENT_MAP = {
    'CX': 'FireIncidentComplexEvent',
    'WF': 'WildlandFireEvent',
    'RX': 'PrescribedFireEvent'
}

_DAILY_ACRES_MAP = "SquareKilometer {daily_acres}"
_INITIAL_RESPONSE_AREA_MAP = "SquareKilometer {initial_response_area}"
_EXPECTED_LOSS_MAP = "USDollar {costs}"

_FIRE_DCID_FORMAT = "fire/irwinId/{id}"


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
            data.append(row["attributes"])
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
    def epoch_to_datetime(date_val):
        if not pd.isna(date_val):
            return datetime.datetime.fromtimestamp(date_val / 1000)
        else:
            return None

    def convert_date_to_str(date_val):
        if not pd.isna(date_val):
            return date_val.strftime("%Y-%m-%d")
        return None

    # Get location associated with each incident.
    def get_place(row):
        latitude = row.InitialLatitude
        latitude_str = str(latitude)
        longitude = row.InitialLongitude
        longitude_str = str(longitude)
        try:
            geoIds = []
            location = ''
            if not (pd.isna(latitude) or pd.isna(longitude)
                   ) and abs(latitude) <= 90 and abs(longitude) <= 180:
                if latitude_str in _LAT_LNG_CACHE:
                    if longitude_str in _LAT_LNG_CACHE[str(latitude)]:
                        return _LAT_LNG_CACHE[latitude_str][str(longitude)]
                geoIds = ll2p.resolve(latitude, longitude)
                for geoId in geoIds:
                    if geoId not in ('northamerica', 'country/CAN',
                                     'country/MEX'):
                        location += 'dcid:%s, ' % geoId
                if 'northamerica' in geoIds:
                    return_val = (location + ('[LatLong %s %s]' %
                                              (latitude, longitude)))
                    if latitude in _LAT_LNG_CACHE:
                        _lat_dict = _LAT_LNG_CACHE[latitude_str]
                        _lat_dict[longitude_str] = return_val
                    else:
                        _LAT_LNG_CACHE[latitude_str] = {
                            longitude_str: return_val
                        }
                    return return_val
            if not row.POOFips or pd.isna(row.POOFips):
                location = mapping.POOSTATE_GEOID_MAP[row.POOState]
                return location
            else:
                return None
        except Exception as e:
            logging.debug("Failed resolution for ({0},{1} for fire {2})".format(
                latitude, longitude, row.UniqueFireIdentifier))
            return ''

    # Get FIPS codes associated with each incident.
    def get_fips(row):
        if row.POOFips and not pd.isna(row.POOFips):
            fips_str = (row.POOFips.zfill(5))
            return "dcid:%s, dcid:%s, dcid:%s" % (
                "geoId/" + fips_str[:2], "geoId/" + fips_str, "country/USA")
        else:
            return None

    # Write expected loss in an ingest-able format.
    def get_cost(cost_val):
        if cost_val and not np.isnan(cost_val):
            return _EXPECTED_LOSS_MAP.format_map({'costs': cost_val})
        else:
            return None

    # Write fire area in an ingest-able format.
    def get_area(area, label, mapping):
        if area and not np.isnan(area):
            return mapping.format_map({label: area * _ACRE_TO_SQ_KM_MULTIPLIER})
        else:
            return None

    # Get cause-dcid for the fire cause.
    def get_cause(cause_str):
        if cause_str:
            cause = cause_str.replace(" ", "").replace("/", "Or")
            if cause in mapping.CAUSE_DCID_MAP:
                cause = mapping.CAUSE_DCID_MAP[cause]
            return cause
        else:
            return None

    # get personnel count for the incident.
    def get_personnel(personnel_val):
        if personnel_val and not np.isnan(personnel_val):
            return personnel_val
        else:
            return None

    # If a parent fire exists, associate it with given fire.
    def get_parent_fire(row):
        if not (np.isnan(row.IsCpxChild)) and row.IsCpxChild == 1 and row.CpxID:
            # remove curly brackets from front and end of string.
            id_without_brackets = row.CpxID[1:-1].lower()
            return _FIRE_DCID_FORMAT.format(id=id_without_brackets)
        else:
            return None

    def format_fire_name(name):
        return (re.sub(
            ' +', ' ',
            name.replace("\n", "").replace("'", "").replace('"', "").replace(
                '[', "")) + ' Fire').title()

    # Convert Fire discovery date to datetime format to string and extract year
    df["FireDiscoveryDateTime"] = df["FireDiscoveryDateTime"].apply(
        epoch_to_datetime)
    df["FireDiscoveryYear"] = df["FireDiscoveryDateTime"].apply(
        lambda x: x.year)
    df["FireDiscoveryDateTime"] = df["FireDiscoveryDateTime"].apply(
        convert_date_to_str)
    # Filter to only have data since the configured start year
    df = df[df["FireDiscoveryYear"] >= _START_YEAR]
    # Convert containement date to datetime format to string
    df["ContainmentDateTime"] = df["ContainmentDateTime"].apply(
        epoch_to_datetime).apply(convert_date_to_str)
    # Convert control date to datetime format to string
    df["ControlDateTime"] = df["ControlDateTime"].apply(
        epoch_to_datetime).apply(convert_date_to_str)
    # Convert Initial response date to datetime format to string
    df["InitialResponseDateTime"] = df["InitialResponseDateTime"].apply(
        epoch_to_datetime).apply(convert_date_to_str)
    # Convert costs to currency labelled string
    df["Costs"] = df["EstimatedCostToDate"].apply(get_cost)
    # Convert burned area to Unit labelled string
    df['BurnedArea'] = df['DailyAcres'].apply(get_area,
                                              args=('daily_acres',
                                                    _DAILY_ACRES_MAP))
    # Causes to Cause Enum IDs
    df["FireCause"] = df["FireCause"].apply(get_cause)
    df["FireCauseGeneral"] = df["FireCauseGeneral"].apply(get_cause)
    df["FireCauseSpecific"] = df["FireCauseSpecific"].apply(get_cause)

    # Set rows with missing incident personnel values to Nulls
    df["TotalIncidentPersonnel"] = df["TotalIncidentPersonnel"].apply(
        get_personnel)
    # If the fire has a parent fire, get the parent fire ID.
    df["ParentFire"] = df.apply(get_parent_fire, axis=1)
    # unit labelled string for initial response area.
    df['InitialResponseAcres'] = df['InitialResponseAcres'].apply(
        get_area, args=('initial_response_area', _INITIAL_RESPONSE_AREA_MAP))

    # Based on available data, get Location IDs.
    df["Location"] = df.apply(get_place, axis=1)
    # If present, get FIPS codes.
    df["FIPS"] = df.apply(get_fips, axis=1)
    # In cases where location data is missing, replace it with FIPS code
    df["Location"] = df["Location"].fillna('')
    df.loc[df["Location"] == '', 'Location'] = df["FIPS"]

    df["IrwinID"] = df["IrwinID"].apply(lambda x: x.lower())
    # Use IrwinID to set dcid.
    df["dcid"] = df["IrwinID"].apply(lambda x: _FIRE_DCID_FORMAT.format(id=x))
    # Clean up Incident Name string to uniformly format fire names.
    df["name"] = df["IncidentName"].apply(lambda x: format_fire_name(x))
    # Get type of fire - Complex, individual or prescribed.
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
    df = get_data(POST_OCT_2022_FIRE_LOCATIONS_URL)

    storage_client = storage.Client(_GCS_PROJECT_ID)
    bucket = storage_client.bucket(_GCS_BUCKET)
    blob = bucket.blob(_GCS_FILE_PATH)
    if FLAGS.read_location_cache:
        try:
            _LAT_LNG_CACHE = json.loads(blob.download_as_string(client=None))
        except Exception as e:  # pylint: disable=broad-except
            logging.error("Reading locations cache failed: %e" % e)
            _LAT_LNG_CACHE = {}

    df = process_df(df)
    df.to_csv("final_processed_data.csv", index=False)
    if FLAGS.save_location_cache:
        with blob.open("w") as locations:
            locations.write(json.dumps(_LAT_LNG_CACHE))


if __name__ == "__main__":
    app.run(main)
