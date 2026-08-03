import csv
import json
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

COUNTIES_API = "https://services.arcgis.com/XG15cJAlne2vxtgt/arcgis/rest/services/National_Risk_Index_Counties/FeatureServer/0/query"
TRACTS_API = "https://services.arcgis.com/XG15cJAlne2vxtgt/arcgis/rest/services/National_Risk_Index_Census_Tracts/FeatureServer/0/query"
DEST_DIR = "source_data"


def get_retry_session():
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


def download_dataset(session, api_url, output_csv_name):
    print(f"Downloading from {api_url} to {output_csv_name}...")
    offset = 0
    record_count = 2000  # Fetch in batches of 2000
    headers = []
    
    csv_path = os.path.join(DEST_DIR, output_csv_name)
    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = None
        
        while True:
            params = {
                "where": "1=1",
                "outFields": "*",
                "resultOffset": offset,
                "resultRecordCount": record_count,
                "orderByFields": "OBJECTID ASC",
                "returnGeometry": "false",  # Exclude heavy map geometry coordinates
                "f": "json"
            }
            response = session.get(api_url, params=params, timeout=120)
            response.raise_for_status()
            data = response.json()
            
            features = data.get("features", [])
            if not features:
                break
                
            if not writer:
                # Extract the attribute field names as CSV headers
                headers = list(features[0]["attributes"].keys())
                writer = csv.DictWriter(csvfile, fieldnames=headers, extrasaction="ignore")
                writer.writeheader()
                
            for feature in features:
                writer.writerow(feature["attributes"])
                
            print(f"  Retrieved {offset + len(features)} records...")
            if len(features) < record_count:
                break
            offset += record_count

os.makedirs(DEST_DIR, exist_ok=True)
session = get_retry_session()
download_dataset(session, COUNTIES_API, "NRI_Table_Counties.csv")
download_dataset(session, TRACTS_API, "NRI_Table_CensusTracts.csv")
print("All downloads completed successfully.")
