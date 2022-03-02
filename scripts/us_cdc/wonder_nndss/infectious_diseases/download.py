"""
Utility to download Nationally Notifiable Infectious Diseases and Conditions, United States: Annual Tables
from 2016-2019
"""
import os
import requests

_BASE_URL = "https://wonder.cdc.gov/"
_ANNUAL_TABLE_STR = "/nndss/static/{year}/annual/{year}-table{table_id}.txt"
_YEARS = [2016, 2017, 2018, 2019]
_TABLE_ID = ['4', '5', '6', '7', '8']


def download_file(url, local_filename):
	# NOTE the stream=True parameter below
	try:
		with requests.get(url, stream=True) as r:
			r.raise_for_status()
			with open(local_filename, 'wb') as f:
				for chunk in r.iter_content(chunk_size=8192): 
					# If you have chunk encoded response uncomment if
					# and set chunk_size parameter to None.
					#if chunk: 
					f.write(chunk)
		return local_filename
	except:
		print("skipping, since the URL does not exist", end="......", flush=True)	
    
for year in _YEARS:
	output_dir_path = f'data/{year}'
	if not os.path.exists(output_dir_path):
		os.makedirs(output_dir_path, exist_ok=True)
	for table in _TABLE_ID:
		file_url = _ANNUAL_TABLE_STR.format(year=year, table_id=table)
		file_url = _BASE_URL + file_url
		filename = file_url.split('/')[-1]
		file_path = os.path.join(output_dir_path, filename)
		print(f"Downloading { filename }", end="........", flush=True)
		download_file(file_url, file_path)
		print("Done.", flush=True)
		 

