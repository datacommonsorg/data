import requests
import pandas as pd
import os
from absl import app
from absl import logging
from absl import flags

input_file = 'input_file'
# Create the input file if it doesn't exist
if not os.path.exists(input_file):
    os.makedirs(input_file)
file_path = os.path.join(input_file, 'monthly_retail.xlsx')

monthly_response = requests.get("https://www.census.gov/retail/mrts/www/mrtssales92-present.xlsx")
if monthly_response.status_code == 200:
    with open(file_path, 'wb') as f:
        f.write(monthly_response.content)
    logging.info(f"Successfully downloaded 'monthly_retail.xlsx' to '{input_file}'")
else:
    logging.fatal(f"Failed to download file. Status code: {monthly_response.status_code}")

