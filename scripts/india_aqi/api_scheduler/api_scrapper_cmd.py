import os
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import argparse
import warnings
warnings.filterwarnings("ignore")

parser = argparse.ArgumentParser()
parser.add_argument('--file_path', type=str, help='Destination of scraped data')
args = parser.parse_args()

api_key = "579b464db66ec23bdd000001dba3bb59f1864f427ba7b1a27c210d9d"
file_format = "json"
limit = 4000
url = f"https://api.data.gov.in/resource/3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69?api-key={api_key}&format={file_format}&limit={limit}"
headers = {
    "Authorization": api_key.strip(),
    'Access-Control-Allow-Origin': "*"
}

response = requests.get(url, headers=headers)
response_str = response.content.decode('utf-8')

with open('data.json', 'w') as f:
    f.write(response_str)
with open('data.json', 'r') as f:
    data = json.load(f)

df = pd.json_normalize(data['records'])
data_columns = ["pollutant_min", "pollutant_max", "pollutant_avg", "pollutant_unit"]
df[data_columns] = df[data_columns].replace(['NA'], np.nan)
df['pollutant_id'] = df['pollutant_id'].replace(['OZONE'], 'O3')
df_full = df.pivot_table(index=['city', 'station', 'state', 'last_update'],
                         columns='pollutant_id',
                         values='pollutant_avg',
                         aggfunc='first').reset_index()
desired_order = ['city', 'station', 'state', 'PM2.5', 'PM10', 'NO2', 'NH3', 'SO2', 'CO', 'O3', 'last_update']
df_full = df_full.reindex(columns=desired_order)
df_full['last_update'] = df_full['last_update'].apply(lambda x: datetime.strptime(x, "%d-%m-%Y %H:%M:%S").strftime("%Y-%m-%dT%H:%M:%S"))
df_full = df_full.rename(columns={'PM2.5': 'PM25', 'last_update': 'Date'})

dcid_json_path =  'dcid_output.json'
with open(dcid_json_path, 'r') as site_dcid_json:
    site_dcid_map = json.load(site_dcid_json)

df_full['dcid'] = df_full['station'].map(site_dcid_map)
df_full = df_full[~df_full['dcid'].isna()]

current_date_folder = datetime.now().strftime("%Y-%m-%d")
current_date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
csv_file_path = os.path.join(args.file_path, current_date_folder)
if not os.path.exists(csv_file_path):
    os.mkdir(csv_file_path)

df_full.to_csv(os.path.join(csv_file_path,f"{current_date}.csv"), index=False)
