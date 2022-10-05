"""Script to import and clean WFIGS data.
"""
from collections.abc import Sequence
import datetime

from absl import app
from absl import logging
import numpy as np
import os
import pandas as pd
import pickle
import re
import requests
import datacommons as dc
import sys
import mapping

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../util/'))  # for recon util
import latlng_recon_geojson

pd.set_option("display.max_columns", None)

PRE_2022_FIRE_LOCATIONS_URL = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Fire_History_Locations_Public/FeatureServer/0/query?where=1%3D1&outFields=InitialLatitude,InitialLongitude,InitialResponseAcres,InitialResponseDateTime,UniqueFireIdentifier,IncidentName,IncidentTypeCategory,IrwinID,FireCauseSpecific,FireCauseGeneral,FireCause,FireDiscoveryDateTime,ContainmentDateTime,ControlDateTime,IsCpxChild,CpxID,DiscoveryAcres,DailyAcres,POOFips,POOState,EstimatedCostToDate,TotalIncidentPersonnel,UniqueFireIdentifier&outSR=4326&f=json&resultType=standard"
YTD_2022_FIRE_LOCATIONS_URL = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/CY_WildlandFire_Locations_ToDate/FeatureServer/0/query?where=1%3D1&outFields=FireCauseGeneral,FireCauseSpecific,FireCause,InitialLatitude,InitialLongitude,InitialResponseAcres,InitialResponseDateTime,IrwinID,UniqueFireIdentifier,IncidentName,IncidentTypeCategory,FireDiscoveryDateTime,ContainmentDateTime,ControlDateTime,IsCpxChild,CpxID,DiscoveryAcres,DailyAcres,POOState,EstimatedCostToDate,TotalIncidentPersonnel,UniqueFireIdentifier&outSR=4326&f=json&resultType=standard"
_OUTPUT = "/cns/jv-d/home/datcom/v3_resolved_mcf/fire/wfigs/"

_FIRE_INCIDENT_MAP = {
    'CX': 'FireIncidentComplexEvent',
    'WF': 'WildlandFireEvent',
    'RX': 'PrescribedFireEvent'
}

_LOCATION_MAP = "\nlocation: {location}"
_DAILY_ACRES_MAP = "[Acre {daily_acres}]"
_INITIAL_RESPONSE_AREA_MAP = "[Acre {initial_response_area}]"
_EXPECTED_LOSS_MAP = "[USDollar {costs}]"


def get_data(url):
    """Get data from the API.

  This method does that by retrieving the max results in a loop till we get to
  the end of the dataset.

  Args:
    url: URL for the API call.

  Returns:
    A Pandas dataframe containing merged historical and YTD data.
  """
    r = requests.get(url)
    x = r.json()
    data = []
    for row in x["features"]:
        data.append(row["attributes"])
    max_record_count = len(x["features"])
    offset_str = "&resultOffset="
    i = 1
    while (x["features"]) and len(x["features"]) == max_record_count:
        r = requests.get(url + offset_str + str(max_record_count * i))
        x = r.json()
        for row in x["features"]:
            data.append(row["attributes"])
        i += 1
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
    df = df.drop_duplicates()
    df["POOFips"] = df["POOFips"].apply(
        lambda x: x.strip() if isinstance(x, str) else x).replace('', np.nan)
    df["POOFips"] = df["POOFips"].astype('Int64')

    # convert epoch time in milliseconds to datetime
    def get_datetime(x):
        if not pd.isna(x):
            return datetime.datetime.fromtimestamp(x / 1000)
        else:
            return None

    # Get location associated with each incident.
    def get_place(x):
        try:
            geoIds = []
            location = ''
            if not (pd.isna(x.InitialLatitude) or pd.isna(x.InitialLongitude)
                   ) and abs(x.InitialLatitude) <= 90 and abs(
                       x.InitialLongitude) <= 180:
                geoIds = ll2p.resolve(x.InitialLatitude, x.InitialLongitude)
                for geoId in geoIds:
                    if geoId != 'northamerica':
                        location += 'dcid:%s, ' % geoId
                if 'northamerica' in geoIds:
                    return (location +
                            ('[LatLong %s %s]' %
                             (x.InitialLatitude, x.InitialLongitude)))
            if pd.isna(x.POOFips):
                location = mapping.POOState_geoID_map[x.POOState]
                return location
            else:
                return None
        except Exception as e:
            print(e)
            print(x.InitialLatitude)
            print(x.InitialLongitude)
            logging.debug("Failed resolution for ({0},{1} for fire {2})".format(
                x.InitialLatitude, x.InitialLongitude, x.UniqueFireIdentifier))
            return ''

    # Get FIPS codes associated with each incident.
    def get_fips(x):
        if not pd.isna(x.POOFips):
            fips_str = str(int(x.POOFips))
            return "dcid:%s, dcid:%s, dcid:%s" % (
                "geoId/" + fips_str, "geoId/" + fips_str[:2], "country/USA")
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
            if cause in mapping.cause_dcid_map:
                cause = mapping.cause_dcid_map[cause]
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
            return ('fire/IRWINID-%s' % x.CpxID[1:-1].lower())
        else:
            return None

    df["FireDiscoveryDateTime"] = df["FireDiscoveryDateTime"].apply(
        get_datetime)
    df["year"] = df["FireDiscoveryDateTime"].apply(lambda x: x.year)
    #filter for records in and after 2019
    df = df[df["year"] >= 2019]
    df["ContainmentDateTime"] = df["ContainmentDateTime"].apply(get_datetime)
    df["ControlDateTime"] = df["ControlDateTime"].apply(get_datetime)
    df["InitialResponseDateTime"] = df["InitialResponseDateTime"].apply(
        get_datetime)
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

    df["IrwinID"] = df["IrwinID"].apply(lambda x: x.lower())
    df["dcid"] = df["IrwinID"].apply(lambda x: "fire/IRWINID-%s" % x)
    df["name"] = df["IncidentName"].apply(lambda x: re.sub(
        ' +', ' ',
        x.replace("\n", "").replace("'", "").replace('"', "").replace('[', ""))
                                          + ' Fire')
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
    ytd_2022_df = get_data(YTD_2022_FIRE_LOCATIONS_URL)
    df = pd.concat([pre_2022_df, ytd_2022_df], ignore_index=True)
    df = process_df(df)
    df.to_csv("processed_data.csv", index=False)


if __name__ == "__main__":
    app.run(main)
