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

from absl import app
from absl import flags
from absl import logging
from datetime import datetime
from google.cloud.storage import Client
from io import StringIO
import os
import pandas as pd
import requests

FLAGS = flags.FLAGS
flags.DEFINE_string("dataFile", "", \
  "Location of air quality data file (local/gcs)") #optional
flags.DEFINE_string("sitesFile", "india_air_quality_sites.csv", \
  "Location of air quality sites file.") #optional

# URL of the RSS feed
RSS_URL = "https://airquality.cpcb.gov.in/caaqms/rss_feed"
POLLUTANTS = {
    "PM2.5" : "PM2.5", 
    "PM10" : "PM10", 
    "NO2" : "NO2", 
    "SO2" : "SO2", 
    "CO" : "CO", 
    "Ammonia" : "NH3", 
    "Ozone" : "OZONE", 
}
STATS = ["Min", "Max", "Mean"]
LGD_FILE="../india/geo/LocalGovernmentDirectory_Districts.csv"
DATA_FILE="india_air_quality_data"

class IndiaAirQualityDataLoader:
  """
  This class is responsible for processing India CPCB air quality data (RSS
  feed).
  """
  def __init__(self):
    self.xslt = "india_air_quality.xslt" # stylesheet for CSV conversion
    self.xpath = "//Station" # Row element in XML
    self.resolve_api_url = "https://api.datacommons.org/v2/resolve?key=" + \
      os.environ["DC_API_KEY"]

  # Downloads a GCS file to local.
  def download_gcs_file(self, uri: str, path: str):
    gcs_client = Client()
    bucket = gcs_client.get_bucket(uri.split("/")[2])
    file_name = uri.split("/")[3]
    blob = bucket.get_blob(file_name)
    blob.download_to_filename(path)
    return file_name

  # Uploads a GCS file from local.
  def upload_gcs_file(self, uri: str, path: str):
    gcs_client = Client()
    bucket = gcs_client.get_bucket(uri.split("/")[2])
    file_name = uri.split("/")[3]
    blob = bucket.blob(file_name)
    blob.upload_from_filename(path)

  # Invokes DC resolve API to get district wikidata id from the LatLang
  # coordinates of the station.
  def __get_place_id(self, row):
    resolve_api =  self.resolve_api_url + "&nodes=" + \
      str(row["Latitude"]) + "%23" + str(row["Longitude"]) + \
      "&property=%3C-geoCoordinate-%3Edcid"
    response = requests.get(resolve_api, timeout=30)
    if response.status_code == 200:
      data = response.json()
      for i in ((data["entities"])[0])["candidates"]:
        if(i["dominantType"] == "AdministrativeArea2" \
          or i["dominantType"] == "City"):
          dcid = i["dcid"]
          return dcid
    return None

  def __cleanup_name(self, name):
    return name.replace("-","").replace(".","")\
      .replace("(","").replace(")","").replace(" ","")

  # Reads RSS feed of air quality data and converts to CSV format using XSLT
  # stylesheet.  Data is read from a local/gcs file if provided. Else it reads
  # the live RSS feed.
  def get_feed(self, file_name: str) -> pd.DataFrame:
    if not file_name:
      response = requests.get(RSS_URL, timeout=60)
      if response.status_code == 200:
        rss_feed = response.text
        print(rss_feed, file = open(DATA_FILE + ".xml", \
          "w", encoding="utf-8"))
      else:
        raise IOError("Error in fetching AQI data from the source: " + RSS_URL)
    else:
      logging.info("Reading AQI data from file: %s", file_name)
      if file_name.startswith("gs://"):
        file_name = self.download_gcs_file(file_name, file_name.split("/")[3])
      feed = open(file_name, "r", encoding="utf-8")
      rss_feed = feed.read()
      feed.close()

    in_df = pd.read_xml(
      StringIO(rss_feed), xpath=self.xpath, stylesheet=self.xslt)
    return in_df

  # Processes air quality data to add formatting and site id info.
  def process_data(self, in_df: pd.DataFrame, \
    site_df: pd.DataFrame) -> pd.DataFrame:
    # Generates the Flattened csv data from India CPCB RSS feed.
    in_df["LastUpdate"] = in_df["LastUpdate"].apply(
      lambda x: datetime.strptime(x,"%d-%m-%Y %H:%M:%S").isoformat())
    place_df = site_df[["SiteName", "DistrictDCID", "LGDDistrictCode","SiteId"]]
    out_df = pd.merge(in_df, place_df, on="SiteName", how="inner")
    return out_df

  # Generates air quality sites CSV from the feed.
  def generate_sites(self, in_df: pd.DataFrame, sites: pd.DataFrame, \
    lgd_df: pd.DataFrame) -> pd.DataFrame:
    lgd_df = lgd_df[["DistrictDCID","LGDDistrictCode"]]
    site_df = in_df[["SiteName","Latitude","Longitude","City","State","Country"]].copy()
    # Perform place resolution only for new sites.
    site_df = site_df[~site_df.SiteName.isin(sites.SiteName)]
    if not site_df.empty:
      logging.info("Performing place resolution for %d entities", site_df.shape[0])
      site_df["WikiDataId"] = site_df.apply(self.__get_place_id, axis=1)
      # Merge site data with LGD data to fetch LGD code for each station.
      site_df = pd.merge(site_df, lgd_df,
        left_on="WikiDataId", right_on="DistrictDCID", how="left")
      site_df.dropna(subset=["LGDDistrictCode"], inplace=True)
      site_df["LGDDistrictCode"] = site_df["LGDDistrictCode"].astype(int).astype(str)
      site_df = site_df.assign(
        Coordinates = lambda x : "[LatLong " + x.Latitude.astype(str) + \
        " " + x.Longitude.astype(str) + "]") 
      site_df = site_df.assign(
        Station = site_df["SiteName"].str.split(",").str[0])
      site_df["Station"] = site_df["Station"].apply(self.__cleanup_name)
      site_df["City"] = site_df["City"].apply(self.__cleanup_name)
      site_df = site_df.assign(
        SiteId = lambda x : "cpcbAq/" +  x.LGDDistrictCode + \
        "_" + x.Station + "_" + x.City)
      site_df.drop_duplicates(subset=["SiteId"],keep = False, inplace=True)
      site_df.drop(columns = ["Latitude","Longitude", "Station","WikiDataId"], inplace=True)
      site_df = pd.concat([sites, site_df])
      return site_df
    return sites

  # Generates template MCF corresponding to air quality pollutant data.
  def generate_mcf(self, out_file: str):
    tmcf_template = (
      "Node: E:{filename}->E{index}\n"
      "typeOf: dcs:StatVarObservation\n"
      "variableMeasured: dcs:{statvar}\n"
      "observationAbout: C:{filename}->SiteId\n"
      "observationDate: C:{filename}->LastUpdate\n"
      "observationPeriod: P1H\n"
      "value: C:{filename}->{value}\n")

    with open(out_file, "w", encoding="utf-8") as tmcf_f:
      index = 1
      for key, value in POLLUTANTS.items():
        for stats in STATS:
          format_dict = {
            "filename": DATA_FILE,
            "statvar": stats + "_Concentration_AirPollutant_" + key,
            "value" : value + "_" + stats,
            "index": index,
            }
          tmcf_f.write(tmcf_template.format_map(format_dict))
          tmcf_f.write("\n")
          index += 1

      index += 1
      format_dict = {
        "filename": DATA_FILE,
        "statvar": "AirQualityIndex_AirPollutant",
        "value" : "AQI",
        "index": index,
      }
      tmcf_f.write(tmcf_template.format_map(format_dict))
      tmcf_f.write("\n")

def main(_):
  """Runs the code."""
  loader = IndiaAirQualityDataLoader()
  logging.info("Loading data from source...")
  in_df = loader.get_feed(FLAGS.dataFile)
  logging.info("Generting sites data...")
  lgd_df = pd.read_csv(LGD_FILE)
  sites_file = FLAGS.sitesFile
  if FLAGS.sitesFile.startswith("gs://"):
    sites_file = loader.download_gcs_file(
      FLAGS.sitesFile, FLAGS.sitesFile.split("/")[3])
  sites = pd.read_csv(sites_file)
  site_df = loader.generate_sites(in_df, sites, lgd_df)
  site_df.to_csv(sites_file, index=False)
  if FLAGS.sitesFile.startswith("gs://"):
    loader.upload_gcs_file(FLAGS.sitesFile, sites_file)
  logging.info("Processing air quality data...")
  result = loader.process_data(in_df, site_df)
  result.to_csv(DATA_FILE + ".csv", index=False)
  logging.info("Generating tmcf file...")
  loader.generate_mcf(DATA_FILE + ".tmcf")

if __name__ == "__main__":
  app.run(main)
